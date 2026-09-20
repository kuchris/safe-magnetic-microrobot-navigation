from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.localization import StateEstimate
from src.navigation import BiplaneNavigation
from src.prediction import ShortHorizonCorrection
from src.vessel import YVessel


def predictor():
    return ShortHorizonCorrection(YVessel(), 0.1e-3, "upper", 0.5,
                                  6 * np.pi * 3.5e-3 * 0.1e-3, 3e-9, 0.2e-3)


def state(position, velocity):
    return StateEstimate(np.array(position), np.array(velocity), np.eye(6) * 1e-12)


def test_prediction_redirects_before_current_wall_gate_would_stop():
    estimate = state([5e-3, 0.9e-3, 0], [0.6e-3, 0.6e-3, 0])
    result = predictor().select(estimate, np.array([1e-9, 0, 0]), np.zeros(3))
    assert YVessel().clearance(estimate.estimated_position, 0.1e-3) > 0.2e-3
    assert result.nominal_clearance_m < 0.2e-3
    assert result.adjusted and result.force_n[1] < 0
    assert result.selected_clearance_m > result.nominal_clearance_m
    assert np.linalg.norm(result.force_n) <= 3e-9 * (1 + 1e-12)


def test_centered_motion_preserves_nominal_force_and_does_not_mutate_estimate():
    estimate = state([5e-3, 0, 0], [0.6e-3, 0, 0])
    before = estimate.covariance.copy()
    nominal = np.array([1e-9, 0, 0])
    result = predictor().select(estimate, nominal, nominal)
    np.testing.assert_array_equal(result.force_n, nominal)
    np.testing.assert_array_equal(estimate.covariance, before)
    assert not result.adjusted


def test_infeasible_prediction_reports_remaining_margin_violation():
    result = predictor().select(state([5e-3, 0.9e-3, 0], [0, 3e-3, 0]),
                                np.zeros(3), np.zeros(3))
    assert result.selected_clearance_m < 0.2e-3
    assert result.selected_clearance_m > result.nominal_clearance_m
    assert np.linalg.norm(result.force_n) <= 3e-9 * (1 + 1e-12)


def test_prediction_uncertainty_includes_velocity_covariance():
    estimate = state([5e-3, 0, 0], [0, 0, 0])
    a = predictor().select(estimate, np.zeros(3), np.zeros(3))
    estimate.covariance[3:, 3:] = np.eye(3) * (0.5e-3)**2
    b = predictor().select(estimate, np.zeros(3), np.zeros(3))
    assert b.nominal_clearance_m < a.nominal_clearance_m - 0.5e-3


def test_previous_command_is_not_counted_twice_in_velocity_prediction():
    correction = predictor()
    previous = np.array([0, 2e-9, 0])
    estimate = state([5e-3, 0.5e-3, 0], previous / correction.drag)
    with_command = correction.select(estimate, previous, previous)
    without_command = correction.select(estimate, previous, np.zeros(3))
    assert with_command.nominal_clearance_m > without_command.nominal_clearance_m


def test_intermediate_samples_detect_gap_even_when_endpoints_are_inside():
    start, end = np.array([0.014, 0.0024, 0.0012]), np.array([0.014, -0.0024, -0.0012])
    vessel = YVessel()
    assert vessel.clearance(start, 0.1e-3) > 0.2e-3
    assert vessel.clearance(end, 0.1e-3) > 0.2e-3
    result = predictor().select(state(start, (end - start) / 0.5), np.zeros(3), np.zeros(3))
    assert result.nominal_clearance_m < 0


@pytest.mark.parametrize("horizon,mode", [(-1, "gated"), (float("nan"), "gated"),
                                        (0.5, "ungated"), (0.5, "passive")])
def test_invalid_prediction_settings(horizon, mode):
    with pytest.raises(ValueError):
        BiplaneNavigation(YVessel(), 0.1e-3, prediction_horizon_s=horizon, control_mode=mode)


@pytest.mark.parametrize("options", [{"dropout_intervals": ((0.3, 0.7),)},
                                    {"frame_rate_hz": 5, "latency_s": 0.2},
                                    {"start_m": (5e-3, 1.2e-3, 0)}])
def test_prediction_never_overrides_existing_stop_gates(options):
    result = run_trial(replace(TrialConfig(duration_s=1, prediction_horizon_s=0.5), **options))
    h = result["history"]
    stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    assert stopped.any()
    np.testing.assert_array_equal(h["force_n"][stopped], np.zeros((stopped.sum(), 3)))
    assert not h["prediction_adjusted"][stopped].any()
    assert np.isnan(h["predicted_selected_clearance_m"][stopped]).all()


def test_enabled_prediction_is_reproducible_and_force_bounded():
    config = TrialConfig(duration_s=0.6, start_m=(5e-3, 0.9e-3, 0),
                         flow_disturbance_m_s=0.3e-3, flow_correlation_s=0.25,
                         prediction_horizon_s=0.5)
    a, b = run_trial(config), run_trial(config)
    for key in a["history"]:
        np.testing.assert_array_equal(a["history"][key], b["history"][key])
    assert a["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
