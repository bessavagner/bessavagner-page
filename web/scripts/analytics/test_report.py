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
