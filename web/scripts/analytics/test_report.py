import unittest

import report
from report import Metric, Section


class RenderReport(unittest.TestCase):
    def _sample(self):
        return report.render_report(
            month="2026-08",
            sections=[
                Section("Reach (Umami)", [Metric("Pageviews", "1,204", "Umami")]),
                Section("Channel & engagement (GA4)", [
                    Metric("Engaged sessions", "312", "GA4"),
                    Metric("Pages / session", "1.4", "GA4", note="goal > 2.0"),
                ]),
                Section("Search demand (GSC)", [
                    Metric("Impressions", "567", "GSC"),
                    Metric("Average position", "23.3", "GSC",
                           note="impression-weighted; unstable at low volume"),
                ]),
                Section("Flagged / pending", [
                    Metric("whatsapp_click", "pending", "Umami",
                           note="pre-GA4 window — no GA4 counterpart"),
                ]),
            ],
            caveats=["Umami bot filtering (A6) not confirmed live — counts may be bot-inflated."],
        )

    def test_every_row_names_its_source(self):
        md = self._sample()
        self.assertIn("| Source |", md)
        self.assertIn("Umami", md)
        self.assertIn("GA4", md)
        self.assertIn("GSC", md)

    def test_section_titles_are_rendered(self):
        md = self._sample()
        self.assertIn("## Reach (Umami)", md)
        self.assertIn("## Search demand (GSC)", md)

    def test_flagged_section_is_present_and_not_zero_filled(self):
        md = self._sample()
        self.assertIn("Flagged / pending", md)
        self.assertIn("no GA4 counterpart", md)
        self.assertNotIn("| whatsapp_click | 0 |", md)  # flagged, never zero-filled

    def test_caveat_rendered(self):
        self.assertIn("bot-inflated", self._sample())

    def test_empty_section_renders_none_placeholder(self):
        md = report.render_report("2026-08", [Section("Empty", [])], [])
        self.assertIn("_(none)_", md)

    def test_empty_source_is_refused(self):
        with self.assertRaises(ValueError):
            report.render_report(
                month="2026-08",
                sections=[Section("Reach (Umami)", [Metric("Pageviews", "1,204", "")])],
                caveats=[],
            )

    def test_rolling_readouts_block_is_always_emitted(self):
        # Regression guard: a prior regeneration silently deleted this
        # hand-appended section (F-fold, commit 2fb04df). It is now a
        # module-level constant that render_report emits on every call, so
        # it can never again be dropped by a regeneration.
        md = self._sample()
        self.assertIn("## Rolling readouts (standing cadence — traffic-gated)", md)
        for readout_id in ("E3", "E8", "C3b", "D6b"):
            self.assertIn(f"| {readout_id} |", md)


class DeltaColumn(unittest.TestCase):
    """The delta column is always rendered, and always says something. A blank
    cell is indistinguishable from "no change"; an em-dash is not.
    """

    def test_the_delta_column_header_is_rendered(self):
        md = report.render_report(
            "2026-09",
            [Section("Reach (Umami)", [Metric("Pageviews", "1,204", "Umami")])],
            [],
        )
        self.assertIn("Δ vs prior month", md)

    def test_a_delta_value_is_rendered_in_its_cell(self):
        m = Metric("Pageviews", "1,204", "Umami")
        m.delta = "+204 (+20.4%)"
        md = report.render_report("2026-09", [Section("Reach (Umami)", [m])], [])
        self.assertIn("+204 (+20.4%)", md)

    def test_a_refusal_is_rendered_verbatim_never_as_a_zero(self):
        m = Metric("cv_download", "pending", "GA4")
        m.delta = "n/a — no 2026-08 in history"
        md = report.render_report("2026-09", [Section("Conversions", [m])], [])
        self.assertIn("n/a — no 2026-08 in history", md)
        self.assertNotIn("| cv_download | pending | 0 |", md)

    def test_an_unstamped_delta_renders_a_dash_not_an_empty_cell(self):
        md = report.render_report(
            "2026-09",
            [Section("Reach (Umami)", [Metric("Pageviews", "1,204", "Umami")])],
            [],
        )
        self.assertIn("| Pageviews | 1,204 | — | Umami |", md)
