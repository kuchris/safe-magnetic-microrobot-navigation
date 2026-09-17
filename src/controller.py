"""Toy closed-loop controller for simulation only."""

import numpy as np


def bounded_target_force(position_m, target_m, gain_n_per_m=2e-8, max_force_n=2e-10):
    """Proportional target-seeking force with a hard magnitude limit."""
    error = np.asarray(target_m, dtype=float) - np.asarray(position_m, dtype=float)
    force = gain_n_per_m * error
    norm = np.linalg.norm(force)
    if norm > max_force_n and norm > 0:
        force = force * (max_force_n / norm)
    return force
