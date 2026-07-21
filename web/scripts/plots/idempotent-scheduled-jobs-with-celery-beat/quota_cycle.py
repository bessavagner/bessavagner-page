"""Two guards, one calendar: when the monthly quota reset actually fires.

The firing days are COMPUTED, not drawn by hand: both guard expressions below
are copied verbatim from `accounts/tasks.py` (the shipped one, and the fix),
and the simulation walks a real daily Beat schedule day by day, advancing
`restored_at` exactly as `restore_values()` does.

Two stated assumptions, both flat and visible on the chart:
  * QUOTA is the real Starter-plan question allowance (1000/month).
  * The user spends a steady SPEND_PER_DAY questions. Real usage is lumpy;
    a constant rate keeps the drain a straight line so the *reset* days are
    what the eye picks up.

The point of the figure is the December anchor: `one_month_later` rolls into
January, so the shipped guard's `today.month > one_month_later.month` compares
12 > 1 and is true every remaining day of the year. That user is pinned at the
cap instead of drawing down a monthly allowance.
"""

import pathlib
import sys
from datetime import date, timedelta

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE, LINESTYLES  # noqa: E402

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from dateutil.relativedelta import relativedelta  # noqa: E402

apply()

QUOTA = 1000            # real Starter-plan monthly question allowance
SPEND_PER_DAY = 30      # assumed steady usage
ANCHOR = date(2026, 12, 10)   # last reset: a December date
DAYS = 100


def shipped(today, restored_at):
    """The guard as it shipped: compares month *numbers*."""
    one_month_later = restored_at + relativedelta(months=1)
    return today == one_month_later or today.month > one_month_later.month


def fixed(today, restored_at):
    """The fix: compares dates."""
    return today >= restored_at + relativedelta(months=1)


def simulate(guard):
    """Walk a daily Beat run, returning (dates, remaining, reset_days)."""
    restored_at = ANCHOR
    level = QUOTA - SPEND_PER_DAY   # the anchor day's spend is already gone
    days, remaining, resets = [], [], []
    for offset in range(1, DAYS + 1):
        today = ANCHOR + timedelta(days=offset)
        if guard(today, restored_at):
            level = QUOTA           # restore_values(): back to the cap
            restored_at = today     # ...and the guard closes behind it
            resets.append(today)
        days.append(today)
        remaining.append(level)
        level = max(0, level - SPEND_PER_DAY)
    return days, remaining, resets


fig, ax = plt.subplots()

for i, (label, guard) in enumerate(
    [
        ("Shipped guard (month numbers)", shipped),
        ("Fixed guard (dates)", fixed),
    ]
):
    days, remaining, resets = simulate(guard)
    ax.plot(days, remaining, color=PALETTE[i * 3], linewidth=2.0,
            linestyle=LINESTYLES[i], label=f"{label}: {len(resets)} refills")
    ax.scatter(resets, [QUOTA] * len(resets), s=48, color=PALETTE[i * 3],
               marker="^", zorder=4)

ax.axvspan(date(2026, 12, 11), date(2026, 12, 31), color=PALETTE[3],
           alpha=0.10, zorder=0)
ax.annotate(
    "12 > 1 every day of December:\nrefilled daily, never drawn down",
    xy=(date(2026, 12, 22), QUOTA * 1.02),
    xytext=(date(2026, 12, 13), QUOTA * 1.22),
    fontsize=9.5, ha="left",
    arrowprops=dict(arrowstyle="->", color=PALETTE[3], lw=1.2),
)

ax.set_ylabel("Questions remaining")
ax.set_title("A December reset date refills every day, until the guard compares dates")
ax.set_ylim(0, QUOTA * 1.38)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=2,
          frameon=False)

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/idempotent-scheduled-jobs-with-celery-beat/quota_cycle.svg",
)
print(f"wrote {out}")

for label, guard in [("shipped", shipped), ("fixed", fixed)]:
    _, _, resets = simulate(guard)
    print(f"{label:8s}: {len(resets)} refills in {DAYS} days; "
          f"first 5 = {[str(d) for d in resets[:5]]}")
