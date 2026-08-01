"""Local faster-whisper tiers vs OpenAI's hosted models — MEASURED, not illustrative.

Methodology (reproducible; harness in ./measure/):
  * Date 2026-07-31, single machine: 13th Gen Intel Core i7-13620H, 16 threads,
    CPU only. Same machine and settings as the earlier local-Whisper post, so
    the local numbers are comparable to it.
  * Corpus: 200 utterances drawn deterministically (seed 1337) from LibriSpeech
    test-clean. Every model saw the identical 200 files.
  * Local models: faster-whisper, compute_type="int8", beam_size=1.
  * Hosted models: POST /v1/audio/transcriptions, FLAC uploaded directly, no
    context parameters. Wall-clock includes network round-trip from Brazil.
  * WER: jiwer, aggregate (total edits / total reference words), case- and
    punctuation-insensitive — the same normalization as the earlier post.

These numbers describe clean, read English speech. They are NOT comparable to
OpenAI's Real World Audio Benchmark or to Artificial Analysis's AA-WER, which
use entirely different audio.
"""

import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

DATA = pathlib.Path(__file__).resolve().parent / "measure" / "bench-n200.json"
d = json.loads(DATA.read_text())
res = d["results"]

# Order: local tiers cheapest-first, then the hosted endpoints.
LOCAL = ["base", "small", "medium"]
HOSTED = ["whisper-1", "gpt-transcribe", "gpt-4o-transcribe"]

fig, ax = plt.subplots()

for names, color, marker, label in (
    (LOCAL, PALETTE[0], "o", "Local faster-whisper (CPU, int8, free)"),
    (HOSTED, PALETTE[3], "D", "OpenAI hosted API (paid)"),
):
    xs = [res[n]["seconds"] for n in names]
    ys = [res[n]["wer"] * 100 for n in names]
    ax.plot(xs, ys, linestyle="none", marker=marker, color=color,
            markersize=9, label=label)
    for x, y, n in zip(xs, ys, names):
        ax.annotate(n, (x, y), textcoords="offset points", xytext=(9, -3),
                    fontsize=9)

ax.set_xscale("log")
# Headroom on the right so the slowest model's label isn't clipped.
lo = min(v["seconds"] for v in res.values())
hi = max(v["seconds"] for v in res.values())
ax.set_xlim(lo * 0.85, hi * 1.6)
ax.set_xlabel(f"Wall-clock to transcribe {d['audio_seconds']/60:.0f} min of audio (s, log scale)")
ax.set_ylabel("Word error rate (%)")
ax.set_title("gpt-transcribe is both the fastest and the most accurate here")
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/openai-transcribe-vs-local-whisper/speed-accuracy.svg",
)
print(f"wrote {out}")
