"""Delayed image-based flow estimation after removing known command displacement."""

from bisect import bisect_right
from dataclasses import replace
import numpy as np

from src.localization import DelayedStateEstimator, StateEstimate
from src.validation import nonnegative, vector


class CommandAwareEstimator:
    """Filter p - integral(F_command / gamma_model) as position plus flow.

    Commands are deterministic known inputs, held until the next command.
    Covariance is unchanged by this coordinate translation; unknown drag or
    actuation errors are not modeled as input uncertainty. No plant data enters.
    """

    def __init__(self, drag_n_s_m, **filter_options):
        self.drag = nonnegative(drag_n_s_m, "drag_n_s_m", positive=True)
        self.residual = DelayedStateEstimator(**filter_options)
        self.times = [0.0]
        self.displacements = [np.zeros(3)]
        self.velocities = [np.zeros(3)]
        self.last_command_s = -np.inf

    @property
    def last_capture_s(self):
        return self.residual.last_capture_s

    def displacement(self, time_s):
        nonnegative(time_s, "time_s")
        i = bisect_right(self.times, time_s) - 1
        return self.displacements[i] + (time_s - self.times[i]) * self.velocities[i]

    def command(self, time_s, force_n):
        nonnegative(time_s, "time_s")
        if time_s <= self.last_command_s:
            raise ValueError("command time must increase strictly")
        velocity = vector(force_n) / self.drag
        displacement = self.displacement(time_s)
        self.times.append(time_s)
        self.displacements.append(displacement)
        self.velocities.append(velocity)
        self.last_command_s = time_s

    def observe(self, reconstruction, captured_at_s, now_s):
        translated = replace(reconstruction, position_m=
                             reconstruction.position_m - self.displacement(captured_at_s))
        self.residual.observe(translated, captured_at_s, now_s)

    def flow_estimate(self, now_s):
        """Residual (uncommanded) velocity at now_s: flow plus any other drift such as settling."""
        estimate = self.residual.estimate(now_s)
        return None if estimate is None else estimate.estimated_velocity

    def estimate(self, now_s):
        estimate = self.residual.estimate(now_s)
        if estimate is None:
            return None
        i = bisect_right(self.times, now_s) - 1
        return StateEstimate(estimate.estimated_position + self.displacement(now_s),
                             estimate.estimated_velocity + self.velocities[i], estimate.covariance)
