# Experiment 24 (flow_error)

Simulation only. Seeds 3, 4, 5; rates pool both branches and all frame rates; brackets are 95% Wilson intervals. Paired changes compare each arm with its material's baseline (C_P2 or N_P2_hold) on every other factor.

| Flow error | Flow cut | Target | Arm | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) |
|---:|---:|---|---|---:|---|---:|---:|---:|---|
| -0.2 | 90% | patent | C_P2_modelff | 18 | 17 [6, 39] | 83 | 39 | 0 | 7.93 / 0.40 |
| -0.2 | 90% | patent | C_P2_modelff_wall50 | 18 | 17 [6, 39] | 83 | 17 | 0 | 6.82 / 0.40 |
| -0.2 | 90% | patent | N_P2_modelff_hold | 18 | 17 [6, 39] | 83 | 39 | 0 | 7.65 / 0.40 |
| -0.2 | 90% | target_occluded | C_P2_modelff | 18 | 0 [0, 18] | 100 | 89 | 0 | 9.99 / 7.22 |
| -0.2 | 90% | target_occluded | C_P2_modelff_wall50 | 18 | 0 [0, 18] | 100 | 56 | 0 | 9.98 / 6.68 |
| -0.2 | 90% | target_occluded | N_P2_modelff_hold | 18 | 0 [0, 18] | 100 | 83 | 0 | 9.96 / 7.65 |
| -0.2 | 99% | patent | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| -0.2 | 99% | patent | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| -0.2 | 99% | patent | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| -0.2 | 99% | target_occluded | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| -0.2 | 99% | target_occluded | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| -0.2 | 99% | target_occluded | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0.2 | 90% | patent | C_P2_modelff | 18 | 6 [1, 26] | 94 | 22 | 0 | 12.15 / 0.40 |
| +0.2 | 90% | patent | C_P2_modelff_wall50 | 18 | 17 [6, 39] | 83 | 0 | 0 | 12.45 / 0.40 |
| +0.2 | 90% | patent | N_P2_modelff_hold | 18 | 0 [0, 18] | 100 | 39 | 0 | 12.23 / 0.41 |
| +0.2 | 90% | target_occluded | C_P2_modelff | 18 | 0 [0, 18] | 100 | 33 | 0 | 12.63 / 9.96 |
| +0.2 | 90% | target_occluded | C_P2_modelff_wall50 | 18 | 0 [0, 18] | 100 | 33 | 0 | 12.65 / 9.91 |
| +0.2 | 90% | target_occluded | N_P2_modelff_hold | 18 | 0 [0, 18] | 100 | 33 | 0 | 12.44 / 9.95 |
| +0.2 | 99% | patent | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0.2 | 99% | patent | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0.2 | 99% | patent | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0.2 | 99% | target_occluded | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0.2 | 99% | target_occluded | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0.2 | 99% | target_occluded | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |

## Paired changes

| Flow error | Flow cut | Target | Arm | Baseline | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|
| -0.2 | 90% | patent | C_P2_modelff | C_P2 | 3 | 2 | 0 | 13 | +0.42 |
| -0.2 | 90% | patent | C_P2_modelff_wall50 | C_P2 | 3 | 2 | 0 | 13 | -0.42 |
| -0.2 | 90% | patent | N_P2_modelff_hold | N_P2_hold | 3 | 0 | 0 | 15 | -0.16 |
| -0.2 | 90% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 0 | 18 | +0.03 |
| -0.2 | 90% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 0 | 18 | +0.04 |
| -0.2 | 90% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 0 | 18 | +0.15 |
| -0.2 | 99% | patent | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | patent | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | patent | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| -0.2 | 99% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| -0.2 | 99% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 90% | patent | C_P2_modelff | C_P2 | 1 | 2 | 0 | 15 | +2.34 |
| +0.2 | 90% | patent | C_P2_modelff_wall50 | C_P2 | 3 | 2 | 0 | 13 | +2.86 |
| +0.2 | 90% | patent | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 0 | 18 | +2.38 |
| +0.2 | 90% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 0 | 18 | +2.61 |
| +0.2 | 90% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 0 | 18 | +2.68 |
| +0.2 | 90% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 0 | 18 | +2.12 |
| +0.2 | 99% | patent | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | patent | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | patent | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0.2 | 99% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
