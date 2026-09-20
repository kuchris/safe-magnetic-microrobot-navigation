import numpy as np

from src.experiment import TrialConfig, run_trial
from src.failure_analysis import analyze_trial, wall_feature
from src.flow import centerline_flow
from src.vessel import YVessel


def test_capsule_sidewall_and_closed_outlet_are_distinguished():
    vessel = YVessel()
    assert wall_feature(np.array([0.005, 0, 0]), vessel) == "none"
    assert wall_feature(np.array([0.005, 0.0016, 0]), vessel) == "capsule_sidewall_proxy"
    branch = vessel.segments[1]
    direction = branch.end_m - branch.start_m
    direction /= np.linalg.norm(direction)
    assert wall_feature(branch.end_m + 0.0015 * direction, vessel) == "closed_outlet_cap_proxy"
    assert wall_feature(np.array([-0.0016, 0, 0]), vessel) == "closed_inlet_cap_proxy"


def test_flow_direction_has_a_discontinuity_at_y_zero_after_junction():
    upper = centerline_flow([0.010001, 1e-9, 0])
    lower = centerline_flow([0.010001, -1e-9, 0])
    assert upper[1] > 0 and lower[1] < 0
    np.testing.assert_array_equal(centerline_flow([0.010001, 0, 0]), upper)
    np.testing.assert_array_equal(centerline_flow([0.009999, -1e-9, 0]), [0.001, 0, 0])


def test_missing_events_and_non_actuating_waypoint_logging():
    result = run_trial(TrialConfig(duration_s=0.1, dropout_probability=1))
    h = result["history"]
    assert len(h["waypoint_index"]) == len(h["time_s"])
    np.testing.assert_array_equal(h["waypoint_index"], 0)
    analysis = analyze_trial(result)
    assert analysis["junction_crossing"] is None
    assert analysis["wrong_branch_confirmed"] is None
    assert analysis["first_wall_violation"] is None
    assert analysis["terminal_wall_feature"] == "none"
    assert analysis["persistent_stop_from_s"] == 0


def test_junction_event_records_truth_without_requiring_an_estimate():
    start = (0.010001, 1e-6, 0)
    result = run_trial(TrialConfig(start_m=start, duration_s=0.005,
                                  dropout_probability=1, branch="lower"))
    event = analyze_trial(result)["junction_crossing"]
    assert event["time_s"] == 0
    assert event["estimated_position_m"] is None
    np.testing.assert_array_equal(event["position_m"], start)
    np.testing.assert_array_equal(event["force_n"], 0)
    np.testing.assert_array_equal(event["nominal_net_velocity_m_s"], event["prescribed_flow_m_s"])
    assert event["prescribed_flow_m_s"][1] > 0
