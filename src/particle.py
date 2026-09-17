"""Minimal simulation model for a magnetically actuated particle.

Simulation/education only. Not a clinical device model.
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Particle:
    """Spherical particle under an overdamped Stokes-drag approximation."""

    radius_m: float
    viscosity_pa_s: float
    position_m: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    @property
    def drag_coefficient(self) -> float:
        """Stokes drag coefficient gamma = 6*pi*eta*r [N s / m]."""
        return 6.0 * np.pi * self.viscosity_pa_s * self.radius_m

    def velocity(self, flow_velocity_m_s, magnetic_force_n):
        """Return v = u + F_m/gamma in the overdamped approximation."""
        u = np.asarray(flow_velocity_m_s, dtype=float)
        force = np.asarray(magnetic_force_n, dtype=float)
        return u + force / self.drag_coefficient

    def step(self, dt_s, flow_velocity_m_s, magnetic_force_n):
        """Advance position by one explicit Euler step."""
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        v = self.velocity(flow_velocity_m_s, magnetic_force_n)
        self.position_m = self.position_m + dt_s * v
        return self.position_m.copy()
