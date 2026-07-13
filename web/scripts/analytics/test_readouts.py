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
