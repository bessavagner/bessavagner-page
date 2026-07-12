"""Comparability boundaries — dates before which a metric does not mean what it
looks like it means.

These live in CODE, not in the rendered report. A boundary recorded only in the
`.md` is silently deleted by the next regeneration — that has already happened to
this project once (see report.ROLLING_READOUTS, which exists for exactly that
reason). Epic B's history store imports this module; its "never compare across an
incomparable window" rule is meaningless without it.

All three dates start as None and are stamped once the real-world event they
name has actually happened: GA4_FIX_DEPLOY_DATE when the window.gtag scoping
fix (A0) ships to production, GA4_KEY_EVENT_MARKING_DATE by A1,
UMAMI_BOT_FILTER_DATE by A2. None means "has not happened yet" — never "no
boundary".
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

# A0 — the date the window.gtag scoping-bug fix (commit 00b6d19) deploys to
# production. Before this date GA4 physically received NONE of the four custom
# conversion events (cv_download, whatsapp_click, generate_lead,
# newsletter_signup): Base.astro's define:vars script wrapped `function gtag(){}`
# in an Astro-generated IIFE, so `window.gtag` was never assigned and
# analytics-core.ts's `track()` — which reads `globalThis.gtag` — silently
# no-op'd on every custom event. Their absence in any window entirely before
# this date is structural (the pipeline could not deliver them), never a
# measured 0 and never evidence of low traffic. This is distinct from
# GA4_KEY_EVENT_MARKING_DATE: key-event marking affects GA4's Conversions
# *report*, not whether an eventName row exists — this boundary governs the raw
# rows this script reads. No GA4 conversion comparison may cross it.
GA4_FIX_DEPLOY_DATE: date | None = date(2026, 7, 12)  # a572edc -> Cloud Run, verified live


def boundary_caveats(
    w: Window,
    ga4_marking: date | None = GA4_KEY_EVENT_MARKING_DATE,
    umami_filter: date | None = UMAMI_BOT_FILTER_DATE,
    ga4_fix_deploy: date | None = GA4_FIX_DEPLOY_DATE,
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
                f"({ga4_marking.isoformat()}). No conversion figure here is a "
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

    if ga4_fix_deploy is not None:
        if w.start < ga4_fix_deploy <= w.end:
            out.append(
                f"The window.gtag scoping-bug fix deployed "
                f"{ga4_fix_deploy.isoformat()}, **inside this window**. Before that "
                f"date GA4 received **none** of the four custom conversion events — "
                f"window.gtag was never defined, so every track() call was a silent "
                f"no-op (A0). The portion of this window before "
                f"{ga4_fix_deploy.isoformat()} cannot be compared against the "
                f"portion after it: the earlier days have no conversions by design "
                f"of a broken pipeline, not by absence of traffic."
            )
        elif w.end < ga4_fix_deploy:
            out.append(
                f"This window ends before the GA4 gtag-fix deploy date "
                f"({ga4_fix_deploy.isoformat()}). No conversion figure here is a "
                f"measured 0 — GA4 could not receive these events at all yet, "
                f"because window.gtag was never defined (A0). Their absence is "
                f"structural, not a traffic signal, and this window may not be "
                f"compared against any post-deploy month."
            )

    return out
