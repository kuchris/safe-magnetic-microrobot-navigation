# Experiment 23 (pilot)

Simulation only. Seeds 0, 1, 2; rates pool both branches and all frame rates. Brackets are 95% Wilson intervals. Closest approach is the continuous distance to the target (success needs <= 0.4 mm). Paired changes match the baseline (P0_kinematic_delay_gain) on every factor except policy.

| Drag error | Flow cut | Target | Policy | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) | Peak force / cap |
|---:|---:|---|---|---:|---|---:|---:|---:|---|---:|
| +0 | 90% | patent | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 94 | 56 | 6 | 9.98 / 0.68 | 0.08 |
| +0 | 90% | patent | P1_predictor_delay_gain | 18 | 0 [0, 18] | 100 | 50 | 0 | 10.06 / 0.69 | 0.07 |
| +0 | 90% | patent | P2_predictor_fast_gain | 18 | 11 [3, 33] | 83 | 50 | 0 | 9.85 / 0.39 | 0.44 |
| +0 | 90% | patent | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 50 | 0 | 10.03 / 0.51 | 0.43 |
| +0 | 90% | patent | P4_fast_wall_prediction | 18 | 22 [9, 45] | 78 | 28 | 0 | 2.51 / 0.39 | 0.43 |
| +0 | 90% | patent | P5_feedforward_prediction | 18 | 0 [0, 18] | 100 | 50 | 0 | 10.10 / 0.40 | 0.43 |
| +0 | 90% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.05 / 10.96 | 0.08 |
| +0 | 90% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.04 / 10.84 | 0.07 |
| +0 | 90% | target_occluded | P2_predictor_fast_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.17 / 9.81 | 0.43 |
| +0 | 90% | target_occluded | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.35 / 10.47 | 0.67 |
| +0 | 90% | target_occluded | P4_fast_wall_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.27 / 9.83 | 0.41 |
| +0 | 90% | target_occluded | P5_feedforward_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.35 / 10.69 | 0.56 |
| +0 | 99% | patent | P0_kinematic_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.09 |
| +0 | 99% | patent | P1_predictor_delay_gain | 18 | 94 [74, 99] | 0 | 0 | 6 | 0.40 / 0.40 | 0.09 |
| +0 | 99% | patent | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.46 |
| +0 | 99% | patent | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.42 |
| +0 | 99% | patent | P4_fast_wall_prediction | 18 | 72 [49, 88] | 28 | 0 | 0 | 0.40 / 0.40 | 0.45 |
| +0 | 99% | patent | P5_feedforward_prediction | 18 | 78 [55, 91] | 22 | 0 | 0 | 0.40 / 0.40 | 0.42 |
| +0 | 99% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 39 | 72 | 28 | 9.76 / 0.61 | 0.14 |
| +0 | 99% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 0 | 100 | 0 | 9.95 / 9.91 | 0.15 |
| +0 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 | 0.46 |
| +0 | 99% | target_occluded | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.44 |
| +0 | 99% | target_occluded | P4_fast_wall_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.45 |
| +0 | 99% | target_occluded | P5_feedforward_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.43 |

## Paired changes against the baseline

| Drag error | Flow cut | Target | Policy | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---:|---:|---:|---:|---:|
| +0 | 90% | patent | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.02 |
| +0 | 90% | patent | P2_predictor_fast_gain | 2 | 0 | 0 | 16 | -0.11 |
| +0 | 90% | patent | P3_fast_feedforward | 0 | 0 | 0 | 18 | +0.28 |
| +0 | 90% | patent | P4_fast_wall_prediction | 4 | 0 | 0 | 14 | -0.18 |
| +0 | 90% | patent | P5_feedforward_prediction | 0 | 0 | 0 | 18 | +0.15 |
| +0 | 90% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | -0.02 |
| +0 | 90% | target_occluded | P2_predictor_fast_gain | 0 | 0 | 0 | 18 | -0.95 |
| +0 | 90% | target_occluded | P3_fast_feedforward | 0 | 0 | 0 | 18 | +0.34 |
| +0 | 90% | target_occluded | P4_fast_wall_prediction | 0 | 0 | 0 | 18 | -0.82 |
| +0 | 90% | target_occluded | P5_feedforward_prediction | 0 | 0 | 0 | 18 | +0.35 |
| +0 | 99% | patent | P1_predictor_delay_gain | 0 | 1 | 17 | 0 | -0.00 |
| +0 | 99% | patent | P2_predictor_fast_gain | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | patent | P3_fast_feedforward | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | P4_fast_wall_prediction | 0 | 5 | 13 | 0 | +0.00 |
| +0 | 99% | patent | P5_feedforward_prediction | 0 | 4 | 14 | 0 | +0.00 |
| +0 | 99% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.18 |
| +0 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 0 | 0 | 0 | -9.37 |
| +0 | 99% | target_occluded | P3_fast_feedforward | 18 | 0 | 0 | 0 | -9.37 |
| +0 | 99% | target_occluded | P4_fast_wall_prediction | 12 | 0 | 0 | 6 | -8.06 |
| +0 | 99% | target_occluded | P5_feedforward_prediction | 12 | 0 | 0 | 6 | -8.11 |
