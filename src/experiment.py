"""Reproducible toy Y-vessel plant and evaluation; all numerical defaults are toy."""

from dataclasses import asdict, dataclass
from collections import Counter
import json
from pathlib import Path
import numpy as np

from src.controller import limit_force
from src.feasibility import Material, magnetic_force_cap, schiller_naumann_factor, volume
from src.flow import (FlowDisturbance, material_acceleration, prescribed_flow, pulsatile_speed,
                      womersley_number)
from src.imaging import BiplaneImager
from src.navigation import BiplaneNavigation
from src.particle import InertialParticle, Particle
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
    # Poiseuille only: shrink dt so one step moves at most this fraction of the
    # vessel radius. 0.02 is a chosen accuracy target (assumed), not a sourced value.
    max_step_radius_fraction: float = 0.02
    # Particle inertia (reduced Maxey-Riley, see InertialParticle). Off keeps
    # the overdamped model. The particle is released at the local flow velocity.
    particle_inertia: bool = False
    particle_density_kg_m3: float = 7500.0  # sintered NdFeB (textbook, assumed)
    fluid_density_kg_m3: float = 1060.0     # whole blood (assumed)
    # Quasi-steady pulsation U(t) = U (1 + A sin(2 pi t / T)); A = 0 is steady flow.
    # PI = 2A for a sinusoid. T = 1 s is 60 bpm (assumed).
    flow_pulsatility: float = 0.0
    cardiac_period_s: float = 1.0
    cardiac_phase: float = 0.0  # release phase as a fraction of the period, in [0, 1)
    # Inertial particles only: add the (3/2) m_f Du/Dt fluid-acceleration force,
    # from the deterministic field (the random disturbance is not differentiated).
    fluid_acceleration_force: bool = False
    # Gravity on the plant: net weight (rho_p - rho_f) V g along gravity_direction.
    # 0 disables it; 9.81 m/s^2 is standard gravity. The direction in the vessel
    # frame depends on patient orientation (assumed).
    gravity_m_s2: float = 0.0
    gravity_direction: tuple = (0.0, 0.0, -1.0)
    # Diagnostic only: flag stops where Stokes settling would reach the wall within
    # the horizon. 0.1 s = one 20 Hz frame period + 50 ms latency (assumed).
    sedimentation_check: bool = False
    sedimentation_horizon_s: float = 0.1
    # Opt-in: command -W (within the cap) while tracking is valid, even when stopped.
    gravity_compensation: bool = False
    # Dead-end branch ("upper" or "lower"); requires flow_model="poiseuille". "" = both patent.
    occluded_branch: str = ""
    # Actuation update period with zero-order hold. 0 updates the command every
    # physics tick (legacy); frames that arrive between updates are queued.
    actuation_period_s: float = 0.0
    # > 0 sets the proportional gain to force_cap / distance, so the command
    # saturates at the same position error whatever the cap. 0 keeps gain_n_per_m.
    gain_saturation_distance_m: float = 0.0
    # Delay-aware control options. flow_feedforward cancels the command-aware
    # estimator's residual drift (requires estimator_mode="command_aware").
    # model_drag_error scales the controller's drag model (estimator, predictor,
    # feedforward) relative to the plant: 0.2 means the model drag is 20% high.
    flow_feedforward: bool = False
    model_drag_error: float = 0.0
    # Model-based feedforward: the controller cancels its own copy of the prescribed
    # flow (same model, occlusion and cardiac phase, assumed known) with the mean
    # speed scaled by (1 + flow_model_error). With the command-aware estimator the
    # same modeled flow is a known input, so the estimator tracks only the residual.
    # The random disturbance is never modeled.
    model_flow_feedforward: bool = False
    flow_model_error: float = 0.0
    # Further controller flow-model errors (plant unchanged): cardiac phase offset as a
    # fraction of the period, the assumed pulsation amplitude (None = same as the plant),
    # the assumed profile exponent (2 = Poiseuille, flux-equivalent), and a scale on the
    # junction transition length and branch width.
    flow_model_phase_error: float = 0.0
    flow_model_pulsatility: float = None
    flow_model_profile_exponent: float = 2.0
    flow_model_junction_scale: float = 1.0
    # With gravity_compensation: hold against the known weight from release, before
    # and without tracking (open loop). Off keeps the tracking-gated hold.
    gravity_hold_from_release: bool = False
    # Command-aware estimator integrates (command + known net weight) instead of the
    # command alone. Off reproduces experiment 23, where a held weight appears as
    # phantom commanded motion.
    estimator_knows_weight: bool = False


def particle_material(config):
    return Material(name="configured", magnetization_a_m=config.magnetization_a_m,
                    density_kg_m3=config.particle_density_kg_m3,
                    magnetic_volume_fraction=config.magnetic_volume_fraction)


def effective_max_force_n(config):
    """Force cap [N] actually enforced for this trial."""
    if config.max_gradient_t_m > 0:
        return magnetic_force_cap(config.particle_radius_m, config.max_gradient_t_m,
                                  particle_material(config))
    return config.max_force_n


def plant_flow_function(config):
    """Deterministic plant flow u(position, time): prescribed field with pulsation."""
    def flow(position_m, time_s):
        speed = pulsatile_speed(config.flow_speed_m_s, time_s + config.cardiac_phase * config.cardiac_period_s,
                                config.flow_pulsatility, config.cardiac_period_s)
        return prescribed_flow(position_m, speed, config.flow_model,
                               config.flow_transition_length_m, config.flow_branch_width_m,
                               occluded_branch=config.occluded_branch or None)
    return flow


def controller_flow_function(config):
    """The controller's own flow model, with the configured model errors (plant unchanged)."""
    model_pulsatility = (config.flow_pulsatility if config.flow_model_pulsatility is None
                         else config.flow_model_pulsatility)

    def flow(position_m, time_s):
        phase = config.cardiac_phase + config.flow_model_phase_error
        speed = pulsatile_speed(config.flow_speed_m_s * (1 + config.flow_model_error),
                                time_s + phase * config.cardiac_period_s,
                                model_pulsatility, config.cardiac_period_s)
        scale = config.flow_model_junction_scale
        return prescribed_flow(position_m, speed, config.flow_model, config.flow_transition_length_m * scale,
                               config.flow_branch_width_m * scale, occluded_branch=config.occluded_branch or None,
                               profile_exponent=config.flow_model_profile_exponent)
    return flow


def run_trial(config=TrialConfig()):
    for name in ("duration_s", "dt_s", "frame_rate_hz", "noise_sigma_px"):
        nonnegative(getattr(config, name), name, positive=True)
    for name in ("flow_speed_m_s", "flow_disturbance_m_s", "calibration_sigma_px",
                 "gain_n_per_m", "max_force_n", "flow_correlation_s", "max_gradient_t_m"):
        nonnegative(getattr(config, name), name)
    for name in ("flow_transition_length_m", "flow_branch_width_m", "particle_radius_m",
                 "max_step_radius_fraction", "particle_density_kg_m3", "fluid_density_kg_m3",
                 "cardiac_period_s"):
        nonnegative(getattr(config, name), name, positive=True)
    if not 0 <= config.cardiac_phase < 1:
        raise ValueError("cardiac_phase must be in [0, 1)")
    if not 0 <= config.flow_pulsatility <= 1:
        raise ValueError("flow_pulsatility must be in [0, 1]; flow reversal is not modeled")
    if config.fluid_acceleration_force and not config.particle_inertia:
        raise ValueError("fluid_acceleration_force requires particle_inertia")
    nonnegative(config.gravity_m_s2, "gravity_m_s2")
    nonnegative(config.sedimentation_horizon_s, "sedimentation_horizon_s", positive=True)
    gravity_axis = vector(config.gravity_direction)
    if np.linalg.norm(gravity_axis) == 0:
        raise ValueError("gravity_direction must be nonzero")
    if config.occluded_branch not in ("", "upper", "lower"):
        raise ValueError("occluded_branch must be '', 'upper' or 'lower'")
    if config.occluded_branch and config.flow_model != "poiseuille":
        raise ValueError("occluded_branch requires flow_model='poiseuille'")
    nonnegative(config.actuation_period_s, "actuation_period_s")
    if not np.isfinite(config.model_drag_error) or config.model_drag_error <= -1:
        raise ValueError("model_drag_error must be finite and > -1")
    if not np.isfinite(config.flow_model_error) or config.flow_model_error <= -1:
        raise ValueError("flow_model_error must be finite and > -1")
    if not np.isfinite(config.flow_model_phase_error):
        raise ValueError("flow_model_phase_error must be finite")
    if config.flow_model_pulsatility is not None and not 0 <= config.flow_model_pulsatility <= 1:
        raise ValueError("flow_model_pulsatility must be None or in [0, 1]")
    nonnegative(config.flow_model_profile_exponent, "flow_model_profile_exponent", positive=True)
    nonnegative(config.flow_model_junction_scale, "flow_model_junction_scale", positive=True)
    if config.estimator_knows_weight and (config.gravity_m_s2 == 0 or config.estimator_mode != "command_aware"):
        raise ValueError("estimator_knows_weight requires gravity and the command_aware estimator")
    if config.gravity_hold_from_release and not config.gravity_compensation:
        raise ValueError("gravity_hold_from_release requires gravity_compensation")
    nonnegative(config.gain_saturation_distance_m, "gain_saturation_distance_m")
    if (config.sedimentation_check or config.gravity_compensation) and config.gravity_m_s2 == 0:
        raise ValueError("sedimentation_check and gravity_compensation require gravity_m_s2 > 0")
    if config.flow_model not in ("piecewise", "smooth", "poiseuille"):
        raise ValueError("flow model must be piecewise, smooth or poiseuille")
    if not np.isfinite(config.actuation_gain_error) or config.actuation_gain_error < -1:
        raise ValueError("actuation gain error must be finite and >= -1")
    if config.dt_s > 1 / config.frame_rate_hz:
        raise ValueError("physics timestep must not exceed the imaging period")
    material = particle_material(config)
    max_force_n = effective_max_force_n(config)
    gain_n_per_m = (max_force_n / config.gain_saturation_distance_m if config.gain_saturation_distance_m > 0
                    else config.gain_n_per_m)
    # Independent streams keep sensor and flow draws reproducible when toggling noise.
    sensor_seed, calibration_seed, flow_seed = np.random.SeedSequence(config.seed).spawn(3)
    sensor_rng = np.random.default_rng(sensor_seed)
    calibration_rng = np.random.default_rng(calibration_seed)
    flow_rng = np.random.default_rng(flow_seed)
    disturbance = FlowDisturbance(config.flow_disturbance_m_s, config.flow_correlation_s, flow_rng)
    vessel = YVessel()
    deterministic_flow = plant_flow_function(config)
    controller_flow_model = controller_flow_function(config)
    model_pulsatility = (config.flow_pulsatility if config.flow_model_pulsatility is None
                         else config.flow_model_pulsatility)

    if config.particle_inertia:
        # Deterministic release velocity; no disturbance draw, so RNG streams are unchanged.
        release = deterministic_flow(vector(config.start_m), 0.0)
        particle = InertialParticle(config.particle_radius_m, 3.5e-3, config.particle_density_kg_m3,
                                    config.fluid_density_kg_m3, vector(config.start_m), release)
    else:
        particle = Particle(config.particle_radius_m, 3.5e-3, vector(config.start_m))
    if particle.radius_m >= min(s.radius_m for s in vessel.segments):
        raise ValueError("particle_radius_m must be smaller than the vessel radius")
    vessel_radius = min(s.radius_m for s in vessel.segments)
    weight = ((config.particle_density_kg_m3 - config.fluid_density_kg_m3) * volume(particle.radius_m)
              * config.gravity_m_s2 * gravity_axis / np.linalg.norm(gravity_axis))
    settling_velocity = weight / particle.drag_coefficient  # Stokes estimate given to the controller
    dt_s = config.dt_s
    if config.flow_model == "poiseuille":
        # Bound |v| by centerline flow, capped drift, a 3-sigma disturbance norm and settling.
        # White disturbance (correlation 0) is redrawn per tick, so its effect
        # shrinks with dt; use flow_correlation_s > 0 for a dt-consistent process.
        speed_bound = (2 * config.flow_speed_m_s * (1 + config.flow_pulsatility)
                       + max_force_n / particle.drag_coefficient
                       + 3 * np.sqrt(3) * config.flow_disturbance_m_s)
        if config.gravity_m_s2 > 0:
            speed_bound += np.linalg.norm(settling_velocity)
        if speed_bound > 0:
            dt_s = min(dt_s, config.max_step_radius_fraction * vessel_radius / speed_bound)
    bias = calibration_rng.normal(0, config.calibration_sigma_px, (2, 2))
    imager = BiplaneImager(noise_sigma_px=config.noise_sigma_px,
        frame_rate_hz=config.frame_rate_hz, latency_s=config.latency_s,
        dropout_probability=config.dropout_probability,
        dropout_intervals=config.dropout_intervals, calibration_bias_px=bias, rng=sensor_rng)
    navigation = BiplaneNavigation(vessel, particle.radius_m, branch=config.branch,
        noise_sigma_px=config.noise_sigma_px, calibration_sigma_px=config.calibration_sigma_px,
        gain_n_per_m=gain_n_per_m, max_force_n=max_force_n,
        max_measurement_age_s=config.max_measurement_age_s,
        max_sigma_m=config.max_sigma_m, safety_margin_m=config.safety_margin_m,
        control_mode=config.control_mode, approach_offset_m=config.approach_offset_m,
        prediction_horizon_s=config.prediction_horizon_s, estimator_mode=config.estimator_mode,
        terminal_guidance_distance_m=config.terminal_guidance_distance_m,
        settling_velocity_m_s=settling_velocity if config.sedimentation_check else None,
        sedimentation_horizon_s=config.sedimentation_horizon_s,
        gravity_compensation_n=-weight if config.gravity_compensation else None,
        flow_feedforward=config.flow_feedforward,
        model_viscosity_pa_s=3.5e-3 * (1 + config.model_drag_error),
        flow_model=controller_flow_model if config.model_flow_feedforward else None,
        hold_without_tracking=config.gravity_hold_from_release,
        known_weight_n=weight if config.estimator_knows_weight else None)
    target = vessel.upper_target if config.branch == "upper" else vessel.lower_target
    history = {k: [] for k in ("time_s", "true_position_m", "estimated_position_m",
        "sigma_m", "true_clearance_m", "estimated_clearance_m", "robust_clearance_m",
        "force_n", "command_force_n", "reason", "measurement_age_s",
        "waypoint_index", "waypoint_m", "flow_velocity_m_s",
        "predicted_nominal_clearance_m", "predicted_selected_clearance_m", "prediction_adjusted",
        "estimated_velocity_m_s", "terminal_active", "terminal_adjusted",
        "baseline_target_miss_m", "selected_target_miss_m")}
    reached = collided = wrong = False
    particle_velocities = []
    sedimentation = {"sedimentation_margin_m": [], "sedimentation_risk": []}
    peak_fluid_acceleration = 0.0
    output, queued_frames, next_update_s, last_update_s = None, [], 0.0, 0.0
    ticks = int(np.ceil(config.duration_s / dt_s))
    for tick in range(ticks + 1):
        now = min(tick * dt_s, config.duration_s)
        # The sensor is part of the simulated plant. Only delivered frames cross
        # the control boundary. Ground truth below is physics/evaluation only.
        frames = imager.advance(now, particle.position_m)
        if config.actuation_period_s > 0:
            queued_frames.extend(frames)
            if output is None or now >= next_update_s - 1e-12:
                output, last_update_s = navigation.step(now, queued_frames), now
                queued_frames = []
                while next_update_s <= now + 1e-12:
                    next_update_s += config.actuation_period_s
        else:
            output, last_update_s = navigation.step(now, frames), now
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
            flow = deterministic_flow(particle.position_m, now)
            if config.fluid_acceleration_force:
                fluid_acceleration = material_acceleration(deterministic_flow, particle.position_m, now)
                peak_fluid_acceleration = max(peak_fluid_acceleration, float(np.linalg.norm(fluid_acceleration)))
            flow += disturbance.sample(now)
        estimate = output.estimate
        values = (now, particle.position_m.copy(),
            np.full(3, np.nan) if estimate is None else estimate.estimated_position,
            np.nan if estimate is None else estimate.position_uncertainty,
            true_clearance, output.estimated_clearance_m, output.robust_clearance_m,
            # Under a hold, age keeps growing so capture = time - age stays exact.
            applied, output.force_n, output.reason, output.measurement_age_s + (now - last_update_s),
            navigation.planner.index, navigation.planner.waypoints[navigation.planner.index].copy(), flow,
            output.predicted_nominal_clearance_m, output.predicted_selected_clearance_m, output.prediction_adjusted,
            np.full(3, np.nan) if estimate is None else estimate.estimated_velocity,
            output.terminal_active, output.terminal_adjusted,
            output.baseline_target_miss_m, output.selected_target_miss_m)
        for key, value in zip(history, values):
            history[key].append(value)
        if config.particle_inertia:
            particle_velocities.append(particle.velocity_m_s.copy())
        if config.sedimentation_check:
            sedimentation["sedimentation_margin_m"].append(output.sedimentation_margin_m)
            sedimentation["sedimentation_risk"].append(output.sedimentation_risk)
        if finished:
            break
        plant_force = applied + weight if config.gravity_m_s2 > 0 else applied
        if config.fluid_acceleration_force:
            particle.step(min(dt_s, config.duration_s - now), flow, plant_force, fluid_acceleration)
        else:
            particle.step(min(dt_s, config.duration_s - now), flow, plant_force)
    history = {k: np.asarray(v) for k, v in history.items()}
    if config.particle_inertia:
        history["particle_velocity_m_s"] = np.asarray(particle_velocities)
    if config.sedimentation_check:
        history.update({k: np.asarray(v) for k, v in sedimentation.items()})
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
    # Present only when a physics option is enabled so archived summaries keep their keys.
    physics = {}
    if config.max_gradient_t_m > 0:
        force_per_gradient = magnetic_force_cap(particle.radius_m, 1.0, material)
        physics.update({
            "force_cap_n": float(max_force_n),
            "max_gradient_t_m": float(config.max_gradient_t_m),
            "maximum_gradient_t_m": summary["maximum_force_n"] / force_per_gradient,
        })
    if config.flow_model == "poiseuille":
        steps = np.linalg.norm(np.diff(history["true_position_m"], axis=0), axis=1)
        physics.update({
            "dt_s": float(dt_s),
            "maximum_step_radius_fraction": float(steps.max() / vessel_radius) if len(steps) else None,
        })
    if config.particle_inertia:
        slip = np.linalg.norm(history["particle_velocity_m_s"][:-1] - history["flow_velocity_m_s"][:-1], axis=1)
        reynolds = config.fluid_density_kg_m3 * 2 * particle.radius_m * slip / particle.viscosity_pa_s
        parent = vessel.segments[0]
        # St = tau U / L as in docs/14, with L the parent-segment length.
        physics.update({
            "relaxation_time_s": particle.relaxation_time_s,
            "stokes_number": particle.relaxation_time_s * config.flow_speed_m_s
                             / float(np.linalg.norm(parent.end_m - parent.start_m)),
            "maximum_slip_m_s": float(slip.max()) if len(slip) else None,
            "maximum_slip_reynolds": float(reynolds.max()) if len(slip) else None,
            "maximum_drag_factor": schiller_naumann_factor(reynolds.max()) if len(slip) else None,
        })
    if config.flow_pulsatility > 0:
        physics["womersley_number"] = float(womersley_number(
            vessel_radius, config.cardiac_period_s, particle.viscosity_pa_s, config.fluid_density_kg_m3))
    if config.fluid_acceleration_force:
        physics["maximum_fluid_acceleration_m_s2"] = peak_fluid_acceleration
    if config.gravity_m_s2 > 0:
        net_weight = float(np.linalg.norm(weight))
        physics.update({
            "net_weight_n": net_weight,
            "stokes_settling_speed_m_s": net_weight / particle.drag_coefficient,
            "gravity_hold_gradient_t_m": net_weight / magnetic_force_cap(particle.radius_m, 1.0, material),
            "can_hold_against_gravity": bool(max_force_n >= net_weight),
        })
    if config.sedimentation_check:
        risk = history["sedimentation_risk"]
        physics.update({
            "sedimentation_risk_fraction": float(risk.mean()),
            "first_sedimentation_risk_s": float(history["time_s"][risk][0]) if risk.any() else None,
        })
    if config.gain_saturation_distance_m > 0:
        physics["gain_n_per_m"] = float(gain_n_per_m)
    if config.actuation_period_s > 0:
        physics["actuation_period_s"] = float(config.actuation_period_s)
    if config.occluded_branch:
        physics["occluded_branch"] = config.occluded_branch
    if config.model_drag_error:
        physics["model_drag_error"] = float(config.model_drag_error)
    if config.model_flow_feedforward:
        physics["flow_model_error"] = float(config.flow_model_error)
        physics["flow_model_errors"] = {
            "phase": float(config.flow_model_phase_error), "pulsatility": float(model_pulsatility),
            "profile_exponent": float(config.flow_model_profile_exponent),
            "junction_scale": float(config.flow_model_junction_scale)}
    if physics:
        # Continuous companion to the binary target-success flag (0.4 mm tolerance).
        physics["closest_target_approach_m"] = float(np.min(np.linalg.norm(
            history["true_position_m"] - target, axis=1)))
        summary["physics"] = physics
    return {"config": asdict(config), "summary": summary, "history": history}


def save_trial(result, output_dir):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(json.dumps(
        {"config": result["config"], "summary": result["summary"]}, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(path / "history.npz", **result["history"])
    from src.plotting import plot_trial
    plot_trial(result, path / "diagnostics.png")
