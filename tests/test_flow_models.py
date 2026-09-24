from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.failure_analysis import analyze_trial
from src.flow import FlowDisturbance, centerline_flow, smooth_junction_flow
from src.particle import Particle


def assert_summary_matches(actual, expected):
    """Exact on keys and non-float fields; floats allow cross-platform round-off."""
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        if isinstance(value, float):
            assert actual[key] == pytest.approx(value, rel=1e-8, abs=1e-15), key
        else:
            assert actual[key] == value, key


def test_smooth_flow_is_continuous_across_both_old_switches():
    for axis, point in ((0, [0.01, 0.0002, 0]), (1, [0.011, 0, 0])):
        a, b = np.array(point), np.array(point)
        a[axis] -= 1e-9
        b[axis] += 1e-9
        assert np.linalg.norm(smooth_junction_flow(a) - smooth_junction_flow(b)) < 1e-8
        assert np.linalg.norm(centerline_flow(a) - centerline_flow(b)) > 1e-4


def test_smooth_flow_speed_symmetry_and_far_branch_direction():
    for x in (0.007, 0.01, 0.014):
        upper = smooth_junction_flow([x, 0.0004, 0.0002], speed_m_s=0.0006)
        lower = smooth_junction_flow([x, -0.0004, -0.0002], speed_m_s=0.0006)
        np.testing.assert_allclose(upper * [1, -1, -1], lower)
        assert np.linalg.norm(upper) == pytest.approx(0.0006)
    np.testing.assert_array_equal(smooth_junction_flow([0.012, 0, 0]), [0.001, 0, 0])
    np.testing.assert_allclose(smooth_junction_flow([0.02, 0.003, 0.0015]),
                               centerline_flow([0.02, 0.003, 0.0015]), rtol=1e-6)


def test_independent_disturbance_preserves_legacy_random_draws():
    noise = FlowDisturbance(0.0003, rng=np.random.default_rng(9))
    reference = np.random.default_rng(9)
    for t in (0, 0.005, 0.02):
        np.testing.assert_array_equal(noise.sample(t), reference.normal(0, 0.0003, 3))
    with pytest.raises(ValueError):
        noise.sample(0.02)


def test_correlated_disturbance_has_configured_stationary_variance_and_correlation():
    noise = FlowDisturbance(0.0003, 0.25, np.random.default_rng(13))
    samples = np.array([noise.sample(i * 0.05) for i in range(20000)])
    assert abs(samples.mean()) < 0.000015
    np.testing.assert_allclose(samples.std(axis=0), 0.0003, rtol=0.04)
    assert np.corrcoef(samples[:-1, 0], samples[1:, 0])[0, 1] == pytest.approx(np.exp(-0.05 / 0.25), abs=0.02)


def test_actual_flow_log_matches_motion_and_smooth_replay_diagnostics():
    config = TrialConfig(duration_s=0.107, start_m=(0.0101, 0.0002, 0.0001),
                         flow_model="smooth", flow_disturbance_m_s=0.0003, flow_correlation_s=0.25)
    result = run_trial(config)
    h = result["history"]
    velocity = np.diff(h["true_position_m"], axis=0) / np.diff(h["time_s"])[:, None]
    gamma = Particle(0.1e-3, 3.5e-3).drag_coefficient
    np.testing.assert_allclose(velocity, h["flow_velocity_m_s"][:-1] + h["force_n"][:-1] / gamma, atol=1e-14)
    assert np.isnan(h["flow_velocity_m_s"][-1]).all()
    event = analyze_trial(result)["junction_crossing"]
    np.testing.assert_allclose(event["prescribed_flow_m_s"], smooth_junction_flow(config.start_m, speed_m_s=config.flow_speed_m_s))
    repeated = run_trial(config)
    for key in h:
        np.testing.assert_array_equal(h[key], repeated["history"][key])


def test_default_flow_preserves_archived_dropout_trial():
    pilot = json.loads((Path(__file__).parents[1] / "docs/results/benchmark_pilot.json").read_text())
    reference = next(r for r in pilot["trials"] if r["scenario"] == "dropout_burst"
                     and r["config"]["branch"] == "lower" and r["config"]["control_mode"] == "gated"
                     and r["config"]["seed"] == 0)
    assert_summary_matches(run_trial(TrialConfig(**reference["config"]))["summary"], reference["summary"])


@pytest.mark.parametrize("options", [{"flow_model": "unknown"}, {"flow_correlation_s": -1},
    {"flow_transition_length_m": 0}, {"flow_branch_width_m": float("nan")}])
def test_invalid_flow_settings(options):
    with pytest.raises(ValueError):
        run_trial(replace(TrialConfig(), **options))
