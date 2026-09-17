# Overdamped particle and synthetic flow

This is computational research/education only. No parameters in the runnable
examples are experimentally validated or claimed to be medically realistic.

## Equations and units

For a rigid spherical particle in an unbounded Newtonian fluid, the Stokes
approximation gives

$$
\gamma=6\pi\eta r,\quad F_{drag}=\gamma(u-v),\quad
v=u+F_m/\gamma,\quad p_{k+1}=p_k+\Delta t\,v_k.
$$

Here `eta` is dynamic viscosity [Pa s], `r` radius [m], `gamma` drag coefficient
[N s/m], `u` local prescribed fluid velocity [m/s], `v` particle velocity [m/s],
and `F_m` applied magnetic-force abstraction [N]. Position is in metres and time
in seconds. The explicit Euler step is exact for constant velocity, but not
for spatially varying flow or closed-loop commands.

The physical approximation assumes small particle Reynolds number
`Re_p = rho * (2*r) * |v-u| / eta << 1` and a particle relaxation time short
relative to resolved dynamics. Density and relaxation time are not modeled
or validated here. Small size alone is not a proof of those assumptions.

## What is actually implemented

`Particle` uses the algebraic force balance, without mass or acceleration.
`centerline_flow` is a piecewise constant-speed vector field. It follows +x
before the junction; afterwards it follows the upper branch for y >= 0 and
the lower branch otherwise. It has no radial velocity profile. In particular,
it is not a Poiseuille solver and does not enforce mass conservation at the
bifurcation. It is discontinuous at branch selection boundaries.

Optional flow disturbance in `TrialConfig` is a per-physics-tick independent
Gaussian velocity perturbation, in m/s. It is not a turbulence or Brownian
model; its effective integrated noise depends on the chosen timestep.

The plant accepts a bounded ideal desired-force vector. A fixed scalar gain
error can perturb that force and a final magnitude cap is enforced. This is
not a coil field model. Dipole orientation, field gradients, coil currents,
hysteresis and heating are unmodeled. See the magnetic-actuation note for
the conceptual force/torque equations.

## Geometry and collisions

The Y-vessel consists of three capsules, not flat-ended cylinders. A capsule
is the set within one radius of a finite line segment. This preserves the
existing geometry's behavior while correcting its description.

For segment e and particle radius r_p:

`d_e(p) = R_e - r_p - distance(p, centerline_segment_e)`.

The implementation returns `d_proxy(p) = max_e d_e(p)`. It is exact for one
capsule and a conservative interior clearance lower bound for the capsule
union. At overlaps it is not the exact union signed distance. For a finite
particle, negative proxy clearance can conservatively flag a configuration
whose sphere still fits in the full union. Recorded `wall_collision` means
a sampled proxy violation (`d_proxy <= 0`), not a validated contact solver.

Containment includes equality, while evaluation treats touching as a wall
violation. Safety uses the stricter positive robust margin. Collisions are
checked at physics sample times only; continuous swept-volume collision
detection is not implemented. No contact response is simulated.

## Excluded physics

No cerebral hemodynamics, compliant vessel walls, pulsation, blood cells,
non-Newtonian rheology, lubrication/wall corrections, particle rotation,
Brownian motion, adhesion, gravity/buoyancy, clot interaction, or tissue model.
The model must not be used to derive human/animal experimental instructions.
