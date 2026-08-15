"""The 20% per-token discount that arrived as a 51% larger bill.

REAL measured data. Sources:

* List prices are the published per-1M-token input prices for the two models.
* Per-run cost and input-token counts come from the expense tracker's eval
  harness, `docs/superpowers/evidence/eval/extraction-*.json` in that repo
  (5 sweeps of gpt-5.4, 4 of gpt-5.6-terra, all on 2026-08-14).

A sweep is one pass over the seven ground-truth receipts. Every run is plotted,
not just the mean, because the point of the right-hand panel is that the two
cost distributions do not overlap: unlike the quality gap, this one is real.

Run with the repo's plotting venv:
    web/scripts/plots/.venv/bin/python price-vs-bill.py
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

# Published list price, input, USD per 1M tokens.
PRICE_IN = {OLD: 2.50, NEW: 2.00}

# Measured USD per sweep of 7 receipts, one entry per harness run.
COST_RUNS = {
    OLD: [0.1979, 0.2110, 0.1676, 0.1677, 0.1908],
    NEW: [0.2795, 0.2825, 0.2717, 0.2929],
}

# Measured input tokens per sweep, averaged over the same runs.
INPUT_TOKENS = {OLD: 33_723, NEW: 89_339}

# The old model is the neutral reference; the new one is the surprise.
COLORS = [PALETTE[0], PALETTE[3]]

COST_MEAN = {m: mean(runs) for m, runs in COST_RUNS.items()}

fig, (ax_price, ax_bill) = plt.subplots(1, 2, figsize=(7.6, 4.0))


def label_bars(ax, bars, values, fmt, tops=None):
    """Label each bar with its value, clearing any run dots drawn above it."""
    for i, (bar, val) in enumerate(zip(bars, values)):
        y = bar.get_height() if tops is None else tops[i]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            fmt(val),
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )


def finish(ax, title, ylabel, top):
    ax.set_title(title, pad=12)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, top)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", length=0)


def delta(ax, text, value):
    """Label the delta in open space above the bar, never on top of it."""
    ax.text(
        1,
        value * 1.13,
        text,
        ha="center",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        color=COLORS[1],
    )


# Left: the published price, which is a single number with no spread to show.
price_vals = list(PRICE_IN.values())
bars = ax_price.bar(list(PRICE_IN), price_vals, color=COLORS, width=0.55, edgecolor="none")
label_bars(ax_price, bars, price_vals, lambda v: f"${v:.2f}")
finish(
    ax_price,
    "What the pricing page said",
    "List price, input (USD / 1M tokens)",
    max(price_vals) * 1.45,
)
delta(ax_price, "20% cheaper\nper token", PRICE_IN[NEW])

# Right: the measured bill, with every individual sweep drawn over the mean.
cost_vals = [COST_MEAN[OLD], COST_MEAN[NEW]]
bars = ax_bill.bar(list(COST_MEAN), cost_vals, color=COLORS, width=0.55, edgecolor="none", alpha=0.5)
for x, model in enumerate(COST_RUNS):
    runs = COST_RUNS[model]
    ax_bill.scatter(
        [x] * len(runs),
        runs,
        s=30,
        color=COLORS[x],
        zorder=3,
        edgecolor="none",
    )
# Clear the dot cloud, so the mean label never lands on a run.
tops = [max(COST_RUNS[OLD]), max(COST_RUNS[NEW])]
label_bars(ax_bill, bars, cost_vals, lambda v: f"${v:.3f}", tops=tops)
finish(
    ax_bill,
    "What the harness measured",
    "Cost per sweep of 7 receipts (USD)",
    max(tops) * 1.45,
)
delta(ax_bill, "51% more\nper sweep", max(COST_RUNS[NEW]))

# The mechanism between the two panels: the discount is multiplied by token burn.
ratio = INPUT_TOKENS[NEW] / INPUT_TOKENS[OLD]
fig.text(
    0.5,
    0.075,
    f"{NEW} read the same 7 images with {ratio:.1f}x the input tokens "
    f"({INPUT_TOKENS[NEW]:,} vs {INPUT_TOKENS[OLD]:,} per sweep)",
    ha="center",
    fontsize=10,
    color=INK,
)
fig.text(
    0.5,
    0.015,
    f"Right panel: one dot per sweep, {len(COST_RUNS[OLD])} and {len(COST_RUNS[NEW])} runs. "
    "The two cost ranges do not overlap.",
    ha="center",
    fontsize=9,
    color=INK,
)

fig.tight_layout(rect=(0, 0.13, 1, 1))

save(fig, "../../../src/assets/blog/the-cheaper-model-that-cost-more/price-vs-bill.svg")
print("wrote price-vs-bill.svg")
