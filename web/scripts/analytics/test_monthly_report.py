import pathlib
import unittest
from datetime import date

import monthly_report as mr
from report import Metric, Section
from window import Window

JULY = Window(date(2026, 7, 1), date(2026, 7, 31))


class PartialMonthCaveat(unittest.TestCase):
    """A month that has not finished must SAY so. Without it, a comparison
    against a full prior month reads as a traffic collapse when it is really
    just fewer elapsed days.
    """

    def test_a_month_still_running_is_flagged_partial(self):
        c = mr.partial_month_caveat("2026-07", JULY, today=date(2026, 7, 20))
        self.assertIsNotNone(c)
        self.assertIn("partial month", c)
        self.assertIn("2026-07-20", c)

    def test_a_finished_month_gets_no_partial_caveat(self):
        self.assertIsNone(mr.partial_month_caveat("2026-07", JULY, today=date(2026, 8, 3)))

    def test_the_final_day_of_the_month_still_counts_as_partial(self):
        # The month's last day has not ELAPSED until it is over.
        self.assertIsNotNone(mr.partial_month_caveat("2026-07", JULY, today=date(2026, 7, 31)))


class Ga4ClampCaveat(unittest.TestCase):
    def test_a_clamped_ga4_window_is_declared(self):
        cmp_w = Window(date(2026, 7, 10), date(2026, 7, 31))
        c = mr.ga4_clamp_caveat(JULY, cmp_w)
        self.assertIsNotNone(c)
        self.assertIn("2026-07-10", c)

    def test_an_unclamped_window_says_nothing(self):
        self.assertIsNone(mr.ga4_clamp_caveat(JULY, Window(date(2026, 7, 1), date(2026, 7, 31))))


class NoGa4WindowFlags(unittest.TestCase):
    """A month predating the GA4 install must FLAG, never zero."""

    def test_the_orphaned_month_is_flagged_not_zeroed(self):
        flags = mr.no_ga4_window_flags("2026-05", "2026-06-28")
        self.assertEqual(len(flags), 1)
        self.assertNotEqual(flags[0].value, "0")
        self.assertEqual(flags[0].value, "pending")
        self.assertIn("predates GA4 install", flags[0].note)
        self.assertEqual(flags[0].source, "GA4")


class GscLaneBranches(unittest.TestCase):
    """'No GSC data' must never read as 'no search demand'. They are different
    claims and only one of them is true.
    """

    def test_no_gsc_data_flags_both_lanes_as_pending(self):
        flags = mr.no_gsc_data_flags("2026-07")
        self.assertEqual([f.value for f in flags], ["pending", "pending"])
        self.assertFalse(any(f.value == "0" for f in flags))
        for f in flags:
            self.assertIn("not a measured zero", f.note)

    def test_a_short_gsc_coverage_window_is_declared(self):
        cov = Window(date(2026, 7, 1), date(2026, 7, 29))  # ~2-day reporting lag
        c = mr.gsc_coverage_caveat("2026-07", JULY, cov)
        self.assertIsNotNone(c)
        self.assertIn("2026-07-29", c)
        self.assertIn("not fully measured", c)

    def test_full_gsc_coverage_says_nothing(self):
        self.assertIsNone(mr.gsc_coverage_caveat("2026-07", JULY, JULY))


class SectionAssembly(unittest.TestCase):
    """WHICH section a metric lands in is load-bearing: history.is_void and
    deltas.STABLE_KEY_SECTIONS both key off these exact titles. Renaming one
    silently disables a refusal rule.
    """

    def _assemble(self):
        return mr.assemble_sections(
            reach=[Metric("cv_download (raw event count)", "4", "Umami")],
            channel=[Metric("Organic Social — sessions", "12", "GA4")],
            conversions_section=[Metric("whatsapp_click", "2", "GA4")],
            gsc_totals=[Metric("Clicks", "3", "GSC")],
            gsc_queries=[Metric("some query", "8 impr", "GSC")],
            gsc_pages=[Metric("/blog/x", "8 impr", "GSC")],
            gsc_pinned=[Metric("/ — impressions", "30", "GSC")],
            gsc_countries=[Metric("BRA", "8 impr", "GSC")],
            indexation=[Metric("/blog/x", "Submitted and indexed", "GSC")],
            indexation_verdict=[Metric("Posts indexed", "1", "GSC")],
            flagged=[Metric("cv_download", "no GA4 events in window", "GA4")],
        )

    def test_the_section_titles_are_exactly_the_contract(self):
        self.assertEqual(
            [s.title for s in self._assemble()],
            [
                "Reach (Umami)",
                "Channel & engagement (GA4)",
                "Conversions",
                "Search demand — totals (GSC)",
                "Top queries (GSC)",
                "Top pages (GSC)",
                "Pinned pages (GSC)",
                "Top countries (GSC)",
                "Indexation (GSC)",
                "Indexation verdict (GSC)",
                "Flagged / pending (no counterpart or traffic-gated)",
            ],
        )

    def test_each_metric_lands_in_its_own_section(self):
        by_title = {s.title: s.metrics for s in self._assemble()}
        self.assertEqual(by_title["Conversions"][0].name, "whatsapp_click")
        self.assertEqual(by_title["Reach (Umami)"][0].source, "Umami")
        self.assertEqual(
            by_title["Flagged / pending (no counterpart or traffic-gated)"][0].value,
            "no GA4 events in window",
        )


class PinnedPagesAreDeltaEligibleAndSurviveTheTop10(unittest.TestCase):
    """The two halves of the trap, asserted together: a pinned row must be in a
    stable-key section AND carry a numeric value. Miss either and the delta
    engine refuses it forever, silently — which is exactly the blind spot the
    watchlist was built to close.
    """

    def test_the_pinned_section_is_in_stable_key_sections(self):
        import deltas
        self.assertIn("Pinned pages (GSC)", deltas.STABLE_KEY_SECTIONS)

    def test_the_top_pages_table_is_still_refused(self):
        import deltas
        self.assertNotIn("Top pages (GSC)", deltas.STABLE_KEY_SECTIONS)

    def test_a_pinned_row_deltas_end_to_end_against_a_stored_prior_month(self):
        import deltas
        import history
        import pinned
        from window import Window

        july_w = Window(date(2026, 7, 1), date(2026, 7, 31))
        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        home = "/"

        july_rows = history.rows_from_sections(
            "2026-07", july_w,
            [Section("Pinned pages (GSC)",
                     pinned.pinned_metrics(
                         [{"keys": [f"https://bessavagner.com{home}"], "clicks": 0,
                           "impressions": 30, "ctr": 0.0, "position": 7.8}],
                         paths=(home,)))],
            partial=False,
        )

        august = [Section("Pinned pages (GSC)", pinned.pinned_metrics(
            [{"keys": [f"https://bessavagner.com{home}"], "clicks": 2,
              "impressions": 34, "ctr": 0.0588, "position": 6.0}],
            paths=(home,)))]
        deltas.attach_deltas(august, "2026-08", august_w, july_rows, partial=False)

        by_name = {m.name: m.delta for m in august[0].metrics}
        self.assertEqual(by_name[f"{home} — impressions"], "+4 (+13.3%)")
        self.assertEqual(by_name[f"{home} — clicks"], "+2 (prior 0 — no percent change)")
        self.assertTrue(by_name[f"{home} — position"].startswith("-1.8"))

    def test_a_pinned_page_absent_in_august_refuses_rather_than_reading_as_zero(self):
        # The page fell out of GSC's response entirely. It did NOT go to zero
        # impressions — and the delta must say so instead of printing -30.
        import deltas
        import history
        import pinned
        from window import Window

        july_w = Window(date(2026, 7, 1), date(2026, 7, 31))
        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        home = "/"

        july_rows = history.rows_from_sections(
            "2026-07", july_w,
            [Section("Pinned pages (GSC)", pinned.pinned_metrics(
                [{"keys": [f"https://bessavagner.com{home}"], "clicks": 0,
                  "impressions": 30, "ctr": 0.0, "position": 7.8}],
                paths=(home,)))],
            partial=False,
        )

        august = [Section("Pinned pages (GSC)", pinned.pinned_metrics([], paths=(home,)))]
        deltas.attach_deltas(august, "2026-08", august_w, july_rows, partial=False)

        impressions = [m for m in august[0].metrics if m.name.endswith("impressions")][0]
        self.assertEqual(impressions.value, "pending")
        self.assertEqual(impressions.delta, "n/a — non-numeric value")
        self.assertNotIn("-30", impressions.delta)


class IndexationVerdictIsDeltaEligible(unittest.TestCase):
    """The count must NOT live in `Indexation (GSC)`: that section's keys are
    URLs, they churn monthly, and delta rule 5 refuses it by name. A count is a
    stable series and needs its own section — forget this and the verdict
    renders once and never trends, which is the entire regression-watch this
    story exists to build.
    """

    def test_the_verdict_section_is_in_stable_key_sections(self):
        import deltas
        self.assertIn("Indexation verdict (GSC)", deltas.STABLE_KEY_SECTIONS)

    def test_the_per_url_table_is_still_refused(self):
        import deltas
        self.assertNotIn("Indexation (GSC)", deltas.STABLE_KEY_SECTIONS)


class NoSilentZeroAnywhere(unittest.TestCase):
    """The regression guard the sprint DoD asks for by name: a refactor that
    reintroduces seen.get(n, "0") at ANY call site must turn this suite red.

    A unit test cannot reach a call site that does not exist yet, so this one
    reads the source. Crude, and exactly proportionate to a bug that has already
    voided four months of conversion data once.

    It looks for a STRING zero default — `.get(n, "0")` — and deliberately not an
    int one. Metric.value is a str, so the bug always wears string clothes; and
    an int default is legitimately used to sum a JSON payload's counters
    (gsc.py's sitemap `c.get("submitted", 0)`), which has nothing to do with a
    metric GA4 never reported.
    """

    def test_no_module_zero_fills_a_missing_ga4_event(self):
        here = pathlib.Path(__file__).parent
        offenders = []
        for py in sorted(here.glob("*.py")):
            if py.name.startswith("test_"):
                continue
            src = py.read_text(encoding="utf-8")
            for lineno, line in enumerate(src.splitlines(), 1):
                code = line.split("#", 1)[0]
                if ".get(" in code and ('"0"' in code or "'0'" in code):
                    offenders.append(f"{py.name}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "a default-to-zero lookup reappeared — GA4 returns NO ROW for an "
            "event it never received, and that absence must be flagged, never "
            "rendered as a measured 0 (ctx 05 section 1):\n" + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
