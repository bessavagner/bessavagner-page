"""Composition of a polymorphic Item table by `kind` (SYNTHETIC seed data).

Mirrors the Item.Kind TextChoices from the vault app. The counts are made up
for illustration — they are not measured from a real database.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# Synthetic composition of a single owner's vault. The labels match
# Item.Kind; the counts are illustrative only.
kinds = [
    "Bookmark",
    "Recipe",
    "Grocery",
    "Journal",
    "Website",
    "Project Idea",
    "Expense",
    "Trip",
    "GitHub Repo",
    "Other",
]
counts = [312, 148, 96, 74, 61, 53, 42, 19, 17, 28]

# Sort descending so the long tail reads left-to-right.
order = sorted(range(len(kinds)), key=lambda i: counts[i], reverse=True)
kinds = [kinds[i] for i in order]
counts = [counts[i] for i in order]

fig, ax = plt.subplots()
bars = ax.bar(kinds, counts, color=PALETTE[0], width=0.66)

ax.set_ylabel("Items (synthetic)")
ax.set_title("One Item table, many kinds (synthetic seed data)")
ax.set_ylim(0, max(counts) * 1.12)
ax.tick_params(axis="x", rotation=35)
for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")

# Value labels on top of each bar.
for rect, c in zip(bars, counts):
    ax.text(
        rect.get_x() + rect.get_width() / 2,
        rect.get_height() + max(counts) * 0.015,
        str(c),
        ha="center",
        va="bottom",
        fontsize=8.5,
    )

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/polymorphic-vaults-in-drf/items_by_kind.svg",
)
print(f"wrote {out}")
