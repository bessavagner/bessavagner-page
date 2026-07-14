import unittest
from datetime import date

import ga4
import history
import readouts


def pps_row(month, value, partial=False):
    return history.Row(
        month=month, section="Channel & engagement (GA4)", name=ga4.SITEWIDE_PPS_NAME,
        value_raw=value, value_num=history.parse_numeric(value), source="GA4",
        note="", void=False, partial=partial,
    )


class C3bIsComputed(unittest.TestCase):
    """C3b stops being a hand-written sentence and becomes a number from the store."""

    def test_the_current_sitewide_figure_is_stated_against_the_goal(self):
        md = readouts.build_readouts("2026-09", [pps_row("2026-09", "1.84")])
        self.assertIn("1.84", md)
        self.assertIn("2.0", md)

    def test_a_prior_month_produces_a_trend(self):
        md = readouts.build_readouts(
            "2026-09", [pps_row("2026-08", "1.69"), pps_row("2026-09", "1.84")]
        )
        self.assertIn("+0.15", md)

    def test_no_stored_figure_says_pending_not_zero(self):
        md = readouts.build_readouts("2026-09", [])
        self.assertIn("| C3b |", md)
        self.assertNotIn("| C3b | 0", md)
        self.assertIn("pending", md.split("| C3b |")[1].split("\n")[0])


class E8IsHonestlyUncomputable(unittest.TestCase):
    """E8 needs a clean post-A/B month. There is not one: pre-2026-07-12
    conversions are void, and A1's non-retroactive clock starts this sprint at
    the earliest. The honest render is an explicit "insufficient history" that
    NAMES what is missing and when it could first be computed.
    """

    def test_e8_renders_insufficient_history_and_names_what_is_missing(self):
        md = readouts.build_readouts("2026-07", [], ga4_marking=date(2026, 7, 15))
        e8 = md.split("| E8 |")[1].split("\n")[0]
        self.assertIn("insufficient history", e8.lower())
        self.assertIn("2026-08", e8)  # the first FULL month after the marking date

    def test_e8_with_no_marking_date_names_A1_as_the_blocker(self):
        md = readouts.build_readouts("2026-07", [], ga4_marking=None)
        e8 = md.split("| E8 |")[1].split("\n")[0]
        self.assertIn("insufficient history", e8.lower())
        self.assertIn("A1", e8)

    def test_e8_never_fabricates_a_number(self):
        md = readouts.build_readouts("2026-07", [], ga4_marking=None)
        e8 = md.split("| E8 |")[1].split("\n")[0]
        self.assertNotIn("%", e8)

    def test_e8_never_fabricates_a_number_once_the_marking_date_is_stamped(self):
        # The branch that goes live the day A1 lands. E8 still has no clean
        # post-A/B month — it names the earliest one it COULD be computed for,
        # and must not smuggle a percentage into the cell in the meantime.
        md = readouts.build_readouts("2026-07", [], ga4_marking=date(2026, 7, 28))
        e8 = md.split("| E8 |")[1].split("\n")[0]
        self.assertIn("insufficient history", e8.lower())
        self.assertIn("2026-08", e8)          # the first FULL month after the marking
        self.assertNotIn("%", e8)             # no fabricated re-baseline
        self.assertNotIn("re-baseline of 0", e8.replace("Not a re-baseline of 0.", ""))


class C3bGetsTheCurrentMonthsOwnRow(unittest.TestCase):
    """monthly_report.main() reads history BEFORE this month is recorded (so
    attach_deltas cannot make the month its own prior), but C3b needs THIS
    month's own site-wide pages/session row to say anything real. The fix is
    to hand build_readouts `cur_rows + hist` instead of `hist` alone — these
    tests pin that contract directly against readouts.py, since main() itself
    cannot be run without live GA4/GSC credentials.
    """

    def test_withholding_the_current_month_row_falsely_renders_pending(self):
        # This is the bug, pinned as a regression guard: `hist` alone (no row
        # for the month being reported) makes C3b claim GA4 emitted nothing,
        # even when GA4 actually reported a real site-wide figure this month —
        # the caller just hasn't been told about it yet.
        hist_only = [pps_row("2026-08", "1.69")]  # no 2026-09 row at all
        md = readouts.build_readouts("2026-09", hist_only)
        c3b = md.split("| C3b |")[1].split("\n")[0]
        self.assertIn("pending", c3b)

    def test_supplying_the_current_month_row_resolves_c3b(self):
        # Same store, PLUS this month's own row (as monthly_report.py's fixed
        # `cur_rows + hist` now supplies) — C3b must report the real figure
        # against the goal instead of falsely claiming an absence.
        hist = [pps_row("2026-08", "1.69")]
        cur_rows = [pps_row("2026-09", "1.83")]
        md = readouts.build_readouts("2026-09", cur_rows + hist)
        c3b = md.split("| C3b |")[1].split("\n")[0]
        self.assertIn("1.83", c3b)
        self.assertIn("2.0", c3b)
        self.assertNotIn("pending", c3b)


class C3bFlagsAPartialCurrentMonth(unittest.TestCase):
    """Pages/session is a ratio, so a partial month does not structurally bias
    it the way a partial-month raw count would — but the cell must still SAY
    the month is partial rather than silently presenting it as finished.
    """

    def test_partial_current_month_is_named_in_the_cell(self):
        cur_rows = [pps_row("2026-09", "1.83", partial=True)]
        md = readouts.build_readouts("2026-09", cur_rows)
        c3b = md.split("| C3b |")[1].split("\n")[0]
        self.assertIn("1.83", c3b)  # the figure is never suppressed
        self.assertIn("partial", c3b.lower())

    def test_non_partial_current_month_stays_silent_about_partial(self):
        cur_rows = [pps_row("2026-09", "1.83", partial=False)]
        md = readouts.build_readouts("2026-09", cur_rows)
        c3b = md.split("| C3b |")[1].split("\n")[0]
        self.assertNotIn("partial", c3b.lower())


class SupplyingTheCurrentMonthCannotMakeItItsOwnPrior(unittest.TestCase):
    """The invariant that makes the fix safe: `_c3b_cell`'s prior-month lookup
    keys on deltas.prior_month(month), a DIFFERENT month string from `month`
    itself, so adding the current month's own rows to the snapshot passed into
    build_readouts can never let it compare itself against itself.
    """

    def test_current_month_only_rows_produce_no_self_comparison_trend(self):
        # Only a 2026-09 row exists anywhere in the snapshot — no 2026-08 row
        # at all. If the current month could become its own prior, this would
        # produce a trend of "+0.00" against itself; it must produce none.
        cur_rows = [pps_row("2026-09", "1.83")]
        md = readouts.build_readouts("2026-09", cur_rows)
        c3b = md.split("| C3b |")[1].split("\n")[0]
        self.assertIn("1.83", c3b)
        self.assertNotIn("vs 2026-09", c3b)
        self.assertNotIn("+0", c3b)


class TheOtherReadoutsSurvive(unittest.TestCase):
    """E3 and D6b are not computable from analytics at all — E3 needs N posts per
    variant, D6b needs a real named testimonial that does not exist and will not
    be fabricated. They stay, verbatim.
    """

    def test_every_readout_id_is_still_emitted(self):
        md = readouts.build_readouts("2026-09", [])
        for rid in ("E3", "E8", "C3b", "D6b"):
            self.assertIn(f"| {rid} |", md)

    def test_d6b_still_refuses_to_fabricate_a_testimonial(self):
        md = readouts.build_readouts("2026-09", [])
        self.assertIn("never fabricated", md)


if __name__ == "__main__":
    unittest.main()
