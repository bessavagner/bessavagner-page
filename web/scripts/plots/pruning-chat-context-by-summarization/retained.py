"""Effective turns retained vs raw tokens added: FIFO vs per-message vs summarize."""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from _sim import simulate  # noqa: E402

apply()

run = simulate(n_turns=60)
x = run["raw_tokens"] / 1000.0  # thousands of tokens added so far

fig, ax = plt.subplots()
ax.plot(x, run["fifo"], linestyle=LINESTYLES[0], label="FIFO truncation")
ax.plot(x, run["per_message"], linestyle=LINESTYLES[1], label="Per-message pruning")
ax.plot(x, run["summarize"], linestyle=LINESTYLES[2], label="Summarization-pruning")

ax.axvline(run["window"] / 1000.0, color="#7a8290", linewidth=0.8, alpha=0.5)
ax.annotate(
    "window fills up",
    xy=(run["window"] / 1000.0, 2),
    xytext=(run["window"] / 1000.0 + 2, 4),
    fontsize=9,
)

ax.set_xlabel("Raw conversation size (thousands of tokens)")
ax.set_ylabel("Effective turns retained")
ax.set_title("How much conversation survives a fixed window")
ax.legend(loc="upper left")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/pruning-chat-context-by-summarization/retained.svg",
)
print(f"wrote {out}")
