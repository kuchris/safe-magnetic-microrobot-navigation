# Repository inspection and validation record

## Starting point

Inspected upstream main at `a17effa4d91a2b44b2d4d7d32a5b2c8fe6d1c914`, including
all 15 tracked files: README, one study note, requirements, six source
modules, three simulations and three test files. No AGENTS.md was present.

The existing implementation had Stokes dynamics, capsule Y geometry,
piecewise flow, bounded target control, a direct noisy 3D sensor, a 3D
random-walk filter, and a basic uncertainty/clearance gate. It had no biplane
imaging, latency/dropout scheduler, six-state filter or explicit route.

No code was changed before baseline execution. pytest was absent from the
execution environment; installing the repository's requirements resolved
that environment issue. Baseline: **8 tests passed**.

| Baseline simulation | Observed result |
|---|---|
| Free space | Final position [2,1,0] mm |
| Y vessel | Target reached; no wall violation; min. clearance 1.282859 mm; 4,126 steps |
| Direct noisy loop | Target reached; 0 stop frames; min. clearance 1.282927 mm |

Direct script invocation failed with `ModuleNotFoundError: src`. Module
execution from the repository root succeeded. README now documents that
supported invocation instead of relying on an unstated PYTHONPATH.

## Defects corrected

- The old safety gate treated uncertainty and margin separately: it could
  allow a state whose uncertainty reached the wall. It now uses robust margin.
- The old Y control used true position directly. It now obtains an explicit
  ideal observation, preserving the baseline through a sensor boundary.
- The noisy loop initialized from true position. It now initializes from a
  sensor measurement. Its prediction includes commanded drift, and its
  estimated/true logged samples refer to the same time.
- The original geometry was described as cylinders although distance to a
  finite line segment defines capsules. Geometry behavior is preserved;
  descriptions now identify the conservative union-clearance approximation.
- Added checks for invalid particle values, nonfinite integration inputs,
  force limits, invalid state, measurement age and tracking loss.
- The retained random-walk filter now uses a Joseph covariance update.

## Implemented milestone

The observation-only navigation interface connects configurable biplane
coordinate projection, delayed/noisy/dropout observations, covariance-aware
reconstruction, a six-state capture-time Kalman filter, selected Y-branch
waypoints, and an uncertainty/freshness-aware stop gate. The ideal force
plant includes optional scalar calibration gain error, not coil currents.

Added tests cover known and random 3D points under rotated/translated/scaled
detectors, singular/near-singular geometry, empirical reconstruction-noise
covariance (5,000 seeded samples), timing, skipped acquisition slots,
dropout/recovery, persistent calibration floor, Kalman kinematics/covariance,
latency extrapolation, invalid input, force saturation, robust stops,
wrong-branch classification, both branches end-to-end, and stale-data failure.

## Executed verification

Environment: Python 3.12, NumPy 2.3.5, Matplotlib 3.10.8, pytest 9.1.1.

```bash
python -m pytest -q                         # 57 passed
python -m simulations.01_free_space
MPLBACKEND=Agg python -m simulations.02_y_vessel
MPLBACKEND=Agg python -m simulations.03_noisy_closed_loop
python -m simulations.04_biplane_localization
python -m simulations.05_latency_safety
git diff --check
```

All executed successfully. No hardware, clinical or external dataset
validation was performed. The updated legacy demos retain their observed
target success and no wall violations. Test counts include parametrized cases.

Full seeded stress metrics and configurations are in
[`results/seed_7_scenarios.json`](results/seed_7_scenarios.json). The nominal
diagnostic plot is in [`figures/biplane_diagnostics.png`](figures/biplane_diagnostics.png).
The five stress cases use the same seed but different configurations; they
are deliberately chosen scenarios, not independent Monte Carlo samples.

| Scenario | Outcome | Main evidence |
|---|---|---|
| Nominal | Target success | 27.660 s; RMSE 0.06010 mm; min. proxy clearance 1.37321 mm |
| Dropout burst | Target success, recovered tracking | 160 stopped samples; 2 stop events including startup |
| Stale upper target | Passive target arrival | All 7,049 samples stopped; maximum force 0 N |
| Stale lower target | Wrong branch and wall-proxy violation | All 7,649 samples stopped; failure at 38.240 s |
| High noise | Target success with uncertainty/wall stops | 30 uncertainty stops and 183 wall-margin stops |

The lower-target stale run proves that the fail-safe action is not an
immobilization or successful-navigation guarantee: the toy flow chooses upper
when y=0. It later crosses the artificial closed capsule outlet. That violation
depends on the toy outlet boundary, not a physical vascular endpoint model.

## Files and remaining limitations

New components: `imaging.py`, the biplane/six-state portions of `localization.py`,
`navigation.py`, `planner.py`, `experiment.py`, `plotting.py`, `validation.py`.
New experiments: 04 and 05. Existing particle, controller, safety, geometry,
02/03 simulations and tests were extended, not discarded. README and four
model notes describe the implemented behavior and pending work.

Limitations: orthographic coordinate observations rather than raster imaging;
fixed-offset calibration only; ordered fixed latency rather than arbitrary
out-of-sequence updates; constant-velocity process model without input-aware
dynamics; covariance not empirically certified coverage; reactive stop gate
rather than predictive collision prevention; discrete capsule-clearance
proxy rather than exact/swept mesh contact; Y-specific routing/classification;
prescribed flow; ideal force rather than coils. Frame capture/delivery are
quantized to physics ticks. No general Monte Carlo experiment, graph/mesh
loader, coil allocation solver, MPC, CBF or RL is claimed implemented.

All numerical defaults are toy. Favorable results are reproducible software
examples, not medically realistic navigation or evidence of clinical validity.

## Subsequent paired-seed benchmark milestone

The original verification record above describes the biplane milestone.
The benchmark extension adds passive and ungated policy ablations while
preserving gated control as the default, plus trial-level position coverage,
outcome-rate intervals and English report/CSV/JSON export. The suite now passes
68 tests, including force-cap retention during ablations, startup without
observations, stale/dropout behavior, known Wilson intervals, paired-seed
reproducibility, missing-metric handling and export validation.

The completed 120-trial pilot and its environment, measured failures and full
statistics are recorded in [the benchmark report](07_benchmark.md). This adds
conditional Monte Carlo results across detector-noise/calibration seeds;
the geometry, physics, predictive-control and clinical limitations above remain.

## Subsequent failure replay milestone

Nine selected pilot trial summaries were reproduced exactly after adding
read-only waypoint history fields. Offline event classification distinguishes
capsule sidewall and closed-outlet cap proxies. Four extra runs checked two
failures at 2.5 ms and 1 ms physics/control resolution; both failures persisted.
The expanded suite passes 72 tests. Four diagnostic figures and a 140-frame
paired GIF were generated and inspected. See
[failure analysis](08_failure_analysis.md) for evidence and remaining limits.

## Subsequent approach-guidance milestone

An optional geometry-only approach offset was evaluated with the original
pilot seeds and a separate validation seed set: 480 original/guided executions
covering 240 matched cases. All 120 rerun original pilot summaries matched
their archived values. Sixteen failures became successes and no successes
regressed; terminal capsule sidewall proxy violations fell from nine to zero.
Stale-data gated failures persisted, and nominal minimum clearance decreased
as expected from the lateral displacement. All 82 tests passed. See
[approach guidance](09_approach_guidance.md) for grouped rates, uncertainty,
clearance tradeoffs, recorded configurations and the before/after animation.

## Subsequent flow-sensitivity milestone

An optional continuous prescribed field and temporally correlated Gaussian
velocity disturbance were added while retaining the original defaults and
archived-trial reproduction. A 360-trial study covers two fields, three mean
speeds, three disturbance amplitudes, two routes, both branches and seeds
10-14. Early guidance rescued 11 piecewise and seven continuous-field cases,
with no success regressions; substantial strong-disturbance failures remain.
All 95 tests passed, including process statistics and interval-aligned flow
logging. See [flow sensitivity](10_flow_sensitivity.md) for conditional rates,
holding-capacity diagnostics, raw records and model limitations.
