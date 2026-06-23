"""Cost overlay: extra summarizer calls accumulated as the chat grows."""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from _sim import simulate  # noqa: E402

apply()

run = simulate(n_turns=60)
x = run["raw_tokens"] / 1000.0

fig, ax = plt.subplots()

# Retained meaning on the left axis (summarization vs the cheapest deletion).
ax.plot(x, run["summarize"], linestyle=LINESTYLES[2], color=PALETTE[2],
        label="Turns retained (summarize)")
ax.plot(x, run["fifo"], linestyle=LINESTYLES[0], color=PALETTE[0],
        label="Turns retained (FIFO)")
ax.set_xlabel("Raw conversation size (thousands of tokens)")
ax.set_ylabel("Effective turns retained")

# Extra summarizer calls on the right axis: the price of keeping meaning.
ax2 = ax.twinx()
ax2.plot(x, run["summarizer_calls"], linestyle=LINESTYLES[3], color=PALETTE[1],
         label="Extra summarizer calls")
ax2.set_ylabel("Cumulative summarizer calls", color=PALETTE[1])
ax2.tick_params(axis="y", colors=PALETTE[1])
ax2.grid(False)
ax2.spines["right"].set_visible(True)
ax2.spines["right"].set_color("#7a8290")

ax.set_title("Keeping meaning costs extra model calls")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc="center right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/pruning-chat-context-by-summarization/cost.svg",
)
print(f"wrote {out}")
