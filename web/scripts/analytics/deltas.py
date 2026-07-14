"""Month-over-month deltas — the mechanism, and the rule that refuses to run it.

The refusal rule is the deliverable. A delta this report is not entitled to draw
is not a smaller mistake than no delta at all: it is a fabricated finding with a
real-looking number attached, and it is the one thing a history store makes
newly possible.

Six comparisons are refused, each by name, and none of them is ever zero-filled
or silently omitted:

  1. ACROSS A BOUNDARY. boundaries.py holds the dates at which our own
     instrumentation changed. A "surge" in GA4 conversions across 2026-07-12 is
     window.gtag starting to work, not the site improving. Boundaries are scoped
     by SOURCE — the gtag bug never touched Umami, and one instrument's history
     must not censor another's.
  2. AGAINST A PARTIAL MONTH. Fewer elapsed days is not a decline. main()
     already detects this for its caveat; here the same signal BLOCKS the delta.
  3. AGAINST A VOID ROW. Pre-2026-07-12 GA4 conversions are void: the pipeline
     could not deliver them. Void is not zero, and it is not a low measurement.
  4. ON A NON-NUMERIC VALUE. "pending" has no arithmetic. A delta of "pending"
     against "4" must never read as -4. This is the silent-zero bug's last
     hiding place.
  5. ON A CHURNING ROW SET. GSC's top-N tables and the per-URL indexation table
     are not metric series — their KEYS turn over month to month. A query that
     "appears" has usually moved from rank 11 to rank 10.
  6. ACROSS UNEQUAL COVERAGE WINDOWS. GSC's window is detected empirically and
     its reporting lag is not constant. A 29-day August against a 31-day July is
     a -6% artifact of the window, not a decline in demand. An UNKNOWN window
     refuses on the same rule: it is not a matching one.

At the time of writing exactly ONE month is stored, so every cell in the next
report will read "n/a — no 2026-06 in history". That is correct. The first real
delta this machine can honestly draw lands in early September.
"""
from __future__ import annotations

from datetime import date

import boundaries
import history
import window
from report import Section
from window import Window

# The ONLY sections whose row keys are a stable series across months. Everything
# else is a churning row set and never deltas — see rule 5 above.
STABLE_KEY_SECTIONS = frozenset({
    "Reach (Umami)",
    "Channel & engagement (GA4)",
    "Conversions",
    "Search demand — totals (GSC)",
    # C2. The per-URL "Indexation (GSC)" table stays OUT — its keys are URLs and
    # they churn wholesale every month. The COUNT is the stable series.
    "Indexation verdict (GSC)",
    # C3a. "Top pages (GSC)" stays OUT — a top-N slice churns by rank, and a page
    # that falls out of it simply vanishes from history. The PINNED list is
    # fetched by name, so its keys are fixed by code and its series never breaks.
    "Pinned pages (GSC)",
    # C4. Keys are the sitemap paths — fixed, not churning. Days-since-download
    # is a real series: a rising number IS the regression.
    "Sitemap health (GSC)",
})

# Which boundaries can invalidate which instrument's history.
_GA4_SOURCE = "GA4"
_UMAMI_SOURCE = "Umami"
_GSC_SOURCE = "GSC"


def prior_month(month: str) -> str:
    """The previous CALENDAR month — not "the previous stored month".

    A gap in the store must refuse, not silently reach further back: comparing
    September against June and calling it a month-over-month change is a lie
    about the window, told with a true number.
    """
    y, m = (int(p) for p in month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _boundaries_for(
    source: str,
    ga4_fix_deploy: date | None,
    ga4_marking: date | None,
    umami_filter: date | None,
) -> list[tuple[str, date]]:
    out: list[tuple[str, date]] = []
    if source == _GA4_SOURCE:
        if ga4_fix_deploy is not None:
            out.append(("GA4 gtag-fix deploy", ga4_fix_deploy))
        if ga4_marking is not None:
            out.append(("GA4 key-event marking", ga4_marking))
    elif source == _UMAMI_SOURCE:
        if umami_filter is not None:
            out.append(("Umami bot-filter switch-on", umami_filter))
    return out


def crosses_boundary(
    source: str,
    prior_w: Window,
    cur_w: Window,
    ga4_fix_deploy: date | None = boundaries.GA4_FIX_DEPLOY_DATE,
    ga4_marking: date | None = boundaries.GA4_KEY_EVENT_MARKING_DATE,
    umami_filter: date | None = boundaries.UMAMI_BOT_FILTER_DATE,
) -> str | None:
    """The name of the first boundary lying between (or inside) the two windows.

    `prior_w.start < b <= cur_w.end` catches all three positions that matter: a
    boundary inside the prior window, one in the gap between them, and one inside
    the current window. Any of them makes the two windows products of different
    instrumentation.
    """
    for label, b in _boundaries_for(source, ga4_fix_deploy, ga4_marking, umami_filter):
        if prior_w.start < b <= cur_w.end:
            return label
    return None


def format_delta(cur_num: str, prior_num: str) -> str:
    c, p = float(cur_num), float(prior_num)
    d = c - p
    if p == 0:
        # +3 on a base of 0 is not "infinite growth". It is 3. And the cell must
        # carry no percent sign at all — a reader scanning for "%" would find one.
        return f"{d:+g} (prior 0 — no percent change)"
    return f"{d:+g} ({d / p * 100:+.1f}%)"


def delta_for(
    cur: history.Row,
    prior: history.Row | None,
    prior_w: Window,
    cur_w: Window,
    prior_month_exists: bool,
    ga4_fix_deploy: date | None = boundaries.GA4_FIX_DEPLOY_DATE,
    ga4_marking: date | None = boundaries.GA4_KEY_EVENT_MARKING_DATE,
    umami_filter: date | None = boundaries.UMAMI_BOT_FILTER_DATE,
) -> str:
    """One row's delta cell: a delta, or `n/a — <what is missing>`.

    Every return path either computes arithmetic on two numbers it is entitled to
    compare, or NAMES the reason it will not. There is no third path, and in
    particular there is no path that returns "0".
    """
    if cur.section not in STABLE_KEY_SECTIONS:
        return "n/a — top-N/churning row set, not a metric series"

    if cur.partial:
        return f"n/a — {cur.month} is a partial month"

    if not prior_month_exists:
        return f"n/a — no {prior_w.start.strftime('%Y-%m')} in history"

    if prior is None:
        return f"n/a — not emitted in {prior_w.start.strftime('%Y-%m')}"

    if prior.partial:
        return f"n/a — {prior.month} was a partial month"

    if cur.void or prior.void:
        return "n/a — void row (window predates the boundary that makes it measurable)"

    crossed = crosses_boundary(
        cur.source, prior_w, cur_w, ga4_fix_deploy, ga4_marking, umami_filter
    )
    if crossed:
        return f"n/a — crosses the {crossed} boundary"

    # 6. UNEQUAL COVERAGE WINDOWS. GSC's window is detected empirically, its lag
    #    is ~2-3 days and NOT constant, and the row's `partial` flag comes from
    #    the calendar month — so a 29-day August would delta against a 31-day
    #    July and print a -6% WINDOW ARTIFACT as a measured decline. An unknown
    #    window refuses too: "" is not "matching", and assuming it is would be
    #    the silent-zero bug wearing a different hat.
    if cur.source == _GSC_SOURCE:
        if not cur.days_measured or not prior.days_measured:
            return "n/a — GSC coverage window is unknown for one of the two months"
        if cur.days_measured != prior.days_measured:
            return (
                f"n/a — GSC coverage windows differ in length "
                f"({prior.days_measured}d in {prior.month}, "
                f"{cur.days_measured}d in {cur.month})"
            )

    if not cur.value_num or not prior.value_num:
        return "n/a — non-numeric value"

    return format_delta(cur.value_num, prior.value_num)


def attach_deltas(
    sections: list[Section],
    month: str,
    month_w: Window,
    history_rows: list[history.Row],
    partial: bool,
    gsc_cov: Window | None = None,
) -> None:
    """Stamp Metric.delta on every metric in place. The one call main() makes.

    Read the history BEFORE this month is recorded, or the month becomes its own
    prior and every delta is 0.
    """
    pm = prior_month(month)
    prior_w = window.month_window(pm)
    prior_rows = [r for r in history_rows if r.month == pm]
    prior_month_exists = bool(prior_rows)
    index = {(r.section, r.name, r.source): r for r in prior_rows}

    for s in sections:
        for m in s.metrics:
            cur = history.Row(
                month=month,
                section=s.title,
                name=m.name,
                value_raw=m.value,
                value_num=history.parse_numeric(m.value),
                source=m.source,
                note=m.note,
                void=history.is_void(s.title, m.source, month_w),
                partial=partial,
                days_measured=history.measured_days(m.source, gsc_cov),
            )
            m.delta = delta_for(
                cur, index.get((s.title, m.name, m.source)),
                prior_w, month_w, prior_month_exists,
            )
