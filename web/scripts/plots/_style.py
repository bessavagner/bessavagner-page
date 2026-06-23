"""Shared matplotlib style for blog charts.

Design goals (see docs/blog/article-pipeline.md → "Plot production & embedding"):

* **Theme-safe.** The site ships both a light and a dark theme, so every figure
  is saved with a fully transparent background and uses a single mid-contrast
  neutral ("ink") for axes, ticks, labels and grid. That neutral is readable on
  both a near-white and a near-black page.
* **Color-independent series.** Series are distinguished by linestyle and marker
  as well as color, so the charts survive colour-blind readers and greyscale.
* **SVG output.** Vector by default; crisp at any zoom and tiny on the wire.

Usage::

    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from _style import apply, save, PALETTE, LINESTYLES, MARKERS

    apply()
    fig, ax = plt.subplots()
    ...
    save(fig, "../../src/assets/blog/<slug>/<name>.svg")
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

# Mid-contrast neutral that reads on both light and dark backgrounds.
INK = "#7a8290"

# Okabe–Ito colour-blind-safe palette.
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 1))]
MARKERS = ["o", "s", "^", "D", "v", "P"]


def apply() -> None:
    """Install the theme-safe rcParams globally for the current process."""
    mpl.rcParams.update(
        {
            "figure.figsize": (7.0, 4.2),
            "figure.dpi": 110,
            "savefig.bbox": "tight",
            "savefig.transparent": True,
            "figure.facecolor": "none",
            "axes.facecolor": "none",
            "savefig.facecolor": "none",
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.labelcolor": INK,
            "ytick.labelcolor": INK,
            "axes.grid": True,
            "grid.color": INK,
            "grid.alpha": 0.18,
            "grid.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "font.size": 11.0,
            "axes.titlesize": 12.0,
            "axes.prop_cycle": cycler(color=PALETTE),
        }
    )


def save(fig, path: str | Path) -> Path:
    """Save ``fig`` as a transparent SVG, creating parent dirs as needed."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="svg", transparent=True, bbox_inches="tight")
    plt.close(fig)
    return out
