"""Experiment 25: controller flow-model shape and phase errors. Simulation only.

The plant never changes. Only the controller's copy of the flow model is wrong,
in scale, cardiac phase, pulsation amplitude, profile shape or junction geometry.
The arms are experiment 24's model-feedforward arms, run on held-out seeds 3-5
only: this is a robustness test of a fixed design, with nothing tuned.
"""

from collections import defaultdict
from dataclasses import replace
from itertools import product

import numpy as np

from src.experiment import controller_flow_function, plant_flow_function, run_trial
from src.feedforward_hold_study import cell_config as feedforward_cell_config
from src.physiological_sweep import summarize_trial
from src.vessel import YVessel

FLOW_REDUCTIONS = (0.9, 0.99)
FRAME_RATES_HZ = (7.5, 15.0, 30.0)
OCCLUSIONS = ("patent", "target_occluded")
BRANCHES = ("upper", "lower")
SEEDS = (3, 4, 5)
ARMS = ("C_P2_modelff", "N_P2_modelff_hold")
# All magnitudes are assumed. Phase is a fraction of the 1 s cardiac period.
CONDITIONS = {
    "exact": {},
    "scale_-20%": {"flow_model_error": -0.2},
    "scale_+20%": {"flow_model_error": 0.2},
    "phase_+0.1": {"flow_model_phase_error": 0.1},
    "phase_+0.25": {"flow_model_phase_error": 0.25},
    "phase_+0.5": {"flow_model_phase_error": 0.5},
    "steady_model": {"flow_model_pulsatility": 0.0},
    "double_pulsation": {"flow_model_pulsatility": 0.9},
    "profile_n4": {"flow_model_profile_exponent": 4.0},
    "profile_n9": {"flow_model_profile_exponent": 9.0},
    "junction_x0.5": {"flow_model_junction_scale": 0.5},
    "junction_x2": {"flow_model_junction_scale": 2.0},
}
ERROR_TYPE = {"exact": "exact", "scale_-20%": "scale", "scale_+20%": "scale", "phase_+0.1": "phase",
              "phase_+0.25": "phase", "phase_+0.5": "phase", "steady_model": "pulsation",
              "double_pulsation": "pulsation", "profile_n4": "profile", "profile_n9": "profile",
              "junction_x0.5": "junction", "junction_x2": "junction"}


def cell_config(flow_reduction, frame_rate_hz, occlusion, arm, branch, seed, condition):
    if arm not in ARMS or condition not in CONDITIONS:
        raise ValueError("unknown arm or condition")
    config = feedforward_cell_config(flow_reduction, frame_rate_hz, occlusion, arm, branch, seed)
    return replace(config, **CONDITIONS[condition])


def cells(conditions=tuple(CONDITIONS), seeds=SEEDS):
    return [dict(flow_reduction=f, frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, condition=c)
            for c, f, fps, o, a, b, s in product(conditions, FLOW_REDUCTIONS, FRAME_RATES_HZ, OCCLUSIONS,
                                                 ARMS, BRANCHES, seeds)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record


def route_points(branch, samples=40, offset_m=0.5e-3):
    """Centerline of parent + branch, plus points offset radially by offset_m in y and z."""
    vessel = YVessel()
    parent, arm = vessel.segments[0], vessel.segments[1 if branch == "upper" else 2]
    points = [parent.start_m + f * (parent.end_m - parent.start_m) for f in np.linspace(0.05, 1, samples // 2)]
    points += [arm.start_m + f * (arm.end_m - arm.start_m) for f in np.linspace(0.05, 0.95, samples // 2)]
    offsets = [np.zeros(3), [0, offset_m, 0], [0, -offset_m, 0], [0, 0, offset_m], [0, 0, -offset_m]]
    return [np.asarray(p) + o for p in points for o in offsets]


def route_velocity_error(condition, flow_reduction, occlusion, times=np.linspace(0, 1, 20, endpoint=False)):
    """Mean |u_model - u_plant| [m/s] over both routes and one cardiac period."""
    errors = []
    for branch in BRANCHES:
        config = cell_config(flow_reduction, 15.0, occlusion, "C_P2_modelff", branch, 3, condition)
        plant, model = plant_flow_function(config), controller_flow_function(config)
        for p in route_points(branch):
            for t in times:
                errors.append(np.linalg.norm(model(p, t) - plant(p, t)))
    return float(np.mean(errors))


MATCH = ("arm", "flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")


def paired_against_exact(records):
    exact = {tuple(r[k] for k in MATCH): r for r in records if r["condition"] == "exact"}
    groups = defaultdict(lambda: {"kept": 0, "lost": 0, "gained": 0, "both_fail": 0})
    for r in records:
        if r["condition"] == "exact":
            continue
        base = exact[tuple(r[k] for k in MATCH)]
        g = groups[(r["condition"], r["flow_reduction"], r["occlusion"], r["arm"])]
        g[{(True, True): "kept", (True, False): "lost", (False, True): "gained",
           (False, False): "both_fail"}[(base["target_success"], r["target_success"])]] += 1
    return [{"condition": c, "flow_reduction": f, "occlusion": o, "arm": a, **g}
            for (c, f, o, a), g in sorted(groups.items(), key=lambda item: tuple(map(str, item[0])))]
