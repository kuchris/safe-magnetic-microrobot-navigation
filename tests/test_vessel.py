import numpy as np

from src.vessel import YVessel
from src.vessel import VesselSegment


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


def test_capsule_endcaps_signed_clearance_and_touching():
    segment = VesselSegment(np.array([0, 0, 0]), np.array([0.01, 0, 0]), 1e-3)
    np.testing.assert_allclose(segment.wall_clearance([-0.5e-3, 0, 0]), 0.5e-3)
    np.testing.assert_allclose(segment.wall_clearance([5e-3, 1e-3, 0]), 0, atol=1e-18)
    assert segment.wall_clearance([5e-3, 1.1e-3, 0]) < 0
