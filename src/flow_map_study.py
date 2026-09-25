"""Experiment 26: model feedforward with a measured flow map. Simulation only.

The controller's flow model is the plant's time-mean field sampled on a voxel
grid, with per-voxel noise (src/flow_map.py). Arms and seeds as experiment 25;
nothing is tuned. 90% reduction runs every condition; 99% runs only the worst.
"""

from dataclasses import replace
from itertools import product

import numpy as np

from src.experiment import plant_flow_function, run_trial
from src.flow_map import measured_flow_map
from src.flow_model_error_study import ARMS, BRANCHES, FRAME_RATES_HZ, OCCLUSIONS, SEEDS, route_points
from src.feedforward_hold_study import cell_config as feedforward_cell_config
from src.physiological_sweep import summarize_trial

# (voxel [m], noise fraction of the centerline mean); all assumed.
CONDITIONS = {
    "exact": (0.0, 0.0),
    "map_0.25mm": (0.25e-3, 0.0),
    "map_0.5mm": (0.5e-3, 0.0),
    "map_1.0mm": (1.0e-3, 0.0),
    "map_0.5mm_noise5%": (0.5e-3, 0.05),
    "map_0.5mm_noise10%": (0.5e-3, 0.10),
    "map_1.0mm_noise10%": (1.0e-3, 0.10),
}
WORST = "map_1.0mm_noise10%"


def cell_config(flow_reduction, frame_rate_hz, occlusion, arm, branch, seed, condition):
    if arm not in ARMS or condition not in CONDITIONS:
        raise ValueError("unknown arm or condition")
    voxel, noise = CONDITIONS[condition]
    config = feedforward_cell_config(flow_reduction, frame_rate_hz, occlusion, arm, branch, seed)
    return replace(config, flow_model_voxel_m=voxel, flow_model_noise=noise)


def cells(seeds=SEEDS):
    grid = [dict(flow_reduction=0.9, frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, condition=c)
            for c, fps, o, a, b, s in product(CONDITIONS, FRAME_RATES_HZ, OCCLUSIONS, ARMS, BRANCHES, seeds)]
    grid += [dict(flow_reduction=0.99, frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, condition=c)
             for c, fps, o, a, b, s in product(("exact", WORST), FRAME_RATES_HZ, OCCLUSIONS, ARMS, BRANCHES, seeds)]
    return grid


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record


def route_velocity_error(condition, flow_reduction, occlusion, seed=3,
                         times=np.linspace(0, 1, 20, endpoint=False)):
    """Mean |u_map - u_plant| [m/s] over both routes and one cardiac period (seed sets the noise)."""
    voxel, noise = CONDITIONS[condition]
    errors = []
    for branch in BRANCHES:
        config = cell_config(flow_reduction, 15.0, occlusion, "C_P2_modelff", branch, seed, condition)
        plant = plant_flow_function(config)
        if voxel == 0:
            return 0.0
        model = measured_flow_map(config, voxel, noise)
        for p in route_points(branch):
            for t in times:
                errors.append(np.linalg.norm(model(p, t) - plant(p, t)))
    return float(np.mean(errors))

