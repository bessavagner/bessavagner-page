import unittest
from datetime import date

import history
from report import Metric, Section
from window import Window

JULY = Window(date(2026, 7, 1), date(2026, 7, 31))
JUNE = Window(date(2026, 6, 1), date(2026, 6, 30))
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


if __name__ == "__main__":
    unittest.main()
