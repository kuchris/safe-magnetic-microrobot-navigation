# Experiment 23 (drag_error)

Simulation only. Seeds 3, 4, 5; rates pool both branches and all frame rates. Brackets are 95% Wilson intervals. Closest approach is the continuous distance to the target (success needs <= 0.4 mm). Paired changes match the baseline (P0_kinematic_delay_gain) on every factor except policy.

| Drag error | Flow cut | Target | Policy | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) | Peak force / cap |
|---:|---:|---|---|---:|---|---:|---:|---:|---|---:|
| -0.2 | 90% | patent | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 78 | 61 | 0 | 6.30 / 0.56 | 0.08 |
| -0.2 | 90% | patent | P1_predictor_delay_gain | 18 | 0 [0, 18] | 78 | 72 | 0 | 9.84 / 0.59 | 0.07 |
| -0.2 | 90% | patent | P2_predictor_fast_gain | 18 | 6 [1, 26] | 89 | 50 | 0 | 10.01 / 0.40 | 0.34 |
| -0.2 | 90% | patent | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 56 | 0 | 10.25 / 0.95 | 0.60 |
| -0.2 | 90% | patent | P4_fast_wall_prediction | 18 | 17 [6, 39] | 83 | 22 | 0 | 2.93 / 0.40 | 0.34 |
| -0.2 | 90% | patent | P5_feedforward_prediction | 18 | 6 [1, 26] | 94 | 44 | 0 | 6.66 / 0.40 | 0.33 |
| -0.2 | 90% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.05 / 10.98 | 0.08 |
| -0.2 | 90% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.06 / 10.89 | 0.07 |
| -0.2 | 90% | target_occluded | P2_predictor_fast_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.55 / 10.13 | 0.34 |
| -0.2 | 90% | target_occluded | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.21 / 9.92 | 0.67 |
| -0.2 | 90% | target_occluded | P4_fast_wall_prediction | 18 | 0 [0, 18] | 94 | 100 | 0 | 10.61 / 9.80 | 0.34 |
| -0.2 | 90% | target_occluded | P5_feedforward_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.28 / 10.95 | 0.50 |
| -0.2 | 99% | patent | P0_kinematic_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.09 |
| -0.2 | 99% | patent | P1_predictor_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.08 |
| -0.2 | 99% | patent | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.37 |
| -0.2 | 99% | patent | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.36 |
| -0.2 | 99% | patent | P4_fast_wall_prediction | 18 | 67 [44, 84] | 33 | 0 | 0 | 0.40 / 0.40 | 0.36 |
| -0.2 | 99% | patent | P5_feedforward_prediction | 18 | 67 [44, 84] | 28 | 0 | 6 | 0.40 / 0.40 | 0.35 |
| -0.2 | 99% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 28 | 72 | 28 | 9.77 / 2.33 | 0.13 |
| -0.2 | 99% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 0 | 100 | 0 | 9.91 / 9.84 | 0.12 |
| -0.2 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.39 |
| -0.2 | 99% | target_occluded | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.42 |
| -0.2 | 99% | target_occluded | P4_fast_wall_prediction | 18 | 67 [44, 84] | 0 | 6 | 28 | 0.40 / 0.40 | 0.36 |
| -0.2 | 99% | target_occluded | P5_feedforward_prediction | 18 | 67 [44, 84] | 17 | 22 | 11 | 0.40 / 0.40 | 0.40 |
| +0.2 | 90% | patent | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 50 | 0 | 5.57 / 0.45 | 0.09 |
| +0.2 | 90% | patent | P1_predictor_delay_gain | 18 | 0 [0, 18] | 89 | 61 | 0 | 9.81 / 0.48 | 0.08 |
| +0.2 | 90% | patent | P2_predictor_fast_gain | 18 | 17 [6, 39] | 83 | 50 | 0 | 9.88 / 0.39 | 0.51 |
| +0.2 | 90% | patent | P3_fast_feedforward | 18 | 6 [1, 26] | 94 | 50 | 0 | 10.24 / 0.40 | 0.61 |
| +0.2 | 90% | patent | P4_fast_wall_prediction | 18 | 28 [12, 51] | 61 | 22 | 6 | 0.98 / 0.39 | 0.49 |
| +0.2 | 90% | patent | P5_feedforward_prediction | 18 | 6 [1, 26] | 94 | 56 | 0 | 9.86 / 0.40 | 0.51 |
| +0.2 | 90% | target_occluded | P0_kinematic_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.03 / 10.96 | 0.09 |
| +0.2 | 90% | target_occluded | P1_predictor_delay_gain | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.02 / 10.81 | 0.08 |
| +0.2 | 90% | target_occluded | P2_predictor_fast_gain | 18 | 0 [0, 18] | 94 | 100 | 0 | 9.96 / 9.76 | 0.52 |
| +0.2 | 90% | target_occluded | P3_fast_feedforward | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.44 / 10.35 | 0.99 |
| +0.2 | 90% | target_occluded | P4_fast_wall_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.27 / 9.81 | 0.49 |
| +0.2 | 90% | target_occluded | P5_feedforward_prediction | 18 | 0 [0, 18] | 100 | 100 | 0 | 11.42 / 10.61 | 0.70 |
| +0.2 | 99% | patent | P0_kinematic_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.10 |
| +0.2 | 99% | patent | P1_predictor_delay_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.09 |
| +0.2 | 99% | patent | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.54 |
| +0.2 | 99% | patent | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 | 0.52 |
| +0.2 | 99% | patent | P4_fast_wall_prediction | 18 | 72 [49, 88] | 0 | 0 | 28 | 0.40 / 0.40 | 0.53 |
| +0.2 | 99% | patent | P5_feedforward_prediction | 18 | 83 [61, 94] | 0 | 0 | 17 | 0.40 / 0.40 | 0.50 |
| +0.2 | 99% | target_occluded | P0_kinematic_delay_gain | 18 | 28 [12, 51] | 39 | 67 | 6 | 9.76 / 0.40 | 0.15 |
| +0.2 | 99% | target_occluded | P1_predictor_delay_gain | 18 | 33 [16, 56] | 0 | 67 | 0 | 9.97 / 0.40 | 0.13 |
| +0.2 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.54 |
| +0.2 | 99% | target_occluded | P3_fast_feedforward | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 | 0.52 |
| +0.2 | 99% | target_occluded | P4_fast_wall_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.53 |
| +0.2 | 99% | target_occluded | P5_feedforward_prediction | 18 | 67 [44, 84] | 0 | 0 | 33 | 0.40 / 0.40 | 0.50 |

## Paired changes against the baseline

| Drag error | Flow cut | Target | Policy | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---:|---:|---:|---:|---:|
| -0.2 | 90% | patent | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.03 |
| -0.2 | 90% | patent | P2_predictor_fast_gain | 1 | 0 | 0 | 17 | +0.08 |
| -0.2 | 90% | patent | P3_fast_feedforward | 0 | 0 | 0 | 18 | +1.05 |
| -0.2 | 90% | patent | P4_fast_wall_prediction | 3 | 0 | 0 | 15 | -0.42 |
| -0.2 | 90% | patent | P5_feedforward_prediction | 1 | 0 | 0 | 17 | +0.08 |
| -0.2 | 90% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | -0.01 |
| -0.2 | 90% | target_occluded | P2_predictor_fast_gain | 0 | 0 | 0 | 18 | -0.55 |
| -0.2 | 90% | target_occluded | P3_fast_feedforward | 0 | 0 | 0 | 18 | +0.17 |
| -0.2 | 90% | target_occluded | P4_fast_wall_prediction | 0 | 0 | 0 | 18 | -0.55 |
| -0.2 | 90% | target_occluded | P5_feedforward_prediction | 0 | 0 | 0 | 18 | +0.23 |
| -0.2 | 99% | patent | P1_predictor_delay_gain | 0 | 0 | 18 | 0 | +0.00 |
| -0.2 | 99% | patent | P2_predictor_fast_gain | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | patent | P3_fast_feedforward | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | patent | P4_fast_wall_prediction | 0 | 6 | 12 | 0 | -0.00 |
| -0.2 | 99% | patent | P5_feedforward_prediction | 0 | 6 | 12 | 0 | -0.00 |
| -0.2 | 99% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.17 |
| -0.2 | 99% | target_occluded | P2_predictor_fast_gain | 18 | 0 | 0 | 0 | -9.37 |
| -0.2 | 99% | target_occluded | P3_fast_feedforward | 18 | 0 | 0 | 0 | -9.37 |
| -0.2 | 99% | target_occluded | P4_fast_wall_prediction | 12 | 0 | 0 | 6 | -2.03 |
| -0.2 | 99% | target_occluded | P5_feedforward_prediction | 12 | 0 | 0 | 6 | -2.03 |
| +0.2 | 90% | patent | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | +0.01 |
| +0.2 | 90% | patent | P2_predictor_fast_gain | 3 | 0 | 0 | 15 | +0.08 |
| +0.2 | 90% | patent | P3_fast_feedforward | 1 | 0 | 0 | 17 | +0.74 |
| +0.2 | 90% | patent | P4_fast_wall_prediction | 5 | 0 | 0 | 13 | -0.37 |
| +0.2 | 90% | patent | P5_feedforward_prediction | 1 | 0 | 0 | 17 | +0.64 |
| +0.2 | 90% | target_occluded | P1_predictor_delay_gain | 0 | 0 | 0 | 18 | -0.02 |
| +0.2 | 90% | target_occluded | P2_predictor_fast_gain | 0 | 0 | 0 | 18 | -1.10 |
| +0.2 | 90% | target_occluded | P3_fast_feedforward | 0 | 0 | 0 | 18 | +0.45 |
| +0.2 | 90% | target_occluded | P4_fast_wall_prediction | 0 | 0 | 0 | 18 | -0.79 |
| +0.2 | 90% | target_occluded | P5_feedforward_prediction | 0 | 0 | 0 | 18 | +0.43 |
| +0.2 | 99% | patent | P1_predictor_delay_gain | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | patent | P2_predictor_fast_gain | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | patent | P3_fast_feedforward | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | patent | P4_fast_wall_prediction | 0 | 5 | 13 | 0 | +0.00 |
| +0.2 | 99% | patent | P5_feedforward_prediction | 0 | 3 | 15 | 0 | +0.00 |
| +0.2 | 99% | target_occluded | P1_predictor_delay_gain | 1 | 0 | 5 | 12 | +0.08 |
| +0.2 | 99% | target_occluded | P2_predictor_fast_gain | 13 | 0 | 5 | 0 | -9.36 |
| +0.2 | 99% | target_occluded | P3_fast_feedforward | 13 | 0 | 5 | 0 | -9.36 |
| +0.2 | 99% | target_occluded | P4_fast_wall_prediction | 7 | 0 | 5 | 6 | -8.35 |
| +0.2 | 99% | target_occluded | P5_feedforward_prediction | 7 | 0 | 5 | 6 | -7.58 |
