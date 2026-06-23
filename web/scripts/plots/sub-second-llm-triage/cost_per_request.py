"""Cost per request by serving strategy (synthetic).

SYNTHETIC harness — no real billing data. Token counts per request are
modelled, and per-token prices use a small-vs-large profile in the same
ballpark as published API tiers (fast tier roughly an order of magnitude
cheaper than the reasoning tier). The cascade pays the fast tier on every
request and the large tier only on the escalated fraction.

Run with the repo's plotting venv:
    web/scripts/plots/.venv/bin/python cost_per_request.py
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# Per-1M-token prices ($), small-vs-large profile (synthetic, illustrative).
FAST_IN, FAST_OUT = 0.05, 0.40       # tiny model
LARGE_IN, LARGE_OUT = 0.50, 1.60     # reasoning model

# Typical tokens per request (synthetic).
IN_TOK, OUT_TOK = 600, 120
ESCALATE_RATE = 0.18                  # fraction routed up to the large tier


def cost(in_price: float, out_price: float) -> float:
    """Dollars per request, scaled to cost per 1,000 requests for readability."""
    per_req = (IN_TOK * in_price + OUT_TOK * out_price) / 1_000_000
    return per_req * 1000


fast_cost = cost(FAST_IN, FAST_OUT)
large_cost = cost(LARGE_IN, LARGE_OUT)
cascade_cost = fast_cost + ESCALATE_RATE * large_cost

labels = ["Fast tier\nonly", "Large tier\nonly", "Cascade\n(fast + escalate)"]
values = [fast_cost, large_cost, cascade_cost]
colors = [PALETTE[0], PALETTE[3], PALETTE[2]]

fig, ax = plt.subplots(figsize=(6.2, 4.2))
bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="none")

for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"${val:.3f}",
        ha="center",
        va="bottom",
        fontsize=10,
    )

ax.set_ylabel("Cost per 1,000 requests (USD) — synthetic")
ax.set_title("Cost by serving strategy (synthetic, illustrative prices)")
ax.set_ylim(0, max(values) * 1.18)
ax.grid(axis="x", visible=False)

save(fig, "../../../src/assets/blog/sub-second-llm-triage/cost-per-request.svg")
print("wrote cost-per-request.svg")
