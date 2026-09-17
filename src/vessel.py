"""Simple 3D Y-shaped vessel geometry for simulation.

The vessel is represented as a union of capsules (rounded-end tubes).
Simulation/education only; not anatomical or clinical geometry.
"""

from dataclasses import dataclass
import numpy as np
from src.validation import nonnegative, vector


@dataclass(frozen=True)
class VesselSegment:
    start_m: np.ndarray
    end_m: np.ndarray
    radius_m: float

    def __post_init__(self):
        object.__setattr__(self, "start_m", vector(self.start_m))
        object.__setattr__(self, "end_m", vector(self.end_m))
        nonnegative(self.radius_m, "radius_m", positive=True)
        if np.linalg.norm(self.end_m - self.start_m) == 0:
            raise ValueError("Vessel segment must have nonzero length")

    def closest_centerline_point(self, point_m):
        p = vector(point_m)
        a = np.asarray(self.start_m, dtype=float)
        b = np.asarray(self.end_m, dtype=float)
        ab = b - a
        denom = float(np.dot(ab, ab))
        if denom == 0.0:
            raise ValueError("Vessel segment must have nonzero length")
        t = np.clip(np.dot(p - a, ab) / denom, 0.0, 1.0)
        return a + t * ab

    def wall_clearance(self, point_m, particle_radius_m=0.0):
        """Exact signed clearance for one capsule, eroded by particle radius.

        Positive: inside with clearance. Zero: touching. Negative: violation.
        """
        nonnegative(particle_radius_m, "particle_radius_m")
        center = self.closest_centerline_point(point_m)
        radial_distance = np.linalg.norm(np.asarray(point_m) - center)
        return self.radius_m - particle_radius_m - radial_distance


class YVessel:
    """Three capsules forming a toy 3D Y bifurcation."""

    def __init__(self, radius_m=1.5e-3):
        origin = np.array([0.0, 0.0, 0.0])
        junction = np.array([10e-3, 0.0, 0.0])
        upper = np.array([20e-3, 6e-3, 3e-3])
        lower = np.array([20e-3, -6e-3, -3e-3])
        self.segments = (
            VesselSegment(origin, junction, radius_m),
            VesselSegment(junction, upper, radius_m),
            VesselSegment(junction, lower, radius_m),
        )

    def clearance(self, point_m, particle_radius_m=0.0):
        """Conservative signed clearance proxy: max of capsule clearances.

        Exact for an isolated capsule. At overlaps it is a lower bound on
        union interior clearance, not the exact union signed distance. For
        finite particles a negative value can be a conservative false alarm.
        """
        return max(
            segment.wall_clearance(point_m, particle_radius_m)
            for segment in self.segments
        )

    def contains(self, point_m, particle_radius_m=0.0):
        return self.clearance(point_m, particle_radius_m) >= 0.0

    @property
    def upper_target(self):
        return self.segments[1].end_m.copy()

    @property
    def lower_target(self):
        return self.segments[2].end_m.copy()
