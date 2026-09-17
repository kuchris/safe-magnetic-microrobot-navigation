"""Synchronized orthographic biplane detector coordinates, not raster images.

Only this simulated sensor/plant boundary accepts ground truth. All parameters
are synthetic. Orthography ignores perspective, attenuation and segmentation.
"""

from collections import deque
from dataclasses import dataclass, field
import numpy as np

from src.validation import nonnegative, vector


@dataclass(frozen=True)
class OrthographicView:
    axes: np.ndarray  # two orthonormal detector directions in world coordinates
    pixel_size_m: float = 50e-6
    origin_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    offset_px: np.ndarray = field(default_factory=lambda: np.zeros(2))

    def __post_init__(self):
        axes = np.asarray(self.axes, dtype=float)
        if axes.shape != (2, 3) or not np.all(np.isfinite(axes)):
            raise ValueError("axes must be a finite 2x3 matrix")
        if not np.allclose(axes @ axes.T, np.eye(2), atol=1e-10):
            raise ValueError("detector axes must be orthonormal")
        object.__setattr__(self, "axes", axes.copy())
        object.__setattr__(self, "origin_m", vector(self.origin_m))
        object.__setattr__(self, "offset_px", vector(self.offset_px, 2))
        nonnegative(self.pixel_size_m, "pixel_size_m", positive=True)

    @property
    def matrix(self):
        return self.axes / self.pixel_size_m

    @property
    def offset(self):
        return self.offset_px - self.matrix @ self.origin_m

    def project(self, position_m):
        return self.matrix @ vector(position_m) + self.offset


def default_views():
    return (OrthographicView(np.array([[1, 0, 0], [0, 1, 0]])),
            OrthographicView(np.array([[1, 0, 0], [0, 0, 1]])))


@dataclass(frozen=True)
class BiplaneFrame:
    captured_at_s: float
    available_at_s: float
    detector_px: np.ndarray | None  # shape (2,2); None means pair tracking loss


class BiplaneImager:
    def __init__(self, views=None, noise_sigma_px=1.0, frame_rate_hz=20.0,
                 latency_s=0.05, dropout_probability=0.0,
                 dropout_intervals=(), calibration_bias_px=None, rng=None):
        self.views = tuple(default_views() if views is None else views)
        if len(self.views) != 2:
            raise ValueError("exactly two views are required")
        self.noise_sigma_px = nonnegative(noise_sigma_px, "noise_sigma_px")
        self.period_s = 1 / nonnegative(frame_rate_hz, "frame_rate_hz", positive=True)
        self.latency_s = nonnegative(latency_s, "latency_s")
        self.dropout_probability = nonnegative(dropout_probability, "dropout_probability")
        if self.dropout_probability > 1:
            raise ValueError("dropout_probability must be <= 1")
        self.dropout_intervals = tuple(dropout_intervals)
        for start, end in self.dropout_intervals:
            if not (np.isfinite(start) and np.isfinite(end) and 0 <= start < end):
                raise ValueError("dropout intervals must satisfy 0 <= start < end")
        bias = np.zeros(4) if calibration_bias_px is None else calibration_bias_px
        self.calibration_bias_px = vector(np.asarray(bias).reshape(-1), 4).reshape(2, 2)
        self.rng = np.random.default_rng() if rng is None else rng
        self._next_capture_s = 0.0
        self._last_time_s = -np.inf
        self._pending = deque()

    def advance(self, now_s, true_position_m):
        """Capture at most once per physics tick; timestamp the actual sample.

        Missed frame slots are skipped, never filled with fictitious past truth.
        Call at dt <= frame period; delivery is quantized to simulation ticks.
        Dropout notifications traverse the same latency queue as valid frames.
        """
        nonnegative(now_s, "now_s")
        if now_s <= self._last_time_s:
            raise ValueError("imaging time must increase strictly")
        self._last_time_s = now_s
        if now_s + 1e-12 >= self._next_capture_s:
            lost = (self.rng.random() < self.dropout_probability or
                    any(a <= now_s < b for a, b in self.dropout_intervals))
            pixels = None if lost else np.stack([v.project(true_position_m) for v in self.views])
            if pixels is not None:
                pixels += self.calibration_bias_px + self.rng.normal(
                    0, self.noise_sigma_px, (2, 2))
            self._pending.append(BiplaneFrame(now_s, now_s + self.latency_s, pixels))
            slots = int(np.floor((now_s + 1e-12 - self._next_capture_s) / self.period_s)) + 1
            self._next_capture_s += slots * self.period_s
        ready = []
        while self._pending and self._pending[0].available_at_s <= now_s + 1e-12:
            ready.append(self._pending.popleft())
        return ready
