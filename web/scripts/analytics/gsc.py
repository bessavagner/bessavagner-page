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
from datetime import date, datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from report import Metric
from window import Window

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Deliberately a SEPARATE scope from SCOPES above, used ONLY by
# build_write_client / submit_sitemap. build_client (and therefore the
# monthly report pipeline) must keep read-only credentials forever — see
# build_write_client for the write-only path.
WRITE_SCOPES = ["https://www.googleapis.com/auth/webmasters"]

DEFAULT_CONFIG = os.path.expanduser("~/.config/claude-seo/google-api.json")


class ConfigError(Exception):
    """Raised when the Search Console credentials cannot be located."""


class AccessError(Exception):
    """Raised when the service account cannot read the property.

    Loud on purpose. A silently-empty GSC section reads as 'no search demand',
    which is the most dangerous wrong answer this module can give.
    """


class TruncationError(Exception):
    """Raised when a breakdown fetch hits the API's row-limit ceiling.

    Loud on purpose, same idiom as AccessError. The Search Analytics API
    truncates server-side by clicks descending (see _BREAKDOWN_FETCH_LIMIT),
    so a response that comes back exactly at the ceiling means we cannot
    tell whether it is the whole dataset or a clicks-biased partial sample.
    Ranking that sample by impressions and slicing to top-N would silently
    resurrect the exact bug this module exists to prevent — a low-impression,
    high-click page or query displacing the true top result, which the API's
    truncation hid before we ever got to sort it. The only correct fix when
    this fires is to page the API (loop on startRow), not to raise the limit
    further.
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


def build_write_client(sa_path: str):
    """A SEPARATE client scoped for writes (sitemap submission only).

    Never use this for the monthly report pipeline — that must stay on
    build_client's read-only scope. See submit_sitemap.
    """
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=WRITE_SCOPES)
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


# The Search Analytics API has no `orderBy` parameter: `rowLimit` truncates
# server-side, before this code ever sees the rows, and the API's own order
# is clicks descending. On a site like this one — 3 clicks total across ~35
# queries — every row ties on zero clicks, so the tie-break the API falls
# back to is effectively alphabetical. That means a naive `rowLimit=N` fetch
# returns the top N by CLICKS (alphabetical among zero-click ties), NOT the
# top N by impressions — and impressions are the entire point of this lane
# (GSC = pre-click/demand truth). Verified against the live API: with
# limit=10 the true #1 query by impressions (22) was absent from the
# response entirely. So we fetch at the API's documented ceiling — a single
# call retrieves every row that could possibly exist for any realistically
# sized site — sort by impressions locally, then slice to the caller's
# requested limit. See TruncationError below for what happens if a
# dimension's true row count ever reaches the ceiling anyway.
_BREAKDOWN_FETCH_LIMIT = 25_000


def _raw_breakdown(client, site: str, w: Window, dimension: str) -> list[dict]:
    """Every row for one dimension, unsorted and unsliced, truncation-guarded."""
    rows = _query(client, site, w, [dimension], limit=_BREAKDOWN_FETCH_LIMIT)
    if len(rows) == _BREAKDOWN_FETCH_LIMIT:
        raise TruncationError(
            f"GSC breakdown for dimension={dimension!r} returned exactly "
            f"_BREAKDOWN_FETCH_LIMIT ({_BREAKDOWN_FETCH_LIMIT}) rows — the "
            f"Search Analytics API almost certainly truncated the response "
            f"server-side. The API has no orderBy and truncates by clicks "
            f"descending, before this code ever sees the rows, so a "
            f"truncated response is a clicks-biased partial sample, not the "
            f"full dataset. Ranking it by impressions and slicing to top-N "
            f"would silently reintroduce the exact bug this module exists "
            f"to prevent (see the comment above _BREAKDOWN_FETCH_LIMIT): a "
            f"low-impression, high-click row could displace the true top "
            f"result, which the truncation hid before we ever got to sort "
            f"it. Refusing to emit an untrustworthy ranking. The fix is to "
            f"page the API (loop on startRow) for this dimension, not to "
            f"raise the limit further."
        )
    return rows


def _fetch_breakdown(
    client,
    site: str,
    w: Window,
    dimension: str,
    limit: int,
    name_fn=lambda r: r["keys"][0],
) -> list[Metric]:
    rows = _raw_breakdown(client, site, w, dimension)
    rows.sort(key=lambda r: r["impressions"], reverse=True)
    return [Metric(name_fn(r), _fmt_row(r), "GSC") for r in rows[:limit]]


def fetch_page_rows(client, site: str, w: Window) -> list[dict]:
    """Every page row for the window — unsorted, unsliced, raw.

    The pinned-page watchlist (pinned.py) looks its pages up BY NAME, not by
    rank: a page that fell out of the top-10 is exactly the page whose series
    must not go blank. So it needs the whole breakdown, not fetch_top_pages'
    ranked slice.
    """
    return _raw_breakdown(client, site, w, "page")


def fetch_top_queries(client, site: str, w: Window, limit: int = 10) -> list[Metric]:
    return _fetch_breakdown(client, site, w, "query", limit)


def fetch_top_pages(client, site: str, w: Window, limit: int = 10) -> list[Metric]:
    def _path(r: dict) -> str:
        url = r["keys"][0]
        return url.split("bessavagner.com", 1)[-1] or url

    return _fetch_breakdown(client, site, w, "page", limit, name_fn=_path)


def fetch_countries(client, site: str, w: Window, limit: int = 5) -> list[Metric]:
    return _fetch_breakdown(
        client, site, w, "country", limit, name_fn=lambda r: r["keys"][0].upper()
    )


def inspect_urls(client, site: str, urls: list[str]) -> list[Metric]:
    """Index status per URL, via the URL Inspection API.

    A failed inspection is reported as PENDING, never as 'not indexed'. Those are
    opposite conclusions: 'not indexed' sends you rewriting a page that may be
    perfectly fine, when all that actually happened was a quota error.
    """
    out: list[Metric] = []
    for url in urls:
        path = url.split("bessavagner.com", 1)[-1] or url
        try:
            resp = (
                client.urlInspection()
                .index()
                .inspect(body={"inspectionUrl": url, "siteUrl": site})
                .execute()
            )
        except HttpError as e:
            out.append(Metric(
                path, "pending", "GSC",
                note=f"inspection failed ({e.resp.status}) — NOT a 'not indexed' verdict; re-run",
            ))
            continue
        except Exception as e:  # noqa: BLE001 — one bad URL must not sink the batch
            # Network errors, auth refresh failures, unexpected response shapes,
            # etc. Same rule as the HttpError branch above: degrade THIS url to
            # pending and keep going, so the other urls' results survive. Strip
            # newlines/pipes so the note stays a single clean Markdown-table cell.
            detail = f"{type(e).__name__}: {e}".replace("\n", " ").replace("|", "/")
            out.append(Metric(
                path, "pending", "GSC",
                note=f"inspection failed ({detail}) — NOT a 'not indexed' verdict; re-run",
            ))
            continue
        state = (
            resp.get("inspectionResult", {})
            .get("indexStatusResult", {})
            .get("coverageState", "")
        )
        if not state:
            out.append(Metric(
                path, "pending", "GSC",
                note="inspection returned no coverageState — NOT a 'not indexed' verdict; re-run",
            ))
            continue
        out.append(Metric(path, state, "GSC"))
    return out


def submit_sitemap(client, site: str, sitemap_url: str) -> None:
    """Ask Google to re-download `sitemap_url` NOW, instead of waiting for its own crawl.

    Requires a WRITE-scoped client (build_write_client), NOT build_client — a
    read-only-scoped credential will 403 here. Same loud-failure idiom as
    _query's AccessError: a silently-swallowed 403 is the dangerous case,
    because the operator would believe Google was pinged when it was not.
    """
    try:
        client.sitemaps().submit(siteUrl=site, feedpath=sitemap_url).execute()
    except HttpError as e:
        if e.resp.status == 403:
            raise AccessError(
                f"403 submitting sitemap {sitemap_url!r} for {site}. Sitemap "
                f"submission needs the service account to be an OWNER on the "
                f"property (Search Console > Settings > Users and permissions) "
                f"AND the write scope ({WRITE_SCOPES[0]}) — a read-only-scoped "
                f"credential (build_client) will always 403 here; use "
                f"build_write_client instead. Refusing to report success when "
                f"the submit did not actually happen."
            ) from e
        raise


def get_sitemaps(client, site: str) -> list[dict]:
    """Current sitemap state: path, lastDownloaded, and submitted-URL count.

    Read-only (fine to call with build_client). Lets the operator SEE the
    staleness before submit_sitemap and confirm Google re-downloaded after.
    """
    resp = client.sitemaps().list(siteUrl=site).execute()
    out: list[dict] = []
    for entry in resp.get("sitemap", []):
        # contents[].submitted is an int64, which the JSON API serializes as
        # a string — cast defensively so callers get a real int either way.
        submitted = sum(int(c.get("submitted", 0)) for c in entry.get("contents", []))
        out.append({
            "path": entry.get("path", ""),
            "lastDownloaded": entry.get("lastDownloaded", ""),
            "submitted": submitted,
        })
    return out


STALE_AFTER_DAYS = 14

_NO_SITEMAP_NOTE = (
    "no sitemap is registered for this property at all — pending, and the "
    "loudest possible finding: nothing is being submitted to Google"
)
_NEVER_NOTE = (
    "Google has NEVER downloaded this sitemap — pending, not 0 days: "
    "'0 days since download' would read as perfectly fresh, the exact "
    "inversion of the truth"
)
_NEVER_SUBMITTED_NOTE = (
    "Google has NEVER downloaded this sitemap — 'submitted' is pending, not "
    "a measured 0: contents (and therefore the submitted count) are only "
    "populated once Google processes the file, so a bare 0 here would read "
    "as 'the sitemap is empty' rather than 'nothing has been measured yet'"
)


def sitemap_freshness_metrics(sitemaps: list[dict], today: date) -> list[Metric]:
    """The report's own sitemap read — C4.

    The CI ping is `continue-on-error` with `exit 0` on every path and emits
    only `::warning::`, so a silent regression is currently indistinguishable
    from success. Nothing fails and nobody reads warnings. This puts the
    staleness in the monthly report, where it deltas.
    """
    if not sitemaps:
        return [
            Metric("Sitemap registered", "pending", "GSC", note=_NO_SITEMAP_NOTE),
            Metric("URLs submitted", "pending", "GSC", note=_NO_SITEMAP_NOTE),
        ]

    out: list[Metric] = []
    for sm in sitemaps:
        path = sm["path"]
        last = sm["lastDownloaded"]
        if not last:
            out.append(Metric(
                f"{path} — days since last download", "pending", "GSC",
                note=_NEVER_NOTE,
            ))
            out.append(Metric(
                f"{path} — URLs submitted", "pending", "GSC",
                note=_NEVER_SUBMITTED_NOTE,
            ))
        else:
            downloaded = datetime.fromisoformat(last.replace("Z", "+00:00")).date()
            days = (today - downloaded).days
            note = (
                f"STALE — Google's copy is {days} days old (> {STALE_AFTER_DAYS})"
                if days > STALE_AFTER_DAYS else ""
            )
            out.append(Metric(
                f"{path} — days since last download", str(days), "GSC", note=note,
            ))
            out.append(Metric(f"{path} — URLs submitted", str(sm["submitted"]), "GSC"))
    return out
