"""Delivery-latency distribution: HTTP polling vs WebSocket push.

SYNTHETIC. This is not a benchmark of any real server. It's a small timing
model that captures the *shape* of the difference: when an event can only be
discovered by the next poll, its delivery latency is dominated by how long it
waited for that poll to come around (on average half the polling interval,
uniformly distributed up to a full interval); when the server can push, the
latency is just the one-way network hop. The point of the plot is the shape of
the two distributions, not the absolute milliseconds.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

rng = np.random.default_rng(7)
N = 20_000

# One-way network hop: a small base plus a little jitter (ms). Shared by both
# transports -- the wire is the same; only *when* the client learns of the
# event differs.
net_hop = 12.0 + rng.gamma(shape=2.0, scale=4.0, size=N)

# WebSocket push: the server already holds the connection open, so the event
# reaches the client after one network hop.
ws_latency = net_hop.copy()

# HTTP polling at a 3-second interval: an event that lands t seconds after the
# previous poll is not seen until the next one. That wait is uniform on
# [0, interval]; add a hop for the request that finally carries it back.
poll_interval_ms = 3000.0
poll_wait = rng.uniform(0.0, poll_interval_ms, size=N)
poll_latency = poll_wait + net_hop

fig, ax = plt.subplots()
bins = np.linspace(0, poll_interval_ms + 200, 60)
ax.hist(
    poll_latency,
    bins=bins,
    color=PALETTE[1],
    alpha=0.75,
    label=f"HTTP polling ({poll_interval_ms / 1000:.0f}s interval)",
)
ax.hist(
    ws_latency,
    bins=bins,
    color=PALETTE[0],
    alpha=0.85,
    label="WebSocket push",
)

ax.axvline(
    np.median(poll_latency),
    color=PALETTE[1],
    linestyle="--",
    linewidth=1.0,
)
ax.axvline(
    np.median(ws_latency),
    color=PALETTE[0],
    linestyle="-",
    linewidth=1.0,
)

ax.set_xlabel("Delivery latency (ms, synthetic)")
ax.set_ylabel("Events")
ax.set_title("How long until the client sees an event: poll vs. push")
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/real-time-websockets-with-django-channels/latency.svg",
)
print(f"wrote {out}")
print(
    f"median poll={np.median(poll_latency):.0f}ms  "
    f"median ws={np.median(ws_latency):.0f}ms"
)
