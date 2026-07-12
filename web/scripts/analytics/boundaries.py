"""Comparability boundaries — dates before which a metric does not mean what it
looks like it means.

These live in CODE, not in the rendered report. A boundary recorded only in the
`.md` is silently deleted by the next regeneration — that has already happened to
this project once (see report.ROLLING_READOUTS, which exists for exactly that
reason). Epic B's history store imports this module; its "never compare across an
incomparable window" rule is meaningless without it.

Both dates start as None and are stamped by the sprint-07 stories that produce
them (A1 and A2). None means "has not happened yet" — never "no boundary".
"""
from __future__ import annotations

from datetime import date

from window import Window

# A1 — the date the four conversion events were marked as GA4 key events.
# GA4 key events are NOT retroactive: marking cv_download does not convert past
# events into conversions. Every conversion comparison starts here, not earlier.
GA4_KEY_EVENT_MARKING_DATE: date | None = None

# A2 — the date Umami bot filtering was confirmed switched on in the dashboard.
# Umami counts either side of this are NOT comparable. A step change across it is
# the filter working, not a traffic drop.
UMAMI_BOT_FILTER_DATE: date | None = None


def boundary_caveats(
    w: Window,
    ga4_marking: date | None = GA4_KEY_EVENT_MARKING_DATE,
    umami_filter: date | None = UMAMI_BOT_FILTER_DATE,
) -> list[str]:
    """Caveats for the boundaries this window touches. Pure and testable.

    Three positions per boundary: the window straddles it (say what changed
    mid-window), the window ends before it (the metric could not have existed —
    so its absence is not a measured 0), or the window starts after it (nothing
    to say; the boundary is history).
    """
    out: list[str] = []

    if ga4_marking is not None:
        if w.start < ga4_marking <= w.end:
            out.append(
                f"The four conversion events were marked as GA4 key events on "
                f"{ga4_marking.isoformat()}, **inside this window**. GA4 key events "
                f"are **not retroactive** — conversions counted here begin at that "
                f"date, not at {w.start.isoformat()}. Do not read a low count as a "
                f"decline, and do not compare it against an earlier month: the "
                f"earlier month has no conversions by design, not by absence of "
                f"traffic."
            )
        elif w.end < ga4_marking:
            out.append(
                f"This window ends before the GA4 key-event marking date "
                f"({ga4_marking.isoformat()}). No conversion figure here is not a "
                f"measured 0 — these events were simply not yet key events. Their "
                f"absence is an absence of measurement."
            )

    if umami_filter is not None:
        if w.start < umami_filter <= w.end:
            out.append(
                f"Umami bot filtering was switched on {umami_filter.isoformat()}, "
                f"**inside this window**. Umami counts before and after that date "
                f"are **not comparable** — a step down across it is the filter "
                f"working, not a traffic drop."
            )
        elif w.end < umami_filter:
            out.append(
                f"This window predates the Umami bot-filter switch-on "
                f"({umami_filter.isoformat()}) — its raw Umami counts were taken "
                f"with filtering unconfirmed and are **not comparable** with any "
                f"post-switch-on month."
            )

    return out
