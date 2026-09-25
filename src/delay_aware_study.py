"""Experiment 23: delay-aware control at physiological scale. Simulation only.

Every policy uses the composite particle and a gravity hold (pure NdFeB settles
before the first frame in experiment 22). P0 is the experiment 22 policy that
succeeded; P1-P5 add a command-aware (Smith-predictor-like) estimator, a gain
limited by the actuation period instead of the observation delay, estimated
flow feedforward and the short-horizon wall prediction. The controller's drag
model can be mis-scaled with model_drag_error. Seeds 0-2 are the pilot and
seeds 3-5 are held out.
"""

from collections import defaultdict
from dataclasses import replace
from itertools import product

import numpy as np

from src.benchmark import wilson_interval
from src.experiment import run_trial
from src.physiological_sweep import DURATION_S, OUTCOMES, UNREDUCED_SPEED_M_S, summarize_trial
from src.presets import physiological_config

FLOW_REDUCTIONS = (0.9, 0.99)   # at 0% no frame arrives before wall contact (experiment 22)
FRAME_RATES_HZ = (7.5, 15.0, 30.0)
OCCLUSIONS = ("patent", "target_occluded")
BRANCHES = ("upper", "lower")
PILOT_SEEDS, HELDOUT_SEEDS = (0, 1, 2), (3, 4, 5)
MODEL_DRAG_ERRORS = (-0.2, 0.2)  # sensitivity, assumed range
GAIN_FRACTION = 0.5              # k / gamma = 0.5 / limiting period, assumed
POLICIES = {
    "P0_kinematic_delay_gain": dict(estimator="kinematic", gain="delay"),
    "P1_predictor_delay_gain": dict(estimator="command_aware", gain="delay"),
    "P2_predictor_fast_gain": dict(estimator="command_aware", gain="actuation"),
    "P3_fast_feedforward": dict(estimator="command_aware", gain="actuation", feedforward=True),
    "P4_fast_wall_prediction": dict(estimator="command_aware", gain="actuation", prediction=True),
    "P5_feedforward_prediction": dict(estimator="command_aware", gain="actuation", feedforward=True,
                                      prediction=True),
}
BASELINE = "P0_kinematic_delay_gain"


def observation_delay_s(config):
    return config.latency_s + 1 / config.frame_rate_hz


def policy_gain(config, gain):
    """Gain [N/m] from the controller's drag model: GAIN_FRACTION * gamma_model / period."""
    model_drag = 6 * np.pi * 3.5e-3 * (1 + config.model_drag_error) * config.particle_radius_m
    period = observation_delay_s(config) if gain == "delay" else config.actuation_period_s
    return GAIN_FRACTION * model_drag / period


def cell_config(flow_reduction, frame_rate_hz, occlusion, policy, branch, seed, model_drag_error=0.0):
    if policy not in POLICIES or occlusion not in OCCLUSIONS:
        raise ValueError("unknown policy or occlusion")
    spec = POLICIES[policy]
    config = physiological_config(
        "composite", flow_speed_m_s=UNREDUCED_SPEED_M_S * (1 - flow_reduction), frame_rate_hz=frame_rate_hz,
        branch=branch, seed=seed, duration_s=DURATION_S[flow_reduction],
        occluded_branch=branch if occlusion == "target_occluded" else "",
        control_mode="gated", gravity_compensation=True, gain_saturation_distance_m=0.0,
        estimator_mode=spec["estimator"], flow_feedforward=spec.get("feedforward", False),
        model_drag_error=model_drag_error)
    if spec.get("prediction"):
        config = replace(config, prediction_horizon_s=observation_delay_s(config))
    return replace(config, gain_n_per_m=policy_gain(config, spec["gain"]))


def cells(seeds, model_drag_errors=(0.0,), policies=tuple(POLICIES)):
    return [dict(flow_reduction=f, frame_rate_hz=fps, occlusion=o, policy=p, branch=b, seed=s,
                 model_drag_error=e)
            for f, fps, o, p, b, s, e in product(FLOW_REDUCTIONS, FRAME_RATES_HZ, OCCLUSIONS, policies,
                                                 BRANCHES, seeds, model_drag_errors)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record


GROUP = ("model_drag_error", "flow_reduction", "frame_rate_hz", "occlusion", "policy")
MATCH = ("model_drag_error", "flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")


def aggregate(records, group=GROUP):
    groups = defaultdict(list)
    for record in records:
        groups[tuple(record[k] for k in group)].append(record)
    rows = []
    for key, trials in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        n = len(trials)
        closest = np.array([t["closest_target_approach_m"] for t in trials])
        outcomes = {}
        for name in OUTCOMES:
            count = sum(bool(t[name]) for t in trials)
            outcomes[name] = {"count": count, "rate": count / n, "wilson_95": wilson_interval(count, n)}
        rows.append({**dict(zip(group, key)), "trials": n, "outcomes": outcomes,
                     "closest_target_approach_m": {"median": float(np.median(closest)),
                                                   "min": float(closest.min())},
                     "median_peak_force_fraction": float(np.median([t["peak_force_fraction"] for t in trials]))})
    return rows


def paired_changes(records, baseline=BASELINE):
    """Matched against the baseline on every factor except policy."""
    reference = {tuple(r[k] for k in MATCH): r for r in records if r["policy"] == baseline}
    groups = defaultdict(lambda: {"rescued": 0, "regressed": 0, "both_success": 0, "both_fail": 0,
                                  "closest_change_m": []})
    for r in records:
        if r["policy"] == baseline:
            continue
        base = reference[tuple(r[k] for k in MATCH)]
        g = groups[(r["model_drag_error"], r["flow_reduction"], r["occlusion"], r["policy"])]
        key = {(True, True): "both_success", (False, False): "both_fail",
               (False, True): "rescued", (True, False): "regressed"}[(base["target_success"], r["target_success"])]
        g[key] += 1
        g["closest_change_m"].append(r["closest_target_approach_m"] - base["closest_target_approach_m"])
    rows = []
    for (error, flow, occlusion, policy), g in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        change = g.pop("closest_change_m")
        rows.append({"model_drag_error": error, "flow_reduction": flow, "occlusion": occlusion, "policy": policy,
                     **g, "median_closest_change_m": float(np.median(change))})
    return rows


def render_report(pooled, paired, title, seeds):
    lines = [f"# {title}", "",
             f"Simulation only. Seeds {', '.join(map(str, seeds))}; rates pool both branches and all "
             "frame rates. Brackets are 95% Wilson intervals. Closest approach is the continuous distance "
             "to the target (success needs <= 0.4 mm). Paired changes match the baseline "
             f"({BASELINE}) on every factor except policy.", "",
             "| Drag error | Flow cut | Target | Policy | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | "
             "Closest mm (median / min) | Peak force / cap |",
             "|---:|---:|---|---|---:|---|---:|---:|---:|---|---:|"]
    for r in pooled:
        o = r["outcomes"]
        low, high = o["target_success"]["wilson_95"]
        lines.append(f"| {r['model_drag_error']:+g} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | "
                     f"{r['policy']} | {r['trials']} | {o['target_success']['rate'] * 100:.0f} "
                     f"[{low * 100:.0f}, {high * 100:.0f}] | {o['wall_collision']['rate'] * 100:.0f} | "
                     f"{o['wrong_branch']['rate'] * 100:.0f} | {o['timeout']['rate'] * 100:.0f} | "
                     f"{r['closest_target_approach_m']['median'] * 1e3:.2f} / "
                     f"{r['closest_target_approach_m']['min'] * 1e3:.2f} | {r['median_peak_force_fraction']:.2f} |")
    lines += ["", "## Paired changes against the baseline", "",
              "| Drag error | Flow cut | Target | Policy | Rescued | Regressed | Both success | Both fail | "
              "Median closest change mm |", "|---:|---:|---|---|---:|---:|---:|---:|---:|"]
    for r in paired:
        lines.append(f"| {r['model_drag_error']:+g} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | "
                     f"{r['policy']} | {r['rescued']} | {r['regressed']} | {r['both_success']} | "
                     f"{r['both_fail']} | {r['median_closest_change_m'] * 1e3:+.2f} |")
    return "\n".join(lines) + "\n"
