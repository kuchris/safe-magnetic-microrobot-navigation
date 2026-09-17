"""Toy closed-loop controller for simulation only."""

import numpy as np
from src.validation import nonnegative, vector


def limit_force(force_n, max_force_n):
    force = vector(force_n)
    limit = nonnegative(max_force_n, "max_force_n")
    norm = np.linalg.norm(force)
    return force * (limit / norm) if norm > limit else force


def bounded_target_force(position_m, target_m, gain_n_per_m=2e-8, max_force_n=2e-10):
    """Proportional target-seeking force with a hard magnitude limit."""
    error = vector(target_m) - vector(position_m)
    return limit_force(nonnegative(gain_n_per_m, "gain_n_per_m") * error, max_force_n)
