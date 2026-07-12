import unittest

import conversions
from report import Metric

PROXY = Metric("file_download (enhanced-measurement)", "3", "GA4",
               note="GA4's nearest auto-tracked download signal")
UMAMI = {"cv_download": 4, "whatsapp_click": 2, "generate_lead": 0, "newsletter_signup": 1}


class MutualExclusion(unittest.TestCase):
    """A3's cardinal rule: exactly ONE authoritative cv_download figure per source.
    The file_download proxy stands in for a cv_download GA4 never reported — the
    instant GA4 reports a real one, the proxy must fall away. Two numbers for one
    action is precisely the ambiguity this sprint kills.
    """

    def test_real_cv_download_suppresses_the_proxy(self):
        convs, flagged = conversions.build_conversions(
            reported=[Metric("cv_download", "2", "GA4")],
            missing=[],
            proxy=PROXY,
            umami_counts=UMAMI,
        )
        names = [m.name for m in convs]
        self.assertIn("cv_download", names)
        self.assertNotIn(PROXY.name, names)
        self.assertEqual(flagged, [])

    def test_absent_cv_download_keeps_the_proxy_as_the_only_download_signal(self):
        convs, flagged = conversions.build_conversions(
            reported=[], missing=["cv_download"], proxy=PROXY, umami_counts=UMAMI,
        )
        self.assertEqual([m.name for m in convs], [PROXY.name])
        self.assertEqual([m.name for m in flagged], ["cv_download"])
        self.assertIn("file_download", flagged[0].note)

    def test_the_proxy_and_the_real_event_are_never_both_emitted(self):
        # The rule, stated once, over every combination that can occur.
        for reported, missing in (
            ([Metric("cv_download", "2", "GA4")], []),
            ([], ["cv_download"]),
        ):
            for proxy in (PROXY, None):
                convs, _ = conversions.build_conversions(
                    reported, missing, proxy, UMAMI
                )
                names = [m.name for m in convs]
                self.assertFalse(
                    "cv_download" in names and PROXY.name in names,
                    f"proxy and real event emitted together: {names}",
                )

    def test_no_proxy_and_no_real_event_emits_neither_and_flags_the_absence(self):
        convs, flagged = conversions.build_conversions(
            reported=[], missing=["cv_download"], proxy=None, umami_counts=UMAMI,
        )
        self.assertEqual(convs, [])
        self.assertEqual([m.name for m in flagged], ["cv_download"])
        self.assertNotIn("file_download", flagged[0].note)


class NoSilentZero(unittest.TestCase):
    """Sprint DoD: no metric can reach Conversions as a silent 0. Marking key
    events (A1) is exactly the change that would tempt someone to zero-fill.
    """

    def test_a_missing_event_never_becomes_a_zero_in_conversions(self):
        convs, flagged = conversions.build_conversions(
            reported=[Metric("whatsapp_click", "1", "GA4")],
            missing=["cv_download", "generate_lead", "newsletter_signup"],
            proxy=None,
            umami_counts=UMAMI,
        )
        self.assertFalse(any(m.value == "0" for m in convs))
        self.assertEqual([m.name for m in convs], ["whatsapp_click"])
        self.assertEqual(len(flagged), 3)

    def test_every_flagged_event_carries_a_stated_reason(self):
        _, flagged = conversions.build_conversions(
            reported=[], missing=["generate_lead"], proxy=None, umami_counts=UMAMI,
        )
        self.assertNotEqual(flagged[0].value, "0")
        self.assertTrue(flagged[0].note)
        self.assertIn("not a measured 0", flagged[0].note)
        self.assertIn("0", flagged[0].note)  # the Umami raw count is stated

    def test_a_ga4_reported_zero_is_a_real_measured_zero_and_stays(self):
        # GA4 DID return a row with count 0 — that is a measurement, not an
        # absence, and it belongs in Conversions. The rule forbids FABRICATING a
        # zero for an event GA4 never reported, not reporting one it did.
        convs, flagged = conversions.build_conversions(
            reported=[Metric("cv_download", "0", "GA4")],
            missing=[], proxy=None, umami_counts=UMAMI,
        )
        self.assertEqual(convs, [Metric("cv_download", "0", "GA4")])
        self.assertEqual(flagged, [])


if __name__ == "__main__":
    unittest.main()
