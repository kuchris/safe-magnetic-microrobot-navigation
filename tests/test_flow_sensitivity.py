from copy import deepcopy

import numpy as np

from src.experiment import TrialConfig, run_trial
from src.flow_sensitivity import aggregate_records, trial_record


def test_timeout_and_holding_demand_are_separate_from_navigation_outcome():
    r = trial_record(run_trial(TrialConfig(duration_s=0.02, dropout_probability=1)))
    assert r["timeout"] and not r["summary"]["wall_collision"]
    assert r["flow_holding_limit_exceeded_fraction"] == 1
    assert r["force_saturation_fraction"] == 0
    assert r["terminal_wall_feature"] == "none"


def test_sensitivity_aggregation_separates_routes_and_reports_trial_counts():
    first = trial_record(run_trial(TrialConfig(duration_s=0.02)))
    second = deepcopy(first)
    second["config"]["seed"] += 1
    second["summary"]["target_success"] = True
    second["summary"]["navigation_time_s"] = 0.02
    second["timeout"] = False
    guided = deepcopy(first)
    guided["config"]["approach_offset_m"] = 0.4e-3
    groups = aggregate_records([first, second, guided])
    assert len(groups) == 2
    assert groups[0]["outcomes"]["target_success"]["rate"] == 0.5
    assert groups[0]["outcomes"]["timeout"]["count"] == 1
    assert groups[0]["metrics"]["navigation_time_s"]["n"] == 1
    assert groups[1]["trials"] == 1
    assert groups[1]["outcomes"]["target_success"]["wilson_95"][1] > 0


def test_terminal_only_trial_does_not_invent_flow_demand_samples():
    r = trial_record(run_trial(TrialConfig(start_m=(0.005, 0.01, 0))))
    assert r["summary"]["wall_collision"] and not r["timeout"]
    assert r["flow_holding_limit_exceeded_fraction"] is None
    assert r["force_saturation_fraction"] is None
    assert not np.isnan(aggregate_records([r])[0]["outcomes"]["wall_collision"]["rate"])
