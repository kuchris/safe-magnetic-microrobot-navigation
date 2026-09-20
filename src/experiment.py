"""Reproducible toy Y-vessel plant and evaluation; all numerical defaults are toy."""

from dataclasses import asdict, dataclass
from collections import Counter
import json
from pathlib import Path
import numpy as np

from src.controller import limit_force
from src.flow import centerline_flow
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


def run_trial(config=TrialConfig()):
    for name in ("duration_s", "dt_s", "frame_rate_hz", "noise_sigma_px"):
        nonnegative(getattr(config, name), name, positive=True)
    for name in ("flow_speed_m_s", "flow_disturbance_m_s", "calibration_sigma_px",
                 "gain_n_per_m", "max_force_n"):
        nonnegative(getattr(config, name), name)
    if not np.isfinite(config.actuation_gain_error) or config.actuation_gain_error < -1:
        raise ValueError("actuation gain error must be finite and >= -1")
    if config.dt_s > 1 / config.frame_rate_hz:
        raise ValueError("physics timestep must not exceed the imaging period")
    # Independent streams keep sensor and flow draws reproducible when toggling noise.
    sensor_seed, calibration_seed, flow_seed = np.random.SeedSequence(config.seed).spawn(3)
    sensor_rng = np.random.default_rng(sensor_seed)
    calibration_rng = np.random.default_rng(calibration_seed)
    flow_rng = np.random.default_rng(flow_seed)
    vessel = YVessel()
    particle = Particle(0.1e-3, 3.5e-3, vector(config.start_m))
    bias = calibration_rng.normal(0, config.calibration_sigma_px, (2, 2))
    imager = BiplaneImager(noise_sigma_px=config.noise_sigma_px,
        frame_rate_hz=config.frame_rate_hz, latency_s=config.latency_s,
        dropout_probability=config.dropout_probability,
        dropout_intervals=config.dropout_intervals, calibration_bias_px=bias, rng=sensor_rng)
    navigation = BiplaneNavigation(vessel, particle.radius_m, branch=config.branch,
        noise_sigma_px=config.noise_sigma_px, calibration_sigma_px=config.calibration_sigma_px,
        gain_n_per_m=config.gain_n_per_m, max_force_n=config.max_force_n,
        max_measurement_age_s=config.max_measurement_age_s,
        max_sigma_m=config.max_sigma_m, safety_margin_m=config.safety_margin_m,
        control_mode=config.control_mode, approach_offset_m=config.approach_offset_m)
    target = vessel.upper_target if config.branch == "upper" else vessel.lower_target
    history = {k: [] for k in ("time_s", "true_position_m", "estimated_position_m",
        "sigma_m", "true_clearance_m", "estimated_clearance_m", "robust_clearance_m",
        "force_n", "command_force_n", "reason", "measurement_age_s",
        "waypoint_index", "waypoint_m")}
    reached = collided = wrong = False
    ticks = int(np.ceil(config.duration_s / config.dt_s))
    for tick in range(ticks + 1):
        now = min(tick * config.dt_s, config.duration_s)
        # The sensor is part of the simulated plant. Only delivered frames cross
        # the control boundary. Ground truth below is physics/evaluation only.
        frames = imager.advance(now, particle.position_m)
        output = navigation.step(now, frames)
        applied = limit_force(output.force_n * (1 + config.actuation_gain_error), config.max_force_n)
        true_clearance = vessel.clearance(particle.position_m, particle.radius_m)
        collided |= true_clearance <= 0
        wrong |= wrong_branch(particle.position_m, vessel, config.branch)
        reached = np.linalg.norm(particle.position_m - target) <= 0.4e-3 and not collided and not wrong
        estimate = output.estimate
        values = (now, particle.position_m.copy(),
            np.full(3, np.nan) if estimate is None else estimate.estimated_position,
            np.nan if estimate is None else estimate.position_uncertainty,
            true_clearance, output.estimated_clearance_m, output.robust_clearance_m,
            applied, output.force_n, output.reason, output.measurement_age_s,
            navigation.planner.index, navigation.planner.waypoints[navigation.planner.index].copy())
        for key, value in zip(history, values):
            history[key].append(value)
        if reached or collided or now >= config.duration_s:
            break
        # Piecewise synthetic flow; disturbance is independent per physics tick.
        flow = centerline_flow(particle.position_m, speed_m_s=config.flow_speed_m_s)
        flow += flow_rng.normal(0, config.flow_disturbance_m_s, 3)
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
    return {"config": asdict(config), "summary": summary, "history": history}


def save_trial(result, output_dir):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(json.dumps(
        {"config": result["config"], "summary": result["summary"]}, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(path / "history.npz", **result["history"])
    from src.plotting import plot_trial
    plot_trial(result, path / "diagnostics.png")
