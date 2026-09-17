"""Toy real-time localization models for simulation only."""

import numpy as np


class NoisyPositionSensor:
    """Direct 3D position sensor used as a stand-in for reconstructed imaging."""

    def __init__(self, sigma_m=0.15e-3, rng=None):
        self.sigma_m = float(sigma_m)
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
        self.P = (np.eye(3) - K) @ self.P
        return self.x.copy()

    @property
    def sigma_max_m(self):
        """Largest principal-axis 1-sigma uncertainty."""
        return float(np.sqrt(np.max(np.linalg.eigvalsh(self.P))))
