"""Toy flow fields for the simulation.

This is deliberately not a patient-specific blood-flow model.
"""

import numpy as np
from src.validation import nonnegative, vector


def centerline_flow(position_m, junction_x_m=10e-3, speed_m_s=1e-3):
    """Piecewise flow following the inlet then a branch selected by y sign."""
    p = np.asarray(position_m, dtype=float)
    if p[0] < junction_x_m:
        direction = np.array([1.0, 0.0, 0.0])
    elif p[1] >= 0:
        direction = np.array([10.0, 6.0, 3.0])
    else:
        direction = np.array([10.0, -6.0, -3.0])
    direction /= np.linalg.norm(direction)
    return speed_m_s * direction


def smooth_junction_flow(position_m, junction_x_m=10e-3, speed_m_s=1e-3,
                         transition_length_m=1e-3, branch_width_m=0.3e-3):
    """Continuous toy direction blend, not a wall-conforming or CFD solution.

    Longitudinal activation and lateral branch selection use tanh transitions.
    The symmetric y=0 streamline stays straight; no upper-branch tie-break is
    imposed. Normalization preserves the prescribed speed, not volume flux.
    """
    p = vector(position_m)
    nonnegative(speed_m_s, "speed_m_s")
    nonnegative(transition_length_m, "transition_length_m", positive=True)
    nonnegative(branch_width_m, "branch_width_m", positive=True)
    activation = 0.5 * (1 + np.tanh((p[0] - junction_x_m) / transition_length_m))
    selection = np.tanh(p[1] / branch_width_m)
    direction = np.array([1.0, 0.6 * activation * selection, 0.3 * activation * selection])
    return speed_m_s * direction / np.linalg.norm(direction)


def prescribed_flow(position_m, speed_m_s, model="piecewise",
                    transition_length_m=1e-3, branch_width_m=0.3e-3):
    if model == "piecewise":
        return centerline_flow(position_m, speed_m_s=speed_m_s)
    if model == "smooth":
        return smooth_junction_flow(position_m, speed_m_s=speed_m_s,
                                    transition_length_m=transition_length_m,
                                    branch_width_m=branch_width_m)
    raise ValueError("flow model must be piecewise or smooth")


class FlowDisturbance:
    """Stationary Gaussian velocity disturbance, independent across axes.

    Positive correlation time gives an Ornstein-Uhlenbeck sampled process.
    Zero correlation time preserves the original independent-per-tick draws.
    This is synthetic velocity uncertainty, not a turbulence model.
    """

    def __init__(self, sigma_m_s, correlation_s=0.0, rng=None):
        self.sigma = nonnegative(sigma_m_s, "sigma_m_s")
        self.correlation_s = nonnegative(correlation_s, "correlation_s")
        self.rng = np.random.default_rng() if rng is None else rng
        self.value = None
        self.last_time_s = None

    def sample(self, now_s):
        nonnegative(now_s, "now_s")
        if self.last_time_s is not None and now_s <= self.last_time_s:
            raise ValueError("disturbance sample time must increase strictly")
        noise = self.rng.normal(0, self.sigma, 3)
        if self.value is None or self.correlation_s == 0:
            self.value = noise
        else:
            rho = np.exp(-(now_s - self.last_time_s) / self.correlation_s)
            self.value = rho * self.value + np.sqrt(-np.expm1(
                -2 * (now_s - self.last_time_s) / self.correlation_s)) * noise
        self.last_time_s = now_s
        return self.value.copy()
