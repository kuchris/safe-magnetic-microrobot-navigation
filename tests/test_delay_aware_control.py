import json
from pathlib import Path

import numpy as np
import pytest

from src.delay_aware_study import (BASELINE, GAIN_FRACTION, POLICIES, cell_config, cells, observation_delay_s,
                                   paired_changes, policy_gain, trial_record)
from src.experiment import TrialConfig, run_trial
from src.localization import StateEstimate
from src.navigation import BiplaneNavigation
from src.vessel import YVessel

RESULTS = Path(__file__).parents[1] / "docs/results"
GAMMA = 6 * np.pi * 3.5e-3 * 100e-6


class StubEstimator:
    """Known estimate and residual drift at a safe point on the parent axis."""

    def __init__(self, drift):
        self.drift = np.asarray(drift, dtype=float)
        self.last_capture_s = 0.0

    def estimate(self, now_s):
        return StateEstimate(np.array([5e-3, 0, 0]), np.zeros(3), np.eye(6) * 1e-12)

    def flow_estimate(self, now_s):
        return self.drift


@pytest.mark.parametrize("hold", [None, np.array([0.0, 0.0, 4e-8])])
def test_feedforward_cancels_the_estimated_drift_with_or_without_a_hold(hold):
    navigation = BiplaneNavigation(YVessel(), 100e-6, gain_n_per_m=0.0, max_force_n=1e-6,
                                   estimator_mode="command_aware", flow_feedforward=True,
                                   gravity_compensation_n=hold)
    drift = np.array([3e-3, -1e-3, -5e-3])  # flow plus settling, as the estimator sees it
    navigation.estimator, navigation.tracking_valid = StubEstimator(drift), True
    output = navigation.step(0.01, [])
    assert output.reason == "safe"
    # The hold covers the known weight; feedforward covers the rest. The sum cancels the drift.
    np.testing.assert_allclose(output.force_n, -GAMMA * drift, rtol=1e-12)


def test_feedforward_respects_the_force_cap():
    navigation = BiplaneNavigation(YVessel(), 100e-6, gain_n_per_m=0.0, max_force_n=1e-9,
                                   estimator_mode="command_aware", flow_feedforward=True)
    navigation.estimator, navigation.tracking_valid = StubEstimator([0.3, 0, 0]), True
    assert np.linalg.norm(navigation.step(0.01, []).force_n) == pytest.approx(1e-9)


@pytest.mark.parametrize("change", [{"flow_feedforward": True},  # kinematic estimator
                                    {"model_drag_error": -1.0}, {"model_drag_error": float("nan")}])
def test_invalid_delay_aware_options_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, **change))


def test_model_drag_error_is_reported_and_off_by_default():
    assert "physics" not in run_trial(TrialConfig(duration_s=0.2))["summary"]
    physics = run_trial(TrialConfig(duration_s=0.2, model_drag_error=0.2))["summary"]["physics"]
    assert physics["model_drag_error"] == 0.2


def test_policy_configs_and_gains():
    config = cell_config(0.99, 15.0, "target_occluded", "P5_feedforward_prediction", "lower", 3, 0.2)
    assert config.estimator_mode == "command_aware" and config.flow_feedforward
    assert config.prediction_horizon_s == pytest.approx(observation_delay_s(config)) == pytest.approx(0.05 + 1 / 15)
    assert config.gravity_compensation and config.occluded_branch == "lower"
    assert config.gain_n_per_m == pytest.approx(GAIN_FRACTION * GAMMA * 1.2 / 0.01)  # actuation-limited
    base = cell_config(0.9, 7.5, "patent", BASELINE, "upper", 0)
    assert base.estimator_mode == "kinematic" and not base.flow_feedforward and base.prediction_horizon_s == 0
    assert base.gain_n_per_m == pytest.approx(GAIN_FRACTION * GAMMA / (0.05 + 1 / 7.5))
    assert policy_gain(base, "actuation") / policy_gain(base, "delay") == pytest.approx((0.05 + 1 / 7.5) / 0.01)
    assert len(cells((0, 1, 2))) == 2 * 3 * 2 * len(POLICIES) * 2 * 3


def test_baseline_matches_experiment_22_archive():
    """P0 is experiment 22's gated_delay_gain_hold policy on the composite particle."""
    exp22 = json.loads((RESULTS / "physiological_sweep/trials.json").read_text())
    exp23 = json.loads((RESULTS / "delay_aware_control/pilot/trials.json").read_text())
    key = ("flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in exp22
                 if r["material"] == "composite" and r["policy"] == "gated_delay_gain_hold"}
    baseline = [r for r in exp23 if r["policy"] == BASELINE]
    assert len(baseline) == 2 * 3 * 2 * 2 * 3
    for r in baseline:
        old = reference[tuple(r[k] for k in key)]
        for field in ("target_success", "wall_collision", "wrong_branch", "frames_used"):
            assert r[field] == old[field], field
        assert r["closest_target_approach_m"] == pytest.approx(old["closest_target_approach_m"], rel=1e-8)


@pytest.mark.parametrize("cell", [
    # Held-out: the predictor with the actuation-limited gain enters the occluded branch.
    dict(flow_reduction=0.99, frame_rate_hz=15.0, occlusion="target_occluded", policy="P2_predictor_fast_gain",
         branch="lower", seed=3, model_drag_error=0.0),
    # Held-out regression: wall prediction at 7.5 fps stops near the closed outlet cap.
    dict(flow_reduction=0.99, frame_rate_hz=7.5, occlusion="patent", policy="P4_fast_wall_prediction",
         branch="upper", seed=3, model_drag_error=0.0),
])
def test_archived_heldout_cells_reproduce(cell):
    archive = json.loads((RESULTS / "delay_aware_control/heldout/trials.json").read_text())
    reference = next(r for r in archive if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used",
                "terminal_wall_feature", "reason_counts"):
        assert record[key] == reference[key], key
    for key in ("elapsed_time_s", "closest_target_approach_m", "peak_force_fraction"):
        assert record[key] == pytest.approx(reference[key], rel=1e-8, abs=1e-15), key


def test_paired_changes_count_rescues_and_regressions():
    base = dict(model_drag_error=0.0, flow_reduction=0.99, frame_rate_hz=15.0, occlusion="patent", branch="upper")
    records = [dict(base, seed=0, policy=BASELINE, target_success=False, closest_target_approach_m=5e-3),
               dict(base, seed=1, policy=BASELINE, target_success=True, closest_target_approach_m=4e-4),
               dict(base, seed=0, policy="P2_predictor_fast_gain", target_success=True, closest_target_approach_m=4e-4),
               dict(base, seed=1, policy="P2_predictor_fast_gain", target_success=False, closest_target_approach_m=1e-3)]
    (row,) = paired_changes(records)
    assert (row["rescued"], row["regressed"], row["both_success"], row["both_fail"]) == (1, 1, 0, 0)
    assert row["median_closest_change_m"] == pytest.approx((-4.6e-3 + 6e-4) / 2)
