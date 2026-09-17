from dataclasses import replace
import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.planner import YWaypointPlanner, wrong_branch
from src.vessel import YVessel


@pytest.mark.parametrize("branch,index", [("upper", 1), ("lower", 2)])
def test_waypoints_choose_requested_branch_and_wrong_branch_detection(branch, index):
    vessel = YVessel()
    planner = YWaypointPlanner(vessel, branch)
    np.testing.assert_array_equal(planner.waypoints[-1], vessel.segments[index].end_m)
    for point in planner.waypoints:
        assert vessel.contains(point)
    assert not wrong_branch(vessel.segments[index].end_m, vessel, branch)
    assert wrong_branch(vessel.segments[3 - index].end_m, vessel, branch)
    assert not wrong_branch(vessel.segments[0].end_m, vessel, branch)
    assert not wrong_branch([10.1e-3, 0, 0], vessel, branch)


def test_complete_loss_stops_force_but_does_not_stop_flow():
    result = run_trial(TrialConfig(duration_s=0.5, dropout_probability=1))
    h, s = result["history"], result["summary"]
    np.testing.assert_array_equal(h["force_n"], np.zeros_like(h["force_n"]))
    assert s["localization_RMSE_m"] is None
    assert s["safety_stop_rate"] == 1
    assert h["true_position_m"][-1, 0] > h["true_position_m"][0, 0]


def test_seed_reproducibility_and_stale_imaging_force_zero():
    config = TrialConfig(duration_s=1, dropout_probability=0.2)
    a, b = run_trial(config), run_trial(config)
    assert a["summary"] == b["summary"]
    for key in a["history"]:
        np.testing.assert_array_equal(a["history"][key], b["history"][key])
    stale = run_trial(replace(config, latency_s=0.25))
    assert stale["summary"]["safety_stop_rate"] == 1
    np.testing.assert_array_equal(stale["history"]["force_n"], 0)


@pytest.mark.parametrize("branch", ["upper", "lower"])
def test_biplane_end_to_end_navigation_both_branches(branch):
    result = run_trial(TrialConfig(branch=branch))
    s = result["summary"]
    assert s["target_success"] and not s["wall_collision"] and not s["wrong_branch"]
    assert s["localization_RMSE_m"] < 0.2e-3
    assert s["maximum_force_n"] <= 3e-9 * (1 + 1e-12)
    h = result["history"]
    stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    np.testing.assert_array_equal(h["force_n"][stopped], 0)


def test_stale_lower_target_demonstrates_passive_wrong_branch_failure():
    result = run_trial(TrialConfig(branch="lower", latency_s=0.25))
    summary = result["summary"]
    assert not summary["target_success"] and summary["wrong_branch"]
    assert summary["safety_stop_rate"] == 1 and summary["maximum_force_n"] == 0
