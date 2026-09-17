"""Safety supervisor for simulation experiments."""

import numpy as np
from src.controller import limit_force
from src.validation import nonnegative, vector


class SafetySupervisor:
    """Allows actuation only when localization and wall clearance are acceptable."""

    def __init__(self, max_sigma_m=0.35e-3, min_clearance_m=0.25e-3,
                 k_sigma=3.0, max_measurement_age_s=0.15, max_force_n=2e-10):
        self.max_sigma_m = nonnegative(max_sigma_m, "max_sigma_m")
        self.min_clearance_m = nonnegative(min_clearance_m, "min_clearance_m")
        self.k_sigma = nonnegative(k_sigma, "k_sigma")
        self.max_measurement_age_s = nonnegative(max_measurement_age_s, "max_measurement_age_s")
        self.max_force_n = nonnegative(max_force_n, "max_force_n")

    def evaluate(self, estimated_position_m, sigma_m, vessel, particle_radius_m,
                 tracking_valid=True, measurement_age_s=0.0):
        if (not tracking_valid or not np.isfinite(measurement_age_s) or
                measurement_age_s < 0 or measurement_age_s > self.max_measurement_age_s):
            return False, "tracking_lost", float("nan")
        try:
            estimated_position_m = vector(estimated_position_m)
        except ValueError:
            return False, "localization_uncertain", float("nan")
        if not np.isfinite(sigma_m) or sigma_m < 0:
            return False, "localization_uncertain", float("nan")
        clearance = vessel.clearance(estimated_position_m, particle_radius_m)
        robust_clearance = clearance - self.k_sigma * sigma_m
        if sigma_m > self.max_sigma_m:
            return False, "localization_uncertain", clearance
        if robust_clearance <= self.min_clearance_m:
            return False, "wall_margin_low", clearance
        return True, "safe", clearance

    def filter_force(self, force_n, allowed):
        return limit_force(force_n, self.max_force_n) if allowed else np.zeros(3)
