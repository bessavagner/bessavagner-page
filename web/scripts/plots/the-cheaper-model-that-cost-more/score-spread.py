"""Why one run is not a measurement: the score gap sits inside the noise.

REAL measured data, from the expense tracker's eval harness
(`docs/superpowers/evidence/eval/extraction-*.json` in that repo). Every
extraction sweep run on 2026-08-14: 5 of gpt-5.4, 4 of gpt-5.6-terra, same
seven receipts, same code, inside one hour.

The figure exists to show one thing: the 0.079 gap between the two means is
narrower than either model's own run-to-run range, so it measures nothing.
Compare with `price-vs-bill.py`, where the cost ranges are disjoint.

Run with the repo's plotting venv:
    web/scripts/plots/.venv/bin/python score-spread.py
"""

import sys
import pathlib
from statistics import mean

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, INK  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

OLD = "GPT-5.4"
NEW = "GPT-5.6-terra"

# Overall extraction score, one entry per sweep.
SCORES = {
    OLD: [0.9671, 0.8296, 0.8375, 0.9671, 0.8278],
    NEW: [0.9387, 0.8027, 0.8054, 0.6801],
}

COLORS = {OLD: PALETTE[0], NEW: PALETTE[3]}
MEANS = {m: mean(s) for m, s in SCORES.items()}

fig, ax = plt.subplots(figsize=(7.6, 3.4))

for y, model in enumerate([NEW, OLD]):
    runs = SCORES[model]
    color = COLORS[model]
    # The run-to-run range, drawn as the band the mean has to beat.
    ax.plot([min(runs), max(runs)], [y, y], color=color, lw=8, alpha=0.22, solid_capstyle="round")
    # Alternate the dots off the centreline so two runs that scored identically
    # stay countable (gpt-5.4 hit 0.9671 twice).
    offsets = [0.075 if i % 2 else -0.075 for i in range(len(runs))]
    ax.scatter(
        runs,
        [y + o for o in offsets],
        s=46,
        color=color,
        zorder=3,
        edgecolor="none",
    )
    # The mean sits on the centreline, clear of every dot.
    ax.scatter(
        [MEANS[model]], [y], marker="|", s=300, linewidth=2.4, color=color, zorder=4
    )
    ax.text(
        min(runs) - 0.012,
        y,
        f"{model}  ",
        ha="right",
        va="center",
        fontsize=11,
        fontweight="bold",
        color=color,
    )
    ax.text(
        max(runs) + 0.014,
        y,
        f"mean {MEANS[model]:.3f}   spread {max(runs) - min(runs):.2f}   n={len(runs)}",
        ha="left",
        va="center",
        fontsize=9.5,
        color=INK,
    )

gap = MEANS[OLD] - MEANS[NEW]
ax.annotate(
    f"gap between the means: {gap:.3f}\nnarrower than either model's own spread",
    xy=((MEANS[OLD] + MEANS[NEW]) / 2, 0.5),
    xytext=((MEANS[OLD] + MEANS[NEW]) / 2, 0.5),
    ha="center",
    va="center",
    fontsize=10,
    color=INK,
)

ax.set_xlim(0.60, 1.14)
ax.set_ylim(-0.6, 1.6)
ax.set_yticks([])
ax.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
ax.set_xlabel("Extraction score, one dot per sweep of the same 7 receipts")
ax.grid(axis="y", visible=False)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

save(fig, "../../../src/assets/blog/the-cheaper-model-that-cost-more/score-spread.svg")
print("wrote score-spread.svg")
