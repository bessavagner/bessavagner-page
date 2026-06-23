"""Per-brand row coverage across the scraped months.

A scrape that runs for hours against a flaky site never lands perfectly square:
some brand/month cells have many models, some have few, and a crash mid-run can
leave a thin month behind. This heatmap shows how many rows each top brand
contributed in each reference month - a quick visual audit of completeness.

Reads the same monthly FIPE parquet files as ``price-trend.py``; falls back to a
clearly-labelled SYNTHETIC matrix when they are absent.

Run::

    web/scripts/plots/.venv/bin/python \
        web/scripts/plots/scraping-a-fragile-legacy-site/coverage-heatmap.py
"""

from __future__ import annotations

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, INK  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

FIPE_DIR = pathlib.Path.home() / "Documents" / "projetos" / "FIPE"
OUT = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/scraping-a-fragile-legacy-site/coverage-heatmap.svg"
)

BRANDS = ["VW - VolksWagen", "GM - Chevrolet", "Fiat", "Ford", "Toyota", "BMW"]
MONTHS = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def load_real() -> pd.DataFrame | None:
    files = sorted(FIPE_DIR.glob("fipe_carros-*-20??.parquet"))
    if not files:
        return None
    rows = []
    for path in files:
        _, month_name, year = path.stem.rsplit("-", 2)
        month = MONTHS.get(month_name)
        if month is None:
            continue
        ref = pd.Timestamp(year=int(year), month=month, day=1)
        df = pd.read_parquet(path, engine="pyarrow", columns=["marca"])
        counts = df[df["marca"].isin(BRANDS)]["marca"].value_counts()
        for brand, n in counts.items():
            rows.append({"ref": ref, "marca": brand, "n": int(n)})
    tidy = pd.DataFrame(rows)
    return tidy.pivot_table(index="marca", columns="ref", values="n", fill_value=0)


def synthesize() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    refs = pd.date_range("2020-08-01", "2023-01-01", freq="MS")
    base = {b: rng.integers(700, 2600) for b in BRANDS}
    mat = np.array(
        [[max(0, int(base[b] * (1 + rng.normal(0, 0.04)))) for _ in refs] for b in BRANDS]
    )
    return pd.DataFrame(mat, index=BRANDS, columns=refs)


def main() -> None:
    pivot = load_real()
    synthetic = pivot is None
    if synthetic:
        pivot = synthesize()
    pivot = pivot.reindex(BRANDS)

    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    im = ax.imshow(pivot.values, aspect="auto", cmap="cividis")

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    cols = list(pivot.columns)
    step = max(1, len(cols) // 8)
    ticks = list(range(0, len(cols), step))
    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [pd.Timestamp(cols[i]).strftime("%b %Y") for i in ticks],
        rotation=45, ha="right", fontsize=9,
    )

    title = "Rows per brand per reference month"
    if synthetic:
        title += " (synthetic)"
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("rows scraped", color=INK, fontsize=9)
    cbar.ax.tick_params(colors=INK, labelsize=8)

    out = save(fig, OUT)
    print(f"wrote {out}  ({'synthetic' if synthetic else 'real FIPE data'})")


if __name__ == "__main__":
    main()
