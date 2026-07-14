"""The indexation VERDICT — a count, not a table.

`Indexation (GSC)` emits one row per URL published that month. Its keys are
URLs, they churn wholesale month to month, and delta rule 5 refuses the whole
section by name — correctly. So a row placed in it can never trend, and an
unindexed post stays buried in a 15-line table nobody scans.

A COUNT is a stable series. It lives in its own section
("Indexation verdict (GSC)", added to deltas.STABLE_KEY_SECTIONS by
monthly_report), and it keeps THREE buckets, never two:

    indexed / not indexed / pending

`gsc.inspect_urls` already guarantees a failed inspection reports `pending`,
and its docstring says why: "'not indexed' sends you rewriting a page that may
be perfectly fine, when all that actually happened was a quota error." Folding
`pending` into `not indexed` is the silent-zero bug wearing a third hat, and a
verdict that does it is worse than the table it replaces.

One interpretation caveat, stated once here so it never has to be guessed: the
buckets count THIS MONTH'S published posts. The denominator is a different set
of posts each month, so a month-over-month delta on these rows is a
publishing-hygiene series ("did this month's posts get indexed as well as last
month's did?"), not a per-page series. That is what the rows say, and it is
carried in their note.

A month with ZERO published posts is NOT a measured zero. Nothing was
inspected, so `verdict_metrics([])` renders `pending` on all three buckets —
never `"0"`. A bare `"0"` is numeric, this section is in
`deltas.STABLE_KEY_SECTIONS`, and every refusal rule in deltas.py would
therefore pass: the delta engine would compute a real percentage against last
month's real count and fabricate a "-100%" deindexation in a month where not
one URL was inspected. The empty case is identical in kind to
`unmeasured_verdict` below — it just has a different reason.
"""
from __future__ import annotations

from report import Metric

PENDING = "pending"

INDEXED = "Posts indexed"
NOT_INDEXED = "Posts not indexed"
PENDING_INSPECTION = "Posts pending inspection"

_NAMES = (INDEXED, NOT_INDEXED, PENDING_INSPECTION)

_DENOMINATOR_NOTE = (
    "counts the posts PUBLISHED this month; the denominator is a different set "
    "each month, so a delta here is publishing hygiene, not a per-page trend"
)


def _is_indexed(coverage_state: str) -> bool:
    """True only when Google says the page IS in the index.

    Substring matching, and the order matters: "Indexed, not submitted in
    sitemap" contains "indexed" AND "not submitted" — but not "not indexed",
    and the page is in the index. "Crawled - currently not indexed" and
    "Discovered - currently not indexed" contain "not indexed". "URL is unknown
    to Google" contains neither, and a page Google has never seen is not
    indexed.
    """
    s = coverage_state.lower()
    return "indexed" in s and "not indexed" not in s


def verdict_metrics(index_rows: list[Metric]) -> list[Metric]:
    """The three-bucket count over gsc.inspect_urls()'s rows. Pure.

    Values are BARE NUMERIC strings on purpose: history.parse_numeric() yields
    "" for anything else, and deltas.delta_for() then refuses the row forever
    as "non-numeric value" — silently, which is the worst way to lose an
    instrument.

    An EMPTY index_rows is not a measured zero: no posts were published this
    month, so nothing was inspected. "0" would be numeric and delta-eligible,
    and the delta engine would then compute a real percentage against last
    month's real count — fabricating a "-100%" deindexation out of an absence
    of measurement. So the empty case renders PENDING, exactly like
    unmeasured_verdict, never "0".

    A FAILED inspection (429 quota, 403, 5xx, network) degrades to `pending`
    per gsc.inspect_urls' documented contract, and the URL Inspection API is
    quota-limited — a batch with some or all inspections failed is routine,
    not exceptional. `indexed` and `not_indexed` are only MEASUREMENTS when
    every inspection in the batch succeeded (`pending == 0`); with any
    pending, they are a LOWER BOUND over the URLs that were actually
    inspected, and a lower bound must not delta:

    - ALL-PENDING (nothing in the batch was successfully inspected): the
      whole verdict is an absence of measurement, identical in kind to the
      empty-index_rows case above — all three buckets render PENDING, never
      "0"/"N".
    - PARTIAL-PENDING (some inspections failed, some succeeded): `indexed`
      and `not_indexed` stay VISIBLE to a human as "N (of M inspected)" but
      that string is not bare-numeric, so history.parse_numeric() yields ""
      for it and deltas.delta_for() refuses it as "non-numeric value" instead
      of computing real arithmetic on a partial count. `pending` itself IS a
      real measurement — of the failure rate — and stays bare numeric so it
      keeps deltaing.
    """
    if not index_rows:
        return [
            Metric(name, PENDING, "GSC", note=(
                "no posts were published in this month — nothing was "
                "inspected; not a measured 0"
            ))
            for name in _NAMES
        ]

    total = len(index_rows)
    pending = sum(1 for m in index_rows if m.value == PENDING)

    if pending == total:
        return [
            Metric(name, PENDING, "GSC", note=(
                f"all {pending} inspection(s) failed — nothing was measured; "
                f"not a measured 0"
            ))
            for name in _NAMES
        ]

    indexed = sum(1 for m in index_rows if m.value != PENDING and _is_indexed(m.value))
    not_indexed = total - pending - indexed

    if pending > 0:
        inspected = total - pending
        lower_bound_note = (
            f"{pending} of {total} inspection(s) failed — this is a LOWER "
            f"BOUND over the {inspected} URL(s) actually inspected, not a "
            f"full count; not delta-eligible"
        )
        return [
            Metric(INDEXED, f"{indexed} (of {inspected} inspected)", "GSC",
                   note=lower_bound_note),
            Metric(NOT_INDEXED, f"{not_indexed} (of {inspected} inspected)", "GSC",
                   note=lower_bound_note),
            Metric(PENDING_INSPECTION, str(pending), "GSC", note=_DENOMINATOR_NOTE),
        ]

    counts = (indexed, not_indexed, pending)
    return [
        Metric(name, str(count), "GSC", note=_DENOMINATOR_NOTE)
        for name, count in zip(_NAMES, counts)
    ]


def unmeasured_verdict(reason: str) -> list[Metric]:
    """The verdict when the GSC lane did not run at all (--skip-gsc, or no GSC
    data for the month).

    A 0/0/0 count on a lane that never ran is a fabricated zero wearing a
    verdict's clothes: it would read as "every post is fine" precisely when
    nothing was checked.
    """
    return [
        Metric(
            name, PENDING, "GSC",
            note=f"{reason} — not a measured zero; no post was inspected",
        )
        for name in _NAMES
    ]
