"""Radial distribution function g(r) of the equilibrated 2D LJ fluid."""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, LINESTYLES, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from _sim import radial_distribution, simulate  # noqa: E402

apply()

run = simulate(seed=1)
r, g = radial_distribution(run["positions"], run["box"])

fig, ax = plt.subplots()
ax.plot(r, g, linestyle=LINESTYLES[0], label="g(r)")
ax.axhline(1.0, linestyle=LINESTYLES[3], color=PALETTE[4], label="Ideal gas (g = 1)")

ax.set_xlabel("Separation r (reduced units)")
ax.set_ylabel("g(r)")
ax.set_title("Radial distribution function of the equilibrated fluid")
ax.legend(loc="upper right")

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/fast-molecular-dynamics-in-numpy/rdf.svg",
)
print(f"wrote {out}")
