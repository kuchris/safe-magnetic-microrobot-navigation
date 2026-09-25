# Combined perturbations at the 99% operating point (experiment 29)

Computational research and education only. This note tests control policies in
a toy Y-vessel with physiological parameters. It is not a device design, not a
safety claim and not clinical guidance.

## Question

Experiment 28 ([docs/20](20_operating_point_robustness.md)) perturbed the 99%
operating point one imperfection at a time. A real procedure would face
several at once. **Does the operating point survive a plausible bundle of
imperfections, and where does it give way?**

Claude chose this step under the standing instruction to keep going.

## Design

Both materials use the command-aware estimator, the actuation-limited gain,
the matched gate and the **open-loop gravity hold**. The hold follows the
experiment 28 follow-up, which showed that a tracking-gated hold fails the
composite during dropouts. The arms are the composite `C_P2` with
`gravity_hold_from_release` added, and pure NdFeB `N_P2_hold`. The flow
reduction is 99%. Each bundle applies every change listed at once. All values
are **assumed**.

| Bundle | Latency | Gain error | Gravity tilt | Calibration σ | Detector σ | Gradient cap | Dropout |
|---|---:|---:|---:|---:|---:|---:|---|
| nominal | 50 ms | 0 | 0° | 0.25 px | 1 px | 1 T/m | none |
| mild | 100 ms | −10% | 5° | 0.5 px | 2 px | 0.5 T/m | none |
| moderate | 100 ms | −20% | 10° | 1 px | 3 px | 0.5 T/m | 0.3–0.5 s |
| severe | 200 ms | −20% | 15° | 1 px | 3 px | 0.25 T/m | 0.3–0.6 s |

The trials cover 7.5, 15 and 30 fps, patent and occluded targets, both
branches and held-out seeds 3–5: 288 trials in all. The command is
`python -m simulations.29_combined_perturbations`.

## Pre-registered hypotheses

- **H20:** The mild bundle keeps at least 90% of successes.
- **H21:** The moderate bundle keeps at least 70%.
- **H22:** The severe bundle keeps fewer than 50%, with failures concentrated
  at 7.5 fps and in pure NdFeB.

## Results

Held-out successes, 288 trials:

| Bundle | Total /72 [95% CI] | Composite patent / occluded | NdFeB patent / occluded | 7.5 / 15 / 30 fps (of 24) |
|---|---|---|---|---|
| nominal | **72** [95%, 100%] | 18 / 18 | 18 / 18 | 24 / 24 / 24 |
| mild | **68** [87%, 98%] | 18 / 18 | 16 / 16 | 20 / 24 / 24 |
| moderate | 33 [35%, 57%] | 16 / 17 | **0 / 0** | 10 / 11 / 12 |
| severe | 11 [9%, 25%] | 4 / 7 | 0 / 0 | 4 / 4 / 3 |

Every failure is a wall contact.

| Hypothesis | Outcome |
|---|---|
| H20: mild keeps ≥ 90% | **Supported.** 68/72 (94%); the 4 losses are pure NdFeB at 7.5 fps |
| H21: moderate keeps ≥ 70% | **Not supported.** 33/72. The composite keeps 33/36, but pure NdFeB fails all 36 trials at every frame rate |
| H22: severe < 50%, with failures concentrated at 7.5 fps and in pure NdFeB | **Partly.** 11/72, and pure NdFeB is 0/36. The failures are spread evenly across frame rates, not concentrated at 7.5 fps |

### Why pure NdFeB fails the moderate bundle (exploratory, not pre-registered)

Two analyses were run after seeing the result. Both use pure NdFeB, the 36
held-out cells, and the moderate bundle.

**Removing one ingredient never helps.** Resetting any single ingredient of
the moderate bundle to nominal leaves pure NdFeB at 0/36: latency, gain error,
tilt, calibration, noise, gradient or dropout. The failure is redundant;
several ingredients are each enough, given the rest.

**Adding one step to mild shows which ingredients matter.** Starting from mild
(32/36 for pure NdFeB) and raising one field to its moderate value:

| Raised to the moderate value | Pure NdFeB success | 7.5 / 15 / 30 fps |
|---|---:|---|
| dropout 0.3–0.5 s | **4/36** | 3 / 1 / 0 |
| actuation gain −10% → −20% | 12/36 | 0 / 0 / 12 |
| gravity tilt 5° → 10° | 20/36 | 0 / 8 / 12 |
| detector noise 2 → 3 px | 24/36 | 0 / 12 / 12 |
| calibration 0.5 → 1 px | 28/36 | 4 / 12 / 12 |

**Mechanism.** A replayed moderate trial (30 fps, patent, seed 3) shows the
chain.

1. Before the first frame arrives at 100 ms, the open-loop hold delivers only
   80% of the weight (gain −20%), and 10° off vertical. Pure NdFeB drifts
   down and sideways at about 7–10 mm/s; its clearance falls from 1.4 to
   0.52 mm by 0.1 s.
2. The weight-aware, command-aware estimator trusts its model, so it predicts
   no motion from the hold and keeps the estimate near the centerline. At
   0.15 s the estimate is still at z ≈ −0.1 mm while the particle is at
   −1.23 mm, touching the wall.

Any bias in the hold, from a gain error or a wrong gravity direction, is a
force the estimator does not model. For pure NdFeB, whose weight is 7× the
composite's, that bias is large. Only fresh, frequent frames can reveal it.
That is why dropout, low frame rate and latency, each harmless alone, become
fatal once the hold is biased. It is the known weakness of a Smith-predictor
structure: a confident model is wrong in proportion to its mismatch.

## Interpretation

- **The composite particle is the robust choice in this model.** It keeps
  33/36 under the moderate bundle, and its failures under the severe bundle
  are spread across conditions.
- **Pure NdFeB is fragile to combined imperfections.** At 15–30 fps it
  survived every single imperfection in docs/20 except a 30° gravity error.
  It does not survive their combination, because its large weight turns small
  hold errors into fast unmodeled drift.
- **The estimator needs a way to learn a constant force bias quickly.** The
  residual filter treats unmodeled drift as slowly varying flow. A
  disturbance-force state (integral action) would learn a biased hold within a
  few frames. That is the natural next test.

## Limitations

Everything in docs/15–20 applies. In addition:

- The bundles are illustrative, not measured error budgets.
- Both analyses of the moderate bundle were exploratory and cover only pure
  NdFeB.
- The gain error scales every command, including the hold. A real system
  might calibrate the hold separately.
