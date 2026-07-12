"""Markdown emitter for the monthly merge.

Structural guarantee of ctx 05 §4: every figure carries its source tool, and
there is NO code path that averages or 1:1-compares two tools. Reach comes from
Umami, channel/conversion from GA4, pre-click/demand from GSC; the renderer only
lays them side by side.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Metric:
    name: str
    value: str
    source: str  # "Umami" | "GA4" — mandatory, never blank
    note: str = ""


@dataclass
class Section:
    title: str
    metrics: list[Metric]


# The standing monthly + weekly operating cadence for four items the sprint
# intentionally deferred pending more traffic (F-fold, commit 2fb04df). This
# was originally hand-appended to the rendered report; a later regeneration
# silently deleted it because the code had no memory of it. Promoted here so
# render_report can re-emit it on every run — see the closing note below.
ROLLING_READOUTS = """## Rolling readouts (standing cadence — traffic-gated)

This is the standing monthly + weekly operating cadence for the four items the
sprint intentionally deferred pending more traffic. None are dropped — each has
a named home below and is re-checked on the cadence noted, not abandoned.

| # | Readout | Home | Status |
|---|---|---|---|
| E3 | Link-placement verdict (body / first-comment / profile-featured) | tracker rollup → [`linkedin-post-tracker.md`](../../playbooks/linkedin-post-tracker.md#e3--link-placement-rollup-pending-n-posts-per-variant) → [`linkedin-playbook.md`](../../playbooks/linkedin-playbook.md#link-placement-ab) | pending ≥N posts per variant |
| E8 | Re-baseline delta once a clean post-A/B month exists | [`kpi-baselines-and-targets.md`](../kpi-baselines-and-targets.md) | pending 1 full post-A/B month |
| C3b | Pages/session crossing 2.0 from the internal-link retrofit | this report's GA4 channel section (above) | trend; pending weeks of traffic — current site-wide baseline is 1.69 (GA4, [`kpi-baselines-and-targets.md`](../kpi-baselines-and-targets.md)), below the 2.0 goal |
| D6b | Conversion shift near the trust block | this report | **pending a real named testimonial** (never fabricated) + weeks of traffic |

> This block is emitted from `report.py` (the `ROLLING_READOUTS` constant), so
> every month carries it automatically — it no longer needs to be hand-appended.
"""


def _table(metrics: list[Metric]) -> str:
    if not metrics:
        return "_(none)_\n"
    lines = ["| Metric | Value | Source | Note |", "|---|---|---|---|"]
    for m in metrics:
        if not m.source:
            raise ValueError(f"metric {m.name!r} has no source tool — refuse to emit")
        lines.append(f"| {m.name} | {m.value} | {m.source} | {m.note} |")
    return "\n".join(lines) + "\n"


def render_report(month: str, sections: list[Section], caveats: list[str]) -> str:
    parts = [
        f"# Monthly analytics report — {month}",
        "",
        "> Umami = reach truth · GA4 = channel/conversion truth · "
        "GSC = pre-click/demand truth (Google organic only). "
        "Every figure names its source; the tools are **never averaged** (ctx 05 §4).",
        "",
    ]
    for s in sections:
        parts += [f"## {s.title}", _table(s.metrics)]
    if caveats:
        parts += ["## Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    parts.append(ROLLING_READOUTS.rstrip("\n"))
    return "\n".join(parts) + "\n"
