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


class ReachLaneGuard(unittest.TestCase):
    """Fix B. `umami.count_event` is `sum(1 for r in rows if ...)`, and
    `sum([])` is 0 — a header-only, truncated, or wrong-date-range export
    parses cleanly, yields zero rows, and every reach row used to render a
    bare "0" (numeric, delta-eligible) purely because a file was empty,
    fabricating a -100% collapse on every conversion channel at once. The
    fix guards ONCE, at the lane, on "any row of ANY kind in the window" —
    NOT "any row of a conversion type", so a genuinely quiet month for one
    event must still render a true bare "0".
    """

    def test_an_export_with_no_rows_in_the_window_renders_every_reach_row_pending(self):
        reach = mr.build_reach([], JULY)
        self.assertEqual(len(reach), 4)
        for m in reach:
            self.assertEqual(m.value, "pending")
            self.assertNotEqual(m.value, "0")
            self.assertIn("does not cover the month", m.note)
            self.assertIn("not a measured 0", m.note)

    def test_real_traffic_with_a_genuine_zero_on_one_event_still_renders_bare_zero(self):
        # Pageviews + some conversions inside the window, but zero
        # whatsapp_click. The lane WAS measured (there is traffic), so this
        # true zero must stay bare-numeric, not become "pending".
        rows = [
            {"event_type": "1", "event_name": "", "created_at": "2026-07-01T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-07-02T10:00:00Z"},
            {"event_type": "2", "event_name": "generate_lead", "created_at": "2026-07-03T10:00:00Z"},
            {"event_type": "2", "event_name": "newsletter_signup", "created_at": "2026-07-04T10:00:00Z"},
        ]
        reach = mr.build_reach(rows, JULY)
        by_name = {m.name: m for m in reach}
        self.assertEqual(by_name["cv_download (raw event count)"].value, "1")
        self.assertEqual(by_name["whatsapp_click (raw event count)"].value, "0")
        self.assertEqual(by_name["generate_lead (raw event count)"].value, "1")
        self.assertEqual(by_name["newsletter_signup (raw event count)"].value, "1")

    def test_a_zero_row_window_refuses_the_delta_instead_of_fabricating_a_collapse(self):
        # End to end: history.rows_from_sections -> deltas.attach_deltas.
        # Before the fix this would have computed "-4 (-100.0%)" etc. against
        # a real prior month for every conversion channel.
        import deltas
        import history
        from report import Section

        june_w = Window(date(2026, 6, 1), date(2026, 6, 30))

        june_rows_raw = [
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-01T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-02T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-03T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-04T10:00:00Z"},
        ]
        june_rows = history.rows_from_sections(
            "2026-06", june_w,
            [Section("Reach (Umami)", mr.build_reach(june_rows_raw, june_w))],
            partial=False,
        )

        july = [Section("Reach (Umami)", mr.build_reach([], JULY))]
        deltas.attach_deltas(july, "2026-07", JULY, june_rows, partial=False)

        by_name = {m.name: m for m in july[0].metrics}
        cv = by_name["cv_download (raw event count)"]
        self.assertEqual(cv.value, "pending")
        self.assertEqual(cv.delta, "n/a — non-numeric value")
        self.assertNotIn("-4", cv.delta)
        self.assertNotIn("-100", cv.delta)

    def test_a_measured_lane_still_deltas_normally(self):
        # The clean path must not regress: real traffic in both months,
        # a real change on one event, still produces a real delta.
        import deltas
        import history
        from report import Section

        june_w = Window(date(2026, 6, 1), date(2026, 6, 30))

        june_rows_raw = [
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-01T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-06-02T10:00:00Z"},
        ]
        june_rows = history.rows_from_sections(
            "2026-06", june_w,
            [Section("Reach (Umami)", mr.build_reach(june_rows_raw, june_w))],
            partial=False,
        )

        july_rows_raw = [
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-07-01T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-07-02T10:00:00Z"},
            {"event_type": "2", "event_name": "cv_download", "created_at": "2026-07-03T10:00:00Z"},
        ]
        july = [Section("Reach (Umami)", mr.build_reach(july_rows_raw, JULY))]
        deltas.attach_deltas(july, "2026-07", JULY, june_rows, partial=False)

        by_name = {m.name: m for m in july[0].metrics}
        cv = by_name["cv_download (raw event count)"]
        self.assertEqual(cv.value, "3")
        self.assertEqual(cv.delta, "+1 (+50.0%)")


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
            sitemap=[Metric("/sitemap-index.xml — URLs submitted", "77", "GSC")],
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
                "Sitemap health (GSC)",
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
            partial=False, gsc_cov=july_w,
        )

        august = [Section("Pinned pages (GSC)", pinned.pinned_metrics(
            [{"keys": [f"https://bessavagner.com{home}"], "clicks": 2,
              "impressions": 34, "ctr": 0.0588, "position": 6.0}],
            paths=(home,)))]
        # Equal-length (31d/31d) coverage windows — this test is not about rule
        # 6, so it must not trip the unequal/unknown-window refusal.
        deltas.attach_deltas(august, "2026-08", august_w, july_rows, partial=False, gsc_cov=august_w)

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
            partial=False, gsc_cov=july_w,
        )

        august = [Section("Pinned pages (GSC)", pinned.pinned_metrics([], paths=(home,)))]
        # Equal-length (31d/31d) coverage windows — this test is about the
        # non-numeric refusal, not rule 6's unequal/unknown-window refusal.
        deltas.attach_deltas(august, "2026-08", august_w, july_rows, partial=False, gsc_cov=august_w)

        impressions = [m for m in august[0].metrics if m.name.endswith("impressions")][0]
        self.assertEqual(impressions.value, "pending")
        self.assertEqual(impressions.delta, "n/a — non-numeric value")
        self.assertNotIn("-30", impressions.delta)


class SitemapNeverDownloadedRefusesRatherThanFabricatingADelta(unittest.TestCase):
    """Regression for the fabricated-delta bug: `URLs submitted` used to be
    appended unconditionally, so a never-downloaded sitemap rendered a bare
    "0" — and the delta engine, seeing two consecutive "0"s, printed a real
    "+0 (prior 0 — no percent change)" asserting a flat measurement that never
    happened. Follows the same store-then-delta shape as
    PinnedPagesAreDeltaEligibleAndSurviveTheTop10 above, against
    `Sitemap health (GSC)` (already a stable-key section) instead of pinned
    pages.
    """

    def test_a_never_downloaded_sitemap_across_two_months_refuses_the_urls_submitted_delta(self):
        import deltas
        import gsc
        import history
        from window import Window

        july_w = Window(date(2026, 7, 1), date(2026, 7, 31))
        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        sitemap_url = "https://bessavagner.com/sitemap-index.xml"

        def never_downloaded(today):
            return gsc.sitemap_freshness_metrics(
                [{"path": sitemap_url, "lastDownloaded": "", "submitted": 0}],
                today=today,
            )

        july_rows = history.rows_from_sections(
            "2026-07", july_w,
            [Section("Sitemap health (GSC)", never_downloaded(date(2026, 7, 31)))],
            partial=False, gsc_cov=july_w,
        )

        august = [Section(
            "Sitemap health (GSC)", never_downloaded(date(2026, 8, 9)),
        )]
        # Equal-length (31d/31d) coverage windows — this test is about the
        # non-numeric refusal, not rule 6's unequal/unknown-window refusal.
        deltas.attach_deltas(august, "2026-08", august_w, july_rows, partial=False, gsc_cov=august_w)

        by_name = {m.name: m for m in august[0].metrics}
        submitted = by_name[f"{sitemap_url} — URLs submitted"]
        self.assertEqual(submitted.value, "pending")
        self.assertEqual(submitted.delta, "n/a — non-numeric value")
        self.assertNotIn("+0", submitted.delta)


class IndexationVerdictIsDeltaEligible(unittest.TestCase):
    """The count must NOT live in `Indexation (GSC)`: that section's keys are
    URLs, they churn monthly, and delta rule 5 refuses it by name. A count is a
    stable series and needs its own section — forget this and the verdict
    renders once and never trends, which is the entire regression-watch this
    story exists to build.
    """

    # August (31d) and September (30d) are different calendar lengths, so a
    # real per-month GSC coverage window would trip rule 6 here — these tests
    # are about the OTHER refusal paths, so both sides share one synthetic,
    # equal-length (30d) coverage window instead.
    _COV = Window(date(2026, 1, 1), date(2026, 1, 30))

    def test_the_verdict_section_is_in_stable_key_sections(self):
        import deltas
        self.assertIn("Indexation verdict (GSC)", deltas.STABLE_KEY_SECTIONS)

    def test_the_per_url_table_is_still_refused(self):
        import deltas
        self.assertNotIn("Indexation (GSC)", deltas.STABLE_KEY_SECTIONS)

    def test_a_zero_publish_month_refuses_the_delta_instead_of_fabricating_deindexation(self):
        # Regression for the critical bug: an EMPTY index_rows month used to
        # render "0" — numeric, and delta-eligible, in a stable-key section.
        # Against a real prior count that "0" computed a genuine-looking
        # "-3 (-100.0%)": a claim that Google deindexed every post, in a month
        # where not one URL was inspected because none was published. Follows
        # the same store-then-delta shape as
        # PinnedPagesAreDeltaEligibleAndSurviveTheTop10 above.
        import deltas
        import history
        import indexation

        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        september_w = Window(date(2026, 9, 1), date(2026, 9, 30))

        august_index_rows = [
            Metric("/a/", "Submitted and indexed", "GSC"),
            Metric("/b/", "Submitted and indexed", "GSC"),
            Metric("/c/", "Submitted and indexed", "GSC"),
        ]
        august_rows = history.rows_from_sections(
            "2026-08", august_w,
            [Section("Indexation verdict (GSC)", indexation.verdict_metrics(august_index_rows))],
            partial=False, gsc_cov=self._COV,
        )

        september = [Section(
            "Indexation verdict (GSC)", indexation.verdict_metrics([]),
        )]
        deltas.attach_deltas(september, "2026-09", september_w, august_rows, partial=False, gsc_cov=self._COV)

        by_name = {m.name: m for m in september[0].metrics}
        indexed = by_name["Posts indexed"]
        self.assertEqual(indexed.value, "pending")
        self.assertEqual(indexed.delta, "n/a — non-numeric value")
        self.assertNotIn("-3", indexed.delta)
        self.assertNotIn("%", indexed.delta)

    def test_all_inspections_failing_refuses_the_delta_instead_of_fabricating_deindexation(self):
        # Fix A, case 1 from the repro: ALL 3 inspections 429'd — not one URL
        # was successfully inspected. Before the fix this rendered "0" for
        # indexed/not_indexed (bare numeric, delta-eligible) and the delta
        # engine fabricated "-3 (-100.0%)" against a real prior count — a
        # claim that Google deindexed every post in a month where nothing was
        # actually inspected.
        import deltas
        import history
        import indexation

        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        september_w = Window(date(2026, 9, 1), date(2026, 9, 30))

        august_index_rows = [
            Metric("/a/", "Submitted and indexed", "GSC"),
            Metric("/b/", "Submitted and indexed", "GSC"),
            Metric("/c/", "Submitted and indexed", "GSC"),
        ]
        august_rows = history.rows_from_sections(
            "2026-08", august_w,
            [Section("Indexation verdict (GSC)", indexation.verdict_metrics(august_index_rows))],
            partial=False, gsc_cov=self._COV,
        )

        september_index_rows = [
            Metric("/d/", "pending", "GSC", note="inspection failed (429)"),
            Metric("/e/", "pending", "GSC", note="inspection failed (429)"),
            Metric("/f/", "pending", "GSC", note="inspection failed (429)"),
        ]
        september = [Section(
            "Indexation verdict (GSC)", indexation.verdict_metrics(september_index_rows),
        )]
        deltas.attach_deltas(september, "2026-09", september_w, august_rows, partial=False, gsc_cov=self._COV)

        by_name = {m.name: m for m in september[0].metrics}
        for name in ("Posts indexed", "Posts not indexed", "Posts pending inspection"):
            self.assertEqual(by_name[name].value, "pending")
            self.assertEqual(by_name[name].delta, "n/a — non-numeric value")
            self.assertNotIn("-3", by_name[name].delta)
            self.assertNotIn("+3", by_name[name].delta)
            self.assertNotIn("%", by_name[name].delta)

    def test_partial_pending_indexed_and_not_indexed_refuse_the_delta_but_pending_still_deltas(self):
        # Fix A, case 2 from the repro: 1 of 3 inspected OK, 2 timed out —
        # the LIKELIER real case. Before the fix this rendered indexed="1"
        # (bare numeric) and the delta engine fabricated "-2 (-66.7%)" — a
        # collapse claim built on a partial, not a full, inspection.
        import deltas
        import history
        import indexation

        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        september_w = Window(date(2026, 9, 1), date(2026, 9, 30))

        august_index_rows = [
            Metric("/a/", "Submitted and indexed", "GSC"),
            Metric("/b/", "Submitted and indexed", "GSC"),
            Metric("/c/", "Submitted and indexed", "GSC"),
        ]
        august_rows = history.rows_from_sections(
            "2026-08", august_w,
            [Section("Indexation verdict (GSC)", indexation.verdict_metrics(august_index_rows))],
            partial=False, gsc_cov=self._COV,
        )

        september_index_rows = [
            Metric("/d/", "Submitted and indexed", "GSC"),
            Metric("/e/", "pending", "GSC", note="inspection failed (429)"),
            Metric("/f/", "pending", "GSC", note="inspection failed (timeout)"),
        ]
        september = [Section(
            "Indexation verdict (GSC)", indexation.verdict_metrics(september_index_rows),
        )]
        deltas.attach_deltas(september, "2026-09", september_w, august_rows, partial=False, gsc_cov=self._COV)

        by_name = {m.name: m for m in september[0].metrics}
        indexed = by_name["Posts indexed"]
        not_indexed = by_name["Posts not indexed"]
        pending = by_name["Posts pending inspection"]

        self.assertEqual(indexed.value, "1 (of 1 inspected)")
        self.assertEqual(indexed.delta, "n/a — non-numeric value")
        self.assertNotIn("-2", indexed.delta)

        self.assertEqual(not_indexed.value, "0 (of 1 inspected)")
        self.assertEqual(not_indexed.delta, "n/a — non-numeric value")

        # `pending` IS a real measurement (of the failure) — it still deltas.
        self.assertEqual(pending.value, "2")
        self.assertEqual(pending.delta, "+2 (prior 0 — no percent change)")

    def test_a_fully_inspected_month_still_deltas_normally(self):
        # The clean path (pending == 0) must NOT regress: real bare counts,
        # real deltas.
        import deltas
        import history
        import indexation

        august_w = Window(date(2026, 8, 1), date(2026, 8, 31))
        september_w = Window(date(2026, 9, 1), date(2026, 9, 30))

        august_index_rows = [
            Metric("/a/", "Submitted and indexed", "GSC"),
            Metric("/b/", "Submitted and indexed", "GSC"),
        ]
        august_rows = history.rows_from_sections(
            "2026-08", august_w,
            [Section("Indexation verdict (GSC)", indexation.verdict_metrics(august_index_rows))],
            partial=False, gsc_cov=self._COV,
        )

        september_index_rows = [
            Metric("/c/", "Submitted and indexed", "GSC"),
            Metric("/d/", "Submitted and indexed", "GSC"),
            Metric("/e/", "Crawled - currently not indexed", "GSC"),
        ]
        september = [Section(
            "Indexation verdict (GSC)", indexation.verdict_metrics(september_index_rows),
        )]
        deltas.attach_deltas(september, "2026-09", september_w, august_rows, partial=False, gsc_cov=self._COV)

        by_name = {m.name: m for m in september[0].metrics}
        self.assertEqual(by_name["Posts indexed"].value, "2")
        self.assertEqual(by_name["Posts indexed"].delta, "+0 (+0.0%)")
        self.assertEqual(by_name["Posts not indexed"].value, "1")
        self.assertEqual(by_name["Posts not indexed"].delta, "+1 (prior 0 — no percent change)")
        self.assertEqual(by_name["Posts pending inspection"].value, "0")


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
