"""bessaviz figure sources for blog posts (light + dark PNG).

The third figure pipeline on this site, alongside the matplotlib charts in
`../../plots/` and the Mermaid flowcharts in `../`. bessaviz renders brand-themed
TikZ through LuaLaTeX and bakes each figure onto the theme's own `base` color, so
a diagram ships as a light/dark pair rendered through `ThemedFigure`.

bessaviz is not on PyPI; point BESSAVIZ_SRC at a checkout's `src/` directory
(default: a `bessaviz` sibling of this repo). Needs lualatex, pdftocairo and
ImageMagick on PATH.

    BESSAVIZ_SRC=~/projects/bessaviz/src python3 render-blog-figures.py
    python3 render-blog-figures.py pgvector-agent-long-term-memory
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]          # web/
ASSETS = REPO / "src" / "assets" / "blog"
DEFAULT_SRC = REPO.parent.parent / "bessaviz" / "src"

sys.path.insert(0, os.environ.get("BESSAVIZ_SRC", str(DEFAULT_SRC)))

from bessaviz.adapters.raster import export_both  # noqa: E402
from bessaviz.diagrams import hexagon_ports, two_lane_flow  # noqa: E402

# Label budgets are tight: the composers use fixed box widths and neither wrap
# nor shrink text, so an over-long label overflows into the arrowhead. Measured
# safe lengths are ~10 chars at two_lane_flow's width and ~12 at hexagon_ports'.
# Labels also pass straight through to TeX, so no braces, underscores, carets,
# percent or dollar signs.
FIGURES: list[tuple[str, str, callable]] = [
    (
        "pgvector-agent-long-term-memory",
        "two-lanes",
        lambda: two_lane_flow(
            "substring", ["cosmos", "trigger", "rule hit"],
            "embedding", ["embed", "d = 0.53", "no match"],
            divider_label="cutoff 0.2: only one lane answers",
            accent_bottom_last=False,
            bottom_dashed=True,
        ),
    ),
    (
        "rendering-my-blog-diagrams-as-code",
        "ports",
        lambda: hexagon_ports("bessaviz", ["lualatex", "pdftocairo", "ImageMagick"]),
    ),
]


def main(only: set[str]) -> None:
    for slug, name, factory in FIGURES:
        if only and slug not in only:
            continue
        for path in export_both(lambda f=factory: f().build(), ASSETS / slug, name):
            print(path.relative_to(REPO))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
