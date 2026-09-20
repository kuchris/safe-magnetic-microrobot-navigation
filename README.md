# Safe Magnetic Microrobot Navigation

**Safe Real-Time Closed-Loop Magnetic Navigation of Microrobots in 3D Vascular Networks**

A simulation-first platform for studying navigation with uncertain, delayed
localization. The current working milestone is a **toy Y-vessel with biplane
2D observations, 3D reconstruction, six-state estimation and uncertainty-aware
actuation stopping**.

> Computational research/education only. No human/animal experimental protocol,
> clinical device design, or clinical validity is provided. All runnable
> numerical defaults are **toy parameters**, not medically realistic values.

## Motivation and research question

Can feedback steer a magnetically actuated particle toward a selected vascular
branch while reducing vessel-wall risk under flow, localization error,
calibration error, imaging delay and lost tracking?

Reaching a target alone is insufficient evidence. This project prioritizes
wall clearance, wall violations, wrong-branch events and uncertainty-triggered
stopping over speed. The present experiments test software/model behavior;
they do not establish safety in real vasculature.

## Implemented architecture

```mermaid
flowchart TD
    G["Toy 3D vessel geometry"] --> P["Selected-branch waypoints"]
    G --> S["Uncertainty-aware safety gate"]
    P --> C["Bounded proportional controller"]
    I["Two simulated 2D projections"] --> L["Triangulation and covariance"]
    L --> E["Six-state estimator at current time"]
    E --> C
    E --> S
    C --> H["Optional short-horizon force correction"]
    E --> H
    G --> H
    H --> S
    S --> A["Bounded ideal force and optional gain error"]
    A --> D["Overdamped particle and prescribed flow"]
    D --> I
    D --> M["Ground-truth evaluation"]
```

The software control boundary is `BiplaneNavigation.step(now_s, frames)`.
It accepts only delivered observations and time. True position stays in the
simulated plant/imaging boundary and evaluation. No filter uses truth for
initialization. The older Y demo uses an explicitly ideal observation sensor.

## Physics and assumptions

For a fixed magnetic dipole:

$$
\tau=m\times B,\qquad F_m=\nabla(m\cdot B).
$$

For the initial overdamped spherical-particle approximation:

$$
\gamma=6\pi\eta r,\qquad F_{drag}=\gamma(u-v),\qquad
v\approx u+F_m/\gamma,\qquad p_{k+1}=p_k+\Delta t\,v_k.
$$

SI units: position/radius [m], time [s], velocity [m/s], force [N],
viscosity [Pa s], magnetic moment [A m²], magnetic field [T].

Implemented dynamics use an ideal force-vector abstraction. Torque, dipole
orientation, field gradients and coils are conceptual equations only.
Stokes/overdamped behavior assumes small particle Reynolds number and short
inertial relaxation time; those assumptions are not experimentally validated
for the toy defaults. The prescribed branch-aligned flow is not a hemodynamics
solver and has no radial profile or conserved bifurcation flux.

The geometry is a **union of capsules** with rounded ends. Clearance is
`max_e(radius_e - particle_radius - distance_to_segment_e)`. It is exact for
one capsule and a conservative interior bound at overlaps, **not the exact
union signed-distance field**. Reported collisions mean sampled violations
of this proxy. See [physics and geometry assumptions](docs/02_low_reynolds_flow.md).

## Installation and execution

Python **3.10+** is required. Tested here with Python 3.12, NumPy 2.3.5,
Matplotlib 3.10.8 and pytest 9.1.1.

```bash
git clone https://github.com/kuchris/safe-magnetic-microrobot-navigation.git
cd safe-magnetic-microrobot-navigation
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

On Windows, activate with `.venv\Scripts\activate`. Run simulations **as
modules from the repository root**, so `src` imports resolve:

```bash
python -m simulations.01_free_space
python -m simulations.02_y_vessel
python -m simulations.03_noisy_closed_loop
python -m simulations.04_biplane_localization
python -m simulations.05_latency_safety
python -m simulations.06_benchmark
```

The older 02/03 demos display a plot. For headless runs, prefix with
`MPLBACKEND=Agg` on Unix. The newer 04/05 experiments always save plots without
a display. Direct `python simulations/...` execution is not supported.

```bash
python -m simulations.04_biplane_localization --branch lower --seed 7
python -m simulations.04_biplane_localization --latency 0.10 --noise 2 --dropout 0.05
python -m simulations.04_biplane_localization --output outputs/my_trial
python -m simulations.05_latency_safety --output outputs/stress
```

04 saves `summary.json` (configuration and metrics), `history.npz` and
`diagnostics.png`. 05 saves the same per scenario plus `comparison.json`.
The plots include both trajectories, centerlines, target, stop locations,
localization error, uncertainty, clearance and force components/magnitude.
Generated outputs are ignored by Git and can be reproduced with the commands above.

### Paired-seed policy benchmark

06 compares passive drift, bounded steering without the safety gate, and the
existing gated controller. All policies use the same estimator, sensor settings
and force limit. Ungated steering starts only after the first valid estimate;
it then ignores tracking freshness, uncertainty and wall-margin stops.
The default gated behavior of experiments 04/05 is unchanged.

```bash
# Default: 10 seeds x 4 scenarios x 2 branches x 3 policies = 240 trials.
python -m simulations.06_benchmark
# Smaller pilot: 120 trials, with the same 40-second time limit per trial.
python -m simulations.06_benchmark --seeds 0 1 2 3 4 --output outputs/06_benchmark_pilot
# Restrict a run to selected scenarios.
python -m simulations.06_benchmark --seeds 7 8 --scenarios nominal stale_imaging
# Plot the saved pilot results without rerunning simulations.
python -m simulations.07_plot_benchmark
```

Outputs are `benchmark.json` (every trial's configuration and summary plus
aggregates), `trials.csv` (one row per trial) and `report.md` (English comparison).
Scenarios are nominal imaging, a tracking-loss burst, stale imaging and high
detector noise. Both branches are reported separately. Trials stop at target
success, a wall-proxy violation, or the configured time limit.

Success, wrong-branch and wall-proxy violation rates have per-group 95% Wilson
intervals across seeds. Continuous metrics report trial-level means and
5th/50th/95th percentiles; arrival time is conditional on success. Position
coverage measures error inside a largest-axis 3-sigma ball, not a calibrated
3D confidence ellipsoid. Correlated time samples are not treated as independent
trials. See the [executed pilot report](docs/07_benchmark.md).

![Benchmark success rates with 95% Wilson intervals](docs/figures/benchmark_success_rates.png)

### Failure replay and animation

```bash
python -m simulations.08_failure_replay
```

Replays nine selected pilot trials, verifies their original summaries, records
waypoint/event evidence, checks two cases at finer physics/control timesteps,
and exports four diagnostic figures plus a success/failure GIF. The analysis
distinguishes capsule sidewall proxy events from artificial closed-outlet caps
without changing control behavior or benchmark counts. See the
[failure analysis and animation](docs/08_failure_analysis.md).

### Earlier branch guidance

The experimental route in 09 adds a 0.4 mm lateral offset near the junction,
starting 3 mm upstream and rejoining the selected branch centerline downstream.
The safety gate and 3 nN force cap are unchanged. Set
`TrialConfig(approach_offset_m=0.4e-3)` to use this route programmatically;
the default offset remains zero for reproduction of the original experiments.

```bash
# Each comparison runs both routes: 240 trials per seed set.
python -m simulations.09_approach_guidance
python -m simulations.09_approach_guidance --seeds 5 6 7 8 9 --output outputs/09_approach_guidance/heldout
# Generate comparisons and a before/after animation from both completed sets.
python -m simulations.10_guidance_figures
```

Each comparison saves complete per-route trial records and confidence intervals,
plus matched-seed success changes and terminal sidewall/outlet proxy counts.
See [the approach guidance evaluation](docs/09_approach_guidance.md).

### Flow-model and disturbance sensitivity

```bash
python -m simulations.11_flow_sensitivity --model piecewise
python -m simulations.11_flow_sensitivity --model smooth
python -m simulations.12_flow_sensitivity_figures
```

This study compares both routes with the gate enabled across three flow speeds
(0.3, 0.6 and 1.2 mm/s), three disturbance standard deviations per velocity axis
(0, 0.1 and 0.3 mm/s), both target branches and seeds 10-14: 360 trials total.
The common horizon is 60 seconds; disturbance correlation time is 0.25 seconds.
The smooth field uses continuous direction transitions, but does not enforce
vessel-wall boundaries or conserve flux. Maps show measured trial rates rather
than certified operating limits. See [the sensitivity report](docs/10_flow_sensitivity.md).

Use `TrialConfig(flow_model="smooth", flow_correlation_s=0.25,
flow_disturbance_m_s=0.1e-3)` programmatically. Original piecewise flow and
independent per-tick disturbances remain the defaults for older experiments.

## Current numerical example

Measured seed-7 results for the implemented toy model:

| Scenario | Success | Wall violation | Wrong branch | Min. clearance proxy [mm] | RMSE [mm] | Stop samples [%] | Time to target [s] |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nominal, 50 ms latency | Yes | No | No | 1.3732 | 0.06010 | 0.181 | 27.660 |
| Tracking-loss burst, 8.00–8.75 s | Yes | No | No | 1.3691 | 0.07708 | 2.874 | 27.835 |
| Stale imaging, 250 ms latency | Yes | No | No | 1.3994 | 0.08475 | 100.000 | 35.240 |
| Stale imaging, lower target | No | Yes | Yes | -0.00224 | 0.08431 | 100.000 | — |
| High detector noise, 12 px sigma | Yes | No | No | 1.2406 | 0.32706 | 3.940 | 28.295 |

**The stale-imaging result is passive advection:** active force is zero
throughout. The toy flow chooses the upper branch when y = 0, so this scenario
can reach the upper target without navigation. It is not evidence of controller
effectiveness. 05 also runs `stale_lower_target` to expose this branch-selection
failure when the intended target is the other branch.
That run enters the upper branch and eventually violates the artificial
rounded outlet boundary at 38.24 s, with zero active force throughout.

The free-space example ends at [2, 1, 0] mm. The baseline suite had eight tests;
the expanded suite passes 109 tests covering imaging, uncertainty, timing,
safety, both branches, policy ablations, benchmark statistics, replay diagnostics,
pre-junction route guidance, continuous flow and correlated disturbances.
See [inspection and verification record](docs/06_validation.md) for measured
results and known limitations. The seed-7 examples above are deterministic
scenarios; the separate paired-seed benchmark reports conditional trial rates.

![Seed-7 biplane navigation diagnostics](docs/figures/biplane_diagnostics.png)

## Imaging, estimation and safety

- Two configurable orthographic views produce noisy 2D detector coordinates.
  This does not render medical images or model segmentation.
- SVD-based reconstruction supports arbitrary view orientations, origins,
  pixel sizes and offsets. Singular geometry is rejected. Random detector
  covariance is propagated into full 3D covariance.
- A fixed detector-offset calibration error is sampled once per trial.
  Its uncertainty is retained as a floor that repeated frames cannot remove.
- Configurable frame rate, fixed latency, stochastic pair dropout and dropout
  bursts are supported. Frames carry capture and delivery timestamps.
- The Kalman state is `[px,py,pz,vx,vy,vz]`. Prediction and update are separate.
  Updates occur at capture time, with a predicted copy exposed at control time.
- Safety requires
  `estimated_clearance - k_sigma * position_uncertainty > safety_margin`.
  Large uncertainty, lost tracking, stale images or low robust clearance
  produce zero active force. This does **not** stop flow-driven motion.
- Logged reasons are `tracking_lost`, `localization_uncertain`,
  `wall_margin_low`, `actuation_limit`, `prediction_adjustment` and `safe`. Saturation is distinct
  from stopping. A three-sigma margin is not a proven 3D collision-risk bound.

See [biplane imaging](docs/03_biplane_localization.md),
[state estimation](docs/04_state_estimation.md) and
[safety/control](docs/05_safety_control.md).

## Parameter provenance

**Every numerical default below is toy, none is experimentally validated.**
Equations are textbook idealizations; no empirical physiological calibration
or literature-derived parameter set is claimed.

| Parameter | Biplane default |
|---|---|
| Vessel radius / particle radius | 1.5 mm / 0.1 mm |
| Viscosity / prescribed flow speed | 3.5e-3 Pa s / 0.6 mm/s |
| Physics timestep / time limit | 5 ms / 40 s |
| Frame rate / fixed latency | 20 Hz / 50 ms |
| Detector pixel size / independent noise sigma | 50 µm/px / 1 px |
| Fixed calibration-offset prior sigma | 0.25 px per detector coordinate |
| Pair dropout / flow disturbance / actuation gain error | 0 / 0 / 0 |
| Force limit / proportional gain | 3 nN / 2e-6 N/m |
| Safety margin / largest-axis sigma limit | 0.20 mm / 0.35 mm |
| Sigma multiplier / maximum capture age | 3 / 150 ms |
| Initial velocity mean / sigma | 0 / 1 mm/s per axis |
| Acceleration spectral density | 1e-7 m²/s³ |
| Waypoint spacing / advance tolerance | 0.5 mm / 0.3 mm |
| Target tolerance / wrong-branch exclusion radius | 0.4 mm / 2 mm |

Programmatic experiment configuration lives in `TrialConfig`; view geometry
and filter options can also be configured through their component APIs.
Legacy demos retain their original toy parameter choices.

### Optional short-horizon correction

An experimental correction predicts motion for 0.5 s using estimated position,
velocity, covariance and previous commanded force. It can redirect force before
the current wall-margin gate stops actuation. The existing gate and 3 nN cap
still apply; prediction is disabled by default (`prediction_horizon_s=0`).

```bash
python -m simulations.13_predictive_control --model piecewise
python -m simulations.13_predictive_control --model smooth
python -m simulations.14_predictive_figures
```

The fixed 160-trial comparison uses new seeds 15-19, both fields and branches,
0.6/1.2 mm/s flow and 0/0.3 mm/s per-axis disturbance. Both controllers use early
guidance. One failure became a success in the piecewise field; continuous-field
success counts were unchanged, with no success regressions in either field.
This limited result does not establish a reliable general improvement.
See [the method, paired results and failure replays](docs/11_predictive_control.md).

## Repository structure

```text
src/
  particle.py           Overdamped Stokes dynamics
  vessel.py             Capsule Y geometry and clearance proxy
  flow.py               Piecewise/smooth flow and correlated disturbances
  flow_sensitivity.py   Trial summaries and flow-holding demand diagnostics
  imaging.py            Orthographic projections and delayed/dropout frames
  localization.py       Legacy sensor/filter, triangulation, six-state filter
  planner.py            Selected Y-branch waypoints and branch evaluation
  controller.py         Proportional control and force cap
  prediction.py         Optional sampled short-horizon force correction
  safety.py             Uncertainty, freshness and wall-margin gate
  navigation.py         Observation-only feedback boundary
  experiment.py         Seeded trial, histories and metrics
  benchmark.py          Policy comparison, trial statistics and report export
  failure_analysis.py   Replay event states and terminal capsule features
  replay_plotting.py    Paired diagnostics and trajectory animation
  plotting.py           Reproducible diagnostic figure
  validation.py         Numerical input validation
simulations/
  01_free_space.py
  02_y_vessel.py
  03_noisy_closed_loop.py
  04_biplane_localization.py
  05_latency_safety.py
  06_benchmark.py
  07_plot_benchmark.py
  08_failure_replay.py
  09_approach_guidance.py
  10_guidance_figures.py
  11_flow_sensitivity.py
  12_flow_sensitivity_figures.py
  13_predictive_control.py
  14_predictive_figures.py
docs/                    Physics, imaging, estimation, safety, verification
tests/                   Deterministic physics, numerical and integration tests
```

## Progress and roadmap

- [x] Overdamped particle integration, prescribed flow and capsule Y-vessel
- [x] Bounded proportional control and direct noisy-observation baseline
- [x] Biplane coordinate projection and covariance-aware reconstruction
- [x] Configurable frame rate, fixed latency, dropout and fixed-offset calibration error
- [x] Six-state filter with separate prediction/update and capture-time handling
- [x] Observation-only navigation and robust-clearance stop gate
- [x] Explicit upper/lower Y branch and centerline waypoint following
- [x] Logged stop reasons, wrong-branch flag, seeded trials and diagnostic plots
- [x] Deterministic latency/dropout/noise stress scenarios and regression tests
- [x] Optional pre-junction lateral guidance with matched original/new-seed evaluation
- [x] Optional short-horizon correction with unchanged gates and held-out comparison
- [ ] General vascular graph routing and branch-crossing surfaces
- [ ] Exact union/mesh wall distance and swept collision checking
- [ ] Perspective/raster imaging, segmentation, outliers and single-view handling
- [ ] Rotation/scale calibration estimation and variable-latency replay
- [ ] Abstract coil matrix A(x), bounded current allocation, unreachable-force diagnostics
- [x] Paired-seed policy benchmark, trial distributions and conditional outcome-rate intervals
- [ ] Control-input-aware estimation and flow disturbance estimation
- [ ] Formal predictive safety constraints, MPC / Control Barrier Functions
- [ ] Synthetic/public mesh import and improved fluid/near-wall physics

No RL, coil-current solver, general vascular graph or mesh loader is claimed
complete. Benchmark rates describe only the configured toy scenarios, not
general safety. The current supervisor is a reactive gate, not a
formal safety guarantee. There is no full cerebral hemodynamics model.
