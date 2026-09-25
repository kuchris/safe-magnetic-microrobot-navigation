# What the physiological-scale experiments show (experiments 22–30)

Computational research and education only. This is a summary of simulations
in a toy Y-vessel with physiological parameters. It is not a device design, a
safety claim or clinical guidance, and none of its thresholds come from
measurement.

Each finding below links to the note with its design, pre-registered
hypotheses and limitations. Rates are held-out results unless stated. They are
conditional on the toy geometry, the idealized flow and the assumed
parameters listed in [docs/15](15_physiological_sweep.md#preset-srcpresetspy).

## The problem in one line

A 100 µm magnetic sphere in M1-scale flow (0.3 m/s mean) crosses a 10 mm
approach in about 33 ms. That is less than one imaging frame plus 50 ms of
latency, so without flow reduction no feedback policy acts in time
([docs/15](15_physiological_sweep.md)).

## What works in this model

**99% proximal flow reduction, with the following controller:**

| Element | Why | Evidence |
|---|---|---|
| Command-aware estimator | Predicts the motion the controller itself commanded, so the gain can follow the 10 ms actuation period instead of the imaging delay | Occluded targets 18/18 against 1/18 ([docs/16](16_delay_aware_control.md)) |
| Gravity hold from release, not waiting for tracking | Pure NdFeB sinks to the wall before the first frame otherwise; any hold that stops with tracking fails in a dropout | Pure NdFeB 0/432 → 18/18 ([docs/17](17_feedforward_and_hold.md)); composite in a 0.3 s dropout 0/36 → 30/36 ([docs/20](20_operating_point_robustness.md)) |
| Estimator told the known weight | Otherwise a held weight reads as commanded motion | [docs/17](17_feedforward_and_hold.md) |
| 15 fps or faster | 7.5 fps fails at 90% reduction in every condition; a gate check confirmed that is not a gate setting | [docs/17](17_feedforward_and_hold.md), [docs/20](20_operating_point_robustness.md) |
| Light composite particle (assumed 2000 kg/m³, 14% NdFeB) | Its weight is 7× smaller, so errors in the hold drift 7× slower | Moderate combined bundle: composite 33/36, pure NdFeB 0/36 ([docs/21](21_combined_perturbations.md)) |

At this operating point, each of the following alone costs nothing (72/72):
latency up to 0.1 s, gradients down to 0.25 T/m, 1 px calibration error,
3 px detector noise, ±20% drag-model error, and flow-model errors of any kind
tested.

## Where it breaks

| Limit | Result | Note |
|---|---|---|
| 90% flow reduction | Needs model feedforward from an accurate local flow field: exact model or a map of 0.5 mm or finer, noise ≤ 5% (32–41/72). A 20% speed bias, a wrong pulsation amplitude, or a 0.25-period timing error removes the benefit. Errors in where the flow turns at the split swing occluded targets from 19/36 to 0/36 | [docs/18](18_flow_model_errors.md), [docs/19](19_measured_flow_map.md) |
| Biased gravity hold (gain or direction error) | Pure NdFeB fails once the unmodeled drift reaches the wall before frames reveal it, roughly v_bias × (latency + 2/fps) > clearance. A faster estimator cannot fix this; it trips the gate instead | [docs/21](21_combined_perturbations.md), [docs/22](22_disturbance_rejection.md) |
| Dropouts | Fatal for any tracking-gated hold, and for pure NdFeB once its hold is biased | [docs/20](20_operating_point_robustness.md), [docs/21](21_combined_perturbations.md) |
| Latency 0.2 s | Composite loses 13/36 | [docs/20](20_operating_point_robustness.md) |
| Gravity direction 30° off | Pure NdFeB 0/36 | [docs/20](20_operating_point_robustness.md) |

## What did not help

- **Estimated-flow feedforward at 99%.** The flow force is small next to the
  feedback force ([docs/16](16_delay_aware_control.md)).
- **Wall prediction with a delay-length horizon.** It regresses at 7.5 fps. A
  50 ms horizon is harmless but adds nothing ([docs/16](16_delay_aware_control.md),
  [docs/17](17_feedforward_and_hold.md)).
- **A faster residual filter against a large hold bias.** It adds uncertainty,
  not speed ([docs/22](22_disturbance_rejection.md)).

## Recurring caveats

- The binary success flag (≤ 0.4 mm) is brittle near its threshold, and
  closed-outlet contacts are a geometry artifact. Several notes report the
  continuous closest approach and terminal wall features for this reason.
- At 90% reduction the outcome sits on a knife edge. Changes too small to
  matter by any average can move rates by a factor of two either way
  ([docs/18](18_flow_model_errors.md)).
- The flow is not CFD, the vessel is three capsules, the imaging is idealized
  biplane, and the actuation is a force cap with a zero-order hold. Imaging a
  100 µm particle through the skull, and embolic risk, are outside the model
  ([docs/14](14_feasibility.md)).

## Open problems

1. Calibrating the gravity hold (gain and direction) before release, and what
   residual bias is achievable.
2. Measuring flow locally at the split in real time, not before the procedure.
3. Combined model errors at 90% reduction, and spatially correlated noise in
   flow maps.
4. A wall-conforming flow model (CFD) and a mesh geometry, to check whether
   the knife edge at the split survives.
5. Coil dynamics, gradient decay with depth and field–gradient coupling, in
   place of an ideal force cap.
