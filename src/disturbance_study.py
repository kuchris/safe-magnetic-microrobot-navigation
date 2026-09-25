"""Experiment 30: rejecting an unmodeled force bias. Simulation only.

Experiment 29 traced pure-NdFeB failures to a biased gravity hold that the
weight-aware estimator does not model. Two existing pieces form a disturbance
canceller: estimated-drift feedforward (flow_feedforward), which cancels the
command-aware residual drift including any bias, and a larger residual-filter
acceleration PSD, which lets that residual adapt faster. Bundles come from
experiment 29; held-out seeds 3-5; nothing else is tuned.
"""

from dataclasses import replace
from itertools import product

from src.combined_study import cell_config as combined_cell_config
from src.experiment import run_trial
from src.physiological_sweep import summarize_trial
from src.robustness_study import BRANCHES, FRAME_RATES_HZ, OCCLUSIONS, SEEDS

ARMS = ("C_P2", "N_P2_hold")
BUNDLES = ("nominal", "mild", "moderate")
ESTIMATORS = {
    "baseline": {"estimator_acceleration_psd": 1e-7},
    "drift_ff": {"estimator_acceleration_psd": 1e-7, "flow_feedforward": True},
    "fast_residual": {"estimator_acceleration_psd": 1e-5},
    "fast_residual_ff": {"estimator_acceleration_psd": 1e-5, "flow_feedforward": True},
    "faster_residual_ff": {"estimator_acceleration_psd": 1e-3, "flow_feedforward": True},
}


def cell_config(frame_rate_hz, occlusion, arm, branch, seed, bundle, estimator):
    if estimator not in ESTIMATORS or bundle not in BUNDLES:
        raise ValueError("unknown estimator or bundle")
    return replace(combined_cell_config(frame_rate_hz, occlusion, arm, branch, seed, bundle), **ESTIMATORS[estimator])


def cells():
    return [dict(frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, bundle=bu, estimator=e)
            for e, bu, fps, o, a, b, s in product(ESTIMATORS, BUNDLES, FRAME_RATES_HZ, OCCLUSIONS, ARMS, BRANCHES,
                                                   SEEDS)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record
