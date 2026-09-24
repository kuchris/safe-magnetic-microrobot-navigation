import numpy as np
import pytest

from src.feasibility import (Fluid, Material, Vessel, closed_form_gradient, gravity_hold_gradient,
                             lateral_path_integral, required_gradient_branch_entry,
                             schiller_naumann_factor, sedimentation_speed, stokes_drag_coefficient,
                             validity, volume, wall_factor_perpendicular)


def test_uncorrected_center_start_matches_closed_form():
    vessel = Vessel()
    radius = 1e-6  # negligible radius so the end point approaches the wall
    numeric = required_gradient_branch_entry(radius, vessel, wall_correction=False,
                                             inertia_correction=False)["gradient_t_m"]
    np.testing.assert_allclose(numeric, closed_form_gradient(radius, vessel), rtol=1e-4)


def test_center_integral_equals_four_thirds_u_r():
    vessel = Vessel(radius_m=2e-3, mean_speed_m_s=0.1)
    integral = lateral_path_integral(1e-9, vessel, wall_correction=False, samples=20001)
    np.testing.assert_allclose(integral, 4 / 3 * 0.1 * 2e-3, rtol=1e-6)


def test_gradient_scaling_with_speed_length_and_radius():
    base = Vessel()
    g = closed_form_gradient(1e-4, base)
    assert closed_form_gradient(1e-4, Vessel(base.radius_m, 2 * base.mean_speed_m_s,
                                             base.approach_length_m)) == pytest.approx(2 * g)
    assert closed_form_gradient(1e-4, Vessel(base.radius_m, base.mean_speed_m_s,
                                             2 * base.approach_length_m)) == pytest.approx(g / 2)
    assert closed_form_gradient(2e-4, base) == pytest.approx(g / 4)


def test_corrections_only_increase_requirement():
    vessel = Vessel()
    plain = required_gradient_branch_entry(1e-4, vessel, wall_correction=False, inertia_correction=False)
    full = required_gradient_branch_entry(1e-4, vessel)
    far = required_gradient_branch_entry(1e-4, vessel, start="far_wall")
    assert plain["gradient_t_m"] < full["gradient_t_m"] < far["gradient_t_m"]


def test_zero_flow_requires_zero_steering_gradient():
    result = required_gradient_branch_entry(1e-4, Vessel(mean_speed_m_s=0.0))
    assert result["gradient_t_m"] == 0.0


def test_gravity_hold_is_size_independent_and_balances_weight():
    material, fluid = Material(), Fluid()
    gradient = gravity_hold_gradient(material, fluid)
    for radius in (1e-5, 1e-4):
        weight = (material.density_kg_m3 - fluid.density_kg_m3) * 9.81 * volume(radius)
        np.testing.assert_allclose(volume(radius) * material.magnetization_a_m * gradient, weight)
    assert gravity_hold_gradient(Material(density_kg_m3=900.0), fluid) == 0.0


def test_sedimentation_reduces_to_stokes_for_small_particles():
    material, fluid, radius = Material(), Fluid(), 1e-6
    weight = (material.density_kg_m3 - fluid.density_kg_m3) * 9.81 * volume(radius)
    np.testing.assert_allclose(sedimentation_speed(radius), weight / stokes_drag_coefficient(radius, fluid),
                               rtol=1e-3)


def test_schiller_naumann_and_wall_factor_limits():
    assert schiller_naumann_factor(0.0) == 1.0
    assert schiller_naumann_factor(10.0) > 1.0
    assert wall_factor_perpendicular(1e-4, 1.0) == pytest.approx(1.0, abs=1e-3)
    with pytest.raises(ValueError):
        wall_factor_perpendicular(1e-4, 1e-4)
    with pytest.raises(ValueError):
        schiller_naumann_factor(-1.0)


def test_magnetic_fraction_scales_requirement():
    vessel = Vessel()
    full = required_gradient_branch_entry(1e-4, vessel)["gradient_t_m"]
    half = required_gradient_branch_entry(1e-4, vessel, Material(magnetic_volume_fraction=0.5))["gradient_t_m"]
    assert half == pytest.approx(2 * full)


def test_validity_numbers_grow_with_radius():
    vessel = Vessel()
    small, large = validity(2e-5, vessel), validity(2e-4, vessel)
    assert small["stokes_number"] < large["stokes_number"]
    assert large["stokes_number"] == pytest.approx(100 * small["stokes_number"])


@pytest.mark.parametrize("kwargs", [{"radius_m": 0}, {"mean_speed_m_s": -1}, {"approach_length_m": 0}])
def test_invalid_vessel(kwargs):
    with pytest.raises(ValueError):
        Vessel(**kwargs)


def test_particle_must_fit_and_start_is_checked():
    with pytest.raises(ValueError):
        lateral_path_integral(1e-3, Vessel(radius_m=1.5e-3))
    with pytest.raises(ValueError):
        lateral_path_integral(1e-4, Vessel(), start="upstream")
    with pytest.raises(ValueError):
        Material(magnetic_volume_fraction=0.0)
