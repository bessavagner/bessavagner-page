import unittest

import report
from report import Metric


class RenderReport(unittest.TestCase):
    def _sample(self):
        return report.render_report(
            month="2026-08",
            reach=[Metric("Pageviews", "1,204", "Umami")],
            channel=[Metric("Engaged sessions", "312", "GA4"),
                     Metric("Pages / session", "1.4", "GA4", note="goal > 2.0")],
            conversions=[Metric("cv_download", "5", "GA4"),
                         Metric("cv_download (raw)", "7", "Umami")],
            flagged=[Metric("whatsapp_click", "pending", "Umami",
                            note="pre-GA4 window — no GA4 counterpart")],
            caveats=["Umami bot filtering (A6) not confirmed live — counts may be bot-inflated."],
        )

    def test_every_row_names_its_source(self):
        md = self._sample()
        self.assertIn("| Source |", md)
        self.assertIn("Umami", md)
        self.assertIn("GA4", md)

    def test_flagged_section_is_present_and_not_zero_filled(self):
        md = self._sample()
        self.assertIn("Flagged / pending", md)
        self.assertIn("no GA4 counterpart", md)
        self.assertNotIn("| whatsapp_click | 0 |", md)  # flagged, never zero-filled

    def test_caveat_rendered(self):
        self.assertIn("bot-inflated", self._sample())

    def test_empty_source_is_refused(self):
        with self.assertRaises(ValueError):
            report.render_report(
                month="2026-08",
                reach=[Metric("Pageviews", "1,204", "")],
                channel=[], conversions=[], flagged=[], caveats=[],
            )
