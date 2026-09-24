"""Experiment 22: factorial sweep at physiological scale (Step 2f). Simulation only.

Every cell starts from presets.physiological_config and changes one factor per
axis. Policies share seeds, imaging and physics; only the control policy
differs. Results are conditional on this toy geometry and these assumptions;
they are not device performance or clinical evidence.
"""

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from itertools import product

import numpy as np

from src.benchmark import wilson_interval
from src.experiment import run_trial
from src.failure_analysis import wall_feature
from src.plotting import frame_timeline
from src.presets import physiological_config
from src.vessel import YVessel

FLOW_REDUCTIONS = (0.0, 0.9, 0.99)
FRAME_RATES_HZ = (7.5, 15.0, 30.0)          # fluoroscopy range, assumed
MATERIALS = ("ndfeb", "composite")
OCCLUSIONS = ("patent", "target_occluded")
POLICIES = ("passive", "gated_toy_gain", "gated_delay_gain", "gated_delay_gain_hold")
BRANCHES = ("upper", "lower")
# Time limits: about 1.5x the ~21 mm centerline transit at each flow (3.5 s at 99%).
DURATION_S = {0.0: 0.25, 0.9: 1.0, 0.99: 5.0}
# Delay-limited gain: k / gamma = beta / (latency + frame period). beta = 0.5 is assumed.
DELAY_GAIN_FRACTION = 0.5
UNREDUCED_SPEED_M_S = 0.30
OUTCOMES = ("target_success", "wall_collision", "wrong_branch", "timeout")


def delay_limited_gain(config):
    """Proportional gain [N/m] whose closed-loop rate is a fraction of 1 / (latency + frame period)."""
    drag = 6 * np.pi * 3.5e-3 * config.particle_radius_m
    return DELAY_GAIN_FRACTION * drag / (config.latency_s + 1 / config.frame_rate_hz)


def cell_config(flow_reduction, frame_rate_hz, material, occlusion, policy, branch, seed):
    if policy not in POLICIES or occlusion not in OCCLUSIONS:
        raise ValueError("unknown policy or occlusion")
    config = physiological_config(
        material, flow_speed_m_s=UNREDUCED_SPEED_M_S * (1 - flow_reduction), frame_rate_hz=frame_rate_hz,
        branch=branch, seed=seed, duration_s=DURATION_S[flow_reduction],
        occluded_branch=branch if occlusion == "target_occluded" else "",
        control_mode="passive" if policy == "passive" else "gated",
        gravity_compensation=policy == "gated_delay_gain_hold")
    if policy in ("gated_delay_gain", "gated_delay_gain_hold"):
        config = replace(config, gain_saturation_distance_m=0.0, gain_n_per_m=delay_limited_gain(config))
    return config


def all_cells(seeds=(0, 1, 2)):
    return [dict(flow_reduction=f, frame_rate_hz=fps, material=m, occlusion=o, policy=p, branch=b, seed=s)
            for f, fps, m, o, p, b, s in product(FLOW_REDUCTIONS, FRAME_RATES_HZ, MATERIALS, OCCLUSIONS,
                                                 POLICIES, BRANCHES, seeds)]


def trial_record(cell):
    """Run one cell and keep scalar metrics only (histories are dropped)."""
    config = cell_config(**cell)
    result = run_trial(config)
    s, physics = result["summary"], result["summary"]["physics"]
    frames = frame_timeline(result)
    timeout = not (s["target_success"] or s["wall_collision"] or s["wrong_branch"])
    return {
        **cell,
        "config": asdict(config),
        "target_success": s["target_success"], "wall_collision": s["wall_collision"],
        "wrong_branch": s["wrong_branch"], "timeout": timeout,
        "elapsed_time_s": s["elapsed_time_s"],
        "closest_target_approach_m": physics["closest_target_approach_m"],
        "frames_used": int(len(frames["delivered_at_s"])),
        "first_frame_used_s": float(frames["delivered_at_s"][0]) if len(frames["delivered_at_s"]) else None,
        "peak_force_fraction": s["maximum_force_n"] / physics["force_cap_n"],
        "gain_n_per_m": physics.get("gain_n_per_m", config.gain_n_per_m),
        "can_hold_against_gravity": physics["can_hold_against_gravity"],
        "sedimentation_risk_fraction": physics["sedimentation_risk_fraction"],
        "stokes_number": physics["stokes_number"],
        "maximum_slip_reynolds": physics["maximum_slip_reynolds"],
        "terminal_wall_feature": wall_feature(result["history"]["true_position_m"][-1], YVessel(),
                                              config.particle_radius_m),
        "reason_counts": s["reason_counts"],
    }


def run_sweep(cells, workers=None, progress=None):
    records = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for record in pool.map(trial_record, cells, chunksize=4):
            records.append(record)
            if progress is not None:
                progress(len(records), len(cells))
    return records


GROUP = ("flow_reduction", "frame_rate_hz", "material", "occlusion", "policy")


def aggregate(records):
    groups = defaultdict(list)
    for record in records:
        groups[tuple(record[k] for k in GROUP)].append(record)
    rows = []
    for key, trials in sorted(groups.items()):
        n = len(trials)
        closest = np.array([t["closest_target_approach_m"] for t in trials])
        outcomes = {}
        for name in OUTCOMES:
            count = sum(bool(t[name]) for t in trials)
            outcomes[name] = {"count": count, "rate": count / n, "wilson_95": wilson_interval(count, n)}
        rows.append({
            **dict(zip(GROUP, key)), "trials": n, "outcomes": outcomes,
            "closest_target_approach_m": {"median": float(np.median(closest)), "min": float(closest.min())},
            "any_frame_used_fraction": float(np.mean([t["frames_used"] > 0 for t in trials])),
            "median_peak_force_fraction": float(np.median([t["peak_force_fraction"] for t in trials])),
            "median_elapsed_time_s": float(np.median([t["elapsed_time_s"] for t in trials])),
            "terminal_features": dict(Counter(t["terminal_wall_feature"] for t in trials)),
        })
    return rows


def render_report(rows, seeds):
    lines = ["# Physiological-scale sweep (experiment 22)", "",
             "Simulation only. Every cell uses `presets.physiological_config` and changes one value per",
             "factor. Rates are per trial over both target branches and seeds "
             f"{', '.join(map(str, seeds))}; brackets are 95% Wilson intervals. "
             "Closest approach is the continuous distance to the target (success needs <= 0.4 mm).", "",
             "| Flow cut | fps | Material | Target | Policy | N | Success % [95% CI] | Wall % | Wrong % | "
             "Timeout % | Closest mm (median / min) | Any frame used % | Peak force / cap (median) |",
             "|---:|---:|---|---|---|---:|---|---:|---:|---:|---|---:|---:|"]
    for r in rows:
        o = r["outcomes"]
        low, high = o["target_success"]["wilson_95"]
        lines.append(
            f"| {r['flow_reduction'] * 100:g}% | {r['frame_rate_hz']:g} | {r['material']} | {r['occlusion']} | "
            f"{r['policy']} | {r['trials']} | {o['target_success']['rate'] * 100:.0f} "
            f"[{low * 100:.0f}, {high * 100:.0f}] | {o['wall_collision']['rate'] * 100:.0f} | "
            f"{o['wrong_branch']['rate'] * 100:.0f} | {o['timeout']['rate'] * 100:.0f} | "
            f"{r['closest_target_approach_m']['median'] * 1e3:.2f} / {r['closest_target_approach_m']['min'] * 1e3:.2f} | "
            f"{r['any_frame_used_fraction'] * 100:.0f} | {r['median_peak_force_fraction']:.2f} |")
    return "\n".join(lines) + "\n"
