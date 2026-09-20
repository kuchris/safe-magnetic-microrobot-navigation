from dataclasses import replace
import csv
import json

import numpy as np
import pytest

from src.benchmark import aggregate_trials, run_benchmark, save_benchmark, wilson_interval
from src.experiment import TrialConfig, run_trial


def test_wilson_interval_including_zero_observed_failures():
    np.testing.assert_allclose(wilson_interval(0, 10), [0, 0.2775328], atol=1e-7)
    np.testing.assert_allclose(wilson_interval(10, 10), [0.7224672, 1], atol=1e-7)
    np.testing.assert_allclose(wilson_interval(5, 10), [0.2365931, 0.7634069], atol=1e-7)
    with pytest.raises(ValueError):
        wilson_interval(0, 0)


def test_policy_ablation_keeps_force_cap_and_stale_estimator():
    config = TrialConfig(duration_s=0.5, latency_s=0.25, max_force_n=1e-11)
    passive, ungated, gated = [run_trial(replace(config, control_mode=mode))
                               for mode in ("passive", "ungated", "gated")]
    for result in (passive, gated):
        np.testing.assert_array_equal(result["history"]["force_n"], 0)
    h = ungated["history"]
    np.testing.assert_array_equal(h["force_n"][h["time_s"] < 0.25], 0)
    assert np.any(np.linalg.norm(h["force_n"], axis=1) > 0)
    assert ungated["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
    assert "actuation_limit" in h["reason"]
    assert passive["summary"]["safety_stop_rate"] == 0
    assert gated["summary"]["safety_stop_rate"] == 1


def test_ungated_continues_during_dropout_but_cannot_start_without_observations():
    config = TrialConfig(duration_s=0.5, latency_s=0,
                         dropout_intervals=((0.1, 0.5),), control_mode="ungated")
    result = run_trial(config)
    h = result["history"]
    assert np.any(np.linalg.norm(h["force_n"][h["time_s"] > 0.3], axis=1) > 0)
    missing = run_trial(replace(config, dropout_probability=1))
    np.testing.assert_array_equal(missing["history"]["force_n"], 0)
    assert missing["summary"]["position_3sigma_coverage"] is None
    assert missing["summary"]["localization_availability"] == 0
    valid = np.all(np.isfinite(h["estimated_position_m"]), axis=1)
    error = np.linalg.norm(h["true_position_m"][valid] - h["estimated_position_m"][valid], axis=1)
    assert result["summary"]["position_3sigma_coverage"] == np.mean(error <= 3 * h["sigma_m"][valid])


def test_benchmark_pairing_reproducibility_and_saved_outputs(tmp_path):
    config = TrialConfig(duration_s=0.1)
    result = run_benchmark(seeds=(2, 3), scenarios=("nominal",), base_config=config)
    assert result == run_benchmark(seeds=(2, 3), scenarios=("nominal",), base_config=config)
    assert len(result["trials"]) == 12 and len(result["aggregates"]) == 6
    assert {(r["config"]["branch"], r["config"]["control_mode"], r["config"]["seed"])
            for r in result["trials"]} == {(b, m, s) for b in ("upper", "lower")
                                            for m in ("passive", "ungated", "gated") for s in (2, 3)}
    save_benchmark(result, tmp_path)
    saved = json.loads((tmp_path / "benchmark.json").read_text())
    assert saved["aggregates"] == result["aggregates"]
    with (tmp_path / "trials.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 12
    report = (tmp_path / "report.md").read_text()
    assert "N/A" in report and "95% Wilson" in report


def test_aggregation_counts_trials_and_excludes_missing_metrics():
    result = run_benchmark(seeds=(0,), scenarios=("nominal",),
                           base_config=TrialConfig(duration_s=0.01))
    first = result["trials"][0]
    second = {**first, "summary": {**first["summary"], "target_success": True,
                                  "navigation_time_s": 4.0, "position_3sigma_coverage": 0.5}}
    group = aggregate_trials([first, second])[0]
    assert group["outcomes"]["target_success"]["rate"] == 0.5
    assert group["metrics"]["navigation_time_s"]["n"] == 1
    assert group["metrics"]["navigation_time_s"]["median"] == 4
    assert group["metrics"]["position_3sigma_coverage"]["n"] == 1
    assert group["metrics"]["localization_RMSE_m"]["n"] == 0


@pytest.mark.parametrize("options", [{"seeds": []}, {"seeds": [1, 1]}, {"seeds": [-1]},
                                     {"scenarios": []}, {"scenarios": ["unknown"]}])
def test_invalid_benchmark_selection(options):
    with pytest.raises(ValueError):
        run_benchmark(**options)


def test_invalid_control_mode():
    with pytest.raises(ValueError, match="control_mode"):
        run_trial(TrialConfig(control_mode="unknown"))
