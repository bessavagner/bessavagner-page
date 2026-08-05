"""What each discount rule actually registers, against the amount really paid.

REAL data, from two receipts photographed on 2026-07-04 and preserved as test
fixtures in expense_tracker_v2
(``src/backend/assistant/tests/test_receipt_discount_reconcile.py``):

* DROGASIL: the coupon prints per-item "Valor Líquido", so the lines are ALREADY
  net and sum to the amount paid (118.86). It also prints ``discount = 27.60``.
  Subtracting that printed discount from already-net lines double-counts it and
  registers 91.26, which is what the app did before commit 3863c36.
* PAGUE MENOS: the lines are GROSS (217.32) and the printed discount (61.42) is
  exactly the gap down to the amount paid (155.90). Here the printed-discount
  rule happens to be right.

The derived rule, ``discount = max(0, sum(lines) - amount_paid)``, lands on the
amount paid for both shapes. That is the point of the figure.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

apply()

# (store, sum of lines, printed discount, amount paid, line shape)
RECEIPTS = [
    ("DROGASIL", 118.86, 27.60, 118.86, "lines already net"),
    ("PAGUE MENOS", 217.32, 61.42, 155.90, "lines gross"),
]

fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=False)

for ax, (store, lines, printed, paid, shape) in zip(axes, RECEIPTS):
    printed_rule = round(lines - printed, 2)
    derived_rule = round(lines - max(0.0, lines - paid), 2)

    labels = [
        "Derived discount\nsum(lines) − amount paid",
        "Printed discount\nthe coupon's own number",
    ]
    values = [derived_rule, printed_rule]
    colors = [
        PALETTE[2] if abs(v - paid) < 0.005 else PALETTE[3] for v in values
    ]

    bars = ax.barh(labels, values, color=colors, height=0.55)
    ax.axvline(paid, color=PALETTE[0], linestyle="--", linewidth=1.4, zorder=3)
    ax.annotate(
        f"amount paid\nR$ {paid:,.2f}".replace(",", "."),
        xy=(paid, 1.55),
        xytext=(4, 0),
        textcoords="offset points",
        color=PALETTE[0],
        fontsize=9,
        va="top",
    )

    for bar, value in zip(bars, values):
        gap = value - paid
        note = f"R$ {value:,.2f}".replace(",", ".")
        if abs(gap) >= 0.005:
            note += f"   ({gap:+.2f} vs paid)"
        ax.annotate(
            note,
            xy=(value, bar.get_y() + bar.get_height() / 2),
            xytext=(-6, 0),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=9.5,
            color="white",
            fontweight="bold",
        )

    ax.set_xlim(0, max(lines, paid) * 1.18)
    ax.set_ylim(-0.6, 1.9)
    ax.set_title(f"{store} · 04/07/2026 · {shape}", loc="left", fontsize=11)
    ax.set_xlabel("total registered (R$)" if ax is axes[-1] else "")
    ax.grid(axis="y", visible=False)

fig.tight_layout(h_pad=2.0)

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/dont-let-the-llm-do-the-math/reconciliation.svg",
)
print(f"wrote {out}")
