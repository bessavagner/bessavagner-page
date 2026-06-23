"""Spending-by-category trend over months.

ALL DATA IN THIS SCRIPT IS SYNTHETIC / FABRICATED. It does not come from any
real user, account, or transaction. It exists only to illustrate the kind of
per-category trend an agent with persistent memory can recognise over time.

Run with the project plot venv:
    web/scripts/plots/.venv/bin/python \
        web/scripts/plots/giving-an-llm-agent-memory/spending-trend.py
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES, MARKERS  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# --- Synthetic monthly spend per category (fabricated, USD) ----------------
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

# Each series is invented to show a distinct, recognisable pattern:
# - Groceries: stable baseline
# - Dining out: steadily creeping up (the anomaly the agent should flag)
# - Transport: seasonal dip then recovery
series = {
    "Groceries": [410, 425, 398, 432, 415, 420],
    "Dining out": [180, 205, 240, 275, 310, 355],
    "Transport": [160, 150, 120, 95, 130, 165],
}

fig, ax = plt.subplots()
for i, (label, values) in enumerate(series.items()):
    ax.plot(
        months,
        values,
        label=label,
        linestyle=LINESTYLES[i % len(LINESTYLES)],
        marker=MARKERS[i % len(MARKERS)],
        linewidth=1.8,
    )

ax.set_xlabel("Month")
ax.set_ylabel("Spend (USD, synthetic)")
ax.set_title("Spending by category over time (synthetic data)")
ax.legend()

# Resolve output against the web/ root so the script works from any cwd.
_WEB = pathlib.Path(__file__).resolve().parents[3]
save(fig, _WEB / "src/assets/blog/giving-an-llm-agent-memory/spending-trend.svg")
