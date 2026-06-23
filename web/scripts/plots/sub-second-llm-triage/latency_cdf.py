"""Latency CDF: fast tier vs large tier vs cascade.

SYNTHETIC timing harness — no real user data. We model each tier's
per-request latency as a log-normal body (typical service time) plus a
small heavy tail (occasional slow calls), which is the shape real LLM
endpoints tend to show. The cascade is the fast tier on every request
plus the large tier on the fraction that escalate, so its tail inherits
the large tier's slow calls but its body stays close to the fast tier.

Run with the repo's plotting venv:
    web/scripts/plots/.venv/bin/python latency_cdf.py
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, LINESTYLES  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

RNG = np.random.default_rng(20260705)
N = 40_000


def tier_latency(median_ms: float, sigma: float, tail_p: float, tail_mult: float) -> np.ndarray:
    """Log-normal body in milliseconds with an occasional heavy tail."""
    body = RNG.lognormal(mean=np.log(median_ms), sigma=sigma, size=N)
    tail_hit = RNG.random(N) < tail_p
    body[tail_hit] *= RNG.uniform(tail_mult, tail_mult * 2.5, size=tail_hit.sum())
    return body


# Fast tier: tiny model, pruned context, no memory recall — quick and tight.
fast = tier_latency(median_ms=180, sigma=0.35, tail_p=0.01, tail_mult=3.0)

# Large tier: reasoning model, larger context — slower with a fatter tail.
large = tier_latency(median_ms=950, sigma=0.45, tail_p=0.04, tail_mult=3.5)

# Cascade: fast tier always runs; ~18% of requests escalate to the large tier
# (the ones the fast tier flags as uncertain), paying both latencies.
escalate = RNG.random(N) < 0.18
cascade = fast.copy()
cascade[escalate] = fast[escalate] + large[escalate]


def cdf(data: np.ndarray):
    xs = np.sort(data)
    ys = np.arange(1, len(xs) + 1) / len(xs)
    return xs, ys


fig, ax = plt.subplots()

series = [
    ("Fast tier only", fast, PALETTE[0], LINESTYLES[0]),
    ("Large tier only", large, PALETTE[3], LINESTYLES[1]),
    ("Cascade (fast + escalate)", cascade, PALETTE[2], LINESTYLES[2]),
]
for label, data, color, ls in series:
    xs, ys = cdf(data)
    ax.plot(xs, ys, label=label, color=color, linestyle=ls, linewidth=1.8)

# Mark a 500 ms budget line for the hot path.
ax.axvline(500, color="#7a8290", linewidth=0.9, linestyle=(0, (1, 2)))
ax.text(515, 0.06, "500 ms budget", fontsize=9, color="#7a8290")

ax.set_xscale("log")
ax.set_xlim(60, 8000)
ax.set_xlabel("Per-request latency (ms, log scale) — synthetic")
ax.set_ylabel("Fraction of requests ≤ x")
ax.set_title("Latency CDF by serving strategy (synthetic harness)")
ax.legend(loc="lower right")

save(fig, "../../../src/assets/blog/sub-second-llm-triage/latency-cdf.svg")
print("wrote latency-cdf.svg")
