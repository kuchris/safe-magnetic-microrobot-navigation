from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.feasibility import Fluid, Material, Vessel, relaxation_time, sedimentation_speed, validity, volume
from src.particle import InertialParticle, Particle

ETA = 3.5e-3
NDFEB, BLOOD = 7500.0, 1060.0


def particle(radius=100e-6, rho_p=NDFEB, rho_f=BLOOD, velocity=(0, 0, 0)):
    return InertialParticle(radius, ETA, rho_p, rho_f, np.zeros(3), velocity)


def test_relaxation_time_matches_feasibility_with_added_mass():
    p = particle()
    assert p.relaxation_time_s == pytest.approx(relaxation_time(100e-6, Material(), Fluid()))
    assert p.relaxation_time_s == pytest.approx(5.1e-3, rel=0.01)  # ~5 ms at r = 100 um


def test_low_reynolds_step_response_has_time_constant_tau():
    # r = 10 um in 10 um/s: Re ~ 6e-5, so the Schiller-Naumann factor is 1 + 2e-4.
    p = particle(radius=10e-6)
    tau, u = p.relaxation_time_s, np.array([1e-5, 0, 0])
    times = np.arange(1, 301) * tau / 100
    speeds = []
    for _ in times:
        p.step(tau / 100, u, np.zeros(3))
        speeds.append(p.velocity_m_s[0])
    np.testing.assert_allclose(speeds, u[0] * (1 - np.exp(-times / tau)), rtol=1e-3)


def test_one_large_step_equals_many_small_steps_at_low_reynolds():
    u, force = np.array([1e-3, 2e-4, 0]), np.array([0, 1e-12, 0])
    coarse, fine = particle(radius=10e-6), particle(radius=10e-6)
    coarse.step(1e-3, u, force)
    for _ in range(1000):
        fine.step(1e-6, u, force)
    np.testing.assert_allclose(coarse.position_m, fine.position_m, rtol=1e-4, atol=1e-15)
    np.testing.assert_allclose(coarse.velocity_m_s, fine.velocity_m_s, rtol=1e-4, atol=1e-12)


def test_vanishing_mass_reduces_to_overdamped_model():
    u, force = np.array([1e-3, 0, 5e-4]), np.array([0, 2e-12, 0])
    light, plain = particle(radius=10e-6, rho_p=1e-12, rho_f=1e-12), Particle(10e-6, ETA)
    for _ in range(10):
        light.step(1e-3, u, force)
        plain.step(1e-3, u, force)
    np.testing.assert_allclose(light.position_m, plain.position_m, rtol=1e-12)


def test_terminal_settling_matches_schiller_naumann_estimate():
    # r = 100 um NdFeB: Re ~ 1, so this exercises the finite-Re drag factor.
    weight = (NDFEB - BLOOD) * 9.81 * volume(100e-6)
    p = particle()
    for _ in range(2000):
        p.step(1e-4, np.zeros(3), np.array([0, 0, -weight]))
    expected = sedimentation_speed(100e-6, Material(), Fluid())
    assert -p.velocity_m_s[2] == pytest.approx(expected, rel=1e-6)
    assert p.slip_reynolds(np.zeros(3)) > 0.5


def test_stable_for_steps_much_longer_than_tau():
    p = particle(radius=10e-6)
    p.step(1.0, np.array([1e-3, 0, 0]), np.zeros(3))  # dt ~ 5000 tau
    np.testing.assert_allclose(p.velocity_m_s, [1e-3, 0, 0], rtol=1e-12)
    assert np.isfinite(p.position_m).all()


@pytest.mark.parametrize("field", ["radius_m", "density_kg_m3", "fluid_density_kg_m3"])
def test_invalid_particle_parameters_are_rejected(field):
    values = {"radius_m": 1e-4, "viscosity_pa_s": ETA, "density_kg_m3": NDFEB, "fluid_density_kg_m3": BLOOD}
    values[field] = 0.0
    with pytest.raises(ValueError):
        InertialParticle(**values)


def test_inertia_off_keeps_history_and_summary_keys():
    result = run_trial(TrialConfig(duration_s=0.3))
    assert "particle_velocity_m_s" not in result["history"] and "physics" not in result["summary"]


def test_inertia_on_reports_stokes_number_and_slip():
    config = TrialConfig(duration_s=0.3, particle_inertia=True)
    result = run_trial(config)
    physics = result["summary"]["physics"]
    tau = relaxation_time(config.particle_radius_m, Material(), Fluid())
    assert physics["relaxation_time_s"] == pytest.approx(tau)
    expected = validity(config.particle_radius_m, Vessel(mean_speed_m_s=config.flow_speed_m_s))
    assert physics["stokes_number"] == pytest.approx(expected["stokes_number"])
    assert physics["maximum_slip_reynolds"] >= 0 and physics["maximum_drag_factor"] >= 1
    assert result["history"]["particle_velocity_m_s"].shape == result["history"]["true_position_m"].shape


def test_toy_scale_inertia_barely_changes_the_trial():
    # St = tau U / L = 5.1 ms * 0.6 mm/s / 10 mm ~ 3e-4, so the path should barely change.
    base = TrialConfig(duration_s=5.0)
    plain, inertial = run_trial(base), run_trial(replace(base, particle_inertia=True))
    assert inertial["summary"]["physics"]["stokes_number"] == pytest.approx(3.06e-4, rel=1e-2)
    # Lag ~ tau * |v| ~ 3 um, plus feedback on slightly different observations.
    gap = np.linalg.norm(inertial["history"]["true_position_m"][-1] - plain["history"]["true_position_m"][-1])
    assert 0 < gap < 10e-6


def test_released_at_flow_velocity_so_axial_transit_is_unchanged():
    config = TrialConfig(duration_s=0.01, flow_model="poiseuille", flow_speed_m_s=0.3,
                         control_mode="passive", particle_inertia=True)
    result = run_trial(config)
    np.testing.assert_allclose(result["history"]["true_position_m"][-1],
                               [0.5e-3 + 2 * 0.3 * 0.01, 0, 0], rtol=1e-9, atol=1e-12)
    assert result["summary"]["physics"]["maximum_slip_m_s"] == pytest.approx(0, abs=1e-12)


def test_physiological_inertia_leaves_the_streamline_at_the_junction():
    base = TrialConfig(duration_s=0.05, flow_model="poiseuille", flow_speed_m_s=0.3,
                       particle_radius_m=100e-6, control_mode="passive", start_m=(0.5e-3, 0.3e-3, 0.15e-3))
    plain, inertial = run_trial(base), run_trial(replace(base, particle_inertia=True))
    physics = inertial["summary"]["physics"]
    assert physics["stokes_number"] > 0.1  # docs/14: overdamped model invalid here
    assert physics["maximum_slip_reynolds"] > 1
    gap = np.linalg.norm(inertial["history"]["true_position_m"][-1] - plain["history"]["true_position_m"][-1])
    assert gap > 0.05e-3
