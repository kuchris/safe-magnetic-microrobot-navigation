from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.flow import material_acceleration, poiseuille_flow, pulsatile_speed, womersley_number
from src.particle import InertialParticle

U, A, T = 0.3, 0.45, 1.0


def test_pulsatile_speed_mean_and_extremes():
    times = np.linspace(0, T, 10001)[:-1]
    speeds = np.array([pulsatile_speed(U, t, A, T) for t in times])
    assert speeds.mean() == pytest.approx(U, rel=1e-12)
    assert pulsatile_speed(U, T / 4, A, T) == pytest.approx(U * (1 + A))
    assert pulsatile_speed(U, 3 * T / 4, A, T) == pytest.approx(U * (1 - A))
    # Gosling pulsatility index of a sinusoid is 2A.
    assert (speeds.max() - speeds.min()) / speeds.mean() == pytest.approx(2 * A, rel=1e-6)
    assert all(pulsatile_speed(U, t, 0.0, T) == U for t in times[::997])


@pytest.mark.parametrize("amplitude", [-0.1, 1.1])
def test_pulsation_amplitude_outside_unit_interval_is_rejected(amplitude):
    with pytest.raises(ValueError):
        pulsatile_speed(U, 0.1, amplitude, T)


def test_womersley_number_at_m1_scale():
    # R = 1.5 mm, blood 3.5 mPa s / 1060 kg/m^3: alpha ~ 2.1 at 60 bpm and ~2.3 at 75 bpm.
    assert womersley_number(1.5e-3, 1.0) == pytest.approx(2.07, rel=1e-2)
    assert womersley_number(1.5e-3, 0.8) == pytest.approx(2.31, rel=1e-2)
    assert womersley_number(3e-3, 1.0) == pytest.approx(2 * womersley_number(1.5e-3, 1.0))


def test_material_acceleration_local_and_convective_terms():
    def uniform(p, t):
        return np.array([pulsatile_speed(U, t, A, T), 0.0, 0.0])
    t = 0.1
    expected = U * A * 2 * np.pi / T * np.cos(2 * np.pi * t / T)
    np.testing.assert_allclose(material_acceleration(uniform, [0, 0, 0], t), [expected, 0, 0], rtol=1e-6)

    k = 20.0
    def strain(p, t):
        return np.array([k * p[0], -k * p[1], 0.0])
    point = np.array([1e-3, 2e-3, 0.0])
    np.testing.assert_allclose(material_acceleration(strain, point, 0.0),
                               [k**2 * point[0], k**2 * point[1], 0], rtol=1e-6)

    def steady_poiseuille(p, t):
        return poiseuille_flow(p, U)
    # Far upstream of the junction the smooth direction blend is straight to ~1e-7, so the
    # convective term is negligible against the junction scale U^2/R = 60 m/s^2.
    upstream = material_acceleration(steady_poiseuille, [2e-3, 0.4e-3, 0], 0.0)
    assert np.linalg.norm(upstream) < 1e-6 * U**2 / 1.5e-3


def test_neutrally_buoyant_particle_follows_pulsation_only_with_fluid_acceleration():
    def run(with_term):
        p = InertialParticle(100e-6, 3.5e-3, 1060.0, 1060.0, np.zeros(3),
                             [pulsatile_speed(U, 0, A, T), 0, 0])
        slips = []
        for step in range(2000):
            t = step * 1e-4
            u = np.array([pulsatile_speed(U, t, A, T), 0.0, 0.0])
            accel = np.array([U * A * 2 * np.pi / T * np.cos(2 * np.pi * t / T), 0, 0])
            p.step(1e-4, u, np.zeros(3), accel if with_term else None)
            slips.append(abs(p.velocity_m_s[0] - pulsatile_speed(U, t + 1e-4, A, T)))
        return max(slips)
    lagging, following = run(False), run(True)
    peak_acceleration, dt = U * A * 2 * np.pi / T, 1e-4
    assert lagging > 5e-4  # ~ tau * dU/dt with tau ~ 1 ms
    # With the term the only slip is the O(dt) hold of u over each step.
    assert following <= peak_acceleration * dt
    assert lagging > 5 * following


def test_passive_axial_transit_follows_pulsatile_centerline_speed():
    config = TrialConfig(duration_s=0.012, flow_model="poiseuille", flow_speed_m_s=U,
                         flow_pulsatility=A, cardiac_period_s=0.04, control_mode="passive")
    result = run_trial(config)
    h = result["history"]
    expected = 2 * U * (1 + A * np.sin(2 * np.pi * h["time_s"][:-1] / 0.04))
    np.testing.assert_allclose(h["flow_velocity_m_s"][:-1, 0], expected, rtol=1e-12)
    physics = result["summary"]["physics"]
    assert physics["dt_s"] <= 0.02 * 1.5e-3 / (2 * U * (1 + A)) * (1 + 1e-12)
    assert physics["womersley_number"] == pytest.approx(womersley_number(1.5e-3, 0.04))


def test_steady_flow_keeps_summary_keys_and_flow():
    base = TrialConfig(duration_s=0.3)
    assert "physics" not in run_trial(base)["summary"]
    steady = run_trial(replace(base, cardiac_period_s=0.7))  # period alone changes nothing
    np.testing.assert_array_equal(steady["history"]["true_position_m"],
                                  run_trial(base)["history"]["true_position_m"])


def test_fluid_acceleration_is_reported_at_the_junction():
    config = TrialConfig(duration_s=0.03, flow_model="poiseuille", flow_speed_m_s=U, particle_radius_m=100e-6,
                         control_mode="passive", start_m=(0.5e-3, 0.6e-3, 0.3e-3),
                         particle_inertia=True, fluid_acceleration_force=True)
    physics = run_trial(config)["summary"]["physics"]
    # Turning a ~0.5 m/s stream through the junction: centripetal acceleration of order 10-100 m/s^2.
    assert physics["maximum_fluid_acceleration_m_s2"] > 1.0


def test_release_phase_shifts_the_cardiac_cycle():
    base = TrialConfig(duration_s=0.004, flow_model="poiseuille", flow_speed_m_s=U, flow_pulsatility=A,
                       control_mode="passive")
    for phase, factor in ((0.25, 1 + A), (0.75, 1 - A)):
        flow = run_trial(replace(base, cardiac_phase=phase))["history"]["flow_velocity_m_s"][0, 0]
        assert flow == pytest.approx(2 * U * factor)


@pytest.mark.parametrize("change", [{"flow_pulsatility": 1.5}, {"flow_pulsatility": -0.1},
                                    {"cardiac_phase": 1.0}, {"cardiac_phase": -0.1},
                                    {"cardiac_period_s": 0.0}, {"fluid_acceleration_force": True}])
def test_invalid_pulsation_settings_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, **change))
