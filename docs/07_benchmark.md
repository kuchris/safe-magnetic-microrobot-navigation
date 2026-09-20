# Paired-seed benchmark: executed pilot

Executed on 2026-09-20 with Python 3.12.11, NumPy 2.3.3,
Matplotlib 3.10.6 and pytest 9.1.1. All 68 tests passed.

```bash
python -m pytest -q
python -m simulations.06_benchmark --seeds 0 1 2 3 4 --output outputs/06_benchmark_pilot
python -m simulations.07_plot_benchmark --output docs/figures/benchmark_success_rates.png
```

The run contains 120 full-duration trials (up to 40 seconds each): four
scenarios, two branches, three policies and five seeds. Complete per-trial
configurations, summaries and aggregates are retained in
[benchmark_pilot.json](results/benchmark_pilot.json). The command also produces
an untracked CSV and generated Markdown report in the output directory.

## Findings

![Success rates by scenario, target branch and policy, with 95% Wilson intervals](figures/benchmark_success_rates.png)

- In nominal conditions, both active policies reached either requested branch
  in 5/5 trials. Passive drift reached the upper target in 5/5 but the lower
  target in 0/5, demonstrating why branches must be evaluated separately.
- Under high noise, both active policies reached the upper target in 4/5 trials
  and the lower target in 3/5. A successful seed-7 example does not generalize
  to every seed.
- At 250 ms latency, the gated policy disabled actuation throughout and reached
  the lower target in 0/5 trials. Ungated steering reached it in 4/5. This
  exposes the cost of the current stop action under flow; it does not establish
  that bypassing the gate is safe.
- During the dropout burst, both active policies reached the lower target in
  4/5 trials, but their failed seeds differed: gated failed at seed 0, ungated
  at seed 2. Matching aggregate rates do not mean identical policy behavior.
- Every unsuccessful trial in this pilot recorded a wrong branch and a later
  wall-proxy violation. These violations include the artificial closed outlets;
  they must not all be interpreted as physical side-wall impacts.
- For a group with 5/5 successes the 95% Wilson interval is 56.6%-100%; with
  0/5 observed violations the upper endpoint is 43.4%. This pilot identifies
  failure cases, but cannot establish low failure probabilities.

## Next experiment

Replay the failed seeds around the bifurcation and separate wrong-branch
entry, side-wall risk and artificial outlet termination. Then use those cases
to evaluate force/flow-aware prediction and a predictive action constraint.
Repeat the same paired-seed benchmark after each change and expand the seed
set before drawing stronger rate comparisons.

## Complete benchmark results

Seeds: 0, 1, 2, 3, 4. Trials: 120.

Policies share seeds, sensor settings, estimator, waypoints and force limits. Passive always applies zero force. Ungated requires an initial estimate, then continues steering despite stale/lost observations or low robust clearance. Gated uses the existing uncertainty, freshness and clearance supervisor.

Rates below are per trial. Brackets show two-sided 95% Wilson score intervals across seeds within each scenario, branch and policy. These are marginal intervals, not simultaneous bounds or tests of paired policy differences. Small seed counts produce wide intervals even with no observed failures.

| Scenario | Branch | Policy | N | Success % [95% CI] | Wall proxy violation % [95% CI] | Wrong branch % [95% CI] |
|---|---|---|---:|---|---|---|
| nominal | upper | passive | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| nominal | upper | ungated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| nominal | upper | gated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| nominal | lower | passive | 5 | 0.0 [0.0, 43.4] | 100.0 [56.6, 100.0] | 100.0 [56.6, 100.0] |
| nominal | lower | ungated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| nominal | lower | gated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| dropout_burst | upper | passive | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| dropout_burst | upper | ungated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| dropout_burst | upper | gated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| dropout_burst | lower | passive | 5 | 0.0 [0.0, 43.4] | 100.0 [56.6, 100.0] | 100.0 [56.6, 100.0] |
| dropout_burst | lower | ungated | 5 | 80.0 [37.6, 96.4] | 20.0 [3.6, 62.4] | 20.0 [3.6, 62.4] |
| dropout_burst | lower | gated | 5 | 80.0 [37.6, 96.4] | 20.0 [3.6, 62.4] | 20.0 [3.6, 62.4] |
| stale_imaging | upper | passive | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| stale_imaging | upper | ungated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| stale_imaging | upper | gated | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| stale_imaging | lower | passive | 5 | 0.0 [0.0, 43.4] | 100.0 [56.6, 100.0] | 100.0 [56.6, 100.0] |
| stale_imaging | lower | ungated | 5 | 80.0 [37.6, 96.4] | 20.0 [3.6, 62.4] | 20.0 [3.6, 62.4] |
| stale_imaging | lower | gated | 5 | 0.0 [0.0, 43.4] | 100.0 [56.6, 100.0] | 100.0 [56.6, 100.0] |
| high_noise | upper | passive | 5 | 100.0 [56.6, 100.0] | 0.0 [0.0, 43.4] | 0.0 [0.0, 43.4] |
| high_noise | upper | ungated | 5 | 80.0 [37.6, 96.4] | 20.0 [3.6, 62.4] | 20.0 [3.6, 62.4] |
| high_noise | upper | gated | 5 | 80.0 [37.6, 96.4] | 20.0 [3.6, 62.4] | 20.0 [3.6, 62.4] |
| high_noise | lower | passive | 5 | 0.0 [0.0, 43.4] | 100.0 [56.6, 100.0] | 100.0 [56.6, 100.0] |
| high_noise | lower | ungated | 5 | 60.0 [23.1, 88.2] | 40.0 [11.8, 76.9] | 40.0 [11.8, 76.9] |
| high_noise | lower | gated | 5 | 60.0 [23.1, 88.2] | 40.0 [11.8, 76.9] | 40.0 [11.8, 76.9] |

## Per-trial metric distributions

Values are medians [5th, 95th percentiles] across trials, not confidence intervals. Arrival time includes successful trials only. Missing estimates are excluded from RMSE and coverage; availability includes all control samples. JSON includes the valid trial count for each metric. Trials receive equal weight.

| Scenario / branch / policy | Min clearance mm | Arrival s | RMSE mm | Inhibited samples % | 3-sigma coverage % | Estimate availability % |
|---|---|---|---|---|---|---|
| nominal / upper / passive | 1.399 [1.399, 1.399] | 35.240 [35.240, 35.240] | 0.052 [0.049, 0.057] | 0.000 [0.000, 0.000] | 99.872 [99.460, 99.977] | 99.858 [99.858, 99.858] |
| nominal / upper / ungated | 1.360 [1.346, 1.374] | 27.680 [27.583, 27.702] | 0.053 [0.050, 0.058] | 0.181 [0.180, 0.181] | 99.819 [99.361, 99.892] | 99.819 [99.819, 99.820] |
| nominal / upper / gated | 1.360 [1.346, 1.374] | 27.680 [27.583, 27.702] | 0.053 [0.050, 0.058] | 0.181 [0.180, 0.181] | 99.819 [99.361, 99.892] | 99.819 [99.819, 99.820] |
| nominal / lower / passive | -0.002 [-0.002, -0.002] | N/A | 0.052 [0.049, 0.057] | 0.000 [0.000, 0.000] | 99.882 [99.440, 99.979] | 99.869 [99.869, 99.869] |
| nominal / lower / ungated | 1.362 [1.349, 1.368] | 27.635 [27.584, 27.685] | 0.053 [0.050, 0.058] | 0.181 [0.181, 0.181] | 99.801 [99.114, 99.833] | 99.819 [99.819, 99.819] |
| nominal / lower / gated | 1.362 [1.349, 1.368] | 27.635 [27.584, 27.685] | 0.053 [0.050, 0.058] | 0.181 [0.181, 0.181] | 99.801 [99.114, 99.833] | 99.819 [99.819, 99.819] |
| dropout_burst / upper / passive | 1.399 [1.399, 1.399] | 35.240 [35.240, 35.240] | 0.052 [0.051, 0.061] | 0.000 [0.000, 0.000] | 99.872 [99.574, 99.977] | 99.858 [99.858, 99.858] |
| dropout_burst / upper / ungated | 1.359 [1.345, 1.372] | 27.700 [27.646, 27.704] | 0.053 [0.052, 0.064] | 0.180 [0.180, 0.181] | 99.819 [98.915, 99.877] | 99.820 [99.819, 99.820] |
| dropout_burst / upper / gated | 1.360 [1.348, 1.375] | 27.800 [27.787, 27.832] | 0.055 [0.054, 0.062] | 2.877 [2.874, 2.879] | 99.820 [99.099, 99.834] | 99.820 [99.820, 99.820] |
| dropout_burst / lower / passive | -0.002 [-0.002, -0.002] | N/A | 0.052 [0.050, 0.061] | 0.000 [0.000, 0.000] | 99.882 [99.607, 99.979] | 99.869 [99.869, 99.869] |
| dropout_burst / lower / ungated | 1.360 [0.269, 1.366] | 27.633 [27.596, 27.669] | 0.054 [0.053, 0.063] | 0.181 [0.181, 0.237] | 99.748 [99.514, 99.891] | 99.819 [99.763, 99.819] |
| dropout_burst / lower / gated | 1.365 [0.269, 1.371] | 27.812 [27.805, 27.833] | 0.055 [0.054, 0.061] | 2.877 [2.874, 41.089] | 99.820 [99.454, 99.892] | 99.820 [99.820, 99.855] |
| stale_imaging / upper / passive | 1.399 [1.399, 1.399] | 35.240 [35.240, 35.240] | 0.077 [0.075, 0.081] | 0.000 [0.000, 0.000] | 100.000 [99.886, 100.000] | 99.291 [99.291, 99.291] |
| stale_imaging / upper / ungated | 1.361 [1.344, 1.371] | 27.590 [27.548, 27.692] | 0.081 [0.078, 0.085] | 0.906 [0.903, 0.907] | 100.000 [100.000, 100.000] | 99.094 [99.093, 99.097] |
| stale_imaging / upper / gated | 1.399 [1.399, 1.399] | 35.240 [35.240, 35.240] | 0.077 [0.075, 0.081] | 100.000 [100.000, 100.000] | 100.000 [99.886, 100.000] | 99.291 [99.291, 99.291] |
| stale_imaging / lower / passive | -0.002 [-0.002, -0.002] | N/A | 0.076 [0.075, 0.081] | 0.000 [0.000, 0.000] | 100.000 [99.895, 100.000] | 99.346 [99.346, 99.346] |
| stale_imaging / lower / ungated | 1.358 [0.267, 1.365] | 27.635 [27.587, 27.654] | 0.082 [0.079, 0.085] | 0.905 [0.904, 1.228] | 100.000 [99.985, 100.000] | 99.095 [98.772, 99.096] |
| stale_imaging / lower / gated | -0.002 [-0.002, -0.002] | N/A | 0.076 [0.075, 0.081] | 100.000 [100.000, 100.000] | 100.000 [99.895, 100.000] | 99.346 [99.346, 99.346] |
| high_noise / upper / passive | 1.399 [1.399, 1.399] | 35.240 [35.240, 35.240] | 0.299 [0.266, 0.314] | 0.000 [0.000, 0.000] | 99.858 [99.023, 100.000] | 99.858 [99.858, 99.858] |
| high_noise / upper / ungated | 1.221 [0.243, 1.239] | 28.523 [28.220, 28.677] | 0.305 [0.289, 0.351] | 0.175 [0.174, 0.243] | 99.649 [96.356, 99.964] | 99.825 [99.757, 99.826] |
| high_noise / upper / gated | 1.233 [0.243, 1.247] | 28.555 [28.507, 28.680] | 0.303 [0.284, 0.328] | 3.420 [2.770, 45.206] | 99.649 [98.079, 99.965] | 99.825 [99.825, 99.855] |
| high_noise / lower / passive | -0.002 [-0.002, -0.002] | N/A | 0.299 [0.265, 0.313] | 0.000 [0.000, 0.000] | 99.869 [99.099, 100.000] | 99.869 [99.869, 99.869] |
| high_noise / lower / ungated | 1.196 [-0.001, 1.235] | 28.555 [28.434, 28.641] | 0.319 [0.291, 0.338] | 0.176 [0.175, 0.260] | 99.648 [97.363, 99.947] | 99.824 [99.740, 99.825] |
| high_noise / lower / gated | 1.233 [-0.002, 1.242] | 28.650 [28.587, 28.677] | 0.313 [0.277, 0.333] | 4.258 [2.642, 54.062] | 99.651 [98.003, 99.973] | 99.826 [99.825, 99.864] |

## Interpretation and limits

- Passive upper-branch arrival can be caused entirely by flow. Inspect both branches.
- Zero force does not immobilize the particle. With default parameters, cancelling 0.6 mm/s flow requires approximately 3.96 nN, above the 3 nN force cap.
- Wall violations use the sampled capsule-clearance proxy. Closed rounded outlets can register as violations; no swept collision or anatomical outlet model is used.
- Coverage is the fraction of localized samples whose Euclidean position error is at most three times the largest-axis position sigma. This is a descriptive ball coverage metric, not a calibrated 3D confidence level or collision-risk bound. Time samples are correlated; no sample-level binomial interval is reported.
- Inhibited samples include startup without an estimate and gate-triggered stops. Passive force is zero by design and is not counted as a gate-triggered stop.
- Seeds are paired between policies. Random draws are shared while observation positions and termination times can differ. Results are conditional on these toy settings; variation across anatomy, physics, or real data is not measured.
