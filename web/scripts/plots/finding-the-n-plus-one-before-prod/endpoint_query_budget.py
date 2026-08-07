"""What the benchmark reported vs what the endpoint actually costs.

MEASURED numbers, not hand-tuned.

* `endpoint_naive` / `endpoint_eager` come from driving the real `/api/items/`
  route with DRF's `APIClient` (router -> ItemViewSet -> PageNumberPagination ->
  ItemSerializer) and counting queries with `CaptureQueriesContext`, at four
  vault sizes. The naive series was produced by monkeypatching
  `ItemViewSet.get_queryset` to drop `.select_related`/`.prefetch_related`.
  Reproduced 2026-08-07 in the personal-registry repo.

* `bench_eager` is what `src/tests/test_query_counts_bench.py` printed for the
  same app on the same day: a flat 3. It is one query short because that
  benchmark builds its own queryset and never goes through the paginator, so it
  never sees the `COUNT(*)`.

The naive series plateaus at 102 rather than climbing, because the server page
size is fixed at 50: pagination caps the N+1's blast radius at 1 COUNT + 1 page
+ 2 lookups per row on the page.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, INK  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# Items in the vault (the endpoint returns at most 50 of them on page 1).
vault_sizes = [10, 25, 50, 100]
rows_on_page_1 = [10, 25, 50, 50]

# Measured through the real endpoint (see module docstring).
endpoint_naive = [22, 52, 102, 102]
endpoint_eager = [4, 4, 4, 4]

# What test_query_counts_bench.py reported for the eager path, same app, same day.
bench_eager = [3, 3, 3, 3]

fig, ax = plt.subplots()

ax.plot(
    vault_sizes,
    endpoint_naive,
    marker="o",
    linestyle="-",
    color=PALETTE[3],
    label="Endpoint, no eager loading",
)
ax.plot(
    vault_sizes,
    endpoint_eager,
    marker="s",
    linestyle="-",
    color=PALETTE[2],
    label="Endpoint, eager-loaded (measured: 4)",
)
ax.plot(
    vault_sizes,
    bench_eager,
    marker="^",
    linestyle="--",
    color=PALETTE[0],
    label="What the benchmark reported (3)",
)

ax.annotate(
    "one query apart: the paginator's\nCOUNT(*), which the benchmark\nnever issued",
    xy=(88, 3.45),
    xytext=(26, 7.6),
    fontsize=9,
    color=INK,
    arrowprops=dict(arrowstyle="->", color=INK, linewidth=0.9),
)

ax.set_xlabel("Items in the vault")
ax.set_ylabel("Queries per list request (log)")
ax.set_title("The number the benchmark printed was not the endpoint's number")
ax.set_xticks(vault_sizes)
ax.set_xticklabels([str(n) for n in vault_sizes])
ax.set_yscale("log")
ax.set_yticks([3, 4, 10, 22, 52, 102])
ax.set_yticklabels(["3", "4", "10", "22", "52", "102"])
ax.minorticks_off()
ax.set_ylim(2.4, 340)
ax.legend(loc="upper left", fontsize=9.5)

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/finding-the-n-plus-one-before-prod/endpoint_query_budget.svg",
)
print(f"wrote {out}")
