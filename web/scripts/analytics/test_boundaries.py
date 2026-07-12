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
            boundaries.boundary_caveats(JULY, ga4_marking=None, umami_filter=None), []
        )

    def test_window_straddling_the_ga4_marking_says_it_is_not_retroactive(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=date(2026, 7, 14), umami_filter=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("2026-07-14", out[0])
        self.assertIn("not retroactive", out[0])

    def test_window_entirely_before_the_marking_forbids_a_measured_zero(self):
        out = boundaries.boundary_caveats(
            JUNE, ga4_marking=date(2026, 7, 14), umami_filter=None
        )
        self.assertEqual(len(out), 1)
        # Pin the corrected phrasing exactly, and reject its double-negative
        # inversion — "is not a measured 0" would flip the rule's meaning
        # (every figure IS a measured 0), which is the bug this test guards
        # against.
        self.assertIn("is a measured 0", out[0])
        self.assertNotIn("not a measured 0", out[0])

    def test_window_entirely_after_the_marking_needs_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                AUGUST, ga4_marking=date(2026, 7, 14), umami_filter=None
            ),
            [],
        )

    def test_window_straddling_the_umami_filter_warns_against_comparing_across_it(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=date(2026, 7, 15)
        )
        self.assertEqual(len(out), 1)
        self.assertIn("2026-07-15", out[0])
        self.assertIn("not comparable", out[0])
        # A step change across the switch-on is the filter working, not a drop.
        self.assertIn("filter working", out[0])

    def test_window_entirely_after_the_umami_filter_needs_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                AUGUST, ga4_marking=None, umami_filter=date(2026, 7, 15)
            ),
            [],
        )

    def test_both_boundaries_inside_one_window_emit_both_caveats(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=date(2026, 7, 14), umami_filter=date(2026, 7, 15)
        )
        self.assertEqual(len(out), 2)

    def test_ga4_marking_exactly_on_window_start_yields_no_caveat(self):
        # boundary <= w.start: the marking happened at or before the window
        # opened, so it is not "inside" the window — nothing to say.
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=JULY.start, umami_filter=None
            ),
            [],
        )

    def test_ga4_marking_exactly_on_window_end_straddles(self):
        # w.start < boundary <= w.end: a boundary landing exactly on w.end is
        # still inside the window — the straddle caveat must fire.
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=JULY.end, umami_filter=None
        )
        self.assertEqual(len(out), 1)
        self.assertIn("not retroactive", out[0])

    def test_umami_filter_exactly_on_window_start_yields_no_caveat(self):
        self.assertEqual(
            boundaries.boundary_caveats(
                JULY, ga4_marking=None, umami_filter=JULY.start
            ),
            [],
        )

    def test_umami_filter_exactly_on_window_end_straddles(self):
        out = boundaries.boundary_caveats(
            JULY, ga4_marking=None, umami_filter=JULY.end
        )
        self.assertEqual(len(out), 1)
        self.assertIn("not comparable", out[0])
        self.assertIn("filter working", out[0])

    def test_the_marking_date_defaults_to_the_module_constant(self):
        # The default argument is the recorded boundary, so callers get it for
        # free and Epic B has a single source of truth to import.
        self.assertIs(
            boundaries.boundary_caveats.__defaults__[0],
            boundaries.GA4_KEY_EVENT_MARKING_DATE,
        )


if __name__ == "__main__":
    unittest.main()
