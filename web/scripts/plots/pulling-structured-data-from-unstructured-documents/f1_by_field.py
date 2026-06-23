"""Synthetic mini-benchmark: per-field extraction quality, heuristics-only
vs. heuristics + an LLM fallback.

The numbers here are *synthetic and illustrative*. They are not measured on
any real corpus; they encode a qualitative point that holds up in practice:
deterministic heuristics are excellent on well-formed, regular fields
(emails, phone numbers) and weaker on fields whose surface form varies a lot
(names, free-text dates, amounts in mixed locales), where an LLM fallback
that is *grounded* against the source text closes most of the gap.

Run with the plots venv:

    web/scripts/plots/.venv/bin/python \
        web/scripts/plots/pulling-structured-data-from-unstructured-documents/f1_by_field.py
"""

from __future__ import annotations

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

# --- Synthetic mini-benchmark -------------------------------------------------
# Per-field F1 (0-1) on an invented set of sample documents (a handful of
# synthetic CVs and recipes). Illustrative only.
FIELDS = ["name", "email", "phone", "date", "amount"]
HEURISTICS_ONLY = [0.58, 0.97, 0.91, 0.66, 0.71]
HEURISTICS_PLUS_LLM = [0.89, 0.98, 0.93, 0.90, 0.92]

x = np.arange(len(FIELDS))
width = 0.38

fig, ax = plt.subplots()

bars_a = ax.bar(
    x - width / 2,
    HEURISTICS_ONLY,
    width,
    label="heuristics only",
    color=PALETTE[0],
    edgecolor=PALETTE[0],
)
bars_b = ax.bar(
    x + width / 2,
    HEURISTICS_PLUS_LLM,
    width,
    label="heuristics + grounded LLM",
    color="none",
    edgecolor=PALETTE[1],
    hatch="////",
    linewidth=1.3,
)

# Value labels so the chart reads in greyscale too.
for bars in (bars_a, bars_b):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )

ax.set_ylabel("F1 (synthetic)")
ax.set_ylim(0, 1.08)
ax.set_xticks(x)
ax.set_xticklabels(FIELDS)
ax.set_title("Per-field extraction quality on a synthetic mini-benchmark")
ax.legend(loc="lower right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/pulling-structured-data-from-unstructured-documents/f1-by-field.svg",
)
print(f"wrote {out}")
