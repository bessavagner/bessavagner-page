"""DB queries per list request: naive vs select_related + prefetch_related.

SYNTHETIC / representative numbers. The naive bars follow the classic N+1
shape: one query for the page of items, then one extra query per related
lookup per row. The eager-loaded bars are constant: one query for the page
plus a small fixed number of prefetch queries, independent of page size.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

# Page sizes (rows returned by an Item list endpoint).
page_sizes = [10, 25, 50, 100]

# Naive: 1 base query + one query per row for each of two related lookups
# (tags, attachments). This is the N+1 pattern, here "N+2N".
naive = [1 + 2 * n for n in page_sizes]

# Eager: 1 base query (with select_related join folded in) + 1 prefetch
# query per related manager (tags, attachments). Constant regardless of N.
eager = [1 + 2 for _ in page_sizes]

x = np.arange(len(page_sizes))
w = 0.38

fig, ax = plt.subplots()
b1 = ax.bar(x - w / 2, naive, w, label="Naive (N+1)", color=PALETTE[3])
b2 = ax.bar(
    x + w / 2,
    eager,
    w,
    label="select_related + prefetch_related",
    color=PALETTE[2],
)

ax.set_xlabel("Items returned per request")
ax.set_ylabel("Database queries (synthetic)")
ax.set_title("Killing the N+1: queries per list request")
ax.set_xticks(x)
ax.set_xticklabels([str(n) for n in page_sizes])
ax.legend(loc="upper left")
ax.set_ylim(0, max(naive) * 1.12)

for rects in (b1, b2):
    for rect in rects:
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + max(naive) * 0.015,
            str(int(rect.get_height())),
            ha="center",
            va="bottom",
            fontsize=8.5,
        )

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/polymorphic-vaults-in-drf/query_counts.svg",
)
print(f"wrote {out}")
