from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from src.controller import bounded_target_force
from src.experiment import TrialConfig, run_trial
from src.localization import StateEstimate
from src.navigation import BiplaneNavigation
from src.prediction import ShortHorizonCorrection
from src.vessel import YVessel


def assert_summary_matches(actual, expected):
    """Exact on keys and non-float fields; floats allow cross-platform round-off."""
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        if isinstance(value, float):
            assert actual[key] == pytest.approx(value, rel=1e-8, abs=1e-15), key
        else:
            assert actual[key] == value, key


def predictor(distance):
    return ShortHorizonCorrection(YVessel(), 0.1e-3, "upper", 0.5,
                                  6 * np.pi * 3.5e-3 * 0.1e-3, 3e-9, 0.2e-3,
                                  terminal_distance_m=distance)


def test_terminal_candidates_reduce_predicted_miss_within_wall_margin():
    target = YVessel().upper_target
    axis = np.array([1, 0.6, 0.3])
    axis /= np.linalg.norm(axis)
    lateral = np.array([-0.6, 1, 0]) / np.linalg.norm([-0.6, 1, 0])
    p = target - 0.6e-3 * axis + 0.3e-3 * lateral
    nominal = bounded_target_force(p, target, 2e-6, 3e-9)
    state = StateEstimate(p, 1.2e-3 * axis + 0.1e-3 * lateral, np.eye(6) * 1e-12)
    result = predictor(2e-3).select(state, nominal, nominal)
    assert result.terminal_active and result.terminal_adjusted
    assert result.selected_target_miss_m < result.baseline_target_miss_m
    assert result.selected_clearance_m >= 0.2e-3
    assert np.linalg.norm(result.force_n) <= 3e-9 * (1 + 1e-12)


def test_terminal_mode_leaves_distant_motion_unchanged():
    state = StateEstimate(np.array([0.015, .003, .0015]), np.array([.001, .0006, .0003]), np.eye(6) * 1e-12)
    force = np.array([1e-9, 0, 0])
    before = predictor(0).select(state, force, force)
    after = predictor(2e-3).select(state, force, force)
    np.testing.assert_array_equal(after.force_n, before.force_n)
    assert after.selected_clearance_m == before.selected_clearance_m
    assert not after.terminal_active and np.isnan(after.selected_target_miss_m)


def test_no_feasible_candidate_keeps_clearance_priority_and_force_limit():
    target = YVessel().upper_target
    axis = np.array([1, 0.6, 0.3])
    axis /= np.linalg.norm(axis)
    state = StateEstimate(target - axis * 0.5e-3, axis * 5e-3, np.eye(6) * 1e-12)
    baseline = predictor(0).select(state, np.zeros(3), np.zeros(3))
    result = predictor(2e-3).select(state, np.zeros(3), np.zeros(3))
    assert result.terminal_active and result.selected_clearance_m < 0.2e-3
    assert result.selected_clearance_m >= baseline.selected_clearance_m
    assert np.linalg.norm(result.force_n) <= 3e-9 * (1 + 1e-12)


def test_zero_speed_candidate_has_finite_target_miss():
    state = StateEstimate(YVessel().upper_target + [0, 0.1e-3, 0], np.zeros(3), np.eye(6) * 1e-12)
    result = predictor(2e-3).select(state, np.zeros(3), np.zeros(3))
    assert np.isfinite(result.baseline_target_miss_m)
    assert result.selected_target_miss_m < 1e-12


@pytest.mark.parametrize("options", [{"terminal_guidance_distance_m": -1},
                                    {"terminal_guidance_distance_m": float("nan")},
                                    {"terminal_guidance_distance_m": 0.002, "prediction_horizon_s": 0},
                                    {"terminal_guidance_distance_m": 0.002, "control_mode": "ungated"}])
def test_terminal_configuration_validation(options):
    with pytest.raises(ValueError):
        BiplaneNavigation(YVessel(), .1e-3, **dict({"prediction_horizon_s": .5}, **options))


@pytest.mark.parametrize("options", [{"dropout_intervals": ((0, 1),)},
                                    {"frame_rate_hz": 5, "latency_s": .2},
                                    {"max_sigma_m": 1e-10}])
def test_terminal_guidance_cannot_override_stop_gates(options):
    config = replace(TrialConfig(duration_s=.5, start_m=(.019, .0054, .0027),
                                 prediction_horizon_s=.5, terminal_guidance_distance_m=.002,
                                 estimator_mode="command_aware"), **options)
    result = run_trial(config)
    h = result["history"]
    stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    assert stopped.any()
    assert np.all(h["force_n"][stopped] == 0)
    assert not h["terminal_active"][stopped].any()
    assert np.isnan(h["selected_target_miss_m"][stopped]).all()


def test_disabled_terminal_guidance_reproduces_archived_predictive_trial():
    path = Path(__file__).parents[1] / "docs/results/flow_estimation/closed_loop_piecewise.json"
    records = json.loads(path.read_text())["trials"]
    reference = next(r for r in records if r["trace_id"] == "piecewise_0.6_0.3_lower_20_command_aware")
    assert_summary_matches(run_trial(TrialConfig(**reference["config"]))["summary"], reference["summary"])


def test_terminal_guidance_replay_is_deterministic():
    config = TrialConfig(duration_s=.5, start_m=(.019, .0054, .0027),
                         prediction_horizon_s=.5, terminal_guidance_distance_m=.002)
    a, b = run_trial(config), run_trial(config)
    assert a["history"]["terminal_active"].any()
    for key in a["history"]:
        np.testing.assert_array_equal(a["history"][key], b["history"][key])
