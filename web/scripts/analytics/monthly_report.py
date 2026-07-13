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

import boundaries
import conversions
import ga4
import gsc
import history
import published
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
    p.add_argument("--skip-gsc", action="store_true",
                   help="skip the Search Console lane (offline runs / no GSC credentials)")
    args = p.parse_args()

    month_w = window.month_window(args.month)
    ga4_start = _parse_iso(args.ga4_start)
    cmp_w = window.comparison_window(month_w, ga4_start)

    caveats = [
        "Umami = reach truth; GA4 = channel/conversion truth; GSC = pre-click/demand "
        "truth (Google organic only). Figures are never averaged (ctx 05 §4).",
        "GSC is blind to LinkedIn — currently most of this site's traffic. A flat GSC "
        "month says nothing about overall reach.",
    ]
    caveats.extend(boundaries.boundary_caveats(month_w))
    if args.bots_unfiltered:
        caveats.append(
            "Umami bot filtering (A6) not confirmed live — raw Umami counts may be bot-inflated; "
            "do not treat a spike as real until UA/IP filtering is confirmed."
        )
    if args.skip_gsc:
        caveats.append(
            "The GSC lane was deliberately skipped — the empty search demand and indexation "
            "sections below are an absence of measurement, not a finding of zero search demand."
        )

    # A month that has not finished yet must say so. Umami and GA4 both
    # assume the calendar month equals the measured window (unlike GSC's
    # empirically-detected coverage below) — without this caveat, a
    # comparison against a full prior month reads as a traffic collapse
    # when it is really just fewer elapsed days.
    today = date.today()
    partial = month_w.end >= today
    if partial:
        elapsed_end = min(today, month_w.end)
        caveats.append(
            f"{args.month} is a **partial month** — as of {today.isoformat()} only "
            f"{month_w.start.isoformat()}..{elapsed_end.isoformat()} has elapsed. "
            f"Every Umami and GA4 figure in this report is provisional and must not "
            f"be compared against a full month; a lower count here can simply mean "
            f"fewer days have happened yet, not a decline in traffic."
        )

    # --- Umami reach (whole month; Umami has the longer history) ---
    rows = umami.load_website_events(args.umami_dir)
    umami_counts = {
        canon: umami.count_event(rows, aliases, month_w.start, month_w.end)
        for canon, aliases in umami.CONVERSION_EVENTS.items()
    }
    reach = [
        Metric(f"{canon} (raw event count)", str(count), "Umami")
        for canon, count in umami_counts.items()
    ]

    # --- GA4 channel/conversion (overlapping window only) ---
    channel: list[Metric] = []
    conversions_section: list[Metric] = []
    flagged: list[Metric] = []
    if cmp_w is None:
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
        if channel:
            caveats.append(
                "GA4's channel-table session counts are summed per-dimension (per "
                "channel) and can differ from GA4's unfiltered site-wide session "
                "total — session modeling/bucketing on a not-yet-final month. "
                "Expected, not a discrepancy to chase."
            )

        # Conversions assembly (mutual exclusion of the file_download proxy; flag,
        # never zero-fill) is pure and lives in conversions.py, where it is tested.
        reported, missing = ga4.fetch_key_event_counts(
            client, args.property_id, cmp_w, list(umami.CONVERSION_EVENTS.keys())
        )
        proxy = ga4.fetch_file_download_proxy(client, args.property_id, cmp_w)
        conversions_section, conv_flagged = conversions.build_conversions(
            reported, missing, proxy, umami_counts
        )
        flagged.extend(conv_flagged)

    # --- GSC search demand + indexation (third lane; own coverage window) ---
    # Split by dimension (totals / queries / pages / countries) rather than one
    # concatenated table — a shared "Metric" column can't otherwise tell a
    # country row ("USA") from a query row ("unstructured data extraction").
    gsc_totals: list[Metric] = []
    gsc_queries: list[Metric] = []
    gsc_pages: list[Metric] = []
    gsc_countries: list[Metric] = []
    indexation: list[Metric] = []
    if not args.skip_gsc:
        sa_path, site = gsc.load_config()
        gclient = gsc.build_client(sa_path)
        cov = gsc.fetch_coverage(gclient, site, month_w)
        if cov is None:
            flagged.append(Metric(
                "GSC search demand", "pending", "GSC",
                note=f"no Search Console data in {args.month} — not a measured zero",
            ))
            flagged.append(Metric(
                "GSC indexation", "pending", "GSC",
                note=f"no Search Console data in {args.month} — not a measured zero",
            ))
        else:
            if (cov.start, cov.end) != (month_w.start, month_w.end):
                caveats.append(
                    f"GSC covers {cov.start}..{cov.end} of {args.month} only "
                    f"(~2-day reporting lag) — the month is not fully measured."
                )
            gsc_totals = gsc.fetch_totals(gclient, site, cov)
            gsc_queries = gsc.fetch_top_queries(gclient, site, cov)
            gsc_pages = gsc.fetch_top_pages(gclient, site, cov)
            gsc_countries = gsc.fetch_countries(gclient, site, cov)
            caveats.append(
                "Google withholds rare queries for privacy, so the GSC query rows do not "
                "sum to the totals row. Expected, not a discrepancy to chase."
            )
            urls = published.published_in(published.run_post_status(REPO_ROOT), month_w)
            indexation = gsc.inspect_urls(gclient, site, urls)

    sections = [
        report.Section("Reach (Umami)", reach),
        report.Section("Channel & engagement (GA4)", channel),
        report.Section("Conversions", conversions_section),
        report.Section("Search demand — totals (GSC)", gsc_totals),
        report.Section("Top queries (GSC)", gsc_queries),
        report.Section("Top pages (GSC)", gsc_pages),
        report.Section("Top countries (GSC)", gsc_countries),
        report.Section("Indexation (GSC)", indexation),
        report.Section("Flagged / pending (no counterpart or traffic-gated)", flagged),
    ]
    md = report.render_report(args.month, sections, caveats)

    out = args.out or os.path.join(REPO_ROOT, "docs", ".ai", "reports", "analytics", f"{args.month}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out}")

    # The store is a SIDE EFFECT of generating the report, never a separate step
    # someone can forget. Rows go in after the .md is safely on disk, and the
    # upsert replaces this month wholesale — re-running is normal and must be
    # byte-identical.
    history.record_month(args.month, month_w, sections, partial)
    print(f"recorded {args.month} -> {history.HISTORY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
