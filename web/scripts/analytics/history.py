"""The metric store — the report's memory.

Every Metric the monthly report emits is persisted here as one row, with its
month, its source, and whether the window it was measured in is structurally
comparable to any other. Written as a SIDE EFFECT of generating the report, so
it can never be the step someone forgets.

Three rules live in this module, and each of them is a bug that has already
happened somewhere in this project:

EMPTY IS A FIRST-CLASS STATE. Metric.value is a str: "1.50", "0.53%",
"pending", "no GA4 events in window". Deltas are arithmetic; strings are not.
So each row carries BOTH the raw string and a parsed numeric — and a value that
is not a number parses to EMPTY, never to 0. Coercing "pending" to 0 is the
silent-zero bug (ctx 05 section 1, conversions.py) relocated into the store.

VOID IS NOT ZERO. A window entirely before a boundary that makes its metric
structurally impossible is VOID: the pipeline could not have delivered the
figure, so there is nothing to compare. Pre-2026-07-12 GA4 conversions are the
live case — window.gtag was never defined, so GA4 received none of the four
custom events (A0). The dates come from boundaries.py; they are never
re-derived here.

UPSERT, NEVER APPEND. Re-running a month REPLACES its rows. An append-only
store silently doubles every figure the second time you regenerate — and
regenerating is normal.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import date

import boundaries
from report import Section
from window import Window

HISTORY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "history", "metrics.csv"
)

FIELDS = [
    "month", "section", "name", "value_raw", "value_num",
    "source", "note", "void", "partial",
]

# The only section whose GA4 rows the gtag bug made structurally impossible.
# Reach (Umami) was never affected — Umami received the events throughout — and
# GSC is a different pipeline entirely.
_GA4_CONVERSION_SECTION = "Conversions"


@dataclass(frozen=True)
class Row:
    month: str
    section: str
    name: str
    value_raw: str
    value_num: str  # "" when value_raw is not a number. NEVER "0" for an absence.
    source: str
    note: str
    void: bool
    partial: bool

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.month, self.section, self.name, self.source)


def parse_numeric(value_raw: str) -> str:
    """The numeric content of a rendered value, or "" when there is none.

    "" is a FIRST-CLASS state, and the single most important behaviour in this
    module: "pending" must never become "0".
    """
    s = value_raw.strip().replace(",", "")
    if s.endswith("%"):
        s = s[:-1]
    if not s:
        return ""
    try:
        v = float(s)
    except ValueError:
        return ""
    if v != v or v in (float("inf"), float("-inf")):  # NaN / inf are not measurements
        return ""
    return s


def is_void(
    section: str,
    source: str,
    w: Window,
    ga4_fix_deploy: date | None = boundaries.GA4_FIX_DEPLOY_DATE,
) -> bool:
    """True when this row's window is entirely before a boundary that makes it
    structurally meaningless — so its value is not a low measurement, it is not
    a measurement at all.

    A window that STRADDLES a boundary is not void: the post-boundary days were
    really measured. Straddling is what boundaries.boundary_caveats() says out
    loud in the report, and what deltas.crosses_boundary() refuses to compare
    across.

    Note GA4_KEY_EVENT_MARKING_DATE deliberately does NOT void anything:
    key-event marking governs GA4's Conversions *report*, not whether an
    eventName row exists — and this store reads the raw eventName rows. See the
    comment on GA4_FIX_DEPLOY_DATE in boundaries.py.
    """
    if section == _GA4_CONVERSION_SECTION and source == "GA4":
        if ga4_fix_deploy is not None and w.end < ga4_fix_deploy:
            return True
    return False


def rows_from_sections(
    month: str, w: Window, sections: list[Section], partial: bool
) -> list[Row]:
    """Flatten a rendered report's sections into store rows. Pure."""
    return [
        Row(
            month=month,
            section=s.title,
            name=m.name,
            value_raw=m.value,
            value_num=parse_numeric(m.value),
            source=m.source,
            note=m.note,
            void=is_void(s.title, m.source, w),
            partial=partial,
        )
        for s in sections
        for m in s.metrics
    ]


def _bool_out(v: bool) -> str:
    return "true" if v else "false"


def _bool_in(v: str) -> bool:
    return v == "true"


def load(path: str = HISTORY_PATH) -> list[Row]:
    """Every stored row. A missing file is an EMPTY history, not an error — the
    first month ever generated has nothing to read.
    """
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Row(
                month=r["month"],
                section=r["section"],
                name=r["name"],
                value_raw=r["value_raw"],
                value_num=r["value_num"],
                source=r["source"],
                note=r["note"],
                void=_bool_in(r["void"]),
                partial=_bool_in(r["partial"]),
            )
            for r in csv.DictReader(f)
        ]


def upsert(existing: list[Row], new: list[Row]) -> list[Row]:
    """Replace every month present in `new`, wholesale. Pure.

    Not a key-by-key merge: a regenerated month that emits FEWER rows must not
    leave the rows it dropped behind. A stale row is a lie with a timestamp on
    it. And not an append: appending doubles the month.
    """
    rewritten = {r.month for r in new}
    merged = {r.key: r for r in existing if r.month not in rewritten}
    for r in new:
        merged[r.key] = r
    return sorted(merged.values(), key=lambda r: r.key)


def write(rows: list[Row], path: str = HISTORY_PATH) -> None:
    """Deterministic on purpose: sorted rows, a fixed header, "\\n" line endings.
    Re-running a month with the same inputs must produce a BYTE-IDENTICAL file,
    so that a real diff in review always means a real change in the data.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(FIELDS)
        for r in sorted(rows, key=lambda r: r.key):
            w.writerow([
                r.month, r.section, r.name, r.value_raw, r.value_num,
                r.source, r.note, _bool_out(r.void), _bool_out(r.partial),
            ])


def record_month(
    month: str,
    w: Window,
    sections: list[Section],
    partial: bool,
    path: str = HISTORY_PATH,
) -> None:
    """Persist one month's metrics. The single call monthly_report.main() makes."""
    write(upsert(load(path), rows_from_sections(month, w, sections, partial)), path)
