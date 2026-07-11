#!/usr/bin/env python3
"""Merge the Umami CSV export + the GA4 Data API into one monthly Markdown report.

Read-only against GA4 (Data API) — no owner write-confirmation needed. Enforces
overlapping-window comparison (ctx 05 §1) and never averages the two tools
(ctx 05 §4). Run from ~/.config/claude-seo/ga4-venv.

Usage (from web/scripts/analytics/):
    python monthly_report.py --umami-dir /tmp/umami-2026-08 --month 2026-08 --ga4-start 2026-06-28
"""
from __future__ import annotations

import argparse
import os
from datetime import date

import ga4
import report
import umami
import window
from report import Metric

# Default GA4 install date — the earliest date GA4 has any data. Confirm against
# the property (GA4 Admin > Data collection start) and override with --ga4-start.
DEFAULT_GA4_START = "2026-06-28"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _parse_iso(s: str) -> date:
    return date.fromisoformat(s)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--umami-dir", required=True, help="unpacked Umami export dir (has website_event.csv)")
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--ga4-start", default=DEFAULT_GA4_START, help="GA4 data-collection start YYYY-MM-DD")
    p.add_argument("--property-id", default=ga4.property_id())
    p.add_argument("--out", default=None, help="report path (default docs/.ai/reports/analytics/<month>.md)")
    p.add_argument("--bots-unfiltered", action="store_true",
                   help="Umami bot filtering (A6) not confirmed live — add the caveat")
    args = p.parse_args()

    month_w = window.month_window(args.month)
    ga4_start = _parse_iso(args.ga4_start)
    cmp_w = window.comparison_window(month_w, ga4_start)

    caveats = [
        "Umami = reach truth; GA4 = channel/conversion truth. Figures are never averaged (ctx 05 §4).",
    ]
    if args.bots_unfiltered:
        caveats.append(
            "Umami bot filtering (A6) not confirmed live — raw Umami counts may be bot-inflated; "
            "do not treat a spike as real until UA/IP filtering is confirmed."
        )

    # --- Umami reach (whole month; Umami has the longer history) ---
    rows = umami.load_website_events(args.umami_dir)
    reach = [
        Metric(
            f"{canon} (raw event count)",
            str(umami.count_event(rows, aliases, month_w.start, month_w.end)),
            "Umami",
        )
        for canon, aliases in umami.CONVERSION_EVENTS.items()
    ]

    # --- GA4 channel/conversion (overlapping window only) ---
    channel: list[Metric] = []
    conversions: list[Metric] = []
    flagged: list[Metric] = []
    if cmp_w is None:
        # Whole month predates GA4 — flag, do NOT zero-fill (ctx 05 §1).
        note = f"{args.month} predates GA4 install ({args.ga4_start}) — no GA4 counterpart"
        flagged.append(Metric("GA4 channel & conversions", "pending", "GA4", note=note))
    else:
        if cmp_w.start != month_w.start:
            caveats.append(
                f"GA4 figures cover {cmp_w.start}..{cmp_w.end} only "
                f"(clamped to the GA4 install date); Umami reach covers the full month."
            )
        client = ga4.build_client()
        channel = ga4.fetch_channel_engagement(client, args.property_id, cmp_w)
        conversions = ga4.fetch_key_event_counts(
            client, args.property_id, cmp_w, list(umami.CONVERSION_EVENTS.keys())
        )

    md = report.render_report(args.month, reach, channel, conversions, flagged, caveats)

    out = args.out or os.path.join(REPO_ROOT, "docs", ".ai", "reports", "analytics", f"{args.month}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
