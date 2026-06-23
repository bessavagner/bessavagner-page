"""Average used-car price over time, by brand segment.

Reads the monthly FIPE parquet files produced by the scraper (one file per
reference month, e.g. ``fipe_carros-outubro-2022.parquet``), parses the
Brazilian-formatted price string into a float, and plots the median price per
reference month for a handful of representative brands.

The data is the public FIPE vehicle price table (Fundacao Instituto de
Pesquisas Economicas). If the source parquet files are not present, the script
falls back to a clearly-labelled SYNTHETIC series so the plot is still
reproducible from a clean checkout.

Run::

    web/scripts/plots/.venv/bin/python \
        web/scripts/plots/scraping-a-fragile-legacy-site/price-trend.py
"""

from __future__ import annotations

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, LINESTYLES, MARKERS  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

# Where the scraper dropped its monthly parquet files.
FIPE_DIR = pathlib.Path.home() / "Documents" / "projetos" / "FIPE"
OUT = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/scraping-a-fragile-legacy-site/price-trend.svg"
)

# Brand segments to follow over time. These are real FIPE brand labels.
BRANDS = ["Toyota", "VW - VolksWagen", "BMW", "Fiat"]

# Portuguese month names -> month number, to turn a filename into a date.
MONTHS = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def parse_price(series: pd.Series) -> pd.Series:
    """'R$ 45.046,00' -> 45046.00. The same cleaning the ETL step uses."""
    cleaned = (
        series.astype("string")
        .str.replace(r"R\$\s*", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def load_real() -> pd.DataFrame | None:
    """Read every monthly parquet into one tidy frame, or None if absent."""
    files = sorted(FIPE_DIR.glob("fipe_carros-*-20??.parquet"))
    if not files:
        return None

    frames = []
    for path in files:
        # filename: fipe_carros-<month>-<year>.parquet
        _, month_name, year = path.stem.rsplit("-", 2)
        month = MONTHS.get(month_name)
        if month is None:
            continue
        ref = pd.Timestamp(year=int(year), month=month, day=1)

        df = pd.read_parquet(path, engine="pyarrow", columns=["marca", "preco_medio"])
        df = df[df["marca"].isin(BRANDS)].copy()
        df["preco"] = parse_price(df["preco_medio"])
        df["ref"] = ref
        frames.append(df[["ref", "marca", "preco"]])

    tidy = pd.concat(frames, ignore_index=True).dropna(subset=["preco"])
    # Median is robust to the long right tail (a few collector cars at R$8M).
    monthly = (
        tidy.groupby(["ref", "marca"])["preco"].median().reset_index()
    )
    return monthly


def synthesize() -> pd.DataFrame:
    """Realistic monthly series, used only when the parquets are missing."""
    rng = np.random.default_rng(42)
    refs = pd.date_range("2020-08-01", "2023-01-01", freq="MS")
    base = {"Toyota": 95_000, "VW - VolksWagen": 60_000, "BMW": 180_000, "Fiat": 45_000}
    rows = []
    for brand, b0 in base.items():
        # gentle upward drift (used-car prices rose through 2021-2022) + noise
        drift = np.linspace(0, 0.22, len(refs))
        noise = rng.normal(0, 0.015, len(refs)).cumsum()
        level = b0 * (1 + drift + noise)
        for ref, price in zip(refs, level):
            rows.append({"ref": ref, "marca": brand, "preco": float(price)})
    return pd.DataFrame(rows)


def main() -> None:
    monthly = load_real()
    synthetic = monthly is None
    if synthetic:
        monthly = synthesize()

    fig, ax = plt.subplots()
    for i, brand in enumerate(BRANDS):
        sub = monthly[monthly["marca"] == brand].sort_values("ref")
        ax.plot(
            sub["ref"],
            sub["preco"] / 1000,
            label=brand,
            color=PALETTE[i % len(PALETTE)],
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            marker=MARKERS[i % len(MARKERS)],
            markersize=4,
            linewidth=1.6,
        )

    ax.set_xlabel("Reference month")
    ax.set_ylabel("Median price (R$ thousands)")
    title = "Median used-car price by brand, monthly FIPE table"
    if synthetic:
        title += " (synthetic)"
    ax.set_title(title)
    ax.legend(ncol=2, fontsize=9)
    fig.autofmt_xdate()

    out = save(fig, OUT)
    print(f"wrote {out}  ({'synthetic' if synthetic else 'real FIPE data'})")


if __name__ == "__main__":
    main()
