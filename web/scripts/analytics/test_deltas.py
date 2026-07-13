import unittest
from datetime import date

import deltas
import history
from window import Window

JUNE = Window(date(2026, 6, 1), date(2026, 6, 30))
JULY = Window(date(2026, 7, 1), date(2026, 7, 31))
AUGUST = Window(date(2026, 8, 1), date(2026, 8, 31))
SEPTEMBER = Window(date(2026, 9, 1), date(2026, 9, 30))

FIX = date(2026, 7, 12)          # GA4_FIX_DEPLOY_DATE — real, already stamped
MARKING = date(2026, 7, 15)      # GA4_KEY_EVENT_MARKING_DATE — if A1' lands


def row(month, section="Search demand — totals (GSC)", name="Clicks",
        value_raw="10", source="GSC", void=False, partial=False):
    return history.Row(
        month=month, section=section, name=name, value_raw=value_raw,
        value_num=history.parse_numeric(value_raw), source=source, note="",
        void=void, partial=partial,
    )


class PriorMonth(unittest.TestCase):
    def test_the_prior_month_is_the_previous_calendar_month(self):
        self.assertEqual(deltas.prior_month("2026-09"), "2026-08")

    def test_january_rolls_back_a_year(self):
        self.assertEqual(deltas.prior_month("2027-01"), "2026-12")


class FormatDelta(unittest.TestCase):
    def test_a_rise_renders_signed_with_a_percentage(self):
        self.assertEqual(deltas.format_delta("12", "10"), "+2 (+20.0%)")

    def test_a_fall_renders_signed(self):
        self.assertIn("-2", deltas.format_delta("8", "10"))

    def test_a_zero_prior_renders_no_percentage(self):
        # +3 on a base of 0 is not "infinite growth"; it is 3.
        out = deltas.format_delta("3", "0")
        self.assertIn("+3", out)
        self.assertNotIn("%", out)  # the string must not contain a '%' AT ALL


class ARealDeltaRenders(unittest.TestCase):
    """The mechanism half. Two comparable, non-void, non-partial months of the
    same source, in a stable-key section, on a numeric value.
    """

    def test_two_comparable_full_months_produce_a_delta(self):
        out = deltas.delta_for(
            cur=row("2026-09", value_raw="12"),
            prior=row("2026-08", value_raw="10"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self.assertEqual(out, "+2 (+20.0%)")

    def test_a_measured_zero_is_comparable_and_deltas(self):
        # GA4 RETURNED a 0. That is a measurement, and it may be compared.
        # The rule forbids fabricating a zero, not comparing one.
        out = deltas.delta_for(
            cur=row("2026-09", value_raw="0", section="Conversions", source="GA4"),
            prior=row("2026-08", value_raw="2", section="Conversions", source="GA4"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self.assertIn("-2", out)


class TheRefusals(unittest.TestCase):
    """The rule half — and the actual deliverable of this sprint. Each of these
    is a comparison the report is NOT entitled to make. Every refusal NAMES what
    is missing. None of them zero-fills, and none of them silently omits.
    """

    def _refused(self, out):
        self.assertTrue(out.startswith("n/a — "), f"expected a refusal, got {out!r}")
        self.assertNotIn("+0", out)
        self.assertNotEqual(out, "0")

    def test_no_prior_month_in_history_refuses_and_says_so(self):
        # THE case this sprint actually ships in. One stored month is not a trend.
        out = deltas.delta_for(
            cur=row("2026-07"), prior=None,
            prior_w=JUNE, cur_w=JULY, prior_month_exists=False,
        )
        self._refused(out)
        self.assertIn("2026-06", out)
        self.assertIn("history", out)

    def test_a_metric_not_emitted_last_month_refuses(self):
        out = deltas.delta_for(
            cur=row("2026-09"), prior=None,
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("not emitted", out)

    def test_a_partial_current_month_refuses(self):
        # main() already detects a partial month for the caveat. That same signal
        # must BLOCK the delta, not merely annotate it.
        out = deltas.delta_for(
            cur=row("2026-09", partial=True), prior=row("2026-08"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("partial", out)

    def test_a_partial_prior_month_refuses(self):
        # July 2026 IS stored partial. August must refuse to compare against it.
        out = deltas.delta_for(
            cur=row("2026-08"), prior=row("2026-07", partial=True),
            prior_w=JULY, cur_w=AUGUST, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("partial", out)

    def test_a_void_prior_row_refuses(self):
        # Pre-07-12 GA4 conversions are VOID — not "low". Comparing against them
        # would report a fabricated surge as a real one.
        out = deltas.delta_for(
            cur=row("2026-09", section="Conversions", source="GA4", value_raw="2"),
            prior=row("2026-08", section="Conversions", source="GA4",
                      value_raw="0", void=True),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("void", out)

    def test_a_void_current_row_refuses(self):
        out = deltas.delta_for(
            cur=row("2026-09", section="Conversions", source="GA4", void=True),
            prior=row("2026-08", section="Conversions", source="GA4"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("void", out)

    def test_a_non_numeric_value_refuses_and_never_becomes_zero(self):
        # "pending" has no arithmetic. This is the silent-zero bug's last hiding
        # place: a delta of "pending" against "4" must not read as -4.
        out = deltas.delta_for(
            cur=row("2026-09", value_raw="pending"), prior=row("2026-08", value_raw="4"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
        )
        self._refused(out)
        self.assertIn("non-numeric", out)
        self.assertNotIn("-4", out)

    def test_a_ga4_delta_across_the_gtag_fix_refuses(self):
        # June -> July straddles 2026-07-12. GA4 received NONE of the four events
        # before it. A "surge" across this boundary is our own instrumentation
        # history, not a fact about the site.
        out = deltas.delta_for(
            cur=row("2026-07", section="Conversions", source="GA4", value_raw="2"),
            prior=row("2026-06", section="Conversions", source="GA4", value_raw="1"),
            prior_w=JUNE, cur_w=JULY, prior_month_exists=True,
            ga4_fix_deploy=FIX, ga4_marking=None, umami_filter=None,
        )
        self._refused(out)
        self.assertIn("boundary", out)

    def test_a_ga4_delta_across_the_key_event_marking_date_refuses(self):
        out = deltas.delta_for(
            cur=row("2026-08", section="Conversions", source="GA4", value_raw="2"),
            prior=row("2026-07", section="Conversions", source="GA4", value_raw="1"),
            prior_w=JULY, cur_w=AUGUST, prior_month_exists=True,
            ga4_fix_deploy=None, ga4_marking=MARKING, umami_filter=None,
        )
        self._refused(out)
        self.assertIn("boundary", out)

    def test_a_umami_delta_across_the_bot_filter_refuses(self):
        out = deltas.delta_for(
            cur=row("2026-09", section="Reach (Umami)", source="Umami", value_raw="10"),
            prior=row("2026-08", section="Reach (Umami)", source="Umami", value_raw="4"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
            ga4_fix_deploy=None, ga4_marking=None, umami_filter=date(2026, 8, 20),
        )
        self._refused(out)
        self.assertIn("boundary", out)

    def test_a_ga4_boundary_does_not_block_a_umami_row(self):
        # The gtag bug never touched Umami. Scoping the boundaries by source is
        # what stops one instrument's history from censoring another's.
        out = deltas.delta_for(
            cur=row("2026-07", section="Reach (Umami)", source="Umami", value_raw="12"),
            prior=row("2026-06", section="Reach (Umami)", source="Umami", value_raw="10"),
            prior_w=JUNE, cur_w=JULY, prior_month_exists=True,
            ga4_fix_deploy=FIX, ga4_marking=None, umami_filter=None,
        )
        self.assertEqual(out, "+2 (+20.0%)")

    def test_an_unstamped_boundary_blocks_nothing(self):
        # boundaries.py treats None as "has not happened yet" — never as "no
        # boundary". An unstamped date must not refuse every comparison.
        out = deltas.delta_for(
            cur=row("2026-09", section="Conversions", source="GA4", value_raw="4"),
            prior=row("2026-08", section="Conversions", source="GA4", value_raw="2"),
            prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
            ga4_fix_deploy=None, ga4_marking=None, umami_filter=None,
        )
        self.assertEqual(out, "+2 (+100.0%)")


class NoTopNDelta(unittest.TestCase):
    """GSC's top queries / pages / countries are CHURNING ROW SETS, not metric
    series. A query that "appears" in September is almost always churn in the
    top-10, not new demand; one that vanishes has not gone to zero, it has fallen
    to rank 11. A top-N delta is a fabricated finding with a real-looking number
    attached — the worst kind.
    """

    CHURNING = [
        "Top queries (GSC)",
        "Top pages (GSC)",
        "Top countries (GSC)",
        "Indexation (GSC)",  # rows are the URLs published THAT month — keys churn wholesale
        "Flagged / pending (no counterpart or traffic-gated)",
    ]

    def test_no_churning_section_ever_emits_a_delta(self):
        for section in self.CHURNING:
            out = deltas.delta_for(
                cur=row("2026-09", section=section, name="some query", value_raw="12"),
                prior=row("2026-08", section=section, name="some query", value_raw="10"),
                prior_w=AUGUST, cur_w=SEPTEMBER, prior_month_exists=True,
            )
            self.assertTrue(out.startswith("n/a — "), f"{section} emitted {out!r}")
            self.assertNotIn("+2", out)

    def test_the_stable_key_sections_are_exactly_the_allow_list(self):
        self.assertEqual(
            deltas.STABLE_KEY_SECTIONS,
            frozenset({
                "Reach (Umami)",
                "Channel & engagement (GA4)",
                "Conversions",
                "Search demand — totals (GSC)",
            }),
        )


if __name__ == "__main__":
    unittest.main()
