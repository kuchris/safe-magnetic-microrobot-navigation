# Safe Magnetic Microrobot Navigation

A simulation-first research project on **safety-constrained, closed-loop magnetic microrobot navigation in 3D vascular networks**.

> Research/education only. This repository does not describe or validate a device for use in humans or animals.

## Research question

Can a magnetically actuated particle be navigated through a complex 3D vascular network toward a target while maintaining vessel-wall safety under fluid-flow disturbances, localization uncertainty, and magnetic-control error?

## MVP

Navigate one simulated magnetic particle through a **3D Y-shaped vessel bifurcation** without touching the vessel wall.

We deliberately start simple: no real blood, drugs, animals, patients, or clinical hardware.

## Learning path

1. Magnetic actuation: field, gradient, force, torque
2. Low-Reynolds-number fluid dynamics and drag
3. 3D vessel geometry and bifurcations
4. Real-time localization and state estimation
5. Closed-loop control
6. Safety constraints and fail-safe behavior
7. Monte-Carlo robustness testing

## Core equations

Magnetic torque:

```text
tau = m x B
```

Magnetic force (dipole approximation):

```text
F_m = grad(m . B)
```

Low-Reynolds-number Stokes drag for a spherical particle:

```text
F_drag = 6 pi eta r (u - v)
```

The first simulator uses an overdamped model: drag dominates inertia, so particle velocity is determined primarily by local flow plus magnetically induced drift.

## Safety objective

Reaching the target is not enough. We will track minimum wall clearance, wall-collision rate, wrong-branch rate, target success rate, navigation time, and sensitivity to localization noise/latency.

The controller must enter a safe state when localization uncertainty becomes too large.

## Repository layout

```text
docs/            Study notes
src/             Simulation modules
simulations/     Runnable experiments
tests/           Physics/unit tests
```

## Start here

Read [`docs/01_magnetic_actuation.md`](docs/01_magnetic_actuation.md), then inspect and run [`simulations/01_free_space.py`](simulations/01_free_space.py).

## Roadmap

### Phase 1 — Foundations
- [x] Define research question and safety scope
- [x] Study magnetic force vs torque
- [x] Implement first free-space overdamped particle model
- [ ] Implement 3D Y-vessel geometry
- [ ] Implement simple laminar flow

### Phase 2 — Closed-loop navigation
- [ ] Add noisy position measurements
- [ ] Add state estimator (Kalman/EKF)
- [ ] Add path-following controller
- [ ] Add vessel-wall safety constraint

### Phase 3 — Robustness
- [ ] Localization noise
- [ ] Imaging latency
- [ ] Flow disturbances
- [ ] Magnetic calibration error
- [ ] Monte-Carlo safety evaluation

## Guiding principle

**If the system is uncertain about where the particle is, it should become less aggressive, not more aggressive.**
