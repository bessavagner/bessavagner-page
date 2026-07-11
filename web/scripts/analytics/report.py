"""Markdown emitter for the monthly merge.

Structural guarantee of ctx 05 §4: every figure carries its source tool, and
there is NO code path that averages or 1:1-compares two tools. Reach comes from
Umami, channel/conversion from GA4; the renderer only lays them side by side.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Metric:
    name: str
    value: str
    source: str  # "Umami" | "GA4" — mandatory, never blank
    note: str = ""


def _table(metrics: list[Metric]) -> str:
    if not metrics:
        return "_(none)_\n"
    lines = ["| Metric | Value | Source | Note |", "|---|---|---|---|"]
    for m in metrics:
        if not m.source:
            raise ValueError(f"metric {m.name!r} has no source tool — refuse to emit")
        lines.append(f"| {m.name} | {m.value} | {m.source} | {m.note} |")
    return "\n".join(lines) + "\n"


def render_report(
    month: str,
    reach: list[Metric],
    channel: list[Metric],
    conversions: list[Metric],
    flagged: list[Metric],
    caveats: list[str],
) -> str:
    parts = [
        f"# Monthly analytics report — {month}",
        "",
        "> Umami = reach truth · GA4 = channel/conversion truth. "
        "Every figure names its source; the two are **never averaged** (ctx 05 §4).",
        "",
        "## Reach (Umami)",
        _table(reach),
        "## Channel & engagement (GA4)",
        _table(channel),
        "## Conversions",
        _table(conversions),
        "## Flagged / pending (no GA4 counterpart or traffic-gated)",
        _table(flagged),
    ]
    if caveats:
        parts += ["## Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    return "\n".join(parts) + "\n"
