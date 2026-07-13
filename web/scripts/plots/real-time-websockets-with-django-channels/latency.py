"""Delivery-latency ECDF: HTTP polling vs WebSocket push. MEASURED.

Data comes from measure/latencies.csv, a real capture against a daphne
server running the post's consumer pattern on loopback: 300 events fired
at random moments, one WebSocket client receiving each as a push, one
HTTP client polling every 3 s (methodology in measure/README.md).

An ECDF on a log x-axis is the honest way to show this: the two
distributions live three orders of magnitude apart, so a linear-scale
histogram crams the push spike into the left edge. The log scale lets
both curves keep their shape, and reading medians off an ECDF needs no
binning choices at all.

Run with the repo's plotting venv:
    web/scripts/plots/.venv/bin/python latency.py
"""

import csv
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, LINESTYLES  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

HERE = pathlib.Path(__file__).resolve().parent
with (HERE / "measure/latencies.csv").open() as fh:
    rows = list(csv.DictReader(fh))
push = np.array([float(r["push_ms"]) for r in rows])
poll = np.array([float(r["poll_ms"]) for r in rows])
POLL_INTERVAL_MS = 3000.0


def cdf(data):
    xs = np.sort(data)
    ys = np.arange(1, len(xs) + 1) / len(xs)
    return xs, ys


fig, ax = plt.subplots()

for label, data, color, ls, offset, align in (
    (f"WebSocket push (n={len(push)})", push, PALETTE[0], LINESTYLES[0],
     (8, -14), "left"),
    ("HTTP polling, 3 s interval", poll, PALETTE[1], LINESTYLES[1],
     (-10, -14), "right"),
):
    xs, ys = cdf(data)
    ax.plot(xs, ys, label=label, color=color, linestyle=ls, linewidth=1.8)
    med = np.median(data)
    ax.plot([med], [0.5], marker="o", color=color, markersize=5)
    unit = f"{med:.1f} ms" if med < 100 else f"{med / 1000:.1f} s"
    ax.annotate(
        f"median {unit}",
        (med, 0.5),
        textcoords="offset points",
        xytext=offset,
        ha=align,
        fontsize=9,
        color=color,
    )

# Nothing polls later than one full interval after the event.
ax.axvline(POLL_INTERVAL_MS, color="#7a8290", linewidth=0.9,
           linestyle=(0, (1, 2)))
ax.text(POLL_INTERVAL_MS * 0.92, 0.06, "poll interval (3 s)", fontsize=9,
        color="#7a8290", rotation=90, va="bottom")

ax.set_xscale("log")
ax.set_xlim(0.3, 5000)
ax.set_ylim(0, 1.02)
ax.set_xlabel("Delivery latency (ms, log scale), measured on loopback")
ax.set_ylabel("Fraction of events delivered ≤ x")
ax.set_title("How long until the client sees an event: poll vs. push")
ax.legend(loc="upper left")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/real-time-websockets-with-django-channels/latency.svg",
)
print(f"wrote {out}")
print(
    f"median poll={np.median(poll):.0f}ms  median push={np.median(push):.2f}ms  "
    f"push max={push.max():.2f}ms  poll max={poll.max():.0f}ms"
)
