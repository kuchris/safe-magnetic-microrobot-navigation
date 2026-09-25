"""Experiment 24: model flow feedforward, a release-time gravity hold and a short
wall-prediction horizon, on top of experiment 23's best policy (P2). Simulation only.

P2 = command-aware estimator + gain 0.5 gamma_model / T_a with a gravity hold.
Every arm except C_P2_exp23 also gives the estimator the known weight, so a
held weight is not read as commanded motion; C_P2_exp23 is experiment 23's P2
unchanged and measures that fix. Composite arms pair against C_P2; pure-NdFeB
arms pair against N_P2_hold.
Seeds 0-2 are the pilot, 3-5 are held out; the flow-model error is applied on
held-out seeds to the arms that use model feedforward.
"""

from collections import defaultdict
from dataclasses import replace
from itertools import product

import numpy as np

from src.delay_aware_study import policy_gain
from src.experiment import run_trial
from src.physiological_sweep import DURATION_S, UNREDUCED_SPEED_M_S, summarize_trial
from src.presets import physiological_config

FLOW_REDUCTIONS = (0.9, 0.99)
FRAME_RATES_HZ = (7.5, 15.0, 30.0)
OCCLUSIONS = ("patent", "target_occluded")
BRANCHES = ("upper", "lower")
PILOT_SEEDS, HELDOUT_SEEDS = (0, 1, 2), (3, 4, 5)
FLOW_MODEL_ERRORS = (-0.2, 0.2)   # assumed mean-speed mismatch
WALL_HORIZON_S = 0.05             # fixed wall-prediction horizon, assumed
ARMS = {
    "C_P2_exp23": dict(material="composite", weight_unaware=True),
    "C_P2": dict(material="composite"),
    "C_P2_modelff": dict(material="composite", model_ff=True),
    "C_P2_wall50": dict(material="composite", wall=True),
    "C_P2_modelff_wall50": dict(material="composite", model_ff=True, wall=True),
    "N_P2_hold": dict(material="ndfeb", release_hold=True),
    "N_P2_modelff_hold": dict(material="ndfeb", model_ff=True, release_hold=True),
}
BASELINES = {"composite": "C_P2", "ndfeb": "N_P2_hold"}
MODEL_FF_ARMS = tuple(arm for arm, spec in ARMS.items() if spec.get("model_ff"))


def cell_config(flow_reduction, frame_rate_hz, occlusion, arm, branch, seed, flow_model_error=0.0):
    if arm not in ARMS or occlusion not in OCCLUSIONS:
        raise ValueError("unknown arm or occlusion")
    spec = ARMS[arm]
    config = physiological_config(
        spec["material"], flow_speed_m_s=UNREDUCED_SPEED_M_S * (1 - flow_reduction),
        frame_rate_hz=frame_rate_hz, branch=branch, seed=seed, duration_s=DURATION_S[flow_reduction],
        occluded_branch=branch if occlusion == "target_occluded" else "", control_mode="gated",
        gravity_compensation=True, gain_saturation_distance_m=0.0, estimator_mode="command_aware",
        model_flow_feedforward=spec.get("model_ff", False), flow_model_error=flow_model_error,
        gravity_hold_from_release=spec.get("release_hold", False),
        estimator_knows_weight=not spec.get("weight_unaware", False),
        prediction_horizon_s=WALL_HORIZON_S if spec.get("wall") else 0.0)
    return replace(config, gain_n_per_m=policy_gain(config, "actuation"))


def cells(seeds, flow_model_errors=(0.0,), arms=tuple(ARMS)):
    return [dict(flow_reduction=f, frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, flow_model_error=e)
            for f, fps, o, a, b, s, e in product(FLOW_REDUCTIONS, FRAME_RATES_HZ, OCCLUSIONS, arms, BRANCHES,
                                                 seeds, flow_model_errors)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    record["material"] = ARMS[cell["arm"]]["material"]
    return record


MATCH = ("flow_model_error", "flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")


def paired_changes(records, baseline_records=None):
    """Pair each arm with its material's baseline on every other factor.

    baseline_records supplies the baselines when they were run separately
    (for example, error-free baselines for the flow-model-error stage).
    """
    pool = records if baseline_records is None else baseline_records
    reference = {(r["arm"],) + tuple(r[k] for k in MATCH[1:]): r for r in pool if r["arm"] in BASELINES.values()}
    groups = defaultdict(lambda: {"rescued": 0, "regressed": 0, "both_success": 0, "both_fail": 0, "closest": []})
    for r in records:
        baseline = BASELINES[r["material"]]
        if r["arm"] == baseline:
            continue
        base = reference[(baseline,) + tuple(r[k] for k in MATCH[1:])]
        g = groups[(r["flow_model_error"], r["flow_reduction"], r["occlusion"], r["arm"])]
        g[{(True, True): "both_success", (False, False): "both_fail", (False, True): "rescued",
           (True, False): "regressed"}[(base["target_success"], r["target_success"])]] += 1
        g["closest"].append(r["closest_target_approach_m"] - base["closest_target_approach_m"])
    rows = []
    for (error, flow, occlusion, arm), g in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        change = g.pop("closest")
        rows.append({"flow_model_error": error, "flow_reduction": flow, "occlusion": occlusion, "arm": arm, **g,
                     "baseline": BASELINES[ARMS[arm]["material"]],
                     "median_closest_change_m": float(np.median(change))})
    return rows
