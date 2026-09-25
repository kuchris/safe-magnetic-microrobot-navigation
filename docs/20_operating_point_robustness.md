# How robust is the 99% operating point? (experiment 28)

Computational research and education only. This note tests control policies in
a toy Y-vessel with physiological parameters. It is not a device design, not a
safety claim and not clinical guidance.

## Question

Experiments 23–26 ([docs/16](16_delay_aware_control.md)–[19](19_measured_flow_map.md))
point to one operating point that works in this model:

- 99% proximal flow reduction;
- a command-aware estimator with the gain set by the 10 ms actuation period;
- a gravity hold (for pure NdFeB, from release).

It succeeded in every trial, for both materials and both target states. Those
trials all used the same idealized imaging and actuation. **How far can these
depart from the ideal before the operating point breaks?**

Claude chose this step under the standing instruction to keep going.

## A confound found while designing

The safety gate stops steering when the newest measurement is older than
`max_measurement_age_s`. That limit has been 0.15 s since the toy experiments.
At 7.5 fps with 50 ms latency, a measurement ages to 0.05 + 0.133 = 0.183 s
before the next one arrives. So at 7.5 fps the gate also stops the controller
for part of every frame period: `tracking_lost` takes 14% of samples at 7.5
fps against 7% at 15–30 fps in experiment 24. The "7.5 fps floor" reported in
docs/17–19 may therefore be partly this setting rather than the physics.

This experiment therefore matches the gate to the imaging:
`max_measurement_age_s = latency + 1/fps + 20 ms` (the margin is assumed). It
also re-runs experiment 24's model-feedforward arms at 90% reduction with the
matched gate, paired trial by trial against the fixed 0.15 s gate.

## Design

`python -m simulations.28_operating_point_robustness` runs 1080 trials on
held-out seeds 3–5, with both branches, both target states and 7.5, 15 and
30 fps.

- **Robustness at 99%.** The arms are `C_P2` (composite) and `N_P2_hold` (pure
  NdFeB, release hold), each with one perturbation at a time. All magnitudes
  are **assumed**.

| Condition | Change from nominal |
|---|---|
| nominal_fixed_gate | None (0.15 s gate, as in experiments 22–26) |
| nominal | Matched gate (every condition below also uses it) |
| latency 0.1 s / 0.2 s | Imaging latency 50 ms → 100 / 200 ms |
| dropout 0.3 s | No frames between 0.3 s and 0.6 s |
| gain −20% / +20% | Delivered force differs from the command by −20% / +20% |
| gradient 0.5 / 0.25 T/m | Weaker cap, for example from depth decay or a smaller system |
| gravity tilt 15° / 30° | The controller's assumed gravity direction is off by that angle (patient orientation) |
| calibration 1 px | Calibration offset σ 0.25 → 1 px |
| noise 3 px | Detector noise σ 1 → 3 px |

- **Gate check at 90%.** The arms are `C_P2_modelff` and `N_P2_modelff_hold`,
  each run with the fixed and the matched gate.

## Pre-registered hypotheses

- **H14:** Latency 0.1 s keeps at least 80% of nominal successes; 0.2 s keeps
  at least 50%.
- **H15:** An actuation gain error of ±20% keeps at least 80%.
- **H16:** Gradients of 0.5 and 0.25 T/m keep at least 80%.
- **H17:** A 15° gravity tilt is tolerable; at 30°, pure NdFeB starts to fail.
- **H18:** A 0.3 s dropout keeps at least 50%.
- **H19:** With the matched gate, 7.5 fps at 90% reduction produces successes,
  so the floor was partly the gate setting.

## Results

Both nominal conditions reach **72/72**. The gate setting makes no difference
at 99%. Held-out successes out of 18 per cell at 99% reduction:

| Condition | Composite patent | Composite occluded | NdFeB patent | NdFeB occluded | Total /72 | By fps (7.5 / 15 / 30) | Lost vs nominal |
|---|---:|---:|---:|---:|---:|---|---:|
| nominal (either gate) | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | — |
| latency 0.1 s | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | 0 |
| latency 0.2 s | 10 | 13 | 18 | 18 | 59 | 16 / 19 / 24 | 13 |
| dropout 0.3 s | **0** | **0** | 18 | 9 | 27 | 12 / 9 / 6 | 45 |
| gain −20% | 18 | 18 | 12 | 12 | 60 | 12 / 24 / 24 | 12 |
| gain +20% | 18 | 18 | 14 | 14 | 64 | 16 / 24 / 24 | 8 |
| gradient 0.5 T/m | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | 0 |
| gradient 0.25 T/m | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | 0 |
| gravity tilt 15° | 18 | 18 | 12 | 12 | 60 | 12 / 24 / 24 | 12 |
| gravity tilt 30° | 18 | 18 | **0** | **0** | 36 | 12 / 12 / 12 | 36 |
| calibration 1 px | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | 0 |
| noise 3 px | 18 | 18 | 18 | 18 | **72** | 24 / 24 / 24 | 0 |

No perturbation rescued a trial; every change against nominal is a loss.

| Hypothesis | Outcome |
|---|---|
| H14: latency 0.1 s keeps ≥ 80%, 0.2 s keeps ≥ 50% | **Supported.** 72/72 and 59/72 (82%). Only the composite loses trials at 0.2 s |
| H15: gain ±20% keeps ≥ 80% | **Supported, barely.** 60/72 (83%) and 64/72. Every loss is pure NdFeB at 7.5 fps |
| H16: 0.5 and 0.25 T/m keep ≥ 80% | **Supported.** 72/72 for both |
| H17: tilt 15° tolerable, 30° starts failing pure NdFeB | **Partly.** At 15° pure NdFeB already loses its 7.5 fps cells (12 trials). At 30° it fails every trial (0/36). The composite is unaffected at both |
| H18: a 0.3 s dropout keeps ≥ 50% | **Not supported.** 27/72, and the composite drops to **0/36** |
| H19: the matched gate gives 7.5 fps successes at 90% | **Not supported.** Identical outcomes in all 72 paired trials (32 successes, 7.5 fps still 0). The 7.5 fps floor in docs/17–19 is not a gate artifact |

### Why the dropout breaks the composite

The composite's gravity hold waits for valid tracking. During a dropout the
gate reports `tracking_lost`, the command, hold included, drops to zero, and
the particle settles at ~6 mm/s. In a replayed trial, clearance fell from
1.37 mm to 0.27 mm during the 0.3 s gap. Pure NdFeB holds from release
without tracking, so it keeps holding through the gap. It still loses 9
occluded-target trials, to wrong branches and walls.

**Exploratory follow-up (not pre-registered).** Giving the composite the
same open-loop hold (`gravity_hold_from_release`) was run afterwards on the
same held-out cells, 72 trials in all:

| Composite with open-loop hold | Success |
|---|---:|
| nominal | 36/36 |
| dropout 0.3 s | **30/36** (against 0/36 with the tracking-gated hold) |

So the hold should not depend on tracking. That is an easy change in this
model, because the weight and the gravity direction are assumed known.

## Interpretation

- **The operating point tolerates most imperfections tested here.** It is
  unaffected by latency up to 0.1 s, gradients down to 0.25 T/m (a quarter of
  the eMNS reference), 1 px calibration error and 3 px detector noise. The
  force needed at 99% reduction is far below the cap, and the command-aware
  estimator absorbs the delay.
- **Three things break it:**
  1. **Losing the gravity hold.** It is lost in a dropout when the hold is
     tracking-gated, or when the assumed gravity direction is 30° off; 15°
     already costs pure NdFeB its 7.5 fps cells.
  2. **Actuation gain errors on pure NdFeB at 7.5 fps.** Its large force cap
     and weight make a 20% gain error a large absolute force error, and 7.5
     fps is too slow to correct it before contact.
  3. **Long latency (0.2 s) for the composite.**
- **Pure NdFeB is the more demanding material.** It depends completely on the
  hold (its weight is 7× the composite's), so errors in the weight model hurt
  it most. The light composite tolerates hold errors but needs the hold to
  keep running through tracking gaps.
- **The 7.5 fps floor is real in this model.** The gate check confirms that
  it comes from the imaging rate itself at 90% reduction.

## Limitations

Everything in docs/15–19 applies. In addition:

- One perturbation at a time; combined perturbations are untested.
- The gain error is uniform and constant. Real field errors vary with
  position and direction.
- The gravity tilt rotates only about the parent axis.
- The follow-up was run after seeing the dropout result and was not
  pre-registered.
