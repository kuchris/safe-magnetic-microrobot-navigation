"""Safety supervisor for simulation experiments."""

import numpy as np


class SafetySupervisor:
    """Allows actuation only when localization and wall clearance are acceptable."""

    def __init__(self, max_sigma_m=0.35e-3, min_clearance_m=0.25e-3):
        self.max_sigma_m = float(max_sigma_m)
        self.min_clearance_m = float(min_clearance_m)

    def evaluate(self, estimated_position_m, sigma_m, vessel, particle_radius_m):
        clearance = vessel.clearance(estimated_position_m, particle_radius_m)
        if sigma_m > self.max_sigma_m:
            return False, "localization_uncertain", clearance
        if clearance < self.min_clearance_m:
            return False, "wall_margin_low", clearance
        return True, "safe", clearance

    def filter_force(self, force_n, allowed):
        return np.asarray(force_n, dtype=float) if allowed else np.zeros(3)
