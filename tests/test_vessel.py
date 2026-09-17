import numpy as np

from src.vessel import YVessel


def test_centerline_is_inside():
    vessel = YVessel(radius_m=1.5e-3)
    assert vessel.contains(np.array([5e-3, 0.0, 0.0]), particle_radius_m=0.1e-3)


def test_far_point_is_outside():
    vessel = YVessel(radius_m=1.5e-3)
    assert not vessel.contains(np.array([5e-3, 5e-3, 0.0]), particle_radius_m=0.1e-3)


def test_centerline_clearance_accounts_for_particle_radius():
    vessel = YVessel(radius_m=1.5e-3)
    clearance = vessel.clearance(np.array([5e-3, 0.0, 0.0]), particle_radius_m=0.1e-3)
    np.testing.assert_allclose(clearance, 1.4e-3)
