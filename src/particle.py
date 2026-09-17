"""Minimal simulation model for a magnetically actuated particle.

Simulation/education only. Not a clinical device model.
"""

from dataclasses import dataclass, field
import numpy as np
from src.validation import nonnegative, vector


@dataclass
class Particle:
    """Spherical particle under an overdamped Stokes-drag approximation."""

    radius_m: float
    viscosity_pa_s: float
    position_m: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    def __post_init__(self):
        nonnegative(self.radius_m, "radius_m", positive=True)
        nonnegative(self.viscosity_pa_s, "viscosity_pa_s", positive=True)
        self.position_m = vector(self.position_m)

    @property
    def drag_coefficient(self) -> float:
        """Stokes drag coefficient gamma = 6*pi*eta*r [N s / m]."""
        return 6.0 * np.pi * self.viscosity_pa_s * self.radius_m

    def velocity(self, flow_velocity_m_s, magnetic_force_n):
        """Return v = u + F_m/gamma in the overdamped approximation."""
        u = vector(flow_velocity_m_s)
        force = vector(magnetic_force_n)
        return u + force / self.drag_coefficient

    def step(self, dt_s, flow_velocity_m_s, magnetic_force_n):
        """Advance position by one explicit Euler step."""
        nonnegative(dt_s, "dt_s", positive=True)
        v = self.velocity(flow_velocity_m_s, magnetic_force_n)
        self.position_m = self.position_m + dt_s * v
        return self.position_m.copy()
