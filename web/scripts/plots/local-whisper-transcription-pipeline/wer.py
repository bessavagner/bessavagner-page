"""Word error rate vs. Whisper model size (illustrative).

The WER axis is ILLUSTRATIVE — these are not measured numbers and not tied to
any benchmark dataset. They only show the qualitative trend: accuracy improves
(WER falls) as you move up the model tiers, with diminishing returns at the top.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, MARKERS, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

models = ["tiny", "base", "small", "medium", "large-v3"]
params_m = [39, 74, 244, 769, 1550]

# Illustrative WER (%) — qualitative shape only, NOT a measured benchmark.
wer_pct = [14.0, 10.5, 6.8, 5.2, 4.6]

fig, ax = plt.subplots()
ax.plot(
    params_m,
    wer_pct,
    linestyle="--",
    marker=MARKERS[1],
    color=PALETTE[1],
)

for x, y, name in zip(params_m, wer_pct, models):
    ax.annotate(
        name,
        (x, y),
        textcoords="offset points",
        xytext=(8, 4),
        fontsize=9,
    )

ax.set_xscale("log")
ax.set_xlabel("Model size (millions of parameters, log scale)")
ax.set_ylabel("Word error rate (%, illustrative)")
ax.set_title("Accuracy improves with size, with diminishing returns (illustrative)")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/local-whisper-transcription-pipeline/wer.svg",
)
print(f"wrote {out}")
