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

`flow_model="smooth"` optionally replaces the switches with a continuous
direction blend. Define `a = (1 + tanh((x - junction_x) / L)) / 2` and
`b = tanh(y / W)`, then normalize `[1, 0.6*a*b, 0.3*a*b]` and multiply by
the prescribed speed. Defaults are `L = 1 mm` and `W = 0.3 mm`. At y = 0 the
field remains straight; there is no upper-branch tie-break. It can point
through the gap between outlet capsules. This is a sensitivity model, not a
wall-conforming, incompressible, flux-conserving or CFD solution. Smoothing
changes the upstream transition and lateral selection rule simultaneously.

Optional flow disturbance in `TrialConfig` has per-axis velocity standard
deviation `flow_disturbance_m_s`. With the default `flow_correlation_s=0`, it
preserves the original independent Gaussian draw per physics tick. Its
effective integrated noise therefore depends on the timestep.

For positive correlation time tau, the first disturbance is drawn from its
stationary Gaussian distribution and subsequent values use
`w_next = rho*w_previous + sqrt(1-rho^2)*epsilon`, where
`rho = exp(-elapsed_time/tau)` and `epsilon ~ N(0, sigma^2 I)`. This exactly
samples the stationary Ornstein-Uhlenbeck process at the requested timestamps;
the simulator holds each sampled velocity over the next integration interval.
It models persistent synthetic velocity uncertainty, not turbulence, Brownian
motion or a measured physiological disturbance. The Gaussian perturbation is
unbounded and may reverse a velocity component.

The optional fields are plant configuration and never enter the observation-only
navigation interface as ground truth. Histories now record the actual
`flow_velocity_m_s` used over each next integration interval, with NaN at the
terminal sample because no next interval is integrated. Replay diagnostics
use the selected model for the nominal field and exclude disturbance from
the explicitly named nominal net velocity.

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
