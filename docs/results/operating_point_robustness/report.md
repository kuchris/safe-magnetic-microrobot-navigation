# Experiment 28: operating-point robustness and gate check

Simulation only. Held-out seeds 3-5 and both branches. Robustness runs at 99% flow reduction;
the gate check at 90%. 'All' pools the three frame rates.

## Robustness at 99% (successes / trials, all frame rates)

| Condition | Arm | Target | Success [95% CI] | Wall | Wrong | Timeout | Median time s |
|---|---|---|---|---:|---:|---:|---:|
| nominal_fixed_gate | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| nominal_fixed_gate | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| nominal_fixed_gate | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.77 |
| nominal_fixed_gate | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| nominal | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| nominal | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| nominal | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| nominal | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| latency_0.1s | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.85 |
| latency_0.1s | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.92 |
| latency_0.1s | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.85 |
| latency_0.1s | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.93 |
| latency_0.2s | C_P2 | patent | 10/18 [34, 75] | 8 | 4 | 0 | 4.19 |
| latency_0.2s | C_P2 | target_occluded | 13/18 [49, 88] | 0 | 5 | 0 | 4.59 |
| latency_0.2s | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 1.67 |
| latency_0.2s | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 1.08 |
| dropout_0.3s | C_P2 | patent | 0/18 [0, 18] | 7 | 0 | 11 | 5.00 |
| dropout_0.3s | C_P2 | target_occluded | 0/18 [0, 18] | 7 | 6 | 8 | 5.00 |
| dropout_0.3s | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 1.00 |
| dropout_0.3s | N_P2_hold | target_occluded | 9/18 [29, 71] | 2 | 9 | 0 | 1.14 |
| gain_-20% | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.94 |
| gain_-20% | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 1.04 |
| gain_-20% | N_P2_hold | patent | 12/18 [44, 84] | 6 | 0 | 0 | 1.01 |
| gain_-20% | N_P2_hold | target_occluded | 12/18 [44, 84] | 6 | 0 | 0 | 1.12 |
| gain_+20% | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.73 |
| gain_+20% | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.81 |
| gain_+20% | N_P2_hold | patent | 14/18 [55, 91] | 4 | 0 | 0 | 0.74 |
| gain_+20% | N_P2_hold | target_occluded | 14/18 [55, 91] | 4 | 0 | 0 | 0.84 |
| gradient_0.5 | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| gradient_0.5 | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| gradient_0.5 | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| gradient_0.5 | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| gradient_0.25 | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.96 |
| gradient_0.25 | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 1.08 |
| gradient_0.25 | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| gradient_0.25 | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| gravity_tilt_15deg | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.78 |
| gravity_tilt_15deg | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.89 |
| gravity_tilt_15deg | N_P2_hold | patent | 12/18 [44, 84] | 6 | 0 | 0 | 0.83 |
| gravity_tilt_15deg | N_P2_hold | target_occluded | 12/18 [44, 84] | 6 | 0 | 0 | 0.90 |
| gravity_tilt_30deg | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.80 |
| gravity_tilt_30deg | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.90 |
| gravity_tilt_30deg | N_P2_hold | patent | 0/18 [0, 18] | 18 | 0 | 0 | 0.08 |
| gravity_tilt_30deg | N_P2_hold | target_occluded | 0/18 [0, 18] | 18 | 0 | 0 | 0.08 |
| calibration_1px | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| calibration_1px | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| calibration_1px | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.76 |
| calibration_1px | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 0.87 |
| noise_3px | C_P2 | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.82 |
| noise_3px | C_P2 | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 1.00 |
| noise_3px | N_P2_hold | patent | 18/18 [82, 100] | 0 | 0 | 0 | 0.82 |
| noise_3px | N_P2_hold | target_occluded | 18/18 [82, 100] | 0 | 0 | 0 | 1.01 |

Paired against the matched-gate nominal (kept / lost / gained / both fail):

- nominal_fixed_gate: 72 / 0 / 0 / 0
- latency_0.1s: 72 / 0 / 0 / 0
- latency_0.2s: 59 / 13 / 0 / 0
- dropout_0.3s: 27 / 45 / 0 / 0
- gain_-20%: 60 / 12 / 0 / 0
- gain_+20%: 64 / 8 / 0 / 0
- gradient_0.5: 72 / 0 / 0 / 0
- gradient_0.25: 72 / 0 / 0 / 0
- gravity_tilt_15deg: 60 / 12 / 0 / 0
- gravity_tilt_30deg: 36 / 36 / 0 / 0
- calibration_1px: 72 / 0 / 0 / 0
- noise_3px: 72 / 0 / 0 / 0

## Gate check at 90% (model feedforward arms)

| Gate | Arm | Target | fps | Success | Wall | Wrong |
|---|---|---|---:|---:|---:|---:|
| fixed_gate | C_P2_modelff | patent | 7.5 | 0/6 | 6 | 2 |
| fixed_gate | C_P2_modelff | patent | 15 | 4/6 | 2 | 1 |
| fixed_gate | C_P2_modelff | patent | 30 | 3/6 | 3 | 3 |
| fixed_gate | C_P2_modelff | patent | all | 7/18 | 11 | 6 |
| fixed_gate | C_P2_modelff | target_occluded | 7.5 | 0/6 | 6 | 6 |
| fixed_gate | C_P2_modelff | target_occluded | 15 | 4/6 | 2 | 0 |
| fixed_gate | C_P2_modelff | target_occluded | 30 | 4/6 | 2 | 0 |
| fixed_gate | C_P2_modelff | target_occluded | all | 8/18 | 10 | 6 |
| fixed_gate | N_P2_modelff_hold | patent | 7.5 | 0/6 | 6 | 3 |
| fixed_gate | N_P2_modelff_hold | patent | 15 | 3/6 | 3 | 2 |
| fixed_gate | N_P2_modelff_hold | patent | 30 | 3/6 | 3 | 3 |
| fixed_gate | N_P2_modelff_hold | patent | all | 6/18 | 12 | 8 |
| fixed_gate | N_P2_modelff_hold | target_occluded | 7.5 | 0/6 | 6 | 6 |
| fixed_gate | N_P2_modelff_hold | target_occluded | 15 | 5/6 | 1 | 0 |
| fixed_gate | N_P2_modelff_hold | target_occluded | 30 | 6/6 | 0 | 0 |
| fixed_gate | N_P2_modelff_hold | target_occluded | all | 11/18 | 7 | 6 |
| matched_gate | C_P2_modelff | patent | 7.5 | 0/6 | 6 | 1 |
| matched_gate | C_P2_modelff | patent | 15 | 4/6 | 2 | 1 |
| matched_gate | C_P2_modelff | patent | 30 | 3/6 | 3 | 3 |
| matched_gate | C_P2_modelff | patent | all | 7/18 | 11 | 5 |
| matched_gate | C_P2_modelff | target_occluded | 7.5 | 0/6 | 5 | 0 |
| matched_gate | C_P2_modelff | target_occluded | 15 | 4/6 | 2 | 0 |
| matched_gate | C_P2_modelff | target_occluded | 30 | 4/6 | 2 | 0 |
| matched_gate | C_P2_modelff | target_occluded | all | 8/18 | 9 | 0 |
| matched_gate | N_P2_modelff_hold | patent | 7.5 | 0/6 | 6 | 1 |
| matched_gate | N_P2_modelff_hold | patent | 15 | 3/6 | 3 | 2 |
| matched_gate | N_P2_modelff_hold | patent | 30 | 3/6 | 3 | 3 |
| matched_gate | N_P2_modelff_hold | patent | all | 6/18 | 12 | 6 |
| matched_gate | N_P2_modelff_hold | target_occluded | 7.5 | 0/6 | 1 | 1 |
| matched_gate | N_P2_modelff_hold | target_occluded | 15 | 5/6 | 1 | 0 |
| matched_gate | N_P2_modelff_hold | target_occluded | 30 | 6/6 | 0 | 0 |
| matched_gate | N_P2_modelff_hold | target_occluded | all | 11/18 | 2 | 1 |

Matched gate paired against the fixed gate (kept / lost / gained / both fail):

- matched_gate: 32 / 0 / 0 / 40
