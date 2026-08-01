"""What the `keywords` parameter does to proper nouns — MEASURED.

Methodology (reproducible; harness in ./measure/keywords.py):
  * Date 2026-07-31, model gpt-transcribe, POST /v1/audio/transcriptions.
  * The three LibriSpeech test-clean utterances from the 200-file run whose only
    remaining errors were proper nouns (a Baum Oz excerpt and two lines from a
    Cervantes novella).
  * Each transcribed three ways: bare, with `keywords=[...]` naming the proper
    nouns, and with `keywords` plus a free-form `prompt` describing the setting.
  * WER: jiwer, case- and punctuation-insensitive, per utterance.

The `keywords+prompt` regression on the third utterance is real and not noise:
the prompt pushes the model to spell "señora" correctly, which the LibriSpeech
reference transcript spells "senora". More context is not monotonically better.
"""

import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

apply()

DATA = pathlib.Path(__file__).resolve().parent / "measure" / "keywords-gpt-transcribe.json"
rows = json.loads(DATA.read_text())

# Short human labels for the utterance ids.
LABELS = {
    "8555-284449-0004": "Oz excerpt\n(Ghip Ghisizzle, Boolooroo)",
    "5639-40744-0007": "Novella, line 1\n(Rodolfo, Leocadia)",
    "5639-40744-0039": "Novella, line 2\n(Rodolfo's, senora)",
}
VARIANTS = [
    ("bare", "No context", PALETTE[3]),
    ("keywords", "+ keywords", PALETTE[2]),
    ("keywords+prompt", "+ keywords + prompt", PALETTE[1]),
]

x = np.arange(len(rows))
width = 0.26

fig, ax = plt.subplots()
for i, (key, label, color) in enumerate(VARIANTS):
    vals = [r[key]["wer"] * 100 for r in rows]
    pos = x + (i - 1) * width
    ax.bar(pos, vals, width, label=label, color=color)
    for p, v in zip(pos, vals):
        ax.annotate(f"{v:.1f}", (p, v), ha="center", va="bottom",
                    textcoords="offset points", xytext=(0, 2), fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels([LABELS[r["id"]] for r in rows], fontsize=9)
ax.set_ylabel("Word error rate (%)")
ax.set_title("Naming the proper nouns takes these utterances to zero")
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/openai-transcribe-vs-local-whisper/keywords.svg",
)
print(f"wrote {out}")
