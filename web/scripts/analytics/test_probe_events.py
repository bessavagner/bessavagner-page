import unittest

import probe_events
from report import Metric


class Verdict(unittest.TestCase):
    """A0's gate. The probe is run AFTER firing all four events by hand in a
    clean prod session, so a missing event means a broken binding — not low
    volume. That is what lets a partial result be a real finding.
    """

    def test_all_four_reported_confirms_the_pipeline_delivers(self):
        reported = [
            Metric("cv_download", "2", "GA4"),
            Metric("whatsapp_click", "1", "GA4"),
            Metric("generate_lead", "1", "GA4"),
            Metric("newsletter_signup", "1", "GA4"),
        ]
        status, why = probe_events.verdict(reported, [])
        self.assertEqual(status, probe_events.CONFIRMS)
        self.assertIn("delivers", why)

    def test_no_rows_at_all_refutes_and_says_stop(self):
        status, why = probe_events.verdict(
            [], ["cv_download", "whatsapp_click", "generate_lead", "newsletter_signup"]
        )
        self.assertEqual(status, probe_events.REFUTES)
        self.assertIn("STOP", why)
        self.assertIn("re-plan", why)

    def test_some_reported_some_not_is_partial_and_names_the_missing(self):
        status, why = probe_events.verdict(
            [Metric("cv_download", "2", "GA4")],
            ["whatsapp_click", "newsletter_signup"],
        )
        self.assertEqual(status, probe_events.PARTIAL)
        self.assertIn("whatsapp_click", why)
        self.assertIn("newsletter_signup", why)
        self.assertNotIn("cv_download", why)

    def test_a_reported_zero_is_still_a_reported_event(self):
        # GA4 returning a row with count 0 is a MEASURED zero — the pipeline
        # delivered. Only the absence of a row is an absence (ctx 05 section 1).
        status, _ = probe_events.verdict([Metric("cv_download", "0", "GA4")], [])
        self.assertEqual(status, probe_events.CONFIRMS)


if __name__ == "__main__":
    unittest.main()
