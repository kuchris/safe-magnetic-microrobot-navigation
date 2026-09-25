# Can the estimator reject a biased hold? (experiment 30)

Computational research and education only. This note tests control policies in
a toy Y-vessel with physiological parameters. It is not a device design, not a
safety claim and not clinical guidance.

## Question

Experiment 29 ([docs/21](21_combined_perturbations.md)) traced pure-NdFeB
failures to a biased gravity hold. The hold is off because of an actuation
gain error or a wrong gravity direction, and the weight-aware estimator does
not model the resulting force. Two existing pieces can act as a disturbance
canceller:

- **Estimated-drift feedforward** (`flow_feedforward`) cancels the
  command-aware residual drift, bias included.
- **A larger residual-filter acceleration PSD** (`estimator_acceleration_psd`,
  new in this step, default 1e-7 m²/s³) lets that residual adapt faster.

**Does combining them rescue the bundles that failed in experiment 29?**

Claude chose this step under the standing instruction to keep going.

## Design

The bundles are nominal, mild and moderate from experiment 29. Both materials
use the open-loop hold and the matched gate at 99% flow reduction, on held-out
seeds 3–5. That gives 1080 trials; the command is
`python -m simulations.30_disturbance_rejection`.

| Estimator | Acceleration PSD | Drift feedforward |
|---|---:|---|
| baseline (= experiment 29) | 1e-7 | no |
| drift_ff | 1e-7 | yes |
| fast_residual | 1e-5 | no |
| fast_residual_ff | 1e-5 | yes |
| faster_residual_ff | 1e-3 | yes |

The baseline reproduces experiment 29 trial for trial, and the test suite
checks that.

## Pre-registered hypotheses

- **H23:** fast_residual_ff rescues at least 18/36 moderate-bundle pure NdFeB
  trials while keeping nominal at 70/72 or better and mild at 66/72 or better.
- **H24:** drift_ff alone rescues fewer than 9/36, because the residual adapts
  too slowly.
- **H25:** A PSD of 1e-3 is no better than 1e-5 on moderate, and worse on
  nominal.

## Results

Held-out successes out of 36 per material and bundle, with the trial-by-trial
comparison against baseline (kept / lost / gained):

| Estimator | Bundle | Composite | Pure NdFeB | Composite vs baseline | NdFeB vs baseline |
|---|---|---:|---:|---|---|
| baseline | nominal | 36 | 36 | — | — |
| baseline | mild | 36 | 32 | — | — |
| baseline | moderate | 33 | 0 | — | — |
| drift_ff | nominal | 36 | 36 | 36 / 0 / 0 | 36 / 0 / 0 |
| drift_ff | mild | 36 | 32 | 36 / 0 / 0 | 32 / 0 / 0 |
| drift_ff | moderate | **35** | 0 | 32 / 1 / 3 | 0 / 0 / 0 |
| fast_residual | nominal | 36 | 36 | 36 / 0 / 0 | 36 / 0 / 0 |
| fast_residual | mild | 36 | 20 | 36 / 0 / 0 | 20 / 12 / 0 |
| fast_residual | moderate | 21 | 0 | 21 / 12 / 0 | 0 / 0 / 0 |
| fast_residual_ff | nominal | 36 | 36 | 36 / 0 / 0 | 36 / 0 / 0 |
| fast_residual_ff | mild | 35 | 20 | 35 / 1 / 0 | 20 / 12 / 0 |
| fast_residual_ff | moderate | 19 | 0 | 19 / 14 / 0 | 0 / 0 / 0 |
| faster_residual_ff | nominal | **7** | **6** | 7 / 29 / 0 | 6 / 30 / 0 |
| faster_residual_ff | mild | 0 | 0 | 0 / 36 / 0 | 0 / 32 / 0 |
| faster_residual_ff | moderate | 0 | 0 | 0 / 33 / 0 | 0 / 0 / 0 |

| Hypothesis | Outcome |
|---|---|
| H23: fast_residual_ff rescues ≥ 18/36 moderate NdFeB without harm | **Not supported, on every count.** It rescues none, drops mild NdFeB from 32 to 20, and drops the moderate composite from 33 to 19 |
| H24: drift_ff alone rescues < 9/36 | **Supported.** It rescues no NdFeB trial. The moderate composite goes from 33 to 35 (3 gained, 1 lost) |
| H25: 1e-3 no better than 1e-5 on moderate, and worse on nominal | **Supported.** 0/36 on moderate either way; nominal falls from 72/72 to 13/72 |

## Why estimation cannot catch this bias

A 20% hold shortfall sinks pure NdFeB at about 8 mm/s. It reaches the wall of
a 1.5 mm vessel from the axis in about 0.17 s. To see that drift, the
controller needs at least two frames after it starts, plus the latency:
roughly 0.12–0.18 s at 15–30 fps with 50–100 ms latency. The detection time
is as long as the time to the wall, so no estimator tuning can act in time.
A faster residual filter does not shorten detection; it only widens the
position uncertainty. The gate then stops steering (at PSD 1e-3, 97% of
nominal samples were held rather than steered) and turns successes into
failures.

With a smaller bias the same canceller works. A separate check used pure
NdFeB, still fluid, no steering gain and a 5% hold shortfall (about 2 mm/s,
about 0.7 s to the wall). Without feedforward the particle reaches the wall
at 0.73 s. With drift feedforward (PSD 1e-5) it stays clear for the full 2 s
and ends 0.2 mm below its start. `tests/test_disturbance_rejection.py`
checks both cases.

## Interpretation

- **Reduce the bias, do not estimate it.** When the time to the wall is
  shorter than the detection time, the fix has to come before release: a
  calibrated hold (gain and gravity direction), lower latency or a higher
  frame rate, or a lighter particle whose bias drift is 7× slower.
- **Keep the default estimator.** None of the faster settings beats the
  baseline overall. Drift feedforward is harmless at the default PSD and
  slightly helps the composite under the moderate bundle; it is worth keeping
  as an option for small, slow biases.
- **The limit, in one condition:** the bias-driven drift speed has to satisfy
  `v_bias × (latency + 2 / fps) < clearance`. For pure NdFeB, with about
  1.4 mm of clearance and ~0.15 s detection, v_bias must stay below about
  9 mm/s. That is a hold error of at most about 20–25% of its weight (its
  full Stokes settling speed is ~40 mm/s). The moderate bundle's 20% shortfall
  with 100 ms latency, plus a 10° tilt, already crossed this limit.

## Limitations

Everything in docs/15–21 applies. In addition:

- Only one disturbance-rejection structure was tested (drift feedforward with
  a faster residual). A dedicated bias state or an adaptive hold that learns
  across procedures might behave differently.
- The detection-time argument is approximate: it ignores the estimator's
  exact dynamics and the gate's thresholds.
