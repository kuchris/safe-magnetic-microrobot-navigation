import numpy as np
import pytest

from src.particle import Particle


def test_zero_force_follows_flow():
    p = Particle(radius_m=1e-4, viscosity_pa_s=3.5e-3)
    u = np.array([1e-3, 0.0, 0.0])
    v = p.velocity(u, np.zeros(3))
    np.testing.assert_allclose(v, u)


def test_force_adds_magnetic_drift():
    p = Particle(radius_m=1e-4, viscosity_pa_s=3.5e-3)
    u = np.array([1e-3, 0.0, 0.0])
    drift = np.array([0.0, 0.5e-3, 0.0])
    force = p.drag_coefficient * drift
    np.testing.assert_allclose(p.velocity(u, force), u + drift)


def test_stokes_coefficient_and_exact_constant_velocity_integration():
    p = Particle(1e-4, 3.5e-3)
    np.testing.assert_allclose(p.drag_coefficient, 6 * np.pi * 3.5e-3 * 1e-4)
    for _ in range(200):
        p.step(0.01, [1e-3, 0, 0], p.drag_coefficient * np.array([0, 0.5e-3, 0]))
    np.testing.assert_allclose(p.position_m, [2e-3, 1e-3, 0], atol=1e-16)


@pytest.mark.parametrize("radius,viscosity", [(0, 1), (-1, 1), (1, 0), (np.nan, 1)])
def test_invalid_particle_parameters(radius, viscosity):
    with pytest.raises(ValueError):
        Particle(radius, viscosity)


def test_invalid_integration_inputs():
    p = Particle(1e-4, 3.5e-3)
    with pytest.raises(ValueError):
        p.step(np.nan, [0, 0, 0], [0, 0, 0])
    with pytest.raises(ValueError):
        p.velocity([0, 0, 0], [np.inf, 0, 0])
