"""Explicit branch choice and centerline waypoints for the deterministic Y."""

import numpy as np
from src.validation import nonnegative, vector


class YWaypointPlanner:
    def __init__(self, vessel, branch="upper", spacing_m=0.5e-3, tolerance_m=0.3e-3):
        if branch not in ("upper", "lower"):
            raise ValueError("branch must be upper or lower")
        nonnegative(spacing_m, "spacing_m", positive=True)
        self.tolerance_m = nonnegative(tolerance_m, "tolerance_m", positive=True)
        self.branch = branch
        segments = [vessel.segments[0], vessel.segments[1 if branch == "upper" else 2]]
        self.waypoints = np.concatenate([
            np.linspace(s.start_m, s.end_m,
                        int(np.ceil(np.linalg.norm(s.end_m - s.start_m) / spacing_m)) + 1)[1:]
            for s in segments])
        self.index = 0

    def target(self, estimated_position_m):
        p = vector(estimated_position_m)
        # Advance passed waypoints by segment projection, even between frames.
        while self.index < len(self.waypoints) - 1:
            current = self.waypoints[self.index]
            following = self.waypoints[self.index + 1]
            if (np.linalg.norm(p - current) <= self.tolerance_m or
                    np.dot(p - current, following - current) >= 0):
                self.index += 1
            else:
                break
        return self.waypoints[self.index].copy()


def wrong_branch(position_m, vessel, intended_branch, confirmation_distance_m=2e-3):
    """Evaluation only: flag entry beyond a junction exclusion region."""
    if intended_branch not in ("upper", "lower"):
        raise ValueError("invalid intended branch")
    nonnegative(confirmation_distance_m, "confirmation_distance_m")
    p = vector(position_m)
    junction = vessel.segments[0].end_m
    if p[0] <= junction[0] or np.linalg.norm(p - junction) < confirmation_distance_m:
        return False
    distances = [np.linalg.norm(p - s.closest_centerline_point(p)) for s in vessel.segments[1:]]
    if np.isclose(distances[0], distances[1], atol=1e-12, rtol=0):
        return False
    actual = "upper" if distances[0] < distances[1] else "lower"
    return actual != intended_branch
