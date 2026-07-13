"""The pinned-page watchlist — a metric series that survives a bad month.

GSC's "Top pages" table cannot measure a page over time, for two independent
reasons, and both of them bite in the same direction:

  1. IT NEVER DELTAS. "Top pages (GSC)" is not in deltas.STABLE_KEY_SECTIONS —
     correctly, because its keys churn: a page that "appears" has usually moved
     from rank 11 to rank 10.
  2. IT DISAPPEARS. history.rows_from_sections stores only what the report
     RENDERED. A page that drops out of the top-10 is simply absent from that
     month's history — so the series goes blank precisely when the page gets
     worse. A watchlist that only records winners is not a measurement.

So the pinned pages are fetched BY NAME, not by rank, out of the full page
breakdown, and they are emitted into their own stable-key section
("Pinned pages (GSC)"). A pinned page GSC returns no row for is `pending` with
a stated reason — NEVER 0. It did not get zero impressions; we do not know what
it got. (gsc.inspect_urls already sets this idiom; this follows it.)

ONE MEASURE PER ROW, and every value bare-numeric. GSC's usual composite —
"41 impr · 0 clicks · 0.00% CTR · pos 3.9" — parses to "" through
history.parse_numeric, and deltas.delta_for then refuses the row forever as
"non-numeric value". Being in STABLE_KEY_SECTIONS is necessary; being numeric
is the other half.

The list lives HERE, in code, because anything that must survive lives in code:
a list kept in the rendered .md is silently deleted by the next regeneration
(see report.ROLLING_READOUTS, which exists for exactly that reason).
"""
from __future__ import annotations

from report import Metric

SITE_HOST = "bessavagner.com"

# The three C3 title-experiment targets, plus the two D-cluster pages, so that
# D1 and D2 inherit the instrument for free the moment this ships: their
# impressions and position become a stable series with no further work.
PINNED_PATHS: tuple[str, ...] = (
    "/building/regwatch/02-fetching-the-gazette-inlabs-ingestor/",  # C3b target
    "/blog/fast-molecular-dynamics-in-numpy/",                      # C3b target
    "/",                                                            # C3b target (homepage)
    "/blog/pulling-structured-data-from-unstructured-documents/",   # D1
    "/blog/beating-browser-fingerprinting/",                        # D2
)

MEASURES: tuple[str, ...] = ("impressions", "clicks", "CTR", "position")

_ABSENT_NOTE = (
    "GSC returned no row for this pinned page in this window — pending, "
    "NOT a measured 0: the page did not get zero impressions, we do not know "
    "what it got"
)
_POSITION_NOTE = (
    "average position — LOWER IS BETTER, so a positive delta here is a WORSE rank"
)
_CTR_NOTE = "a delta on this row is in percentage POINTS, not percent"


def _path(url: str) -> str:
    return url.split(SITE_HOST, 1)[-1] or url


def _name(path: str, measure: str) -> str:
    return f"{path} — {measure}"


def pinned_metrics(
    page_rows: list[dict], paths: tuple[str, ...] = PINNED_PATHS
) -> list[Metric]:
    """Four numeric metrics per pinned page, looked up BY NAME. Pure.

    `page_rows` is GSC's FULL page breakdown for the window (gsc.fetch_page_rows)
    — not the top-N slice, which is the whole point.
    """
    by_path = {_path(r["keys"][0]): r for r in page_rows}
    out: list[Metric] = []
    for path in paths:
        r = by_path.get(path)
        if r is None:
            out.extend(
                Metric(_name(path, measure), "pending", "GSC", note=_ABSENT_NOTE)
                for measure in MEASURES
            )
            continue
        out.append(Metric(_name(path, "impressions"), str(r["impressions"]), "GSC"))
        out.append(Metric(_name(path, "clicks"), str(r["clicks"]), "GSC"))
        out.append(Metric(
            _name(path, "CTR"), f"{r['ctr'] * 100:.2f}%", "GSC", note=_CTR_NOTE,
        ))
        out.append(Metric(
            _name(path, "position"), f"{r['position']:.1f}", "GSC", note=_POSITION_NOTE,
        ))
    return out
