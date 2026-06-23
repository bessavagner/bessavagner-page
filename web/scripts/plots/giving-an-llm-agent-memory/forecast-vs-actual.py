"""Forecast vs. actual monthly spend.

ALL DATA IN THIS SCRIPT IS SYNTHETIC / FABRICATED. The "forecast" is not the
output of any real model and the "actual" figures are invented. The chart only
illustrates how an agent that remembers a user's history can project the next
months and then be checked against what actually happened.

Run with the project plot venv:
    web/scripts/plots/.venv/bin/python \
        web/scripts/plots/giving-an-llm-agent-memory/forecast-vs-actual.py
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, LINESTYLES, MARKERS  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# --- Synthetic total monthly spend (fabricated, USD) -----------------------
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

# A forecast the agent might produce from recalled history, and the values that
# "actually" came in. Both are invented for illustration.
forecast = [820, 845, 860, 880, 905, 930]
actual = [810, 870, 845, 905, 980, 1015]

fig, ax = plt.subplots()
ax.plot(
    months,
    forecast,
    label="Forecast (synthetic)",
    color=PALETTE[0],
    linestyle=LINESTYLES[1],
    marker=MARKERS[0],
    linewidth=1.8,
)
ax.plot(
    months,
    actual,
    label="Actual (synthetic)",
    color=PALETTE[3],
    linestyle=LINESTYLES[0],
    marker=MARKERS[1],
    linewidth=1.8,
)

# Shade the gap so the growing divergence (an anomaly worth flagging) reads.
ax.fill_between(months, forecast, actual, color=PALETTE[3], alpha=0.10)

ax.set_xlabel("Month")
ax.set_ylabel("Total spend (USD, synthetic)")
ax.set_title("Forecast vs. actual spend (synthetic data)")
ax.legend()

# Resolve output against the web/ root so the script works from any cwd.
_WEB = pathlib.Path(__file__).resolve().parents[3]
save(fig, _WEB / "src/assets/blog/giving-an-llm-agent-memory/forecast-vs-actual.svg")
