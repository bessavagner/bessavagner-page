import unittest
from datetime import date

import boundaries
from window import Window

JULY = Window(date(2026, 7, 1), date(2026, 7, 31))
AUGUST = Window(date(2026, 8, 1), date(2026, 8, 31))
JUNE = Window(date(2026, 6, 1), date(2026, 6, 30))


class BoundaryCaveats(unittest.TestCase):
    def test_no_boundaries_set_yields_no_caveats(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=None, umami_filter=None, ga4_fix_deploy=None
            ),
            [],
        )

    def test_window_straddling_the_ga4_marking_says_it_is_not_retroactive(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=date(2026, 7, 14), umami_filter=None, ga4_fix_deploy=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("2026-07-14", out[0])
        self.assertIn("not retroactive", out[0])

    def test_window_entirely_before_the_marking_forbids_a_measured_zero(self):
        out = boundaries.boundary_caveats(
            JUNE, ga4_marking=date(2026, 7, 14), umami_filter=None, ga4_fix_deploy=None
        )
        self.assertEqual(len(out), 1)
        # Pin the corrected phrasing exactly. A substring check on "is a
        # measured 0" alone is invertible: "Every conversion figure here is a
        # measured 0" (the exact inversion of the rule) contains that substring
        # and does NOT contain "not a measured 0", so it would pass both old
        # assertions. The negation lives in the word "No" — assert the full
        # clause so an inverted string cannot slip through.
        self.assertIn("No conversion figure here is a measured 0", out[0])

    def test_window_entirely_after_the_marking_needs_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                AUGUST,
                ga4_marking=date(2026, 7, 14),
                umami_filter=None,
                ga4_fix_deploy=None,
            ),
            [],
        )

    def test_window_straddling_the_umami_filter_warns_against_comparing_across_it(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=date(2026, 7, 15), ga4_fix_deploy=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("2026-07-15", out[0])
        self.assertIn("not comparable", out[0])
        # A step change across the switch-on is the filter working, not a drop.
        # Pin the full clause, not just "filter working": that substring alone
        # is invertible — "a step down across it is a traffic drop, not the
        # filter working" (swapping which cause is blamed) still contains
        # "filter working" (inside "not the filter working") and would slip
        # past a bare substring check while "not comparable" stays untouched.
        self.assertIn("is the filter working, not a traffic drop", out[0])

    def test_window_entirely_after_the_umami_filter_needs_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                AUGUST,
                ga4_marking=None,
                umami_filter=date(2026, 7, 15),
                ga4_fix_deploy=None,
            ),
            [],
        )

    def test_both_boundaries_inside_one_window_emit_both_caveats(self):
        out = boundaries.boundary_caveats(
            JULY,
            ga4_marking=date(2026, 7, 14),
            umami_filter=date(2026, 7, 15),
            ga4_fix_deploy=None,
        )
        self.assertEqual(len(out), 2)

    def test_ga4_marking_exactly_on_window_start_yields_no_caveat(self):
        # boundary <= w.start: the marking happened at or before the window
        # opened, so it is not "inside" the window — nothing to say.
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=JULY.start, umami_filter=None, ga4_fix_deploy=None
            ),
            [],
        )

    def test_ga4_marking_exactly_on_window_end_straddles(self):
        # w.start < boundary <= w.end: a boundary landing exactly on w.end is
        # still inside the window — the straddle caveat must fire.
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=JULY.end, umami_filter=None, ga4_fix_deploy=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("not retroactive", out[0])

    def test_umami_filter_exactly_on_window_start_yields_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=None, umami_filter=JULY.start, ga4_fix_deploy=None
            ),
            [],
        )

    def test_umami_filter_exactly_on_window_end_straddles(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=JULY.end, ga4_fix_deploy=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("not comparable", out[0])
        self.assertIn("is the filter working, not a traffic drop", out[0])

    def test_the_marking_date_defaults_to_the_module_constant(self):
        # The default argument is the recorded boundary, so callers get it for
        # free and Epic B has a single source of truth to import.
        self.assertIs(
            boundaries.boundary_caveats.__defaults__[0],
            boundaries.GA4_KEY_EVENT_MARKING_DATE,
        )


class GA4FixDeployBoundary(unittest.TestCase):
    """A0's boundary: before the gtag-fix deploy date, GA4 physically received
    none of the four custom events — a structural absence, never a measured 0,
    and distinct from GA4_KEY_EVENT_MARKING_DATE (which governs the Conversions
    *report*, not whether an eventName row exists at all).
    """

    def test_window_straddling_the_fix_deploy_says_it_is_structural(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=None,
            ga4_fix_deploy=date(2026, 7, 14),
        )
        self.assertEqual(len(out), 1)
        self.assertIn("2026-07-14", out[0])
        self.assertIn("GA4 received **none** of the four custom conversion events", out[0])
        self.assertIn("cannot be compared against", out[0])

    def test_window_entirely_before_the_fix_deploy_forbids_a_measured_zero(self):
        out = boundaries.boundary_caveats(
            JUNE, ga4_marking=None, umami_filter=None,
            ga4_fix_deploy=date(2026, 7, 14),
        )
        self.assertEqual(len(out), 1)
        # Same invertibility trap as the ga4_marking caveat: pin the full
        # clause, not just "is a measured 0", which an inverted string like
        # "Every conversion figure here is a measured 0" would also contain.
        self.assertIn("No conversion figure here is a measured 0", out[0])

    def test_window_entirely_after_the_fix_deploy_needs_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                AUGUST, ga4_marking=None, umami_filter=None,
                ga4_fix_deploy=date(2026, 7, 14),
            ),
            [],
        )

    def test_fix_deploy_exactly_on_window_start_yields_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=None, umami_filter=None,
                ga4_fix_deploy=JULY.start,
            ),
            [],
        )

    def test_fix_deploy_exactly_on_window_end_straddles(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=None, ga4_fix_deploy=JULY.end,
        )
        self.assertEqual(len(out), 1)
        self.assertIn("GA4 received **none** of the four custom conversion events", out[0])

    def test_all_three_boundaries_inside_one_window_emit_three_caveats(self):
        out = boundaries.boundary_caveats(
            JULY,
            ga4_marking=date(2026, 7, 14),
            umami_filter=date(2026, 7, 15),
            ga4_fix_deploy=date(2026, 7, 10),
        )
        self.assertEqual(len(out), 3)

    def test_the_fix_deploy_date_defaults_to_the_module_constant(self):
        self.assertIs(
            boundaries.boundary_caveats.__defaults__[2],
            boundaries.GA4_FIX_DEPLOY_DATE,
        )


if __name__ == "__main__":
    unittest.main()
