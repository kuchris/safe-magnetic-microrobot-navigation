from dataclasses import replace
import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.flow_estimation import CommandAwareEstimator
from src.localization import DelayedStateEstimator, Reconstruction
from src.prediction_audit import forecast_metrics


DRAG = 6 * np.pi * 3.5e-3 * 0.1e-3


def reconstruction(position):
    return Reconstruction(np.array(position), np.eye(3) * 1e-10,
                          np.eye(3) * 1e-12, np.zeros(4))


def test_command_integral_uses_capture_time_not_delivery_time():
    flow = np.array([0.0006, 0, 0])
    estimator = CommandAwareEstimator(DRAG, initial_velocity_m_s=flow,
                                     acceleration_spectral_density=0, velocity_sigma_m_s=0)
    estimator.command(0, [0, 2e-9, 0])
    estimator.command(0.2, [0, -1e-9, 0])
    observed = flow * 0.1 + np.array([0, 2e-9, 0]) / DRAG * 0.1
    estimator.observe(reconstruction(observed), 0.1, 0.3)
    expected = flow * 0.3 + np.array([0, 2e-9 * 0.2 - 1e-9 * 0.1, 0]) / DRAG
    snapshot = estimator.estimate(0.3)
    np.testing.assert_allclose(snapshot.estimated_position, expected, atol=1e-16)
    np.testing.assert_allclose(snapshot.estimated_velocity, flow + np.array([0, -1e-9, 0]) / DRAG)
    np.testing.assert_array_equal(estimator.estimate(0.3).covariance, snapshot.covariance)
    np.testing.assert_allclose(estimator.residual.filter.estimated_position, flow * 0.1, atol=1e-16)


def test_fixed_flow_is_separated_from_reversing_commands():
    flow = np.array([0.0006, 0, 0])
    aware = CommandAwareEstimator(DRAG)
    legacy = DelayedStateEstimator()
    errors = [[], []]
    positions = []
    p, previous = np.zeros(3), np.zeros(3)
    for tick in range(81):
        now = tick * 0.05
        if tick:
            p += 0.05 * (flow + previous / DRAG)
        positions.append(p.copy())
        if tick >= 2:
            rec = reconstruction(positions[tick - 2])
            for estimator in (legacy, aware):
                estimator.observe(rec, (tick - 2) * 0.05, now)
        if now >= 1:
            for k, estimator in enumerate((legacy, aware)):
                estimated_flow = estimator.estimate(now).estimated_velocity - previous / DRAG
                errors[k].append(np.linalg.norm(estimated_flow - flow))
        previous = np.array([0, 3e-9 * (-1)**(tick // 4), 0])
        aware.command(now, previous)
    assert np.mean(errors[1]) < 0.05 * np.mean(errors[0])


def test_command_validation_and_no_observation_initialization():
    estimator = CommandAwareEstimator(DRAG)
    estimator.command(0, [1e-9, 0, 0])
    assert estimator.estimate(0.1) is None
    with pytest.raises(ValueError, match="increase"):
        estimator.command(0, [0, 0, 0])
    with pytest.raises(ValueError):
        estimator.command(0.1, [np.nan, 0, 0])
    with pytest.raises(ValueError, match="future"):
        estimator.observe(reconstruction([0, 0, 0]), 1, 0.5)
    with pytest.raises(ValueError):
        run_trial(TrialConfig(estimator_mode="unknown"))


@pytest.mark.parametrize("options", [{"dropout_intervals": ((0.3, 0.7),)},
                                    {"frame_rate_hz": 5, "latency_s": 0.2},
                                    {"start_m": (5e-3, 1.2e-3, 0)}])
def test_command_aware_mode_preserves_stop_invariants_and_replay(options):
    config = replace(TrialConfig(duration_s=1, prediction_horizon_s=0.5,
                                 estimator_mode="command_aware"), **options)
    result = run_trial(config)
    h = result["history"]
    stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    assert stopped.any()
    assert np.all(h["force_n"][stopped] == 0)
    assert not h["prediction_adjusted"][stopped].any()
    assert result["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
    repeat = run_trial(config)
    for key in h:
        np.testing.assert_array_equal(h[key], repeat["history"][key])


def test_audit_removes_future_command_changes_without_claiming_online_prediction():
    t = np.arange(0, 3.005, 0.005)
    force = np.zeros((len(t), 3))
    force[t >= 1.5, 1] = 3e-9
    previous = np.vstack([np.zeros(3), force[:-1]])
    flow = np.tile([0.0006, 0, 0], (len(t), 1))
    motion = np.vstack([np.zeros(3), np.cumsum(np.diff(t)[:, None] * force[:-1] / DRAG, axis=0)])
    position = t[:, None] * flow + motion
    history = dict(time_s=t, command_force_n=force, estimated_velocity_m_s=flow + previous / DRAG,
                   estimated_position_m=position, true_position_m=position, flow_velocity_m_s=flow)
    rows = forecast_metrics(history, DRAG)
    row = next(r for r in rows if r["horizon_s"] == 0.5 and r["subset"] == "all")
    assert row["samples"] > 0
    assert row["recorded_command_RMSE_m"] < 1e-15
    assert row["held_command_RMSE_m"] > 1e-5
    assert row["flow_RMSE_m_s"] < 1e-15
    short = {key: value[:5] for key, value in history.items()}
    assert all(r["samples"] == 0 and r["held_command_RMSE_m"] is None for r in forecast_metrics(short, DRAG))
