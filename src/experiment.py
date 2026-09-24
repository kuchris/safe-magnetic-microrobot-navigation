"""Reproducible toy Y-vessel plant and evaluation; all numerical defaults are toy."""

from dataclasses import asdict, dataclass
from collections import Counter
import json
from pathlib import Path
import numpy as np

from src.controller import limit_force
from src.feasibility import Material, magnetic_force_cap
from src.flow import FlowDisturbance, prescribed_flow
from src.imaging import BiplaneImager
from src.navigation import BiplaneNavigation
from src.particle import Particle
from src.planner import wrong_branch
from src.validation import nonnegative, vector
from src.vessel import YVessel


@dataclass(frozen=True)
class TrialConfig:
    seed: int = 7
    duration_s: float = 40.0
    dt_s: float = 0.005
    frame_rate_hz: float = 20.0
    latency_s: float = 0.05
    noise_sigma_px: float = 1.0
    calibration_sigma_px: float = 0.25
    dropout_probability: float = 0.0
    dropout_intervals: tuple = ()
    max_measurement_age_s: float = 0.15
    max_sigma_m: float = 0.35e-3
    safety_margin_m: float = 0.2e-3
    flow_speed_m_s: float = 0.6e-3
    flow_disturbance_m_s: float = 0.0
    actuation_gain_error: float = 0.0
    gain_n_per_m: float = 2e-6
    max_force_n: float = 3e-9
    start_m: tuple = (0.5e-3, 0.0, 0.0)
    branch: str = "upper"
    control_mode: str = "gated"
    approach_offset_m: float = 0.0
    flow_model: str = "piecewise"
    flow_transition_length_m: float = 1e-3
    flow_branch_width_m: float = 0.3e-3
    flow_correlation_s: float = 0.0
    prediction_horizon_s: float = 0.0
    estimator_mode: str = "kinematic"
    terminal_guidance_distance_m: float = 0.0
    particle_radius_m: float = 0.1e-3
    # Gradient cap [T/m]. Zero keeps the legacy max_force_n cap; positive values
    # replace it with V * M_eff * |grad B| from the material below.
    max_gradient_t_m: float = 0.0
    magnetization_a_m: float = 1.0e6       # NdFeB, Br ~ 1.26 T (textbook, assumed)
    magnetic_volume_fraction: float = 1.0  # pure magnet (assumed)


def particle_material(config):
    return Material(name="configured", magnetization_a_m=config.magnetization_a_m,
                    magnetic_volume_fraction=config.magnetic_volume_fraction)


def effective_max_force_n(config):
    """Force cap [N] actually enforced for this trial."""
    if config.max_gradient_t_m > 0:
        return magnetic_force_cap(config.particle_radius_m, config.max_gradient_t_m,
                                  particle_material(config))
    return config.max_force_n


def run_trial(config=TrialConfig()):
    for name in ("duration_s", "dt_s", "frame_rate_hz", "noise_sigma_px"):
        nonnegative(getattr(config, name), name, positive=True)
    for name in ("flow_speed_m_s", "flow_disturbance_m_s", "calibration_sigma_px",
                 "gain_n_per_m", "max_force_n", "flow_correlation_s", "max_gradient_t_m"):
        nonnegative(getattr(config, name), name)
    for name in ("flow_transition_length_m", "flow_branch_width_m", "particle_radius_m"):
        nonnegative(getattr(config, name), name, positive=True)
    if config.flow_model not in ("piecewise", "smooth"):
        raise ValueError("flow model must be piecewise or smooth")
    if not np.isfinite(config.actuation_gain_error) or config.actuation_gain_error < -1:
        raise ValueError("actuation gain error must be finite and >= -1")
    if config.dt_s > 1 / config.frame_rate_hz:
        raise ValueError("physics timestep must not exceed the imaging period")
    material = particle_material(config)
    max_force_n = effective_max_force_n(config)
    # Independent streams keep sensor and flow draws reproducible when toggling noise.
    sensor_seed, calibration_seed, flow_seed = np.random.SeedSequence(config.seed).spawn(3)
    sensor_rng = np.random.default_rng(sensor_seed)
    calibration_rng = np.random.default_rng(calibration_seed)
    flow_rng = np.random.default_rng(flow_seed)
    disturbance = FlowDisturbance(config.flow_disturbance_m_s, config.flow_correlation_s, flow_rng)
    vessel = YVessel()
    particle = Particle(config.particle_radius_m, 3.5e-3, vector(config.start_m))
    if particle.radius_m >= min(s.radius_m for s in vessel.segments):
        raise ValueError("particle_radius_m must be smaller than the vessel radius")
    bias = calibration_rng.normal(0, config.calibration_sigma_px, (2, 2))
    imager = BiplaneImager(noise_sigma_px=config.noise_sigma_px,
        frame_rate_hz=config.frame_rate_hz, latency_s=config.latency_s,
        dropout_probability=config.dropout_probability,
        dropout_intervals=config.dropout_intervals, calibration_bias_px=bias, rng=sensor_rng)
    navigation = BiplaneNavigation(vessel, particle.radius_m, branch=config.branch,
        noise_sigma_px=config.noise_sigma_px, calibration_sigma_px=config.calibration_sigma_px,
        gain_n_per_m=config.gain_n_per_m, max_force_n=max_force_n,
        max_measurement_age_s=config.max_measurement_age_s,
        max_sigma_m=config.max_sigma_m, safety_margin_m=config.safety_margin_m,
        control_mode=config.control_mode, approach_offset_m=config.approach_offset_m,
        prediction_horizon_s=config.prediction_horizon_s, estimator_mode=config.estimator_mode,
        terminal_guidance_distance_m=config.terminal_guidance_distance_m)
    target = vessel.upper_target if config.branch == "upper" else vessel.lower_target
    history = {k: [] for k in ("time_s", "true_position_m", "estimated_position_m",
        "sigma_m", "true_clearance_m", "estimated_clearance_m", "robust_clearance_m",
        "force_n", "command_force_n", "reason", "measurement_age_s",
        "waypoint_index", "waypoint_m", "flow_velocity_m_s",
        "predicted_nominal_clearance_m", "predicted_selected_clearance_m", "prediction_adjusted",
        "estimated_velocity_m_s", "terminal_active", "terminal_adjusted",
        "baseline_target_miss_m", "selected_target_miss_m")}
    reached = collided = wrong = False
    ticks = int(np.ceil(config.duration_s / config.dt_s))
    for tick in range(ticks + 1):
        now = min(tick * config.dt_s, config.duration_s)
        # The sensor is part of the simulated plant. Only delivered frames cross
        # the control boundary. Ground truth below is physics/evaluation only.
        frames = imager.advance(now, particle.position_m)
        output = navigation.step(now, frames)
        applied = limit_force(output.force_n * (1 + config.actuation_gain_error), max_force_n)
        true_clearance = vessel.clearance(particle.position_m, particle.radius_m)
        collided |= true_clearance <= 0
        wrong |= wrong_branch(particle.position_m, vessel, config.branch)
        reached = np.linalg.norm(particle.position_m - target) <= 0.4e-3 and not collided and not wrong
        finished = reached or collided or now >= config.duration_s
        # Log the actual velocity used over the next integration interval.
        # The terminal sample has no next interval and therefore records NaN.
        flow = np.full(3, np.nan)
        if not finished:
            flow = prescribed_flow(particle.position_m, config.flow_speed_m_s,
                config.flow_model, config.flow_transition_length_m, config.flow_branch_width_m)
            flow += disturbance.sample(now)
        estimate = output.estimate
        values = (now, particle.position_m.copy(),
            np.full(3, np.nan) if estimate is None else estimate.estimated_position,
            np.nan if estimate is None else estimate.position_uncertainty,
            true_clearance, output.estimated_clearance_m, output.robust_clearance_m,
            applied, output.force_n, output.reason, output.measurement_age_s,
            navigation.planner.index, navigation.planner.waypoints[navigation.planner.index].copy(), flow,
            output.predicted_nominal_clearance_m, output.predicted_selected_clearance_m, output.prediction_adjusted,
            np.full(3, np.nan) if estimate is None else estimate.estimated_velocity,
            output.terminal_active, output.terminal_adjusted,
            output.baseline_target_miss_m, output.selected_target_miss_m)
        for key, value in zip(history, values):
            history[key].append(value)
        if finished:
            break
        particle.step(min(config.dt_s, config.duration_s - now), flow, applied)
    history = {k: np.asarray(v) for k, v in history.items()}
    valid = np.all(np.isfinite(history["estimated_position_m"]), axis=1)
    errors = history["true_position_m"][valid] - history["estimated_position_m"][valid]
    reasons = Counter(history["reason"].tolist())
    stopped = np.isin(history["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    summary = {
        "seed": config.seed, "target_success": bool(reached), "wall_collision": bool(collided),
        "wrong_branch": bool(wrong),
        "minimum_wall_clearance_m": float(history["true_clearance_m"].min()),
        "navigation_time_s": float(history["time_s"][-1]) if reached else None,
        "elapsed_time_s": float(history["time_s"][-1]),
        "safety_stop_rate": float(stopped.mean()),
        "safety_stop_events": int(np.count_nonzero(stopped & ~np.r_[False, stopped[:-1]])),
        "localization_RMSE_m": float(np.sqrt(np.mean(np.sum(errors**2, axis=1)))) if len(errors) else None,
        "localized_sample_count": int(valid.sum()), "sample_count": len(valid),
        # Descriptive coverage of a largest-axis 3-sigma ball, not a calibrated
        # 3D confidence ellipsoid or a collision-probability guarantee.
        "position_3sigma_coverage": float(np.mean(
            np.linalg.norm(errors, axis=1) <= 3 * history["sigma_m"][valid])) if len(errors) else None,
        "localization_availability": float(valid.mean()),
        "maximum_force_n": float(np.linalg.norm(history["force_n"], axis=1).max()),
        "reason_counts": dict(reasons),
    }
    if config.max_gradient_t_m > 0:
        # Present only for gradient-capped trials so archived summaries keep their keys.
        force_per_gradient = magnetic_force_cap(particle.radius_m, 1.0, material)
        summary["physics"] = {
            "force_cap_n": float(max_force_n),
            "max_gradient_t_m": float(config.max_gradient_t_m),
            "maximum_gradient_t_m": summary["maximum_force_n"] / force_per_gradient,
        }
    return {"config": asdict(config), "summary": summary, "history": history}


def save_trial(result, output_dir):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(json.dumps(
        {"config": result["config"], "summary": result["summary"]}, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(path / "history.npz", **result["history"])
    from src.plotting import plot_trial
    plot_trial(result, path / "diagnostics.png")
