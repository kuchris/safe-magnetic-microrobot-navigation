from dataclasses import replace

import numpy as np
import pytest

from src.disturbance_study import BUNDLES, ESTIMATORS, cell_config, cells
from src.experiment import TrialConfig, run_trial
from src.presets import physiological_config


def test_estimator_psd_defaults_to_the_old_value_and_changes_the_estimate():
    base = TrialConfig(duration_s=1.0)
    assert base.estimator_acceleration_psd == 1e-7
    a = run_trial(base)["history"]["estimated_position_m"]
    b = run_trial(replace(base, estimator_acceleration_psd=1e-5))["history"]["estimated_position_m"]
    valid = np.isfinite(a).all(axis=1)
    assert not np.allclose(a[valid], b[valid])
    with pytest.raises(ValueError):
        run_trial(replace(base, estimator_acceleration_psd=0.0))


def test_drift_feedforward_cancels_a_small_hold_bias_but_not_a_large_one():
    # Quiescent fluid, no steering gain: the only drift is the unmodeled part of the hold.
    base = physiological_config(flow_speed_m_s=0.0, duration_s=2.0, start_m=(5e-3, 0.0, 0.0),
                                gravity_compensation=True, gravity_hold_from_release=True,
                                estimator_mode="command_aware", estimator_knows_weight=True,
                                gain_saturation_distance_m=0.0, gain_n_per_m=0.0,
                                estimator_acceleration_psd=1e-5)
    # A 5% hold shortfall sinks pure NdFeB at ~2 mm/s: slow enough for frames to reveal it.
    small = replace(base, actuation_gain_error=-0.05)
    assert run_trial(small)["summary"]["wall_collision"]
    held = run_trial(replace(small, flow_feedforward=True))["summary"]
    assert not held["wall_collision"] and held["minimum_wall_clearance_m"] > 1e-3
    # A 20% shortfall (~8 mm/s) reaches the wall in ~0.2 s, before the drift can be learned.
    large = replace(base, actuation_gain_error=-0.2, flow_feedforward=True)
    assert run_trial(large)["summary"]["wall_collision"]


def test_study_configs_and_grid():
    c = cell_config(15.0, "patent", "N_P2_hold", "upper", 3, "moderate", "fast_residual_ff")
    assert c.estimator_acceleration_psd == 1e-5 and c.flow_feedforward
    assert c.gravity_hold_from_release and c.actuation_gain_error == -0.2 and c.latency_s == 0.1
    base = cell_config(15.0, "patent", "C_P2", "upper", 3, "nominal", "baseline")
    assert base.estimator_acceleration_psd == 1e-7 and not base.flow_feedforward
    assert len(cells()) == len(ESTIMATORS) * len(BUNDLES) * 72
    with pytest.raises(ValueError):
        cell_config(15.0, "patent", "C_P2", "upper", 3, "severe", "baseline")


def test_baseline_matches_experiment_29_archive():
    import json
    from pathlib import Path
    root = Path(__file__).parents[1] / "docs/results"
    exp29 = json.loads((root / "combined_perturbations/trials.json").read_text())
    exp30 = json.loads((root / "disturbance_rejection/trials.json").read_text())
    key = ("bundle", "arm", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in exp29 if r["bundle"] in BUNDLES}
    baseline = [r for r in exp30 if r["estimator"] == "baseline"]
    assert len(baseline) == len(reference) == 216
    for r in baseline:
        assert r["target_success"] == reference[tuple(r[k] for k in key)]["target_success"]


def test_archived_disturbance_cell_reproduces():
    import json
    from pathlib import Path
    from src.disturbance_study import trial_record
    archive = json.loads((Path(__file__).parents[1] / "docs/results/disturbance_rejection/trials.json").read_text())
    cell = dict(frame_rate_hz=15.0, occlusion="patent", arm="C_P2", branch="upper", seed=3, bundle="moderate",
                estimator="fast_residual_ff")
    reference = next(r for r in archive if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used", "reason_counts"):
        assert record[key] == reference[key], key
    assert record["elapsed_time_s"] == pytest.approx(reference["elapsed_time_s"], rel=1e-8)
