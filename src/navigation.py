"""Feedback boundary: time and image observations in; bounded force out.

No particle/plant reference, true position, true velocity, or true flow enters
this module. Geometry and robot radius are configured model information.
"""

from dataclasses import dataclass
import numpy as np

from src.controller import bounded_target_force
from src.localization import BiplaneTriangulator, DelayedStateEstimator
from src.planner import YWaypointPlanner
from src.prediction import ShortHorizonCorrection
from src.safety import SafetySupervisor
from src.validation import nonnegative


@dataclass(frozen=True)
class ControlOutput:
    force_n: np.ndarray
    estimate: object
    reason: str
    estimated_clearance_m: float
    robust_clearance_m: float
    measurement_age_s: float
    actuation_limited: bool  # Nominal waypoint request exceeded the force cap.
    predicted_nominal_clearance_m: float = np.nan
    predicted_selected_clearance_m: float = np.nan
    prediction_adjusted: bool = False


class BiplaneNavigation:
    def __init__(self, vessel, particle_radius_m, branch="upper", views=None,
                 noise_sigma_px=1.0, calibration_sigma_px=0.25,
                 gain_n_per_m=2e-6, max_force_n=3e-9,
                 max_measurement_age_s=0.15, max_sigma_m=0.35e-3,
                 safety_margin_m=0.20e-3, acceleration_spectral_density=1e-7,
                 control_mode="gated", approach_offset_m=0.0,
                 prediction_horizon_s=0.0, model_viscosity_pa_s=3.5e-3):
        if control_mode not in ("passive", "ungated", "gated"):
            raise ValueError("control_mode must be passive, ungated, or gated")
        self.control_mode = control_mode
        self.vessel = vessel
        self.particle_radius_m = particle_radius_m
        self.triangulator = BiplaneTriangulator(views, noise_sigma_px, calibration_sigma_px)
        self.estimator = DelayedStateEstimator(
            acceleration_spectral_density=acceleration_spectral_density)
        self.planner = YWaypointPlanner(vessel, branch, approach_offset_m=approach_offset_m)
        self.supervisor = SafetySupervisor(max_sigma_m, safety_margin_m,
            max_measurement_age_s=max_measurement_age_s, max_force_n=max_force_n)
        self.gain = gain_n_per_m
        self.max_force_n = max_force_n
        nonnegative(prediction_horizon_s, "prediction_horizon_s")
        nonnegative(model_viscosity_pa_s, "model_viscosity_pa_s", positive=True)
        if prediction_horizon_s > 0 and control_mode != "gated":
            raise ValueError("prediction requires gated control")
        self.predictor = ShortHorizonCorrection(vessel, particle_radius_m, branch,
            prediction_horizon_s, 6 * np.pi * model_viscosity_pa_s * particle_radius_m,
            max_force_n, safety_margin_m, self.supervisor.k_sigma,
            acceleration_spectral_density) if prediction_horizon_s > 0 else None
        self.previous_force_n = np.zeros(3)
        self.tracking_valid = False
        self.last_frame_s = -np.inf
        self.last_step_s = -np.inf

    def step(self, now_s, frames):
        if not np.isfinite(now_s) or now_s < 0 or now_s <= self.last_step_s:
            raise ValueError("control time must increase strictly")
        self.last_step_s = now_s
        for frame in frames:
            if (not np.isfinite(frame.captured_at_s) or
                    not np.isfinite(frame.available_at_s) or
                    frame.captured_at_s < 0 or
                    frame.available_at_s < frame.captured_at_s or
                    frame.available_at_s > now_s + 1e-12):
                raise ValueError("invalid or not-yet-delivered frame")
            if frame.captured_at_s <= self.last_frame_s:
                continue  # never let stale/duplicate frames re-enable tracking
            self.last_frame_s = frame.captured_at_s
            self.tracking_valid = frame.detector_px is not None
            if self.tracking_valid:
                try:
                    reconstruction = self.triangulator.reconstruct(frame.detector_px)
                except ValueError:
                    self.tracking_valid = False
                else:
                    self.estimator.observe(reconstruction, frame.captured_at_s, now_s)
        estimate = self.estimator.estimate(now_s)
        if estimate is None:
            self.previous_force_n = np.zeros(3)
            reason = "passive" if self.control_mode == "passive" else "tracking_lost"
            return ControlOutput(np.zeros(3), None, reason, np.nan, np.nan, np.inf, False)
        age = now_s - self.estimator.last_capture_s
        allowed, reason, _ = self.supervisor.evaluate(
            estimate.estimated_position, estimate.position_uncertainty,
            self.vessel, self.particle_radius_m, self.tracking_valid, age)
        clearance = self.vessel.clearance(estimate.estimated_position, self.particle_radius_m)
        robust = clearance - self.supervisor.k_sigma * estimate.position_uncertainty
        # Benchmark ablations keep the same observations, estimator and force cap.
        # Ungated control requires an initial estimate, then ignores the gate.
        if self.control_mode == "passive":
            allowed, reason = False, "passive"
        elif self.control_mode == "ungated":
            allowed, reason = True, "ungated"
        force = np.zeros(3)
        limited = False
        prediction = None
        if allowed:
            target = self.planner.target(estimate.estimated_position)
            limited = np.linalg.norm(self.gain * (target - estimate.estimated_position)) > self.max_force_n
            force = bounded_target_force(estimate.estimated_position, target, self.gain, self.max_force_n)
            if limited:
                reason = "actuation_limit"
            if self.predictor is not None:
                prediction = self.predictor.select(estimate, force, self.previous_force_n)
                force = prediction.force_n
                if prediction.adjusted:
                    reason = "prediction_adjustment"
        self.previous_force_n = self.supervisor.filter_force(force, allowed)
        return ControlOutput(self.previous_force_n.copy(), estimate,
                             reason, clearance, robust, age, limited,
                             np.nan if prediction is None else prediction.nominal_clearance_m,
                             np.nan if prediction is None else prediction.selected_clearance_m,
                             prediction is not None and prediction.adjusted)
