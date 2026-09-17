"""Toy real-time localization models for simulation only."""

import numpy as np

from dataclasses import dataclass
from src.imaging import default_views
from src.validation import covariance, nonnegative, vector


class NoisyPositionSensor:
    """Direct 3D position sensor used as a stand-in for reconstructed imaging."""

    def __init__(self, sigma_m=0.15e-3, rng=None):
        self.sigma_m = nonnegative(sigma_m, "sigma_m")
        self.rng = rng or np.random.default_rng()

    def measure(self, true_position_m):
        true_position_m = np.asarray(true_position_m, dtype=float)
        return true_position_m + self.rng.normal(0.0, self.sigma_m, size=3)


class PositionKalmanFilter:
    """Minimal 3D random-walk Kalman filter: x[k+1] = x[k] + w."""

    def __init__(self, initial_position_m, initial_sigma_m=0.3e-3,
                 process_sigma_m=0.03e-3, measurement_sigma_m=0.15e-3):
        self.x = np.asarray(initial_position_m, dtype=float).copy()
        self.P = np.eye(3) * initial_sigma_m**2
        self.Q = np.eye(3) * process_sigma_m**2
        self.R = np.eye(3) * measurement_sigma_m**2

    def predict(self, displacement_m=None):
        if displacement_m is not None:
            self.x = self.x + np.asarray(displacement_m, dtype=float)
        self.P = self.P + self.Q
        return self.x.copy()

    def update(self, measurement_m):
        z = np.asarray(measurement_m, dtype=float)
        innovation = z - self.x
        S = self.P + self.R
        K = self.P @ np.linalg.inv(S)
        self.x = self.x + K @ innovation
        residual = np.eye(3) - K
        self.P = residual @ self.P @ residual.T + K @ self.R @ K.T
        return self.x.copy()

    @property
    def sigma_max_m(self):
        """Largest principal-axis 1-sigma uncertainty."""
        return float(np.sqrt(np.max(np.linalg.eigvalsh(self.P))))


@dataclass(frozen=True)
class Reconstruction:
    position_m: np.ndarray
    noise_covariance_m2: np.ndarray
    calibration_covariance_m2: np.ndarray
    residual_px: np.ndarray

    @property
    def covariance(self):
        return self.noise_covariance_m2 + self.calibration_covariance_m2

    @property
    def position_uncertainty(self):
        return float(np.sqrt(np.linalg.eigvalsh(self.covariance).max()))


class BiplaneTriangulator:
    """Weighted linear reconstruction with propagated random and fixed error.

    calibration_sigma_px models a fixed detector-offset error prior. Rotation,
    scale, anatomy-registration errors are NOT bounded by this covariance.
    """

    def __init__(self, views=None, noise_sigma_px=1.0, calibration_sigma_px=0.0,
                 max_condition=1e6):
        self.views = tuple(default_views() if views is None else views)
        if len(self.views) != 2:
            raise ValueError("exactly two views are required")
        sigmas = np.broadcast_to(np.asarray(noise_sigma_px, dtype=float), (4,)).copy()
        if not np.all(np.isfinite(sigmas)) or np.any(sigmas <= 0):
            raise ValueError("positive detector noise is required for weighting")
        nonnegative(calibration_sigma_px, "calibration_sigma_px")
        nonnegative(max_condition, "max_condition", positive=True)
        self.H = np.vstack([v.matrix for v in self.views])
        self.offset = np.concatenate([v.offset for v in self.views])
        whitened = self.H / sigmas[:, None]
        singular = np.linalg.svd(whitened, compute_uv=False)
        if singular[-1] <= 0 or singular[0] / singular[-1] > max_condition:
            raise ValueError("unobservable or ill-conditioned biplane geometry")
        self.inverse = np.linalg.pinv(whitened) / sigmas[None, :]
        self.noise_covariance_m2 = (self.inverse * sigmas**2) @ self.inverse.T
        self.calibration_covariance_m2 = calibration_sigma_px**2 * self.inverse @ self.inverse.T

    def reconstruct(self, detector_px):
        pixels = np.asarray(detector_px, dtype=float)
        if pixels.shape != (2, 2) or not np.all(np.isfinite(pixels)):
            raise ValueError("reconstruction needs two finite 2D measurements")
        observations = pixels.reshape(4) - self.offset
        position = self.inverse @ observations
        return Reconstruction(position, self.noise_covariance_m2.copy(),
                              self.calibration_covariance_m2.copy(),
                              observations - self.H @ position)


@dataclass(frozen=True)
class StateEstimate:
    estimated_position: np.ndarray
    estimated_velocity: np.ndarray
    covariance: np.ndarray

    @property
    def position_uncertainty(self):
        return float(np.sqrt(max(0.0, np.linalg.eigvalsh(self.covariance[:3, :3]).max())))


class KinematicKalmanFilter:
    """State [p(m), v(m/s)], constant velocity, continuous white acceleration.

    acceleration_spectral_density has units m^2/s^3. Prediction uncertainty
    grows with actual elapsed time, including time without received images.
    """

    def __init__(self, initial_position_m, position_covariance_m2,
                 initial_velocity_m_s=None, velocity_sigma_m_s=1e-3,
                 acceleration_spectral_density=1e-7,
                 calibration_covariance_m2=None):
        self.x = np.r_[vector(initial_position_m), vector(
            np.zeros(3) if initial_velocity_m_s is None else initial_velocity_m_s)]
        self.P = np.zeros((6, 6))
        self.P[:3, :3] = covariance(position_covariance_m2, 3, positive=True)
        self.P[3:, 3:] = np.eye(3) * nonnegative(velocity_sigma_m_s, "velocity_sigma_m_s")**2
        self.q = nonnegative(acceleration_spectral_density, "acceleration_spectral_density")
        self.calibration_covariance = covariance(
            np.zeros((3, 3)) if calibration_covariance_m2 is None else calibration_covariance_m2, 3)

    def predict(self, dt_s):
        dt = nonnegative(dt_s, "dt_s")
        F = np.eye(6)
        F[:3, 3:] = np.eye(3) * dt
        Q = self.q * np.kron(np.array([[dt**3 / 3, dt**2 / 2],
                                      [dt**2 / 2, dt]]), np.eye(3))
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q
        self.P = (self.P + self.P.T) / 2
        return self.snapshot()

    def update(self, position_m, measurement_covariance_m2):
        z = vector(position_m)
        R = covariance(measurement_covariance_m2, 3, positive=True)
        H = np.eye(3, 6)
        S = H @ self.P @ H.T + R
        K = np.linalg.solve(S, H @ self.P).T
        self.x += K @ (z - H @ self.x)
        J = np.eye(6) - K @ H
        self.P = J @ self.P @ J.T + K @ R @ K.T
        self.P = (self.P + self.P.T) / 2
        return self.snapshot()

    @property
    def estimated_position(self):
        return self.x[:3].copy()

    @property
    def estimated_velocity(self):
        return self.x[3:].copy()

    @property
    def covariance(self):
        result = self.P.copy()
        result[:3, :3] += self.calibration_covariance
        return result

    @property
    def position_uncertainty(self):
        return self.snapshot().position_uncertainty

    def snapshot(self):
        return StateEstimate(self.estimated_position, self.estimated_velocity, self.covariance)


class DelayedStateEstimator:
    """Filter ordered observations at capture time; predict a copy to now.

    This avoids treating a delayed measurement as current. Fixed-latency,
    synchronized imaging is supported; out-of-order observations are rejected.
    No interpolation of true trajectories or true-state initialization occurs.
    """

    def __init__(self, **filter_options):
        self.filter_options = filter_options
        self.filter = None
        self.last_capture_s = None

    def observe(self, reconstruction, captured_at_s, now_s):
        nonnegative(captured_at_s, "captured_at_s")
        nonnegative(now_s, "now_s")
        if captured_at_s > now_s + 1e-12:
            raise ValueError("cannot observe a future measurement")
        if self.last_capture_s is not None and captured_at_s <= self.last_capture_s:
            raise ValueError("duplicate or out-of-order measurement")
        if self.filter is None:
            self.filter = KinematicKalmanFilter(
                reconstruction.position_m, reconstruction.noise_covariance_m2,
                calibration_covariance_m2=reconstruction.calibration_covariance_m2,
                **self.filter_options)
        else:
            self.filter.predict(captured_at_s - self.last_capture_s)
            self.filter.update(reconstruction.position_m, reconstruction.noise_covariance_m2)
        self.last_capture_s = captured_at_s

    def estimate(self, now_s):
        import copy

        nonnegative(now_s, "now_s")
        if self.filter is None:
            return None
        if now_s < self.last_capture_s:
            raise ValueError("estimate time precedes last observation")
        projected = copy.deepcopy(self.filter)
        return projected.predict(now_s - self.last_capture_s)
