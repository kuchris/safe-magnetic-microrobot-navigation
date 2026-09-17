import numpy as np

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
