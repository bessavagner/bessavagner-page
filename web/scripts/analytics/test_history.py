import os
import tempfile
import unittest
from datetime import date

import history
from report import Metric, Section
from window import Window

JULY = Window(date(2026, 7, 1), date(2026, 7, 31))
JUNE = Window(date(2026, 6, 1), date(2026, 6, 30))
AUGUST = Window(date(2026, 8, 1), date(2026, 8, 31))
FIX = date(2026, 7, 12)


class ParseNumeric(unittest.TestCase):
    """Empty is a FIRST-CLASS state. "pending" must never become "0" — that is
    the silent-zero bug (conversions.py's whole reason to exist) relocated into
    the store.
    """

    def test_a_plain_number_parses(self):
        self.assertEqual(history.parse_numeric("1.50"), "1.50")

    def test_an_integer_parses(self):
        self.assertEqual(history.parse_numeric("42"), "42")

    def test_a_percentage_keeps_its_number(self):
        self.assertEqual(history.parse_numeric("0.53%"), "0.53")

    def test_a_thousands_separator_is_stripped(self):
        self.assertEqual(history.parse_numeric("1,204"), "1204")

    def test_pending_is_empty_not_zero(self):
        self.assertEqual(history.parse_numeric("pending"), "")

    def test_the_no_ga4_events_sentinel_is_empty_not_zero(self):
        self.assertEqual(history.parse_numeric("no GA4 events in window"), "")

    def test_a_gsc_breakdown_row_is_empty_not_zero(self):
        # "22 impr · 0 clicks · 0.00% CTR · pos 12.3" is a composite, not a number.
        self.assertEqual(
            history.parse_numeric("22 impr · 0 clicks · 0.00% CTR · pos 12.3"), ""
        )

    def test_an_index_coverage_state_is_empty_not_zero(self):
        self.assertEqual(history.parse_numeric("Submitted and indexed"), "")

    def test_nan_and_inf_are_empty(self):
        for s in ("nan", "inf", "-inf", "NaN"):
            self.assertEqual(history.parse_numeric(s), "", s)

    def test_a_real_measured_zero_survives_as_zero(self):
        # GA4 DID return a row with count 0 — that is a MEASUREMENT and must be
        # stored as one. The rule forbids FABRICATING a zero, not recording one.
        self.assertEqual(history.parse_numeric("0"), "0")

    def test_no_non_numeric_value_ever_parses_to_zero(self):
        for s in ("pending", "no GA4 events in window", "Submitted and indexed", ""):
            self.assertNotEqual(history.parse_numeric(s), "0", s)


class IsVoid(unittest.TestCase):
    """Void = the row's window is entirely before a boundary that makes it
    structurally meaningless. Pre-07-12 GA4 conversions are VOID — not "low".
    GA4 physically could not receive those events (A0).
    """

    def test_a_ga4_conversion_row_wholly_before_the_fix_is_void(self):
        self.assertTrue(history.is_void("Conversions", "GA4", JUNE, ga4_fix_deploy=FIX))

    def test_a_ga4_conversion_row_straddling_the_fix_is_not_void(self):
        # Straddling is a caveat (boundaries.boundary_caveats), not a void row —
        # the post-fix days really were measured.
        self.assertFalse(history.is_void("Conversions", "GA4", JULY, ga4_fix_deploy=FIX))

    def test_a_umami_reach_row_before_the_fix_is_not_void(self):
        # The gtag bug never touched Umami. Umami reach is measured throughout.
        self.assertFalse(history.is_void("Reach (Umami)", "Umami", JUNE, ga4_fix_deploy=FIX))

    def test_a_gsc_row_before_the_fix_is_not_void(self):
        self.assertFalse(
            history.is_void("Search demand — totals (GSC)", "GSC", JUNE, ga4_fix_deploy=FIX)
        )

    def test_an_unstamped_boundary_voids_nothing(self):
        self.assertFalse(history.is_void("Conversions", "GA4", JUNE, ga4_fix_deploy=None))


class RowsFromSections(unittest.TestCase):
    def _sections(self):
        return [
            Section("Reach (Umami)", [Metric("cv_download (raw event count)", "4", "Umami")]),
            Section("Conversions", [Metric("whatsapp_click", "2", "GA4")]),
            Section("Flagged / pending", [
                Metric("cv_download", "no GA4 events in window", "GA4", note="not a measured 0"),
            ]),
        ]

    def test_every_metric_becomes_exactly_one_row(self):
        rows = history.rows_from_sections("2026-07", JULY, self._sections(), partial=True)
        self.assertEqual(len(rows), 3)

    def test_a_row_carries_its_month_section_source_and_note(self):
        rows = history.rows_from_sections("2026-07", JULY, self._sections(), partial=True)
        r = rows[1]
        self.assertEqual(r.month, "2026-07")
        self.assertEqual(r.section, "Conversions")
        self.assertEqual(r.name, "whatsapp_click")
        self.assertEqual(r.source, "GA4")
        self.assertEqual(r.value_raw, "2")
        self.assertEqual(r.value_num, "2")

    def test_the_flagged_sentinel_stores_an_empty_value_num(self):
        rows = history.rows_from_sections("2026-07", JULY, self._sections(), partial=True)
        flagged = [r for r in rows if r.section == "Flagged / pending"][0]
        self.assertEqual(flagged.value_raw, "no GA4 events in window")
        self.assertEqual(flagged.value_num, "")

    def test_partial_is_recorded_on_every_row(self):
        # Without this, next month cannot learn that THIS month was partial, and
        # the "never compare a partial month against a full one" rule is
        # unenforceable from history alone.
        rows = history.rows_from_sections("2026-07", JULY, self._sections(), partial=True)
        self.assertTrue(all(r.partial for r in rows))

    def test_the_key_is_month_section_name_source(self):
        rows = history.rows_from_sections("2026-07", JULY, self._sections(), partial=False)
        self.assertEqual(rows[1].key, ("2026-07", "Conversions", "whatsapp_click", "GA4"))


class StoreRoundTrip(unittest.TestCase):
    """Upsert, never append. Re-running a month REPLACES its rows and produces a
    BYTE-IDENTICAL file. An append-only store silently doubles every figure the
    second time you regenerate — and regenerating is normal.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "history", "metrics.csv")
        self.addCleanup(self.tmp.cleanup)

    def _july(self, whatsapp="2"):
        return [
            Section("Reach (Umami)", [Metric("cv_download (raw event count)", "4", "Umami")]),
            Section("Conversions", [Metric("whatsapp_click", whatsapp, "GA4")]),
            Section("Flagged / pending", [
                Metric("cv_download", "pending", "GA4", note="not a measured 0"),
            ]),
        ]

    def test_loading_a_missing_file_is_empty_not_an_error(self):
        self.assertEqual(history.load(self.path), [])

    def test_a_month_round_trips(self):
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        rows = history.load(self.path)
        self.assertEqual(len(rows), 3)
        self.assertEqual({r.month for r in rows}, {"2026-07"})

    def test_a_non_numeric_value_round_trips_as_empty_never_zero(self):
        # THE test of the sprint DoD. "pending" goes in, "" comes out — not "0".
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        pending = [r for r in history.load(self.path) if r.value_raw == "pending"][0]
        self.assertEqual(pending.value_num, "")
        self.assertNotEqual(pending.value_num, "0")

    def test_the_void_and_partial_flags_round_trip_as_booleans(self):
        history.record_month("2026-06", JUNE, self._july(), partial=False, path=self.path)
        conv = [r for r in history.load(self.path) if r.section == "Conversions"][0]
        reach = [r for r in history.load(self.path) if r.section == "Reach (Umami)"][0]
        self.assertTrue(conv.void)      # June GA4 conversions predate the 07-12 fix
        self.assertFalse(reach.void)    # Umami was never broken
        self.assertFalse(conv.partial)

    def test_rerunning_a_month_produces_a_byte_identical_file(self):
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        with open(self.path, "rb") as f:
            first = f.read()
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        with open(self.path, "rb") as f:
            second = f.read()
        self.assertEqual(first, second)

    def test_rerunning_a_month_does_not_double_its_rows(self):
        for _ in range(3):
            history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        self.assertEqual(len(history.load(self.path)), 3)

    def test_regenerating_a_month_overwrites_its_values(self):
        history.record_month("2026-07", JULY, self._july(whatsapp="2"), partial=True, path=self.path)
        history.record_month("2026-07", JULY, self._july(whatsapp="9"), partial=True, path=self.path)
        conv = [r for r in history.load(self.path) if r.name == "whatsapp_click"]
        self.assertEqual(len(conv), 1)
        self.assertEqual(conv[0].value_raw, "9")

    def test_regenerating_a_month_drops_rows_it_no_longer_emits(self):
        # A GSC row that vanishes from the regenerated report must vanish from
        # the store too — a stale row is a lie with a timestamp on it.
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        shrunk = [Section("Reach (Umami)", [Metric("cv_download (raw event count)", "4", "Umami")])]
        history.record_month("2026-07", JULY, shrunk, partial=True, path=self.path)
        self.assertEqual([r.section for r in history.load(self.path)], ["Reach (Umami)"])

    def test_writing_a_second_month_leaves_the_first_untouched(self):
        history.record_month("2026-06", JUNE, self._july(), partial=False, path=self.path)
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        months = {r.month for r in history.load(self.path)}
        self.assertEqual(months, {"2026-06", "2026-07"})

    def test_rows_are_written_in_a_stable_sorted_order(self):
        history.record_month("2026-07", JULY, self._july(), partial=True, path=self.path)
        history.record_month("2026-06", JUNE, self._july(), partial=False, path=self.path)
        rows = history.load(self.path)
        self.assertEqual([r.key for r in rows], sorted(r.key for r in rows))


class MeasuredDays(unittest.TestCase):
    """The store must record the window it ACTUALLY measured, not the calendar
    month it was asked about. GSC's coverage window is detected empirically and
    its lag is not constant, so a 29-day August against a 31-day July is a -6%
    window artifact wearing a measured decline's clothes.

    "" is the EMPTY state again, exactly as in parse_numeric: an unknown window
    is not a matching window. It must refuse, never assume.
    """

    def test_a_gsc_row_records_its_coverage_day_count(self):
        cov = Window(date(2026, 8, 1), date(2026, 8, 29))
        self.assertEqual(history.measured_days("GSC", cov), "29")

    def test_the_count_is_inclusive_of_both_endpoints(self):
        # Aug 1..Aug 31 is 31 days measured, not 30.
        cov = Window(date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(history.measured_days("GSC", cov), "31")

    def test_a_single_day_of_coverage_is_one_day(self):
        cov = Window(date(2026, 8, 1), date(2026, 8, 1))
        self.assertEqual(history.measured_days("GSC", cov), "1")

    def test_no_gsc_coverage_is_empty_not_zero(self):
        # fetch_coverage returned None: the month has no GSC data at all. That
        # is an ABSENCE of measurement. "0" here would be a fabrication with a
        # prior month waiting to divide into it.
        self.assertEqual(history.measured_days("GSC", None), "")

    def test_a_non_gsc_row_has_no_measured_window(self):
        # Rule 6 governs GSC only. Umami and GA4 have their own window bugs
        # (follow-ups C-2, C-3) and are Sprint 10's, not this rule's.
        cov = Window(date(2026, 8, 1), date(2026, 8, 29))
        self.assertEqual(history.measured_days("Umami", cov), "")
        self.assertEqual(history.measured_days("GA4", cov), "")


class RowsCarryTheMeasuredWindow(unittest.TestCase):
    def _sections(self):
        return [Section("Search demand — totals (GSC)", [
            Metric("Impressions", "128", "GSC"),
        ]), Section("Reach (Umami)", [
            Metric("cv_download (raw event count)", "4", "Umami"),
        ])]

    def test_the_gsc_row_carries_the_coverage_length(self):
        cov = Window(date(2026, 8, 1), date(2026, 8, 29))
        rows = history.rows_from_sections(
            "2026-08", AUGUST, self._sections(), partial=False, gsc_cov=cov
        )
        gsc_row = next(r for r in rows if r.source == "GSC")
        self.assertEqual(gsc_row.days_measured, "29")

    def test_the_umami_row_does_not(self):
        cov = Window(date(2026, 8, 1), date(2026, 8, 29))
        rows = history.rows_from_sections(
            "2026-08", AUGUST, self._sections(), partial=False, gsc_cov=cov
        )
        umami_row = next(r for r in rows if r.source == "Umami")
        self.assertEqual(umami_row.days_measured, "")


class LegacyRowsLoadWithoutTheColumn(unittest.TestCase):
    """A history.csv written before this column existed must still load — and
    must load as UNKNOWN, which rule 6 refuses. Back-filling it with the
    calendar length would silently re-enable the exact artifact this rule
    exists to catch.
    """

    def test_a_csv_without_days_measured_loads_as_unknown(self):
        legacy = (
            "month,section,name,value_raw,value_num,source,note,void,partial\n"
            "2026-07,Search demand — totals (GSC),Impressions,128,128,GSC,,false,false\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "metrics.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write(legacy)
            rows = history.load(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].days_measured, "")


class TheColumnSurvivesARoundTrip(unittest.TestCase):
    def test_write_then_load_preserves_days_measured(self):
        cov = Window(date(2026, 8, 1), date(2026, 8, 29))
        rows = history.rows_from_sections(
            "2026-08", AUGUST,
            [Section("Search demand — totals (GSC)", [Metric("Impressions", "128", "GSC")])],
            partial=False, gsc_cov=cov,
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "metrics.csv")
            history.write(rows, path)
            back = history.load(path)
        self.assertEqual(back[0].days_measured, "29")


if __name__ == "__main__":
    unittest.main()
