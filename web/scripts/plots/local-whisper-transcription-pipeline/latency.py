"""Transcription latency vs. Whisper model size (illustrative benchmark).

Synthetic, illustrative numbers — NOT measured from the repo's real media.
They sketch the shape every CPU int8 faster-whisper user sees: latency climbs
steeply with the parameter count, roughly tracking model size.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, MARKERS, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# Model tiers and their parameter counts (from the Whisper model card).
models = ["tiny", "base", "small", "medium", "large-v3"]
params_m = [39, 74, 244, 769, 1550]

# Illustrative wall-clock latency (seconds) to transcribe one fixed 60 s clip,
# faster-whisper, CPU, int8. Shape only — your hardware will differ.
latency_s = [8, 14, 38, 105, 196]

fig, ax = plt.subplots()
ax.plot(
    params_m,
    latency_s,
    linestyle="-",
    marker=MARKERS[0],
    color=PALETTE[0],
)

for x, y, name in zip(params_m, latency_s, models):
    ax.annotate(
        name,
        (x, y),
        textcoords="offset points",
        xytext=(8, -4),
        fontsize=9,
    )

ax.set_xscale("log")
ax.set_xlabel("Model size (millions of parameters, log scale)")
ax.set_ylabel("Latency for a 60 s clip (s, CPU int8)")
ax.set_title("Transcription latency climbs steeply with model size (illustrative)")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/local-whisper-transcription-pipeline/latency.svg",
)
print(f"wrote {out}")
