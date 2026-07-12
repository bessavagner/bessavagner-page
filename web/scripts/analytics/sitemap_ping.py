#!/usr/bin/env python3
"""Ask Google to re-download the sitemap NOW, instead of waiting for its own crawl.

Why this exists: the GSC sitemaps API can report a `lastDownloaded` timestamp
and a submitted-URL count that are stale relative to the live sitemap — e.g.
Google's copy sees 65 URLs when the live sitemap already has 77. This is not a
site defect (pages 200, correct canonical, no noindex, in-sitemap, internally
linked) — it is purely Google working from an old copy. Resubmitting nudges
Google to re-read it sooner.

Uses a SEPARATE write-scoped client (gsc.build_write_client) for the actual
submit, and the existing read-only client (gsc.build_client) to report state
before and after — the monthly report pipeline's read-only credentials are
never touched or upgraded by this script.

Usage (from web/scripts/analytics/):
    source ~/.config/claude-seo/ga4-venv/bin/activate
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    python sitemap_ping.py
    python sitemap_ping.py --sitemap-url https://bessavagner.com/sitemap-index.xml --property sc-domain:bessavagner.com
"""
from __future__ import annotations

import argparse

import gsc

DEFAULT_SITEMAP_URL = "https://bessavagner.com/sitemap-index.xml"


def _print_state(client, site: str, label: str) -> None:
    print(f"--- {label} ---")
    sitemaps = gsc.get_sitemaps(client, site)
    if not sitemaps:
        print("(no sitemaps registered for this property)")
        return
    for sm in sitemaps:
        last = sm["lastDownloaded"] or "never"
        print(f"{sm['path']}  lastDownloaded={last}  submitted={sm['submitted']}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sitemap-url", default=DEFAULT_SITEMAP_URL, help="feedpath to resubmit")
    p.add_argument("--property", default=None, help="GSC site property (default: gsc.load_config())")
    p.add_argument("--config", default=None, help="path to the claude-seo google-api.json config")
    args = p.parse_args()

    sa_path, default_site = gsc.load_config(args.config)
    site = args.property or default_site

    read_client = gsc.build_client(sa_path)
    print(f"property: {site}")
    _print_state(read_client, site, "BEFORE")

    write_client = gsc.build_write_client(sa_path)
    gsc.submit_sitemap(write_client, site, args.sitemap_url)
    print(f"\nsubmitted {args.sitemap_url} for {site}\n")

    _print_state(read_client, site, "AFTER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
