import numpy as np
import pytest

from src.imaging import BiplaneImager, OrthographicView, default_views
from src.localization import BiplaneTriangulator


def test_known_projection_and_reconstruction():
    views = default_views()
    p = np.array([2e-3, -3e-3, 4e-3])
    pixels = np.stack([v.project(p) for v in views])
    np.testing.assert_allclose(pixels, [[40, -60], [40, 80]])
    result = BiplaneTriangulator(views).reconstruct(pixels)
    np.testing.assert_allclose(result.position_m, p, atol=1e-17)
    np.testing.assert_allclose(result.covariance, np.diag([0.5, 1, 1]) * (50e-6)**2, atol=1e-22)


def test_arbitrary_points_rotated_translated_scaled_detectors():
    rng = np.random.default_rng(21)
    rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    views = (OrthographicView(rotation[[0, 1]], 31e-6, np.array([0.1, -0.2, 0.3]), np.array([35, 28])),
             OrthographicView(rotation[[0, 2]], 73e-6, np.array([-0.2, 0.4, 0.1]), np.array([-8, 72])))
    reconstructor = BiplaneTriangulator(views)
    for point in rng.uniform(-0.03, 0.03, (80, 3)):
        result = reconstructor.reconstruct(np.stack([v.project(point) for v in views]))
        np.testing.assert_allclose(result.position_m, point, atol=1e-14)


def test_parallel_views_rejected_and_near_parallel_increases_uncertainty():
    a, b = default_views()
    with pytest.raises(ValueError, match="geometry"):
        BiplaneTriangulator((a, a))
    angle = 0.02
    oblique = OrthographicView(np.array([[1, 0, 0], [0, np.cos(angle), np.sin(angle)]]))
    weak = BiplaneTriangulator((a, oblique)).noise_covariance_m2
    good = BiplaneTriangulator((a, b)).noise_covariance_m2
    assert np.linalg.eigvalsh(weak).max() > 100 * np.linalg.eigvalsh(good).max()


def test_empirical_reconstruction_covariance_matches_model():
    rng = np.random.default_rng(123)
    t = BiplaneTriangulator(noise_sigma_px=[1, 2, 3, 4])
    p = np.array([0.01, -0.002, 0.003])
    perfect = np.stack([v.project(p) for v in t.views])
    errors = np.array([t.reconstruct(perfect + rng.normal(size=(2, 2)) * [[1, 2], [3, 4]]).position_m - p
                       for _ in range(5000)])
    empirical = np.cov(errors, rowvar=False)
    np.testing.assert_allclose(np.diag(empirical), np.diag(t.noise_covariance_m2), rtol=0.06)


def test_frame_rate_latency_and_actual_capture_timestamps():
    imager = BiplaneImager(frame_rate_hz=10, latency_s=0.025, noise_sigma_px=0,
                          rng=np.random.default_rng(1))
    delivered = []
    for time in np.arange(0, 0.251, 0.01):
        frames = imager.advance(time, [time * 1e-3, 0, 0])
        assert all(f.available_at_s <= time + 1e-12 for f in frames)
        delivered.extend(frames)
    np.testing.assert_allclose([f.captured_at_s for f in delivered], [0, 0.1, 0.2])
    np.testing.assert_allclose([f.available_at_s for f in delivered], [0.025, 0.125, 0.225])
    np.testing.assert_allclose(delivered[1].detector_px[:, 0], [2, 2])


def test_frame_skip_does_not_fabricate_historical_observations():
    imager = BiplaneImager(frame_rate_hz=10, latency_s=0, noise_sigma_px=0)
    imager.advance(0, [0, 0, 0])
    frames = imager.advance(0.35, [0.0035, 0, 0])
    assert len(frames) == 1 and frames[0].captured_at_s == 0.35


def test_fixed_calibration_error_persists_across_frames():
    bias = np.array([[1, 2], [3, 4]])
    imager = BiplaneImager(noise_sigma_px=0, latency_s=0, calibration_bias_px=bias)
    for time in [0, 0.1]:
        frame = imager.advance(time, [0, 0, 0])[0]
        np.testing.assert_array_equal(frame.detector_px, bias)


def test_dropout_burst_recovery_and_probability_one():
    imager = BiplaneImager(latency_s=0, dropout_intervals=((0.1, 0.3),), rng=np.random.default_rng(3))
    assert imager.advance(0, [0, 0, 0])[0].detector_px is not None
    assert imager.advance(0.1, [0, 0, 0])[0].detector_px is None
    assert imager.advance(0.3, [0, 0, 0])[0].detector_px is not None
    always_lost = BiplaneImager(latency_s=0, dropout_probability=1)
    assert always_lost.advance(0, [0, 0, 0])[0].detector_px is None


@pytest.mark.parametrize("options", [{"frame_rate_hz": 0}, {"latency_s": -1},
    {"dropout_probability": 1.2}, {"noise_sigma_px": np.nan}])
def test_invalid_imaging_configuration(options):
    with pytest.raises(ValueError):
        BiplaneImager(**options)


def test_invalid_projection_and_detector_data():
    with pytest.raises(ValueError):
        OrthographicView(np.ones((2, 3)))
    with pytest.raises(ValueError):
        BiplaneTriangulator().reconstruct([[np.nan, 0], [0, 0]])
