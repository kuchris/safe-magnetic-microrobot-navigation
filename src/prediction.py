"""Observation-based, sampled short-horizon force correction for the toy vessel."""

from dataclasses import dataclass
import numpy as np

from src.controller import limit_force
from src.validation import nonnegative


@dataclass(frozen=True)
class PredictionResult:
    force_n: np.ndarray
    nominal_clearance_m: float
    selected_clearance_m: float
    adjusted: bool
    terminal_active: bool = False
    terminal_adjusted: bool = False
    baseline_target_miss_m: float = np.nan
    selected_target_miss_m: float = np.nan


class ShortHorizonCorrection:
    """Try bounded forces using a constant estimated drift over five samples.

    Velocity changes are approximated by (candidate - previous command)/drag.
    Estimated velocity can lag commands; this is not a calibrated flow observer,
    a continuous-time safety guarantee, or a constrained optimal controller.
    Optional terminal guidance ranks wall-feasible candidates by target approach.
    """

    def __init__(self, vessel, particle_radius_m, branch, horizon_s,
                 drag_n_s_m, max_force_n, margin_m, k_sigma=3.0,
                 acceleration_spectral_density=1e-7, terminal_distance_m=0.0):
        self.vessel = vessel
        self.radius = particle_radius_m
        self.times = np.linspace(0, nonnegative(horizon_s, "horizon_s", positive=True), 6)
        self.drag = nonnegative(drag_n_s_m, "drag_n_s_m", positive=True)
        self.max_force = nonnegative(max_force_n, "max_force_n")
        self.margin = nonnegative(margin_m, "margin_m")
        self.k_sigma = nonnegative(k_sigma, "k_sigma")
        self.q = nonnegative(acceleration_spectral_density, "acceleration_spectral_density")
        self.route_segments = (vessel.segments[0], vessel.segments[1 if branch == "upper" else 2])
        self.terminal_distance = nonnegative(terminal_distance_m, "terminal_distance_m")

    def select(self, estimate, nominal_force_n, previous_force_n):
        p, v, covariance = estimate.estimated_position, estimate.estimated_velocity, estimate.covariance
        t = self.times
        future_covariance = (covariance[:3, :3] + t[:, None, None] *
            (covariance[:3, 3:] + covariance[3:, :3]) + t[:, None, None] ** 2 *
            covariance[3:, 3:] + self.q * t[:, None, None] ** 3 / 3 * np.eye(3))
        uncertainty = self.k_sigma * np.sqrt(np.maximum(0, np.linalg.eigvalsh(future_covariance)[:, -1]))
        nominal = limit_force(nominal_force_n, self.max_force)
        endpoint = p + t[-1] * (v + (nominal - previous_force_n) / self.drag)
        centers = [segment.closest_centerline_point(endpoint) for segment in self.route_segments]
        center = min(centers, key=lambda c: np.linalg.norm(c - endpoint))
        correction = limit_force(nominal + self.drag * (center - endpoint) / t[-1], self.max_force)
        # Candidate zero is included because stopping actuation still leaves flow.
        candidates = np.array([nominal + weight * (correction - nominal)
                               for weight in (0, 0.25, 0.5, 0.75, 1)] + [np.zeros(3)])
        baseline_count = len(candidates)
        target = self.route_segments[-1].end_m
        terminal_active = self.terminal_distance > 0 and np.linalg.norm(p - target) <= self.terminal_distance
        if terminal_active:
            flow = v - previous_force_n / self.drag
            intercept = limit_force(self.drag * ((target - p) / t[-1] - flow), self.max_force)
            candidates = np.vstack([candidates, [nominal + weight * (intercept - nominal)
                                     for weight in (0.25, 0.5, 0.75, 1)]])
        points = p + t[None, :, None] * (v + (candidates - previous_force_n) / self.drag)[:, None, :]
        clearances = []
        for segment in self.vessel.segments:
            axis = segment.end_m - segment.start_m
            fraction = np.clip((points - segment.start_m) @ axis / (axis @ axis), 0, 1)
            centers = segment.start_m + fraction[..., None] * axis
            clearances.append(segment.radius_m - self.radius - np.linalg.norm(points - centers, axis=-1))
        robust = np.max(clearances, axis=0) - uncertainty
        minimum = robust.min(axis=1)
        baseline_feasible = np.flatnonzero(minimum[:baseline_count] >= self.margin)
        # Prefer the smallest change that meets the sampled margin. If none do,
        # choose the best predicted clearance; do not label it safe or feasible.
        baseline = (min(baseline_feasible, key=lambda i: np.linalg.norm(candidates[i] - nominal))
                    if len(baseline_feasible) else int(np.argmax(minimum[:baseline_count])))
        selected = baseline
        misses = None
        if terminal_active:
            velocity = v + (candidates - previous_force_n) / self.drag
            speed_squared = np.sum(velocity**2, axis=1)
            closest_time = np.clip(np.divide(velocity @ (target - p), speed_squared,
                                   out=np.zeros(len(candidates)), where=speed_squared > 0), 0, t[-1])
            misses = np.linalg.norm(p + closest_time[:, None] * velocity - target, axis=1)
            feasible = np.flatnonzero(minimum >= self.margin)
            # Keep wall feasibility ahead of target approach. If no candidate is
            # feasible, retain the greatest-minimum-clearance fallback.
            selected = (min(feasible, key=lambda i: (misses[i], np.linalg.norm(candidates[i] - nominal)))
                        if len(feasible) else int(np.argmax(minimum)))
        adjusted = bool(np.linalg.norm(candidates[selected] - nominal) > 1e-18)
        terminal_adjusted = bool(terminal_active and np.linalg.norm(candidates[selected] - candidates[baseline]) > 1e-18)
        return PredictionResult(candidates[selected], float(minimum[0]), float(minimum[selected]), adjusted,
                                bool(terminal_active), terminal_adjusted,
                                np.nan if misses is None else float(misses[baseline]),
                                np.nan if misses is None else float(misses[selected]))
