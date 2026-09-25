"""Experiment 28: robustness of the recommended operating point, and a gate check.

Operating point: 99% flow reduction with experiment 24's P2 arms (command-aware
estimator, actuation-limited gain, weight-aware gravity hold; pure NdFeB holds
from release). One perturbation at a time, all magnitudes assumed. The safety
gate's maximum measurement age is matched to latency + frame period + 20 ms in
every condition except "nominal_fixed_gate", which keeps the 0.15 s used so far.

The gate check re-runs experiment 24's model-feedforward arms at 90% with the
matched gate, to test whether the 7.5 fps floor reported in docs/17-19 was partly
caused by the fixed 0.15 s limit (shorter than 50 ms + 133 ms at 7.5 fps).
"""

from dataclasses import replace
from itertools import product

from src.experiment import run_trial
from src.feedforward_hold_study import cell_config as feedforward_cell_config
from src.physiological_sweep import summarize_trial

FRAME_RATES_HZ = (7.5, 15.0, 30.0)
OCCLUSIONS = ("patent", "target_occluded")
BRANCHES = ("upper", "lower")
SEEDS = (3, 4, 5)
ARMS = ("C_P2", "N_P2_hold")
GATE_MARGIN_S = 0.02  # assumed
CONDITIONS = {
    "nominal_fixed_gate": {},
    "nominal": {},
    "latency_0.1s": {"latency_s": 0.1},
    "latency_0.2s": {"latency_s": 0.2},
    "dropout_0.3s": {"dropout_intervals": ((0.3, 0.6),)},
    "gain_-20%": {"actuation_gain_error": -0.2},
    "gain_+20%": {"actuation_gain_error": 0.2},
    "gradient_0.5": {"max_gradient_t_m": 0.5},
    "gradient_0.25": {"max_gradient_t_m": 0.25},
    "gravity_tilt_15deg": {"gravity_model_tilt_deg": 15.0},
    "gravity_tilt_30deg": {"gravity_model_tilt_deg": 30.0},
    "calibration_1px": {"calibration_sigma_px": 1.0},
    "noise_3px": {"noise_sigma_px": 3.0},
}
GATE_CHECK_ARMS = ("C_P2_modelff", "N_P2_modelff_hold")
# Exploratory follow-up, added after the results (not pre-registered): does an open-loop
# hold also protect the composite particle through a dropout?
FOLLOWUP = {
    "nominal_open_loop_hold": {"gravity_hold_from_release": True},
    "dropout_0.3s_open_loop_hold": {"dropout_intervals": ((0.3, 0.6),), "gravity_hold_from_release": True},
}


def matched_gate(config):
    return replace(config, max_measurement_age_s=config.latency_s + 1 / config.frame_rate_hz + GATE_MARGIN_S)


def cell_config(stage, frame_rate_hz, occlusion, arm, branch, seed, condition):
    if stage == "robustness":
        if arm not in ARMS or condition not in CONDITIONS:
            raise ValueError("unknown arm or condition")
        config = feedforward_cell_config(0.99, frame_rate_hz, occlusion, arm, branch, seed)
        config = replace(config, **CONDITIONS[condition])
        return config if condition == "nominal_fixed_gate" else matched_gate(config)
    if stage == "gate_check":
        if arm not in GATE_CHECK_ARMS or condition not in ("fixed_gate", "matched_gate"):
            raise ValueError("unknown arm or condition")
        config = feedforward_cell_config(0.9, frame_rate_hz, occlusion, arm, branch, seed)
        return config if condition == "fixed_gate" else matched_gate(config)
    if stage == "followup":
        if arm != "C_P2" or condition not in FOLLOWUP:
            raise ValueError("unknown follow-up arm or condition")
        config = feedforward_cell_config(0.99, frame_rate_hz, occlusion, arm, branch, seed)
        return matched_gate(replace(config, **FOLLOWUP[condition]))
    raise ValueError("stage must be robustness, gate_check or followup")


def cells():
    grid = [dict(stage="robustness", frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, condition=c)
            for c, fps, o, a, b, s in product(CONDITIONS, FRAME_RATES_HZ, OCCLUSIONS, ARMS, BRANCHES, SEEDS)]
    grid += [dict(stage="gate_check", frame_rate_hz=fps, occlusion=o, arm=a, branch=b, seed=s, condition=c)
             for c, fps, o, a, b, s in product(("fixed_gate", "matched_gate"), FRAME_RATES_HZ, OCCLUSIONS,
                                                GATE_CHECK_ARMS, BRANCHES, SEEDS)]
    return grid


def followup_cells():
    return [dict(stage="followup", frame_rate_hz=fps, occlusion=o, arm="C_P2", branch=b, seed=s, condition=c)
            for c, fps, o, b, s in product(FOLLOWUP, FRAME_RATES_HZ, OCCLUSIONS, BRANCHES, SEEDS)]


def trial_record(cell):
    config = cell_config(**cell)
    record = summarize_trial(cell, config, run_trial(config))
    record.pop("config")
    return record
