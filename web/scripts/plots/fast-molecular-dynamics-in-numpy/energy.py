"""Total vs kinetic vs potential energy over time (energy conservation)."""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from _sim import simulate  # noqa: E402

apply()

run = simulate(seed=1)

# Only look at the production window, after the thermostat is switched off,
# so the plot shows genuine NVE energy conservation rather than the
# thermostat doing work.
mask = run["time"] >= run["thermostat_off_time"]
t = run["time"][mask]
t0 = t[0]

fig, ax = plt.subplots()
ax.plot(t - t0, run["e_tot"][mask], linestyle=LINESTYLES[0], label="Total")
ax.plot(t - t0, run["e_kin"][mask], linestyle=LINESTYLES[1], label="Kinetic")
ax.plot(t - t0, run["e_pot"][mask], linestyle=LINESTYLES[2], label="Potential")

ax.set_xlabel("Time (reduced units)")
ax.set_ylabel("Energy per particle (reduced units)")
ax.set_title("Energy conservation under velocity-Verlet (NVE)")
ax.legend(loc="center right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/fast-molecular-dynamics-in-numpy/energy.svg",
)
print(f"wrote {out}")
