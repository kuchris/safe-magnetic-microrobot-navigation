"""Order-of-magnitude feasibility of gradient steering at a cerebral bifurcation.

Analytical estimates only. Not a clinical device model, not a safety claim.

Scenario: a magnetized sphere travels along a parent artery with a Poiseuille
profile and must drift laterally to the side of a target branch within an
approach length L. In an occlusion scenario the target branch carries little
or no flow, so the particle must cross streamlines rather than follow a flow
split. Lateral drift speed is the magnetic force divided by the drag force
per unit slip velocity, with optional near-wall and finite-Reynolds corrections.

Units are SI throughout. See docs/14_feasibility.md for sources and limits.
"""

from dataclasses import dataclass
import numpy as np
from src.validation import nonnegative

MU0 = 4e-7 * np.pi
GRAVITY_M_S2 = 9.81


@dataclass(frozen=True)
class Fluid:
    viscosity_pa_s: float = 3.5e-3      # typical high-shear whole blood (assumed)
    density_kg_m3: float = 1060.0       # whole blood (assumed)

    def __post_init__(self):
        nonnegative(self.viscosity_pa_s, "viscosity_pa_s", positive=True)
        nonnegative(self.density_kg_m3, "density_kg_m3", positive=True)


@dataclass(frozen=True)
class Material:
    name: str = "NdFeB"
    magnetization_a_m: float = 1.0e6    # ~Br/mu0 for Br ~ 1.26 T (textbook, assumed)
    density_kg_m3: float = 7500.0       # sintered NdFeB (textbook, assumed)
    magnetic_volume_fraction: float = 1.0

    def __post_init__(self):
        nonnegative(self.magnetization_a_m, "magnetization_a_m", positive=True)
        nonnegative(self.density_kg_m3, "density_kg_m3", positive=True)
        if not 0 < self.magnetic_volume_fraction <= 1:
            raise ValueError("magnetic_volume_fraction must be in (0, 1]")

    @property
    def effective_magnetization_a_m(self):
        return self.magnetic_volume_fraction * self.magnetization_a_m


@dataclass(frozen=True)
class Vessel:
    radius_m: float = 1.5e-3            # M1-like lumen, see docs
    mean_speed_m_s: float = 0.30        # cross-sectional mean, see docs
    approach_length_m: float = 10e-3    # steering length before the branch (assumed)

    def __post_init__(self):
        nonnegative(self.radius_m, "radius_m", positive=True)
        nonnegative(self.mean_speed_m_s, "mean_speed_m_s")
        nonnegative(self.approach_length_m, "approach_length_m", positive=True)


def volume(radius_m):
    return 4.0 / 3.0 * np.pi * radius_m ** 3


def stokes_drag_coefficient(radius_m, fluid):
    nonnegative(radius_m, "radius_m", positive=True)
    return 6.0 * np.pi * fluid.viscosity_pa_s * radius_m


def particle_reynolds(radius_m, slip_m_s, fluid):
    return fluid.density_kg_m3 * 2.0 * radius_m * abs(slip_m_s) / fluid.viscosity_pa_s


def schiller_naumann_factor(reynolds):
    """Drag multiplier relative to Stokes; empirical, stated range Re < ~800."""
    reynolds = float(reynolds)
    if not np.isfinite(reynolds) or reynolds < 0:
        raise ValueError("reynolds must be finite and nonnegative")
    return 1.0 + 0.15 * reynolds ** 0.687


def wall_factor_perpendicular(radius_m, center_to_wall_m):
    """First-order Lorentz correction for motion normal to a plane wall.

    Only asymptotically valid for center_to_wall >> radius; it underestimates
    the true divergence as the gap closes.
    """
    if center_to_wall_m <= radius_m:
        raise ValueError("particle overlaps the wall")
    return 1.0 + 9.0 * radius_m / (8.0 * center_to_wall_m)


def relaxation_time(radius_m, material, fluid):
    """Momentum relaxation time including added mass (rho_p + rho_f / 2)."""
    rho = material.density_kg_m3 + 0.5 * fluid.density_kg_m3
    return 2.0 * rho * radius_m ** 2 / (9.0 * fluid.viscosity_pa_s)


def poiseuille_speed(y_m, vessel):
    return np.clip(2.0 * vessel.mean_speed_m_s * (1.0 - (y_m / vessel.radius_m) ** 2), 0.0, None)


def lateral_path_integral(radius_m, vessel, start="center", clearance_m=None,
                          wall_correction=True, samples=4001):
    """Return I = integral u(y) f(y) dy [m^2/s]; required lateral speed is I / L.

    The particle ends with a gap `clearance_m` (default one radius) to the
    target-side wall. `start="center"` begins on the axis; `start="far_wall"`
    begins with the same gap at the opposite wall.
    """
    clearance_m = radius_m if clearance_m is None else nonnegative(clearance_m, "clearance_m")
    y_end = vessel.radius_m - radius_m - clearance_m
    if y_end <= 0:
        raise ValueError("particle and clearance do not fit in the vessel")
    if start == "center":
        y_start = 0.0
    elif start == "far_wall":
        y_start = -y_end
    else:
        raise ValueError("start must be 'center' or 'far_wall'")
    y = np.linspace(y_start, y_end, samples)
    integrand = poiseuille_speed(y, vessel)
    if wall_correction:
        distance = vessel.radius_m - y
        integrand = integrand * (1.0 + 9.0 * radius_m / (8.0 * distance))
    return float(np.trapezoid(integrand, y))


def required_gradient_branch_entry(radius_m, vessel, material=Material(), fluid=Fluid(),
                                   start="center", wall_correction=True, inertia_correction=True):
    """Gradient [T/m] needed to reach the target-side wall within the approach length."""
    lateral_speed = lateral_path_integral(radius_m, vessel, start, wall_correction=wall_correction) \
        / vessel.approach_length_m
    reynolds = particle_reynolds(radius_m, lateral_speed, fluid)
    factor = schiller_naumann_factor(reynolds) if inertia_correction else 1.0
    force = stokes_drag_coefficient(radius_m, fluid) * lateral_speed * factor
    gradient = force / (volume(radius_m) * material.effective_magnetization_a_m)
    return {"gradient_t_m": gradient, "lateral_speed_m_s": lateral_speed,
            "particle_reynolds": reynolds, "drag_factor": factor, "force_n": force}


def closed_form_gradient(radius_m, vessel, material=Material(), fluid=Fluid()):
    """Uncorrected center-to-wall limit: 6 eta U R / (M r^2 L)."""
    return (6.0 * fluid.viscosity_pa_s * vessel.mean_speed_m_s * vessel.radius_m /
            (material.effective_magnetization_a_m * radius_m ** 2 * vessel.approach_length_m))


def gravity_hold_gradient(material=Material(), fluid=Fluid()):
    """Gradient [T/m] balancing net weight; independent of particle size."""
    net_density = material.density_kg_m3 - fluid.density_kg_m3
    return max(net_density, 0.0) * GRAVITY_M_S2 / material.effective_magnetization_a_m


def sedimentation_speed(radius_m, material=Material(), fluid=Fluid(), iterations=50):
    """Terminal settling speed with the Schiller-Naumann correction (fixed point)."""
    weight = (material.density_kg_m3 - fluid.density_kg_m3) * GRAVITY_M_S2 * volume(radius_m)
    gamma = stokes_drag_coefficient(radius_m, fluid)
    speed = abs(weight) / gamma
    for _ in range(iterations):
        speed = abs(weight) / (gamma * schiller_naumann_factor(particle_reynolds(radius_m, speed, fluid)))
    return speed


def validity(radius_m, vessel, material=Material(), fluid=Fluid(), lateral_speed_m_s=None):
    """Dimensionless checks for the overdamped Stokes model used by the simulator."""
    tau = relaxation_time(radius_m, material, fluid)
    transit = vessel.approach_length_m / max(vessel.mean_speed_m_s, 1e-30)
    wall_shear = 4.0 * vessel.mean_speed_m_s / vessel.radius_m
    result = {
        "relaxation_time_s": tau,
        "stokes_number": tau / transit,
        "shear_reynolds": fluid.density_kg_m3 * wall_shear * radius_m ** 2 / fluid.viscosity_pa_s,
        "diameter_ratio": radius_m / vessel.radius_m,
    }
    if lateral_speed_m_s is not None:
        result["slip_reynolds"] = particle_reynolds(radius_m, lateral_speed_m_s, fluid)
    return result


def drift_to_flow_ratio(force_n, radius_m, mean_speed_m_s, fluid=Fluid()):
    """Pi = (F / gamma) / U, the group shared by the toy simulator and real scale."""
    return force_n / stokes_drag_coefficient(radius_m, fluid) / mean_speed_m_s
