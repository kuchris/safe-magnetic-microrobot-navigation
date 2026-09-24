from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.feasibility import Fluid, Material, gravity_hold_gradient, sedimentation_speed, volume

R = 100e-6
GAMMA = 6 * np.pi * 3.5e-3 * R
# Quiescent fluid, particle on the parent axis: only gravity (and any command) moves it.
STILL = TrialConfig(flow_speed_m_s=0.0, start_m=(5e-3, 0.0, 0.0), particle_radius_m=R,
                    gravity_m_s2=9.81, control_mode="passive")
# A light composite (2000 kg/m^3, assumed) settles slowly enough for frames to arrive first.
LIGHT = replace(STILL, particle_density_kg_m3=2000.0, duration_s=0.3)


def weight(density=7500.0):
    return (density - 1060.0) * volume(R) * 9.81


def test_gravity_off_keeps_legacy_trial():
    result = run_trial(TrialConfig(duration_s=0.3))
    assert "physics" not in result["summary"] and "sedimentation_risk" not in result["history"]


def test_overdamped_particle_settles_at_stokes_speed():
    result = run_trial(replace(STILL, duration_s=0.02))
    h = result["history"]
    np.testing.assert_allclose(h["true_position_m"][-1], [5e-3, 0, -weight() / GAMMA * 0.02], rtol=1e-9)
    physics = result["summary"]["physics"]
    assert physics["net_weight_n"] == pytest.approx(weight())
    assert physics["stokes_settling_speed_m_s"] == pytest.approx(0.0401, rel=1e-2)  # ~40 mm/s


def test_inertial_particle_reaches_finite_re_settling_speed():
    result = run_trial(replace(STILL, duration_s=0.03, particle_inertia=True))
    settled = -result["history"]["particle_velocity_m_s"][-1, 2]
    assert settled == pytest.approx(sedimentation_speed(R, Material(), Fluid()), rel=1e-3)


def test_buoyant_particle_rises_along_the_opposite_direction():
    result = run_trial(replace(STILL, duration_s=0.02, particle_density_kg_m3=900.0))
    assert result["history"]["true_position_m"][-1, 2] > 0


def test_gravity_direction_is_normalized_and_configurable():
    result = run_trial(replace(STILL, duration_s=0.02, gravity_direction=(0.0, 2.0, 0.0)))
    np.testing.assert_allclose(result["history"]["true_position_m"][-1],
                               [5e-3, weight() / GAMMA * 0.02, 0], rtol=1e-9)


def test_hold_gradient_matches_feasibility_and_cap_check():
    physics = run_trial(replace(STILL, duration_s=0.01, max_gradient_t_m=1.0))["summary"]["physics"]
    assert physics["gravity_hold_gradient_t_m"] == pytest.approx(gravity_hold_gradient(), rel=1e-3)
    assert physics["gravity_hold_gradient_t_m"] == pytest.approx(0.063, rel=0.01)  # docs/14
    assert physics["can_hold_against_gravity"]
    weak = run_trial(replace(STILL, duration_s=0.01, max_gradient_t_m=0.04))["summary"]["physics"]
    assert not weak["can_hold_against_gravity"]  # clinical MRI imaging gradients (docs/14)


def test_sedimentation_check_is_diagnostic_and_flags_before_contact():
    plain = run_trial(LIGHT)
    checked = run_trial(replace(LIGHT, sedimentation_check=True))
    np.testing.assert_array_equal(checked["history"]["true_position_m"], plain["history"]["true_position_m"])
    physics, h = checked["summary"]["physics"], checked["history"]
    assert physics["sedimentation_risk_fraction"] > 0
    first = physics["first_sedimentation_risk_s"]
    assert first >= 0.05  # needs an estimate; the first frame arrives at 50 ms
    contact = h["time_s"][np.argmax(h["true_clearance_m"] <= 0)] if (h["true_clearance_m"] <= 0).any() else np.inf
    assert first < contact
    assert np.isnan(h["sedimentation_margin_m"][h["time_s"] < 0.05]).all()


def test_gravity_compensation_holds_when_the_cap_allows():
    held = run_trial(replace(LIGHT, control_mode="gated", max_gradient_t_m=1.0, gravity_compensation=True))
    sinking = run_trial(replace(LIGHT, control_mode="gated", max_gradient_t_m=1.0))
    assert held["summary"]["physics"]["can_hold_against_gravity"]

    def z_drift(result):
        h = result["history"]
        window = (h["time_s"] >= 0.1) & (h["time_s"] <= 0.2)
        return abs(h["true_position_m"][window][-1, 2] - h["true_position_m"][window][0, 2])
    assert z_drift(held) < 0.05 * z_drift(sinking)
    h = held["history"]
    np.testing.assert_allclose(h["force_n"][h["time_s"] < 0.05], 0)  # no tracking yet: no hold
    assert h["force_n"][-1, 2] == pytest.approx(weight(2000.0), rel=0.05)


def test_gravity_compensation_is_clipped_by_the_cap_and_skipped_when_passive():
    clipped = run_trial(replace(LIGHT, control_mode="gated", gravity_compensation=True))  # 3 nN toy cap
    assert not clipped["summary"]["physics"]["can_hold_against_gravity"]
    assert clipped["summary"]["maximum_force_n"] <= 3e-9 * (1 + 1e-12)
    passive = run_trial(replace(LIGHT, max_gradient_t_m=1.0, gravity_compensation=True))
    assert passive["summary"]["maximum_force_n"] == 0


@pytest.mark.parametrize("change", [{"gravity_m_s2": -1.0}, {"gravity_direction": (0.0, 0.0, 0.0)},
                                    {"gravity_m_s2": 0.0, "sedimentation_check": True},
                                    {"gravity_m_s2": 0.0, "gravity_compensation": True},
                                    {"sedimentation_horizon_s": 0.0}])
def test_invalid_gravity_settings_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(replace(STILL, duration_s=0.01, **change))
