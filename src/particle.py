"""Minimal simulation model for a magnetically actuated particle.

Simulation/education only. Not a clinical device model.
"""

from dataclasses import dataclass, field
import numpy as np
from src.feasibility import schiller_naumann_factor, volume
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


@dataclass
class InertialParticle:
    """Sphere with inertia: reduced Maxey-Riley, added mass, Schiller-Naumann drag.

    (m_p + m_f/2) dv/dt = F + gamma f(Re) (u - v) + (3/2) m_f Du/Dt, with Re from
    the slip |u - v|. The last (pressure-gradient plus added-mass) term is used
    only when a fluid acceleration is passed to step. Omitted: Basset history
    force and lift; shear lift is not small at r >~ 80 um.
    Each step holds u, F and the drag factor (from the slip at step start)
    constant and integrates exactly, so it is stable for any dt and tends to
    the overdamped model as the relaxation time goes to zero at low Re.
    """

    radius_m: float
    viscosity_pa_s: float
    density_kg_m3: float
    fluid_density_kg_m3: float
    position_m: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    velocity_m_s: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    def __post_init__(self):
        nonnegative(self.radius_m, "radius_m", positive=True)
        nonnegative(self.viscosity_pa_s, "viscosity_pa_s", positive=True)
        nonnegative(self.density_kg_m3, "density_kg_m3", positive=True)
        nonnegative(self.fluid_density_kg_m3, "fluid_density_kg_m3", positive=True)
        self.position_m = vector(self.position_m)
        self.velocity_m_s = vector(self.velocity_m_s)

    @property
    def drag_coefficient(self) -> float:
        """Stokes drag coefficient gamma = 6*pi*eta*r [N s / m], before the Re correction."""
        return 6.0 * np.pi * self.viscosity_pa_s * self.radius_m

    @property
    def effective_mass_kg(self) -> float:
        return (self.density_kg_m3 + 0.5 * self.fluid_density_kg_m3) * volume(self.radius_m)

    @property
    def relaxation_time_s(self) -> float:
        """Stokes-regime momentum relaxation time, including added mass."""
        return self.effective_mass_kg / self.drag_coefficient

    def slip_reynolds(self, flow_velocity_m_s):
        slip = np.linalg.norm(vector(flow_velocity_m_s) - self.velocity_m_s)
        return self.fluid_density_kg_m3 * 2.0 * self.radius_m * slip / self.viscosity_pa_s

    def step(self, dt_s, flow_velocity_m_s, magnetic_force_n, fluid_acceleration_m_s2=None):
        nonnegative(dt_s, "dt_s", positive=True)
        u, force = vector(flow_velocity_m_s), vector(magnetic_force_n)
        if fluid_acceleration_m_s2 is not None:
            force = force + 1.5 * self.fluid_density_kg_m3 * volume(self.radius_m) * vector(fluid_acceleration_m_s2)
        gamma = self.drag_coefficient * schiller_naumann_factor(self.slip_reynolds(u))
        terminal = u + force / gamma
        tau = self.effective_mass_kg / gamma
        relaxed = -np.expm1(-dt_s / tau)
        self.position_m = self.position_m + dt_s * terminal + (self.velocity_m_s - terminal) * tau * relaxed
        self.velocity_m_s = terminal + (self.velocity_m_s - terminal) * (1.0 - relaxed)
        return self.position_m.copy()
