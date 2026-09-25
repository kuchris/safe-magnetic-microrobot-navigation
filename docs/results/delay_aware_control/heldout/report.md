# Experiment 23 (heldout)

Simulation only. Seeds 3, 4, 5; rates pool both branches and all frame rates. Brackets are 95% Wilson intervals. Closest approach is the continuous distance to the target (success needs <= 0.4 mm). Paired changes match the baseline (P0_kinematic_delay_gain) on every factor except policy.

| Drag error | Flow cut | Target | Policy | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) | Peak force / cap |
|---:|---:|---|---|---:|---|---:|---:|---:|---|---:|
| +0 | 90% | patent | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 50 | 0 | 5.58 / 0.50 | 0.09 |
| +0 | 90% | patent | P1_predictor_delay_gain | 18 | 0 [0, 18] | 78 | 67 | 0 | 9.79 / 0.53 | 0.08 |
| +0 | 90% | patent | P2_predictor_fast_gain | 18 | 6 [1, 26] | 89 | 61 | 0 | 9.89 / 0.28 | 0.43 |
| +0 | 90% | patent | P3_fast_feedforward | 18 | 6 [1, 26] | 94 | 50 | 0 | 10.27 / 0.40 | 0.46 |
| +0 | 90% | patent | P4_fast_wall_prediction | 18 | 28 [12, 51] | 72 | 22 | 0 | 2.35 / 0.39 | 0.43 |
| +0 | 90% | patent | P5_feedforward_prediction | 18 | 6 [1, 26] | 94 | 56 | 0 | 9.00 / 0.40 | 0.42 |
| +0 | 90% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.04 / 10.97 | 0.09 |
| +0 | 90% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.04 / 10.85 | 0.08 |
| +0 | 90% | target_occluded | P2_predictor_fast_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.19 / 9.85 | 0.43 |
| +0 | 90% | target_occluded | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.35 / 10.46 | 0.70 |
| +0 | 90% | target_occluded | P4_fast_wall_prediction | 18 | 0 [0, 18] | 89 | 100 | 0 | 10.41 / 9.76 | 0.42 |
| +0 | 90% | target_occluded | P5_feedforward_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.34 / 10.86 | 0.57 |
| +0 | 99% | patent | P0_kinematic_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.10 |
| +0 | 99% | patent | P1_predictor_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.09 |
| +0 | 99% | patent | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.46 |
| +0 | 99% | patent | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 | 0.42 |
| +0 | 99% | patent | P4_fast_wall_prediction | 18 | 78 [55, 91] | 22 | 0 | 0 | 0.40 / 0.40 | 0.45 |
| +0 | 99% | patent | P5_feedforward_prediction | 18 | 83 [61, 94] | 17 | 0 | 0 | 0.40 / 0.40 | 0.42 |
| +0 | 99% | target_occluded | P0_kinematic_delay_gain | 18 | 6 [1, 26] | 28 | 72 | 22 | 9.77 / 0.40 | 0.13 |
| +0 | 99% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 0 | 100 | 0 | 9.96 / 9.88 | 0.14 |
| +0 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.46 |
| +0 | 99% | target_occluded | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 | 0.45 |
| +0 | 99% | target_occluded | P4_fast_wall_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.45 |
| +0 | 99% | target_occluded | P5_feedforward_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.43 |

## Paired changes against the baseline

| Drag error | Flow cut | Target | Policy | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---:|---:|---:|---:|---:|
| +0 | 90% | patent | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.01 |
| +0 | 90% | patent | P2_predictor_fast_gain | 1 | 0 | 0 | 17 | +0.05 |
| +0 | 90% | patent | P3_fast_feedforward | 1 | 0 | 0 | 17 | +0.50 |
| +0 | 90% | patent | P4_fast_wall_prediction | 5 | 0 | 0 | 13 | -0.29 |
| +0 | 90% | patent | P5_feedforward_prediction | 1 | 0 | 0 | 17 | +0.18 |
| +0 | 90% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | -0.02 |
| +0 | 90% | target_occluded | P2_predictor_fast_gain | 0 | 0 | 0 | 18 | -0.91 |
| +0 | 90% | target_occluded | P3_fast_feedforward | 0 | 0 | 0 | 18 | +0.34 |
| +0 | 90% | target_occluded | P4_fast_wall_prediction | 0 | 0 | 0 | 18 | -0.67 |
| +0 | 90% | target_occluded | P5_feedforward_prediction | 0 | 0 | 0 | 18 | +0.33 |
| +0 | 99% | patent | P1_predictor_delay_gain | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | P2_predictor_fast_gain | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | P3_fast_feedforward | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | P4_fast_wall_prediction | 0 | 4 | 14 | 0 | -0.00 |
| +0 | 99% | patent | P5_feedforward_prediction | 0 | 3 | 15 | 0 | -0.00 |
| +0 | 99% | target_occluded | P1_predictor_delay_gain | 0 | 1 | 0 | 17 | +0.19 |
| +0 | 99% | target_occluded | P2_predictor_fast_gain | 17 | 0 | 1 | 0 | -9.37 |
| +0 | 99% | target_occluded | P3_fast_feedforward | 17 | 0 | 1 | 0 | -9.37 |
| +0 | 99% | target_occluded | P4_fast_wall_prediction | 11 | 0 | 1 | 6 | -5.51 |
| +0 | 99% | target_occluded | P5_feedforward_prediction | 11 | 0 | 1 | 6 | -7.62 |
