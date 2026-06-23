"""Grouped bar chart: detection-test pass rate, vanilla Selenium vs a stealth setup.

IMPORTANT: the numbers below are REPRESENTATIVE / ILLUSTRATIVE, not live
measurements. They sketch the qualitative gap a stealth configuration tends to
close on common detection suites — vanilla automation fails most checks, a
stealth build passes the cheap ones but still gives ground on the deepest
fingerprinting (CreepJS). Detection sites evolve constantly, so treat any
single number as a cartoon, not a benchmark.
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

apply()

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Detection suites referenced in the post (illustrative pass rates, %).
suites = ["BotD", "Pixelscan", "deviceandbrowserinfo", "CreepJS"]
vanilla = [10, 15, 25, 8]
stealth = [92, 80, 78, 55]

x = np.arange(len(suites))
width = 0.38

fig, ax = plt.subplots(figsize=(7.4, 4.2))

bars_vanilla = ax.bar(
    x - width / 2, vanilla, width,
    label="Vanilla Selenium",
    color=PALETTE[3], edgecolor="none",
)
bars_stealth = ax.bar(
    x + width / 2, stealth, width,
    label="Stealth setup",
    color=PALETTE[2], hatch="//", edgecolor="white", linewidth=0,
)

ax.set_ylabel("Checks passed (%)")
ax.set_title("Detection-test pass rate (representative, not measured)")
ax.set_xticks(x)
ax.set_xticklabels(suites)
ax.set_ylim(0, 100)
ax.legend(loc="upper right")

# Value labels so the grouping reads even in greyscale.
for bars in (bars_vanilla, bars_stealth):
    ax.bar_label(bars, fmt="%d%%", padding=2, fontsize=9)

out = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/beating-browser-fingerprinting/pass-rate.svg"
)
save(fig, out)
print(f"wrote {out}")
