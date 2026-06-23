"""Purchase date vs. billing month: six months of card purchases mapped to the
invoice month they're actually paid, plus one installment plan spread across
consecutive cycles. All data is SYNTHETIC — no real transactions."""

import pathlib
import sys
from datetime import date

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, MARKERS  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

apply()

CLOSING_DAY = 20  # the card closes on the 20th each month


def month_index(d: date) -> float:
    """Months since Jan of the first year, as a float position on the axis."""
    return (d.year - 2026) * 12 + (d.month - 1) + (d.day - 1) / 31.0


def billing_month(purchase: date, closing_day: int) -> date:
    """Mirror of compute_billing_month for a credit card: a purchase on/before
    the closing day lands on the next invoice (paid M+1); after it, M+2."""
    first = purchase.replace(day=1)
    close = first if purchase.day <= closing_day else _next(first)
    return _next(close)


def _next(d: date) -> date:
    return date(d.year + 1, 1, 1) if d.month == 12 else date(d.year, d.month + 1, 1)


# Six synthetic one-off purchases, deliberately straddling the closing day.
purchases = [
    date(2026, 1, 8),
    date(2026, 1, 27),   # after the 20th -> rolls an extra month
    date(2026, 2, 19),
    date(2026, 3, 25),   # after the 20th
    date(2026, 4, 11),
    date(2026, 5, 22),   # after the 20th
]

# One installment plan: a single purchase split into 4 charges, each on a
# consecutive invoice starting from its own billing month.
plan_start = date(2026, 2, 14)
plan_first = billing_month(plan_start, CLOSING_DAY)
plan_months = [plan_first]
for _ in range(3):
    plan_months.append(_next(plan_months[-1]))

fig, ax = plt.subplots(figsize=(7.4, 4.4))

PURCHASE_Y, BILL_Y = 1.0, 0.0

# One-off purchases: a marker on the purchase row, a marker on the billing row,
# and an arrow showing the shift from one to the other.
for p in purchases:
    b = billing_month(p, CLOSING_DAY)
    xp, xb = month_index(p), month_index(b)
    late = p.day > CLOSING_DAY
    color = PALETTE[3] if late else PALETTE[0]
    ax.scatter([xp], [PURCHASE_Y], color=color, marker=MARKERS[0], zorder=3, s=55)
    ax.scatter([xb], [BILL_Y], color=color, marker=MARKERS[1], zorder=3, s=55)
    ax.add_patch(
        FancyArrowPatch(
            (xp, PURCHASE_Y - 0.05), (xb, BILL_Y + 0.05),
            arrowstyle="-|>", mutation_scale=11,
            color=color, alpha=0.55, lw=1.1, shrinkA=2, shrinkB=2,
        )
    )

# Installment plan: one purchase, four billing months on consecutive invoices.
xp = month_index(plan_start)
ax.scatter([xp], [PURCHASE_Y], color=PALETTE[2], marker=MARKERS[2], zorder=4, s=70)
for i, b in enumerate(plan_months):
    xb = month_index(b)
    ax.scatter([xb], [BILL_Y], color=PALETTE[2], marker=MARKERS[2], zorder=4, s=55)
    ax.add_patch(
        FancyArrowPatch(
            (xp, PURCHASE_Y - 0.05), (xb, BILL_Y + 0.05),
            arrowstyle="-|>", mutation_scale=11,
            color=PALETTE[2], alpha=0.5, lw=1.1,
            connectionstyle=f"arc3,rad={-0.18 - 0.04 * i}",
            shrinkA=2, shrinkB=2,
        )
    )

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
ax.set_xticks(range(len(months)))
ax.set_xticklabels(months)
ax.set_yticks([BILL_Y, PURCHASE_Y])
ax.set_yticklabels(["Billing month\n(invoice paid)", "Purchase date"])
ax.set_ylim(-0.5, 1.5)
ax.set_xlim(-0.4, len(months) - 0.6)
ax.set_title(f"Purchase date vs. billing month (card closes on the {CLOSING_DAY}th)")

# Legend by hand: the three categories the colours encode.
handles = [
    plt.Line2D([], [], color=PALETTE[0], marker=MARKERS[0], linestyle="none",
               label="Purchase on/before closing day (paid in M+1)"),
    plt.Line2D([], [], color=PALETTE[3], marker=MARKERS[0], linestyle="none",
               label="Purchase after closing day (rolls to M+2)"),
    plt.Line2D([], [], color=PALETTE[2], marker=MARKERS[2], linestyle="none",
               label="One installment plan, spread over 4 invoices"),
]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1)

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/credit-card-billing-cycles/timeline.svg",
)
print(f"wrote {out}")
