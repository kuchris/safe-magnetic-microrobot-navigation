from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.flow import poiseuille_flow, prescribed_flow, smooth_junction_flow
from src.vessel import YVessel

U = 0.3  # M1-like cross-sectional mean [m/s], docs/14
R = 1.5e-3


def test_centerline_carries_twice_the_mean_and_wall_is_zero():
    np.testing.assert_allclose(poiseuille_flow([5e-3, 0, 0], U), [2 * U, 0, 0], rtol=1e-12)
    for point in ([5e-3, R, 0], [5e-3, 0, -R], [5e-3, 2 * R, 0]):
        np.testing.assert_array_equal(poiseuille_flow(point, U), np.zeros(3))


def test_cross_sectional_mean_equals_u_in_parent_segment():
    radial = (np.arange(400) + 0.5) / 400 * R
    angles = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    flux = 0.0
    for rho in radial:
        axial = np.mean([poiseuille_flow([5e-3, rho * np.cos(a), rho * np.sin(a)], U)[0]
                         for a in angles])
        flux += axial * 2 * np.pi * rho * (R / 400)
    assert flux / (np.pi * R ** 2) == pytest.approx(U, rel=1e-4)


def test_profile_is_parabolic_and_bounded():
    for rho in np.linspace(0, R, 7):
        speed = np.linalg.norm(poiseuille_flow([5e-3, rho, 0], U))
        assert speed == pytest.approx(2 * U * (1 - (rho / R) ** 2), abs=1e-12)
    rng = np.random.default_rng(0)
    for point in rng.uniform([0, -8e-3, -4e-3], [20e-3, 8e-3, 4e-3], (500, 3)):
        speed = np.linalg.norm(poiseuille_flow(point, U))
        assert 0 <= speed <= 2 * U * (1 + 1e-12)


def test_direction_follows_smooth_junction_model():
    for point in ([12e-3, 1e-3, 0.5e-3], [14e-3, -2e-3, -1e-3]):
        flow = poiseuille_flow(point, U)
        unit = smooth_junction_flow(point, speed_m_s=1.0)
        np.testing.assert_allclose(flow / np.linalg.norm(flow), unit, rtol=1e-12)


def test_field_is_continuous_across_junction_and_capsule_seams():
    vessel = YVessel()
    rng = np.random.default_rng(1)
    for point in rng.uniform([9e-3, -1.5e-3, -1e-3], [13e-3, 1.5e-3, 1e-3], (300, 3)):
        if vessel.clearance(point) <= 0:
            continue
        step = rng.normal(size=3)
        step *= 1e-9 / np.linalg.norm(step)
        jump = np.linalg.norm(poiseuille_flow(point + step, U) - poiseuille_flow(point, U))
        assert jump < 2 * U * 1e-4


def test_prescribed_flow_dispatches_and_rejects_unknown_models():
    np.testing.assert_array_equal(prescribed_flow([5e-3, 0.2e-3, 0], U, "poiseuille"),
                                  poiseuille_flow([5e-3, 0.2e-3, 0], U))
    with pytest.raises(ValueError):
        prescribed_flow([0, 0, 0], U, "cfd")
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, flow_model="cfd"))


def test_physiological_passive_axis_transit_uses_centerline_speed():
    config = TrialConfig(duration_s=0.01, flow_model="poiseuille", flow_speed_m_s=U,
                         control_mode="passive")
    result = run_trial(config)
    physics = result["summary"]["physics"]
    assert physics["dt_s"] <= 0.02 * R / (2 * U) * (1 + 1e-12)
    assert physics["maximum_step_radius_fraction"] <= 0.02 * (1 + 1e-9)
    np.testing.assert_allclose(result["history"]["true_position_m"][-1],
                               [0.5e-3 + 2 * U * 0.01, 0, 0], rtol=1e-9, atol=1e-12)


def test_auto_dt_accounts_for_capped_drift_and_step_fraction():
    base = TrialConfig(duration_s=0.002, flow_model="poiseuille", flow_speed_m_s=U,
                       particle_radius_m=100e-6, max_gradient_t_m=1.0)
    physics = run_trial(base)["summary"]["physics"]
    drag = 6 * np.pi * 3.5e-3 * 100e-6
    assert physics["dt_s"] == pytest.approx(0.02 * R / (2 * U + physics["force_cap_n"] / drag))
    finer = run_trial(replace(base, max_step_radius_fraction=0.01))["summary"]["physics"]
    assert finer["dt_s"] == pytest.approx(physics["dt_s"] / 2)
    assert finer["maximum_step_radius_fraction"] <= 0.01 * (1 + 1e-9)


def test_legacy_models_keep_configured_dt_and_summary_keys():
    for model in ("piecewise", "smooth"):
        result = run_trial(TrialConfig(duration_s=0.5, flow_model=model))
        np.testing.assert_allclose(np.diff(result["history"]["time_s"]), 0.005, rtol=1e-9)
        assert "physics" not in result["summary"]


def test_slow_poiseuille_keeps_configured_dt():
    result = run_trial(TrialConfig(duration_s=0.5, flow_model="poiseuille"))
    assert result["summary"]["physics"]["dt_s"] == 0.005  # 0.6 mm/s never binds


@pytest.mark.parametrize("fraction", [0.0, -0.1])
def test_invalid_step_fraction_is_rejected(fraction):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, flow_model="poiseuille", max_step_radius_fraction=fraction))
