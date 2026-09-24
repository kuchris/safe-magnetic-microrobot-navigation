"""Toy flow fields for the simulation.

This is deliberately not a patient-specific blood-flow model.
"""

from functools import lru_cache

import numpy as np
from src.validation import nonnegative, vector
from src.vessel import YVessel


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


@lru_cache(maxsize=1)
def _default_vessel():
    return YVessel()


@lru_cache(maxsize=8)
def _segment_arrays(vessel):
    starts = np.array([s.start_m for s in vessel.segments])
    axes = np.array([s.end_m - s.start_m for s in vessel.segments])
    return starts, axes, np.sum(axes ** 2, axis=1), np.array([s.radius_m for s in vessel.segments])


OCCLUDED_SEGMENT = {"upper": 1, "lower": 2}


def poiseuille_flow(position_m, mean_speed_m_s, vessel=None,
                    transition_length_m=1e-3, branch_width_m=0.3e-3, occluded_branch=None):
    """Parabolic speed 2U(1 - rho^2/R^2) along the smooth junction direction.

    U is the cross-sectional mean of a straight segment; the centerline carries
    2U. rho is taken per capsule and the largest profile value is kept, so the
    field is continuous across the junction and zero on and outside the wall.
    Quasi-analytic, not CFD: no flux split, secondary flow or entrance length,
    and the particle samples the fluid at its center (no Faxen correction).
    The direction blend assumes the default YVessel junction at x = 10 mm.

    occluded_branch ("upper" or "lower") models a dead-end branch: every
    streamline turns into the patent branch and the occluded capsule carries no
    profile of its own, so its flow decays within about one radius of the
    junction. No recirculation or flux conservation is modeled.
    """
    p = vector(position_m)
    nonnegative(mean_speed_m_s, "mean_speed_m_s")
    nonnegative(transition_length_m, "transition_length_m", positive=True)
    nonnegative(branch_width_m, "branch_width_m", positive=True)
    starts, axes, lengths, radii = _segment_arrays(_default_vessel() if vessel is None else vessel)
    fraction = np.clip(np.einsum("ij,ij->i", p - starts, axes) / lengths, 0.0, 1.0)
    rho = np.linalg.norm(p - starts - fraction[:, None] * axes, axis=1)
    profile = 1 - (rho / radii) ** 2
    if occluded_branch is not None:
        if occluded_branch not in OCCLUDED_SEGMENT:
            raise ValueError("occluded_branch must be None, 'upper' or 'lower'")
        profile[OCCLUDED_SEGMENT[occluded_branch]] = -np.inf
        selection = -1.0 if occluded_branch == "upper" else 1.0
    else:
        selection = np.tanh(p[1] / branch_width_m)
    activation = 0.5 * (1 + np.tanh((p[0] - 10e-3) / transition_length_m))
    direction = np.array([1.0, 0.6 * activation * selection, 0.3 * activation * selection])
    return 2 * mean_speed_m_s * max(profile.max(), 0.0) * direction / np.linalg.norm(direction)


def prescribed_flow(position_m, speed_m_s, model="piecewise",
                    transition_length_m=1e-3, branch_width_m=0.3e-3, vessel=None, occluded_branch=None):
    if occluded_branch is not None and model != "poiseuille":
        raise ValueError("occluded_branch requires the poiseuille flow model")
    if model == "poiseuille":
        return poiseuille_flow(position_m, speed_m_s, vessel, transition_length_m, branch_width_m,
                               occluded_branch)
    if model == "piecewise":
        return centerline_flow(position_m, speed_m_s=speed_m_s)
    if model == "smooth":
        return smooth_junction_flow(position_m, speed_m_s=speed_m_s,
                                    transition_length_m=transition_length_m,
                                    branch_width_m=branch_width_m)
    raise ValueError("flow model must be piecewise, smooth or poiseuille")


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


def pulsatile_speed(mean_speed_m_s, time_s, amplitude=0.0, period_s=1.0):
    """Quasi-steady pulsation U(t) = U (1 + A sin(2 pi t / T)), with 0 <= A <= 1.

    The whole profile is scaled in phase, which is valid only for a small
    Womersley number; see womersley_number. For a sinusoid, Gosling's
    pulsatility index PI = (V_max - V_min) / V_mean equals 2A.
    """
    nonnegative(mean_speed_m_s, "mean_speed_m_s")
    if not 0 <= amplitude <= 1:
        raise ValueError("pulsation amplitude must be in [0, 1]; flow reversal is not modeled")
    nonnegative(period_s, "period_s", positive=True)
    return mean_speed_m_s * (1.0 + amplitude * np.sin(2 * np.pi * time_s / period_s))


def womersley_number(vessel_radius_m, period_s, viscosity_pa_s=3.5e-3, density_kg_m3=1060.0):
    """alpha = R sqrt(omega rho / eta); alpha >~ 1 means the profile is not quasi-steady."""
    omega = 2 * np.pi / nonnegative(period_s, "period_s", positive=True)
    return vessel_radius_m * np.sqrt(omega * density_kg_m3 / viscosity_pa_s)


def material_acceleration(velocity_field, position_m, time_s, step_m=1e-6, step_s=1e-4):
    """Du/Dt = du/dt + (u . grad) u by central differences of velocity_field(p, t).

    The convective term differentiates along the local flow direction only,
    which is all (u . grad) u needs.
    """
    p = vector(position_m)
    u = velocity_field(p, time_s)
    local = (velocity_field(p, time_s + step_s) - velocity_field(p, time_s - step_s)) / (2 * step_s)
    speed = np.linalg.norm(u)
    if speed == 0:
        return local
    along = u / speed * step_m
    convective = speed * (velocity_field(p + along, time_s) - velocity_field(p - along, time_s)) / (2 * step_m)
    return local + convective
