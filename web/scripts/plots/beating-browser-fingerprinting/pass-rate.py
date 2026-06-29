"""Detection results by setup — MEASURED, not illustrative.

Methodology (reproducible):
  * Date 2026-06-29, Google Chrome 149.0.7827.155 on Linux, headful on a real
    X display (DISPLAY=:1), single machine / single residential IP.
  * Three setups: stock Selenium ("vanilla"), selenium-stealth, and
    undetected-chromedriver (pinned to Chrome 149).
  * Three self-hosted measurements per setup, 3 trials each:
      - Automation-tells panel: 17 concrete signals the post discusses
        (navigator.webdriver, $cdc_ props, chrome object, plugins/mimeTypes,
        languages, UA headless token, productSub, WebGL renderer/vendor,
        permissions consistency, error-stack cleanliness, eval length, etc.),
        scored as % passed. Served from localhost.
      - BotD (FingerprintJS, open source), self-hosted: binary bot verdict.
      - CreepJS, self-hosted: count of locally-detected "lies" (inconsistencies).
        Its headline "trust score" needs CreepJS's API, so it isn't measurable
        on a self-hosted copy; the local lie count is.
  * Results were stable across the 3 trials: BotD verdict and CreepJS lies were
    identical every run; the tells panel varied only on vanilla's window-outer
    check (a window-manager quirk, not an automation tell): 14-15/17.

These are a snapshot of one environment on one day, not a guarantee — detection
evolves, and a setup that passes today can fail next month.
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

apply()

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

setups = ["Vanilla\nSelenium", "selenium-\nstealth", "undetected-\nchromedriver"]
tells_pct = [88, 94, 94]          # automation-tells panel, % of 17 passed (vanilla 14-15/17)
botd_passed = [False, False, True]  # BotD bot verdict: did it pass (not flagged)?
creep_lies = [0, 2, 0]            # CreepJS locally-detected lies

CAUGHT = PALETTE[3]   # vermillion
PASSED = PALETTE[2]   # green
colors = [PASSED if p else CAUGHT for p in botd_passed]

x = np.arange(len(setups))
fig, ax = plt.subplots(figsize=(7.4, 4.6))

bars = ax.bar(x, tells_pct, width=0.6, color=colors, edgecolor="white", linewidth=0.5)

ax.set_ylabel("Automation-tells passed (%)")
ax.set_title("Detection results by setup (measured · Chrome 149 · self-hosted)")
ax.set_xticks(x)
ax.set_xticklabels(setups)
ax.set_ylim(0, 100)

# Value labels on the bars.
ax.bar_label(bars, fmt="%d%%", padding=3, fontsize=10)

# Per-setup annotations under the axis: BotD verdict + CreepJS lies.
tr = ax.get_xaxis_transform()  # x in data coords, y in axes fraction
for xi, passed, lies in zip(x, botd_passed, creep_lies):
    verdict = "BotD: passed" if passed else "BotD: caught"
    vcolor = PASSED if passed else CAUGHT
    ax.text(xi, -0.16, verdict, transform=tr, ha="center", va="top",
            fontsize=9.5, color=vcolor, fontweight="bold", clip_on=False)
    ax.text(xi, -0.24, f"CreepJS lies: {lies}", transform=tr, ha="center", va="top",
            fontsize=9.5, clip_on=False)

# Legend explains the bar colour (the headline result).
ax.legend(handles=[
    Patch(facecolor=PASSED, label="Passed BotD"),
    Patch(facecolor=CAUGHT, label="Caught by BotD (as 'selenium')"),
], loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.42))

fig.subplots_adjust(bottom=0.30)

out = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/beating-browser-fingerprinting/pass-rate.svg"
)
save(fig, out)
print(f"wrote {out}")
