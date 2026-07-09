"""DB queries per list request: naive vs select_related + prefetch_related.

MEASURED numbers, not hand-tuned. They come from rendering the real
`ItemSerializer` over an Item list in the personal-registry app, counting
queries with Django's `CaptureQueriesContext`, at each page size. Reproduce with:

    # in the personal-registry repo
    uv run pytest src/tests/test_query_counts_bench.py -s -q

The naive queryset shows the classic N+1 shape (one query for the page, then
one extra query per related lookup per row, here tags + attachments = 2N). The
eager-loaded queryset (`select_related("owner").prefetch_related("tags",
"attachments")`) is flat at 3 regardless of page size.
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

# Measured by src/tests/test_query_counts_bench.py in the personal-registry repo
# (each item seeded with 2 tags + 1 attachment, rendered through ItemSerializer).
# Naive follows the N+1 shape (1 base + 2 per row); eager is flat at 3.
naive = [21, 51, 101, 201]
eager = [3, 3, 3, 3]

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
ax.set_ylabel("Database queries (measured)")
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
