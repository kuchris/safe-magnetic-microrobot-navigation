"""Small SI-vector and covariance validators shared by numerical models."""

import numpy as np


def vector(value, size=3):
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"expected a finite vector of shape ({size},)")
    return result.copy()


def covariance(value, size, positive=False):
    result = np.asarray(value, dtype=float)
    if result.shape != (size, size) or not np.all(np.isfinite(result)):
        raise ValueError("invalid covariance shape or values")
    if not np.allclose(result, result.T, rtol=1e-10, atol=1e-18):
        raise ValueError("covariance must be symmetric")
    minimum = np.linalg.eigvalsh(result).min()
    if minimum < 0 or (positive and minimum <= 0):
        raise ValueError("covariance must be positive (semi)definite")
    return result.copy()


def nonnegative(value, name, positive=False):
    if not np.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name} must be finite and {'positive' if positive else 'nonnegative'}")
    return float(value)
