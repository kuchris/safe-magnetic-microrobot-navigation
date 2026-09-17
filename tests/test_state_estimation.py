import numpy as np
import pytest

from src.localization import KinematicKalmanFilter, DelayedStateEstimator, BiplaneTriangulator


def test_prediction_matches_constant_velocity_and_white_acceleration_covariance():
    kf = KinematicKalmanFilter([0, 0, 0], np.eye(3) * 1e-8,
        initial_velocity_m_s=[1e-3, -2e-3, 3e-3], velocity_sigma_m_s=0,
        acceleration_spectral_density=2e-7)
    before = kf.covariance
    kf.predict(0.5)
    np.testing.assert_allclose(kf.estimated_position, [0.5e-3, -1e-3, 1.5e-3])
    np.testing.assert_allclose(kf.covariance[:3, :3] - before[:3, :3], np.eye(3) * 2e-7 * 0.5**3 / 3)
    np.testing.assert_allclose(kf.covariance[3:, 3:], np.eye(3) * 1e-7)


def test_updates_reduce_error_and_learn_velocity():
    rng = np.random.default_rng(8)
    velocity = np.array([0.7e-3, -0.3e-3, 0.2e-3])
    R = np.eye(3) * (80e-6)**2
    kf = KinematicKalmanFilter([0, 0, 0], R, acceleration_spectral_density=1e-10)
    measured_errors, estimated_errors = [], []
    for tick in range(1, 151):
        truth = velocity * tick * 0.05
        measurement = truth + rng.normal(0, 80e-6, 3)
        kf.predict(0.05)
        kf.update(measurement, R)
        measured_errors.append(np.linalg.norm(measurement - truth)**2)
        estimated_errors.append(np.linalg.norm(kf.estimated_position - truth)**2)
        assert np.linalg.eigvalsh(kf.covariance).min() >= -1e-20
    assert np.mean(estimated_errors) < 0.4 * np.mean(measured_errors)
    np.testing.assert_allclose(kf.estimated_velocity, velocity, atol=30e-6)


def test_fixed_calibration_uncertainty_does_not_average_away():
    floor = np.diag([1, 2, 3]) * 1e-8
    kf = KinematicKalmanFilter([0, 0, 0], np.eye(3) * 1e-8,
                              calibration_covariance_m2=floor)
    for _ in range(200):
        kf.update([0, 0, 0], np.eye(3) * 1e-8)
    assert kf.position_uncertainty >= np.sqrt(3e-8)
    np.testing.assert_allclose(kf.covariance[:3, :3], floor, atol=1e-10)


def test_latency_updates_at_capture_time_then_extrapolates_without_mutation():
    triangulator = BiplaneTriangulator()
    estimator = DelayedStateEstimator(acceleration_spectral_density=0,
                                     initial_velocity_m_s=[1e-3, 0, 0])
    rec = triangulator.reconstruct(np.zeros((2, 2)))
    estimator.observe(rec, captured_at_s=0, now_s=0.2)
    snapshot = estimator.estimate(0.2)
    np.testing.assert_allclose(snapshot.estimated_position, [0.2e-3, 0, 0])
    np.testing.assert_array_equal(estimator.filter.estimated_position, [0, 0, 0])
    assert estimator.estimate(0.7).position_uncertainty > snapshot.position_uncertainty
    # Polling the current estimate cannot advance the measurement-time anchor.
    again = estimator.estimate(0.2)
    np.testing.assert_array_equal(again.covariance, snapshot.covariance)
    with pytest.raises(ValueError, match="out-of-order"):
        estimator.observe(rec, 0, 0.3)
    with pytest.raises(ValueError, match="future"):
        estimator.observe(rec, 1, 0.3)


def test_uninitialized_filter_and_snapshot_isolation():
    assert DelayedStateEstimator().estimate(1) is None
    kf = KinematicKalmanFilter([0, 0, 0], np.eye(3))
    snapshot = kf.snapshot()
    snapshot.estimated_position[:] = 5
    snapshot.covariance[:] = 0
    np.testing.assert_array_equal(kf.estimated_position, [0, 0, 0])
    assert kf.covariance[0, 0] == 1


@pytest.mark.parametrize("dt", [-1, np.nan, np.inf])
def test_invalid_prediction_time(dt):
    with pytest.raises(ValueError):
        KinematicKalmanFilter([0, 0, 0], np.eye(3)).predict(dt)


def test_invalid_covariance():
    with pytest.raises(ValueError):
        KinematicKalmanFilter([0, 0, 0], np.diag([1, -1, 1]))
