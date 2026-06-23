"""Quota-over-time sawtooth across a billing cycle, with daily Beat runs.

SYNTHETIC illustration. The numbers (a 1000-question monthly quota, a usage
curve) are made up to show the *shape* of the system: the scheduled task fires
every day, but only the month-boundary run actually resets state. Every other
run -- including a duplicate redelivery on the boundary day -- is a no-op,
because the task is gated on `restored_at`.
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

apply()

rng = np.random.default_rng(7)

QUOTA = 1000          # monthly question quota (synthetic)
DAYS = 62             # two ~31-day months
RESET_DAYS = [0, 31]  # the 1st of each month: the only days that reset

# Build a sawtooth: quota refills to QUOTA on reset days, then drains as the
# user spends questions through the month at a noisy daily rate.
remaining = np.empty(DAYS)
level = QUOTA
for day in range(DAYS):
    if day in RESET_DAYS:
        level = QUOTA            # restore_values(): back to the cap
    remaining[day] = level
    spend = max(0, rng.normal(38, 12))   # questions used that day
    level = max(0, level - spend)

days = np.arange(DAYS)

fig, ax = plt.subplots()
ax.plot(days, remaining, color=PALETTE[0], linewidth=2.0,
        label="Questions remaining")

# Mark every daily Beat run. Most are no-ops; only boundary runs reset state.
noop_days = [d for d in days if d not in RESET_DAYS]
ax.scatter(noop_days, remaining[noop_days], s=14, color=PALETTE[5],
           alpha=0.55, zorder=3, label="Daily Beat run (no-op)")
ax.scatter(RESET_DAYS, [QUOTA] * len(RESET_DAYS), s=70, color=PALETTE[3],
           marker="^", zorder=4, label="Boundary run (resets quota)")

# A duplicate redelivery on the second boundary: at-least-once delivery fires
# the task twice, but the second run sees restored_at == today and does nothing.
ax.annotate(
    "duplicate redelivery\n-> no-op (already restored)",
    xy=(31, QUOTA), xytext=(36, QUOTA * 0.74),
    fontsize=9.5,
    arrowprops=dict(arrowstyle="->", color=PALETTE[3], lw=1.2),
)

ax.set_xlabel("Day of billing cycle")
ax.set_ylabel("Questions remaining (synthetic)")
ax.set_title("Idempotent monthly reset: every day runs, only the 1st acts")
ax.set_ylim(0, QUOTA * 1.08)
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/idempotent-scheduled-jobs-with-celery-beat/quota_cycle.svg",
)
print(f"wrote {out}")
