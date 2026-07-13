"""The rolling readouts, computed from the store instead of hand-written.

report.ROLLING_READOUTS is a static markdown constant. It exists because a
hand-appended block was silently deleted by a regeneration — anything that must
survive lives in CODE. With a history store, part of it can do better than
survive: it can be computed.

C3b becomes real. E8 does not — and that is the point. E8 needs a clean post-A/B
month; there is none. Pre-2026-07-12 conversions are void (GA4 received none of
the four events), and A1's non-retroactive clock starts, at the earliest, this
sprint. Its honest render is an explicit "insufficient history" that names what
is missing and the first month it could be computed. A fabricated re-baseline is
worse than an honest gap.

E3 and D6b are not analytics questions at all and are carried verbatim.
"""
from __future__ import annotations

from datetime import date

import boundaries
import deltas
import ga4
import history

PPS_GOAL = "2.0"
PPS_BASELINE = "1.69"


def _sitewide_pps(month: str, rows: list[history.Row]) -> history.Row | None:
    for r in rows:
        if r.month == month and r.name == ga4.SITEWIDE_PPS_NAME:
            return r
    return None


def _c3b_cell(month: str, rows: list[history.Row]) -> str:
    cur = _sitewide_pps(month, rows)
    if cur is None or not cur.value_num:
        return (
            f"pending — GA4 emitted no site-wide pages/session for {month}; "
            f"baseline {PPS_BASELINE}, goal > {PPS_GOAL}. Not a measured 0."
        )
    prior = _sitewide_pps(deltas.prior_month(month), rows)
    trend = ""
    if prior is not None and prior.value_num and not prior.partial and not cur.partial:
        trend = f" ({deltas.format_delta(cur.value_num, prior.value_num).split(' ')[0]} vs {prior.month})"
    verdict = "at or above" if float(cur.value_num) >= float(PPS_GOAL) else "below"
    # Pages/session is a RATIO, not a raw count — a partial month does not
    # structurally bias it the way a partial-month raw count would (that is why
    # only the trend, not the figure itself, is withheld above). But the reader
    # comparing this cell against the 2.0 goal still deserves to know the month
    # is not finished, so say so; never suppress the figure and never invent one.
    partial_note = f"; {month} is still a partial month" if cur.partial else ""
    return (
        f"**{cur.value_num}**{trend} — {verdict} the {PPS_GOAL} goal "
        f"(baseline {PPS_BASELINE}){partial_note}"
    )


def _first_full_month_after(d: date) -> str:
    """The first month wholly after `d` — the earliest month that could be clean."""
    y, m = (d.year, d.month + 1) if d.month < 12 else (d.year + 1, 1)
    return f"{y}-{m:02d}"


def _e8_cell(ga4_marking: date | None) -> str:
    if ga4_marking is None:
        return (
            "**insufficient history** — needs one full month of conversions after "
            "the GA4 key events are marked (A1). A1 has not landed: the marking "
            "date is unstamped, so the earliest clean month cannot yet be named. "
            "Not a re-baseline of 0."
        )
    return (
        f"**insufficient history** — needs one full month of conversions after the "
        f"GA4 key-event marking date ({ga4_marking.isoformat()}); GA4 key events "
        f"are not retroactive. Earliest computable: "
        f"**{_first_full_month_after(ga4_marking)}**, reportable the month after. "
        f"Not a re-baseline of 0."
    )


def build_readouts(
    month: str,
    history_rows: list[history.Row],
    ga4_marking: date | None = boundaries.GA4_KEY_EVENT_MARKING_DATE,
) -> str:
    """The rolling-readouts block for one month. Pure — the store is the input."""
    return f"""## Rolling readouts (standing cadence — traffic-gated)

The four items the sprint deferred pending more traffic. None are dropped — each
has a named home below and is re-checked on the cadence noted. C3b and E8 are now
**computed from `history/metrics.csv`**, not hand-written; a readout that cannot
be computed says exactly what it is missing rather than showing a number it has
not earned.

| # | Readout | Home | Status |
|---|---|---|---|
| E3 | Link-placement verdict (body / first-comment / profile-featured) | tracker rollup → [`linkedin-post-tracker.md`](../../playbooks/linkedin-post-tracker.md#e3--link-placement-rollup-pending-n-posts-per-variant) → [`linkedin-playbook.md`](../../playbooks/linkedin-playbook.md#link-placement-ab) | pending ≥N posts per variant |
| E8 | Re-baseline delta once a clean post-A/B month exists | [`kpi-baselines-and-targets.md`](../kpi-baselines-and-targets.md) | {_e8_cell(ga4_marking)} |
| C3b | Pages/session crossing {PPS_GOAL} from the internal-link retrofit | this report's GA4 channel section (above) | {_c3b_cell(month, history_rows)} |
| D6b | Conversion shift near the trust block | this report | **pending a real named testimonial** (never fabricated) + weeks of traffic |

> This block is emitted from `readouts.py` and computed from the metric store, so
> every month carries it automatically and its numbers cannot go stale.
"""
