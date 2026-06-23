"""Temperature equilibration toward the target via velocity rescaling."""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from _sim import simulate  # noqa: E402

apply()

run = simulate(seed=1)

fig, ax = plt.subplots()
ax.plot(run["time"], run["temp"], linestyle=LINESTYLES[0], label="Instantaneous T")
ax.axhline(
    run["t_target"],
    linestyle=LINESTYLES[1],
    color=PALETTE[1],
    label=f"Target T = {run['t_target']:.1f}",
)
ax.axvline(
    run["thermostat_off_time"],
    linestyle=LINESTYLES[3],
    color=PALETTE[3],
    label="Thermostat off",
)

ax.set_xlabel("Time (reduced units)")
ax.set_ylabel("Temperature (reduced units)")
ax.set_title("Temperature equilibration")
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/fast-molecular-dynamics-in-numpy/temperature.svg",
)
print(f"wrote {out}")
