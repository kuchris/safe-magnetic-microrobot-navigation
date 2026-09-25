"""Experiment 29: combined perturbations at the 99% operating point. Simulation only.

Both materials use the open-loop gravity hold that experiment 28's follow-up
suggested (the composite adds gravity_hold_from_release; pure NdFeB already
holds from release) and the matched gate. Each bundle applies several assumed
imperfections at once. Held-out seeds 3-5; nothing is tuned.
"""

from dataclasses import replace
from itertools import product

from src.experiment import run_trial
from src.feedforward_hold_study import cell_config as feedforward_cell_config
from src.physiological_sweep import summarize_trial
from src.robustness_study import BRANCHES, FRAME_RATES_HZ, OCCLUSIONS, SEEDS, matched_gate

ARMS = ("C_P2", "N_P2_hold")
BUNDLES = {
    "nominal": {},
    "mild": {"latency_s": 0.1, "actuation_gain_error": -0.1, "gravity_model_tilt_deg": 5.0,
             "calibration_sigma_px": 0.5, "noise_sigma_px": 2.0, "max_gradient_t_m": 0.5},
    "moderate": {"latency_s": 0.1, "actuation_gain_error": -0.2, "gravity_model_tilt_deg": 10.0,
                 "calibration_sigma_px": 1.0, "noise_sigma_px": 3.0, "max_gradient_t_m": 0.5,
                 "dropout_intervals": ((0.3, 0.5),)},
    "severe": {"latency_s": 0.2, "actuation_gain_error": -0.2, "gravity_model_tilt_deg": 15.0,
               "calibration_sigma_px": 1.0, "noise_sigma_px": 3.0, "max_gradient_t_m": 0.25,
               "dropout_intervals": ((0.3, 0.6),)},
}


# Exploratory ablation, added after the results (not pre-registered): the moderate bundle
# with one ingredient reset to its nominal value, for pure NdFeB.
NOMINAL_VALUES = {"latency_s": 0.05, "actuation_gain_error": 0.0, "gravity_model_tilt_deg": 0.0,
                  "calibration_sigma_px": 0.25, "noise_sigma_px": 1.0, "max_gradient_t_m": 1.0,
                  "dropout_intervals": ()}


# Second exploratory step: the mild bundle with one field raised to its moderate value.
MILD_TO_MODERATE = ("actuation_gain_error", "gravity_model_tilt_deg", "calibration_sigma_px", "noise_sigma_px",
                    "dropout_intervals")


def cell_config(frame_rate_hz, occlusion, arm, branch, seed, bundle, without=None, raised=None):
    if arm not in ARMS or bundle not in BUNDLES:
        raise ValueError("unknown arm or bundle")
    config = feedforward_cell_config(0.99, frame_rate_hz, occlusion, arm, branch, seed)
    config = replace(config, gravity_hold_from_release=True, **BUNDLES[bundle])
    if raised is not None:
        if bundle != "mild" or raised not in MILD_TO_MODERATE:
            raise ValueError("raised applies to the mild bundle and a field that differs from moderate")
        config = replace(config, **{raised: BUNDLES["moderate"][raised]})
    if without is not None:
        if without not in BUNDLES[bundle]:
            raise ValueError("ablated field is not part of the bundle")
        config = replace(config, **{without: NOMINAL_VALUES[without]})
    return matched_gate(config)


def cells():
    return [dict(frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, bundle=bu)
            for bu, fps, o, a, b, s in product(BUNDLES, FRAME_RATES_HZ, OCCLUSIONS, ARMS, BRANCHES, SEEDS)]


def ablation_cells():
    return [dict(frame_rate_hz=fps, occlusion=o, arm="N_P2_hold", branch=b, seed=s, bundle="moderate", without=w)
            for w, fps, o, b, s in product(BUNDLES["moderate"], FRAME_RATES_HZ, OCCLUSIONS, BRANCHES, SEEDS)]


def raise_cells():
    return [dict(frame_rate_hz=fps, occlusion=o, arm="N_P2_hold", branch=b, seed=s, bundle="mild", raised=f)
            for f, fps, o, b, s in product(MILD_TO_MODERATE, FRAME_RATES_HZ, OCCLUSIONS, BRANCHES, SEEDS)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record
