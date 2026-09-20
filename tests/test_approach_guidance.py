from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.planner import YWaypointPlanner
from src.vessel import YVessel


def test_approach_route_is_symmetric_internal_and_rejoins_centerline():
    vessel = YVessel()
    baseline = YWaypointPlanner(vessel)
    upper = YWaypointPlanner(vessel, approach_offset_m=0.4e-3)
    lower = YWaypointPlanner(vessel, "lower", approach_offset_m=0.4e-3)
    np.testing.assert_allclose(upper.waypoints * [1, -1, -1], lower.waypoints)
    np.testing.assert_array_equal(upper.waypoints[0], baseline.waypoints[0])
    np.testing.assert_array_equal(upper.waypoints[-1], vessel.upper_target)
    junction = np.argmin(np.abs(upper.waypoints[:, 0] - 0.01))
    assert np.linalg.norm(upper.waypoints[junction, 1:]) == pytest.approx(0.4e-3)
    assert np.any(upper.waypoints[upper.waypoints[:, 0] < 0.01, 1] > 0)
    # Check interpolated segments, including the bends, for the toy particle.
    for a, b in zip(upper.waypoints, upper.waypoints[1:]):
        for p in np.linspace(a, b, 10):
            assert vessel.clearance(p, 0.1e-3) >= 1e-3 - 1e-12


@pytest.mark.parametrize("offset", [-1, np.nan, np.inf, 1.5e-3])
def test_invalid_offset_is_rejected(offset):
    with pytest.raises(ValueError):
        YWaypointPlanner(YVessel(), approach_offset_m=offset)


@pytest.mark.parametrize("branch,seed,mode,noise,burst", [
    ("lower", 0, "gated", 1, ((8.0, 8.75),)),
    ("lower", 2, "ungated", 1, ((8.0, 8.75),)),
    ("lower", 0, "gated", 12, ()),
    ("upper", 1, "gated", 12, ()),
])
def test_approach_guidance_recovers_known_branch_failures(branch, seed, mode, noise, burst):
    result = run_trial(TrialConfig(branch=branch, seed=seed, control_mode=mode,
        noise_sigma_px=noise, dropout_intervals=burst, approach_offset_m=0.4e-3))
    s, h = result["summary"], result["history"]
    assert s["target_success"] and not s["wrong_branch"] and not s["wall_collision"]
    assert s["maximum_force_n"] <= 3e-9 * (1 + 1e-12)
    stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    np.testing.assert_array_equal(h["force_n"][stopped], 0)
    crossing = np.flatnonzero(h["true_position_m"][:, 0] >= 0.01)[0]
    assert h["true_position_m"][crossing, 1] * (1 if branch == "upper" else -1) > 0.1e-3


def test_guidance_does_not_bypass_stale_gate_or_change_passive_motion():
    base = TrialConfig(duration_s=0.5, start_m=(9e-3, 0, 0), latency_s=0.25)
    original = run_trial(base)
    guided = run_trial(replace(base, approach_offset_m=0.4e-3))
    np.testing.assert_array_equal(original["history"]["true_position_m"], guided["history"]["true_position_m"])
    np.testing.assert_array_equal(guided["history"]["force_n"], 0)
    passive = run_trial(replace(base, control_mode="passive", latency_s=0))
    passive_guided = run_trial(replace(base, control_mode="passive", latency_s=0, approach_offset_m=0.4e-3))
    assert passive["summary"] == passive_guided["summary"]
