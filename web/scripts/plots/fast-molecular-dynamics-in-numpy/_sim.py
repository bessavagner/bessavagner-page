"""A tiny, self-contained 2D Lennard-Jones molecular-dynamics simulation.

This is a standalone reproduction of the ideas in the article — cell-list
neighbour search, a cutoff-shifted Lennard-Jones force, velocity-Verlet
integration and a velocity-rescaling thermostat — all in reduced units
(sigma = epsilon = mass = 1). It is deliberately short and exists only to
produce reproducible data for the article's plots; it is not the dynamol
package itself.
"""

from __future__ import annotations

import numpy as np


def lj_force_and_potential(r2, cutoff):
    """Shifted-force Lennard-Jones in reduced units, given squared distances.

    Returns (scalar force / r, potential) for separations inside the cutoff.
    The force is shifted so it goes smoothly to zero at the cutoff radius,
    which keeps energy continuous and conserved.
    """
    inv_r2 = 1.0 / r2
    inv_r6 = inv_r2 ** 3
    inv_r12 = inv_r6 ** 2
    # f_scalar = (force magnitude) / r, ready to multiply the separation vector.
    f_scalar = 24.0 * (2.0 * inv_r12 - inv_r6) * inv_r2
    pot = 4.0 * (inv_r12 - inv_r6)
    # Shift the potential so V(cutoff) = 0.
    rc2 = cutoff * cutoff
    inv_rc6 = (1.0 / rc2) ** 3
    pot_shift = 4.0 * (inv_rc6 ** 2 - inv_rc6)
    return f_scalar, pot - pot_shift


def build_cell_list(positions, box, cutoff):
    """Bin particles into a grid of cells of side >= cutoff (a spatial hash)."""
    n_cells = max(int(np.floor(box / cutoff)), 1)
    cell_size = box / n_cells
    cell_idx = np.floor(positions / cell_size).astype(int) % n_cells
    grid = {}
    for i, (cx, cy) in enumerate(cell_idx):
        grid.setdefault((cx, cy), []).append(i)
    return grid, n_cells


def compute_forces(positions, box, cutoff):
    """Accumulate forces and potential energy using a cell list.

    Each particle only checks the 8 neighbouring cells plus its own, so the
    work scales with N rather than N^2.
    """
    n = len(positions)
    forces = np.zeros_like(positions)
    potential = 0.0
    rc2 = cutoff * cutoff
    grid, n_cells = build_cell_list(positions, box, cutoff)

    for (cx, cy), members in grid.items():
        # Gather candidate neighbours from this cell and its 8 neighbours.
        candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                key = ((cx + dx) % n_cells, (cy + dy) % n_cells)
                candidates.extend(grid.get(key, ()))
        candidates = np.array(candidates)
        for i in members:
            rij = positions[i] - positions[candidates]
            rij -= box * np.round(rij / box)          # minimum-image convention
            r2 = np.einsum("ij,ij->i", rij, rij)
            mask = (r2 < rc2) & (r2 > 1e-12)           # inside cutoff, not self
            if not np.any(mask):
                continue
            f_scalar, pot = lj_force_and_potential(r2[mask], cutoff)
            forces[i] += np.sum(f_scalar[:, None] * rij[mask], axis=0)
            potential += 0.5 * np.sum(pot)             # 0.5 for double counting
    return forces, potential


def kinetic_and_temperature(velocities):
    n, dim = velocities.shape
    kinetic = 0.5 * np.sum(velocities * velocities)
    # Equipartition with centre-of-mass momentum removed: dim*(N-1)/2 dof.
    temperature = 2.0 * kinetic / (dim * (n - 1))
    return kinetic, temperature


def simulate(
    n_side=20,
    spacing=1.12,
    dt=0.004,
    steps=4000,
    cutoff=2.5,
    t_target=1.2,
    thermostat_until=1500,
    tau=0.1,
    seed=0,
    sample_every=10,
):
    """Run a 2D LJ gas and return time series plus the final configuration."""
    rng = np.random.default_rng(seed)
    n = n_side * n_side
    box = n_side * spacing

    # Square lattice start, slightly jittered so it is not pathologically perfect.
    grid = np.arange(n_side) * spacing
    gx, gy = np.meshgrid(grid, grid)
    positions = np.column_stack([gx.ravel(), gy.ravel()])
    positions += rng.normal(scale=0.01, size=positions.shape)
    positions %= box

    # Maxwell-Boltzmann velocities, drift removed, rescaled to the target T.
    velocities = rng.normal(scale=np.sqrt(t_target), size=positions.shape)
    velocities -= velocities.mean(axis=0)
    _, temp0 = kinetic_and_temperature(velocities)
    velocities *= np.sqrt(t_target / temp0)

    forces, potential = compute_forces(positions, box, cutoff)

    times, e_kin, e_pot, e_tot, temps = [], [], [], [], []
    half_dt = 0.5 * dt
    for step in range(steps):
        # Velocity-Verlet: half-kick, drift, recompute forces, half-kick.
        velocities += half_dt * forces
        positions = (positions + dt * velocities) % box
        forces, potential = compute_forces(positions, box, cutoff)
        velocities += half_dt * forces

        kinetic, temperature = kinetic_and_temperature(velocities)

        # Gentle velocity rescaling (Berendsen-style) only while equilibrating.
        if step < thermostat_until:
            lam = np.sqrt(1.0 + (dt / tau) * (t_target / temperature - 1.0))
            velocities *= lam

        if step % sample_every == 0:
            kinetic, temperature = kinetic_and_temperature(velocities)
            times.append(step * dt)
            e_kin.append(kinetic / n)
            e_pot.append(potential / n)
            e_tot.append((kinetic + potential) / n)
            temps.append(temperature)

    return {
        "time": np.array(times),
        "e_kin": np.array(e_kin),
        "e_pot": np.array(e_pot),
        "e_tot": np.array(e_tot),
        "temp": np.array(temps),
        "positions": positions,
        "box": box,
        "n": n,
        "t_target": t_target,
        "thermostat_off_time": thermostat_until * dt,
    }


def radial_distribution(positions, box, n_bins=120, r_max=None):
    """Compute g(r) for a 2D periodic box of point particles."""
    n = len(positions)
    if r_max is None:
        r_max = box / 2.0
    diff = positions[:, None, :] - positions[None, :, :]
    diff -= box * np.round(diff / box)
    dist = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
    iu = np.triu_indices(n, k=1)
    dist = dist[iu]
    dist = dist[dist < r_max]

    counts, edges = np.histogram(dist, bins=n_bins, range=(0.0, r_max))
    centres = 0.5 * (edges[:-1] + edges[1:])
    # Normalise by the ideal-gas expectation (ring area * number density).
    density = n / (box * box)
    ring_area = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    ideal = density * ring_area * n / 2.0
    g = counts / ideal
    return centres, g
