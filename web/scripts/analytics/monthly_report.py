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
import deltas
import ga4
import gsc
import history
import indexation as indexation_mod
import pinned
import published
import readouts
import report
import umami
import window
from report import Metric
from window import Window

# Default GA4 install date — the earliest date GA4 has any data. Confirm against
# the property (GA4 Admin > Data collection start) and override with --ga4-start.
DEFAULT_GA4_START = "2026-06-28"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

BASE_CAVEATS = [
    "Umami = reach truth; GA4 = channel/conversion truth; GSC = pre-click/demand "
    "truth (Google organic only). Figures are never averaged (ctx 05 §4).",
    "GSC is blind to LinkedIn — currently most of this site's traffic. A flat GSC "
    "month says nothing about overall reach.",
]

SKIP_GSC_CAVEAT = (
    "The GSC lane was deliberately skipped — the empty search demand and indexation "
    "sections below are an absence of measurement, not a finding of zero search demand."
)

CHANNEL_SUM_CAVEAT = (
    "GA4's channel-table session counts are summed per-dimension (per channel) and "
    "can differ from GA4's unfiltered site-wide session total — session "
    "modeling/bucketing on a not-yet-final month. Expected, not a discrepancy to chase."
)

GSC_WITHHELD_CAVEAT = (
    "Google withholds rare queries for privacy, so the GSC query rows do not sum to "
    "the totals row. Expected, not a discrepancy to chase."
)


def _parse_iso(s: str) -> date:
    return date.fromisoformat(s)


def partial_month_caveat(month: str, w: Window, today: date) -> str | None:
    """A month that has not finished must say so.

    Umami and GA4 both assume the calendar month equals the measured window
    (unlike GSC's empirically-detected coverage). Without this, a comparison
    against a full prior month reads as a traffic collapse when it is really just
    fewer elapsed days. Pure so that B2 can reuse the same signal to BLOCK the
    delta rather than merely annotate it.
    """
    if w.end < today:
        return None
    elapsed_end = min(today, w.end)
    return (
        f"{month} is a **partial month** — as of {today.isoformat()} only "
        f"{w.start.isoformat()}..{elapsed_end.isoformat()} has elapsed. "
        f"Every Umami and GA4 figure in this report is provisional and must not "
        f"be compared against a full month; a lower count here can simply mean "
        f"fewer days have happened yet, not a decline in traffic."
    )


def ga4_clamp_caveat(month_w: Window, cmp_w: Window) -> str | None:
    """GA4's window is clamped to the install date; Umami's is not."""
    if cmp_w.start == month_w.start:
        return None
    return (
        f"GA4 figures cover {cmp_w.start}..{cmp_w.end} only "
        f"(clamped to the GA4 install date); Umami reach covers the full month."
    )


def gsc_coverage_caveat(month: str, month_w: Window, cov: Window) -> str | None:
    """GSC lags ~2-3 days. Never claim a month GSC did not measure."""
    if (cov.start, cov.end) == (month_w.start, month_w.end):
        return None
    return (
        f"GSC covers {cov.start}..{cov.end} of {month} only "
        f"(~2-day reporting lag) — the month is not fully measured."
    )


def no_ga4_window_flags(month: str, ga4_start: str) -> list[Metric]:
    """The cmp_w-is-None branch: a month wholly predating the GA4 install.

    It has no GA4 counterpart at all. That is an absence of measurement, and it
    is FLAGGED — never rendered as a measured 0.
    """
    return [Metric(
        "GA4 channel & conversions", "pending", "GA4",
        note=f"{month} predates GA4 install ({ga4_start}) — no GA4 counterpart",
    )]


def no_gsc_data_flags(month: str) -> list[Metric]:
    """The fetch_coverage-is-None branch: GSC returned nothing for this month.

    "No GSC data" and "no search demand" are different claims, and only one of
    them is true. Both lanes flag as pending.
    """
    note = f"no Search Console data in {month} — not a measured zero"
    return [
        Metric("GSC search demand", "pending", "GSC", note=note),
        Metric("GSC indexation", "pending", "GSC", note=note),
    ]


def assemble_sections(
    reach: list[Metric],
    channel: list[Metric],
    conversions_section: list[Metric],
    gsc_totals: list[Metric],
    gsc_queries: list[Metric],
    gsc_pages: list[Metric],
    gsc_pinned: list[Metric],
    gsc_countries: list[Metric],
    indexation: list[Metric],
    indexation_verdict: list[Metric],
    flagged: list[Metric],
) -> list[report.Section]:
    """The report's shape. These titles are a CONTRACT, not decoration:
    history.is_void() and deltas.STABLE_KEY_SECTIONS both key off them. Rename
    one and you silently switch off a refusal rule — hence the test.

    GSC is split by dimension (totals / queries / pages / countries) rather than
    one concatenated table, because a shared "Metric" column cannot otherwise
    tell a country row ("USA") from a query row ("unstructured data extraction").
    """
    return [
        report.Section("Reach (Umami)", reach),
        report.Section("Channel & engagement (GA4)", channel),
        report.Section("Conversions", conversions_section),
        report.Section("Search demand — totals (GSC)", gsc_totals),
        report.Section("Top queries (GSC)", gsc_queries),
        report.Section("Top pages (GSC)", gsc_pages),
        report.Section("Pinned pages (GSC)", gsc_pinned),
        report.Section("Top countries (GSC)", gsc_countries),
        report.Section("Indexation (GSC)", indexation),
        report.Section("Indexation verdict (GSC)", indexation_verdict),
        report.Section("Flagged / pending (no counterpart or traffic-gated)", flagged),
    ]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--umami-dir", required=True, help="unpacked Umami export dir (has website_event.csv)")
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--ga4-start", default=DEFAULT_GA4_START, help="GA4 data-collection start YYYY-MM-DD")
    p.add_argument("--property-id", default=ga4.property_id())
    p.add_argument("--out", default=None, help="report path (default docs/.ai/reports/analytics/<month>.md)")
    p.add_argument("--skip-gsc", action="store_true",
                   help="skip the Search Console lane (offline runs / no GSC credentials)")
    args = p.parse_args()

    month_w = window.month_window(args.month)
    ga4_start = _parse_iso(args.ga4_start)
    cmp_w = window.comparison_window(month_w, ga4_start)

    today = date.today()
    partial = month_w.end >= today

    caveats = list(BASE_CAVEATS)
    caveats.extend(boundaries.boundary_caveats(month_w))
    if args.skip_gsc:
        caveats.append(SKIP_GSC_CAVEAT)
    partial_c = partial_month_caveat(args.month, month_w, today)
    if partial_c:
        caveats.append(partial_c)

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
        flagged.extend(no_ga4_window_flags(args.month, args.ga4_start))
    else:
        clamp_c = ga4_clamp_caveat(month_w, cmp_w)
        if clamp_c:
            caveats.append(clamp_c)
        client = ga4.build_client()
        channel = ga4.fetch_channel_engagement(client, args.property_id, cmp_w)
        if channel:
            caveats.append(CHANNEL_SUM_CAVEAT)

        sitewide = ga4.fetch_sitewide_engagement(client, args.property_id, cmp_w)
        if sitewide is not None:
            channel.append(sitewide)
        else:
            flagged.append(Metric(
                ga4.SITEWIDE_PPS_NAME, "pending", "GA4",
                note="GA4 reported no site-wide pages/session in this window — not a measured 0",
            ))

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
    gsc_totals: list[Metric] = []
    gsc_queries: list[Metric] = []
    gsc_pages: list[Metric] = []
    gsc_pinned: list[Metric] = []
    gsc_countries: list[Metric] = []
    indexation: list[Metric] = []
    indexation_verdict: list[Metric] = []
    if args.skip_gsc:
        indexation_verdict = indexation_mod.unmeasured_verdict(
            "the GSC lane was deliberately skipped (--skip-gsc)"
        )
    else:
        sa_path, site = gsc.load_config()
        gclient = gsc.build_client(sa_path)
        cov = gsc.fetch_coverage(gclient, site, month_w)
        if cov is None:
            flagged.extend(no_gsc_data_flags(args.month))
            indexation_verdict = indexation_mod.unmeasured_verdict(
                f"no Search Console data in {args.month}"
            )
        else:
            cov_c = gsc_coverage_caveat(args.month, month_w, cov)
            if cov_c:
                caveats.append(cov_c)
            gsc_totals = gsc.fetch_totals(gclient, site, cov)
            gsc_queries = gsc.fetch_top_queries(gclient, site, cov)
            gsc_pages = gsc.fetch_top_pages(gclient, site, cov)
            gsc_pinned = pinned.pinned_metrics(gsc.fetch_page_rows(gclient, site, cov))
            gsc_countries = gsc.fetch_countries(gclient, site, cov)
            caveats.append(GSC_WITHHELD_CAVEAT)
            urls = published.published_in(published.run_post_status(REPO_ROOT), month_w)
            indexation = gsc.inspect_urls(gclient, site, urls)
            indexation_verdict = indexation_mod.verdict_metrics(indexation)

    sections = assemble_sections(
        reach, channel, conversions_section,
        gsc_totals, gsc_queries, gsc_pages, gsc_pinned, gsc_countries,
        indexation, indexation_verdict, flagged,
    )

    # Read history BEFORE this month is recorded, or the month becomes its own
    # prior and every delta reads as 0. Every refusal is stamped into the cell
    # by name — see deltas.py's five rules.
    #
    # attach_deltas and build_readouts have OPPOSITE requirements of this same
    # snapshot: attach_deltas must NOT see this month's own rows (or the month
    # becomes its own prior and every future delta zeroes out), but C3b in
    # build_readouts is looking for THIS month's site-wide pages/session row —
    # which is not in `hist` yet, because record_month() has not run. Passing
    # `hist` alone to build_readouts is what used to make C3b falsely claim GA4
    # emitted nothing (or, on a second run, show a stale prior-run figure) even
    # though the Channel & engagement table three sections above had the real
    # number. So `hist` stays untainted for attach_deltas, and build_readouts
    # gets `cur_rows + hist` instead. This is safe: `_c3b_cell`'s prior-month
    # lookup keys on deltas.prior_month(month), a DIFFERENT month string, so
    # adding this month's own rows can never make it its own prior.
    hist = history.load()
    deltas.attach_deltas(sections, args.month, month_w, hist, partial)
    cur_rows = history.rows_from_sections(args.month, month_w, sections, partial)
    md = report.render_report(
        args.month, sections, caveats,
        readouts=readouts.build_readouts(args.month, cur_rows + hist),
    )

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
