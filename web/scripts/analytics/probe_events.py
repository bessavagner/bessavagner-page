#!/usr/bin/env python3
"""Raw GA4 eventName probe over an ARBITRARY window — Epic A's A0 instrument.

Answers exactly one question: did GA4 actually receive these events, in this
window, at all? Read-only (Data API).

Why this exists and monthly_report.py does not suffice: the report can only ask
about a calendar month, and the July window is the wrong question. The dual-track
helper (analytics-core.ts `track()` firing Umami *and* gtag) shipped 2026-07-09,
so ~27 of July's 30 days predate GA4 ever receiving these events. Probing the
month would "prove" a break that is really an install date.

Two things to know before trusting a result:
  1. Fire all four events BY HAND first, against a production/preview build, in a
     clean ad-blocker-free profile — `import.meta.env.PROD` gates gtag, so the dev
     server never exercises the GA4 path. Only then is a missing event evidence of
     a broken binding rather than of low traffic.
  2. The Data API lags real time (up to ~24-48h). DebugView is the real-time check;
     this probe is the durable one. An empty probe + a green DebugView means
     PROCESSING LAG — re-probe tomorrow, do not conclude REFUTES.

Usage (from web/scripts/analytics/, in the ga4-venv):
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    python probe_events.py --start 2026-07-09 --end 2026-07-12
"""
from __future__ import annotations

import argparse
from datetime import date

import ga4
import umami
from report import Metric
from window import Window

CONFIRMS = "CONFIRMS"
PARTIAL = "PARTIAL"
REFUTES = "REFUTES"


def verdict(reported: list[Metric], missing: list[str]) -> tuple[str, str]:
    """Turn a probe result into A0's gate decision. Pure — no client needed.

    A0 asks whether the events reach GA4 *at all*. Any event GA4 reported —
    even with a count of 0, which is a measured zero and therefore a delivered
    row — proves the pipeline delivers.
    """
    if reported and not missing:
        return CONFIRMS, (
            "GA4 reported every probed event — the pipeline delivers. GA4's "
            "silence in the monthly report is low volume plus a days-old install, "
            "not a break. Proceed to A1."
        )
    if reported:
        total = len(reported) + len(missing)
        return PARTIAL, (
            f"GA4 reported {len(reported)} of {total} probed events; NO ROWS for: "
            f"{', '.join(missing)}. The transport works, so these are either "
            f"individually broken bindings or were not actually fired in this "
            f"window. Fire each one by hand against prod and re-probe before A1."
        )
    return REFUTES, (
        "GA4 reported NO ROWS for any probed event. The bindings do not reach GA4. "
        "STOP: do not run A1 against a pipeline that isn't delivering. The epic is "
        "not S — re-plan it (sprint 07, A0 DoD). First rule out Data API processing "
        "lag by checking DebugView in real time."
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", required=True, help="window start YYYY-MM-DD")
    p.add_argument("--end", required=True, help="window end YYYY-MM-DD")
    p.add_argument("--property-id", default=ga4.property_id())
    args = p.parse_args()

    w = Window(date.fromisoformat(args.start), date.fromisoformat(args.end))
    names = list(umami.CONVERSION_EVENTS.keys())

    client = ga4.build_client()
    reported, missing = ga4.fetch_key_event_counts(client, args.property_id, w, names)

    print(f"GA4 property {args.property_id}, window {w.start}..{w.end}")
    print(f"probed: {', '.join(names)}\n")
    for m in reported:
        print(f"  reported  {m.name:20} eventCount={m.value}")
    for name in missing:
        print(f"  NO ROW    {name:20} (an absence, never a measured 0)")

    status, why = verdict(reported, missing)
    print(f"\nVERDICT: {status}\n{why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
