"""Overlapping-window guard (ctx 05 §1).

GA4 loads only in PROD and started later than Umami, so a month that predates
the GA4 install has no GA4 counterpart. We compare ONLY overlapping ranges and
flag orphaned metrics rather than zero-filling them.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date


@dataclass
class Window:
    start: date
    end: date


def month_window(month: str) -> Window:
    year, mon = (int(p) for p in month.split("-"))
    last = calendar.monthrange(year, mon)[1]
    return Window(date(year, mon, 1), date(year, mon, last))


def comparison_window(month: Window, ga4_start: date) -> Window | None:
    start = max(month.start, ga4_start)
    if start > month.end:
        return None  # whole month predates GA4 — orphaned, must be flagged
    return Window(start, month.end)


def is_reconcilable(month: Window, ga4_start: date) -> bool:
    return comparison_window(month, ga4_start) is not None
