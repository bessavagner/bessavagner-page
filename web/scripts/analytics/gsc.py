"""Google Search Console pull (read-only). The THIRD truth lane.

ctx 05 §4 fixes Umami = reach truth and GA4 = channel/conversion truth. Neither
sees anything before the click. GSC is the pre-click lane:

    GSC = demand truth, GOOGLE ORGANIC ONLY.

It is blind to LinkedIn, which is currently most of this site's traffic. GSC
clicks, GA4 sessions and Umami pageviews are three different instruments and are
never averaged into one figure.

Unlike GA4 there is no hardcoded install date here: fetch_coverage detects the
real data range empirically, because GSC lags ~2-3 days and the data knows its
own start better than a constant does.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from report import Metric
from window import Window

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DEFAULT_CONFIG = os.path.expanduser("~/.config/claude-seo/google-api.json")


class ConfigError(Exception):
    """Raised when the Search Console credentials cannot be located."""


class AccessError(Exception):
    """Raised when the service account cannot read the property.

    Loud on purpose. A silently-empty GSC section reads as 'no search demand',
    which is the most dangerous wrong answer this module can give.
    """


def load_config(path: str | None = None) -> tuple[str, str]:
    cfg_path = path or os.environ.get("CLAUDE_SEO_CONFIG", DEFAULT_CONFIG)
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError as e:
        raise ConfigError(
            f"Search Console config not found at {cfg_path}. It must be a JSON file "
            f"with 'service_account_path' and 'default_property'."
        ) from e

    sa = os.path.expanduser(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or cfg.get("service_account_path", "")
    )
    site = os.environ.get("GSC_SITE_URL") or cfg.get("default_property", "")
    if not sa or not site:
        raise ConfigError(
            f"{cfg_path} is missing 'service_account_path' and/or 'default_property'."
        )
    if not os.path.exists(sa):
        raise ConfigError(f"service-account key file does not exist: {sa}")
    return sa, site


def build_client(sa_path: str):
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def _query(client, site: str, w: Window, dimensions: list[str], limit: int = 25) -> list[dict]:
    body = {
        "startDate": w.start.isoformat(),
        "endDate": w.end.isoformat(),
        "dimensions": dimensions,
        "rowLimit": limit,
    }
    try:
        resp = client.searchanalytics().query(siteUrl=site, body=body).execute()
    except HttpError as e:
        if e.resp.status == 403:
            raise AccessError(
                f"403 from Search Console for {site}. The service account is not a user "
                f"on that property (or the property name is wrong). Add it in Search "
                f"Console > Settings > Users and permissions. Refusing to emit an empty "
                f"GSC section, which would read as 'no search demand'."
            ) from e
        raise
    return resp.get("rows", [])


def fetch_coverage(client, site: str, w: Window) -> Window | None:
    """The ACTUAL first/last day with data inside the month.

    Returns None when the month has no GSC data at all — the caller must flag
    that as pending, never zero-fill it (the rule in window.py).
    """
    rows = _query(client, site, w, ["date"], limit=100)
    if not rows:
        return None
    days = sorted(date.fromisoformat(r["keys"][0]) for r in rows)
    return Window(days[0], days[-1])


def _fmt_row(r: dict) -> str:
    return (
        f"{r['impressions']} impr · {r['clicks']} clicks · "
        f"{r['ctr'] * 100:.2f}% CTR · pos {r['position']:.1f}"
    )


def fetch_totals(client, site: str, w: Window) -> list[Metric]:
    rows = _query(client, site, w, [], limit=1)
    if not rows:
        return []  # no data — the caller flags it; never zero-fill
    r = rows[0]
    return [
        Metric("Clicks", str(r["clicks"]), "GSC"),
        Metric("Impressions", str(r["impressions"]), "GSC"),
        Metric("CTR", f"{r['ctr'] * 100:.2f}%", "GSC"),
        Metric(
            "Average position", f"{r['position']:.1f}", "GSC",
            note="impression-weighted; unstable at low volume — a few points is not a trend",
        ),
    ]


def fetch_top_queries(client, site: str, w: Window, limit: int = 10) -> list[Metric]:
    rows = _query(client, site, w, ["query"], limit=limit)
    rows.sort(key=lambda r: r["impressions"], reverse=True)
    return [Metric(r["keys"][0], _fmt_row(r), "GSC") for r in rows]


def fetch_top_pages(client, site: str, w: Window, limit: int = 10) -> list[Metric]:
    rows = _query(client, site, w, ["page"], limit=limit)
    rows.sort(key=lambda r: r["impressions"], reverse=True)
    out = []
    for r in rows:
        url = r["keys"][0]
        path = url.split("bessavagner.com", 1)[-1] or url
        out.append(Metric(path, _fmt_row(r), "GSC"))
    return out


def fetch_countries(client, site: str, w: Window, limit: int = 5) -> list[Metric]:
    rows = _query(client, site, w, ["country"], limit=limit)
    rows.sort(key=lambda r: r["impressions"], reverse=True)
    return [Metric(r["keys"][0].upper(), _fmt_row(r), "GSC") for r in rows]
