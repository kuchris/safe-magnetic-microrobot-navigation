# Experiment 24 (heldout)

Simulation only. Seeds 3, 4, 5; rates pool both branches and all frame rates; brackets are 95% Wilson intervals. Paired changes compare each arm with its material's baseline (C_P2 or N_P2_hold) on every other factor.

| Flow error | Flow cut | Target | Arm | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) |
|---:|---:|---|---|---:|---|---:|---:|---:|---|
| +0 | 90% | patent | C_P2 | 18 | 11 [3, 33] | 89 | 50 | 0 | 6.97 / 0.39 |
| +0 | 90% | patent | C_P2_exp23 | 18 | 6 [1, 26] | 89 | 61 | 0 | 9.89 / 0.28 |
| +0 | 90% | patent | C_P2_modelff | 18 | 39 [20, 61] | 61 | 33 | 0 | 3.40 / 0.40 |
| +0 | 90% | patent | C_P2_modelff_wall50 | 18 | 28 [12, 51] | 72 | 50 | 0 | 10.37 / 0.40 |
| +0 | 90% | patent | C_P2_wall50 | 18 | 11 [3, 33] | 89 | 50 | 0 | 6.97 / 0.39 |
| +0 | 90% | patent | N_P2_hold | 18 | 0 [0, 18] | 100 | 50 | 0 | 9.82 / 0.86 |
| +0 | 90% | patent | N_P2_modelff_hold | 18 | 33 [16, 56] | 67 | 44 | 0 | 3.23 / 0.40 |
| +0 | 90% | target_occluded | C_P2 | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.04 / 9.85 |
| +0 | 90% | target_occluded | C_P2_exp23 | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.19 / 9.85 |
| +0 | 90% | target_occluded | C_P2_modelff | 18 | 44 [25, 66] | 56 | 33 | 0 | 9.50 / 0.40 |
| +0 | 90% | target_occluded | C_P2_modelff_wall50 | 18 | 22 [9, 45] | 78 | 33 | 0 | 11.16 / 0.40 |
| +0 | 90% | target_occluded | C_P2_wall50 | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.01 / 9.83 |
| +0 | 90% | target_occluded | N_P2_hold | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.33 / 9.77 |
| +0 | 90% | target_occluded | N_P2_modelff_hold | 18 | 61 [39, 80] | 39 | 33 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2_exp23 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | patent | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | patent | C_P2_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | N_P2_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2_exp23 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | N_P2_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |

## Paired changes

| Flow error | Flow cut | Target | Arm | Baseline | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|
| +0 | 90% | patent | C_P2_exp23 | C_P2 | 0 | 1 | 1 | 16 | +0.14 |
| +0 | 90% | patent | C_P2_modelff | C_P2 | 7 | 2 | 0 | 9 | -0.27 |
| +0 | 90% | patent | C_P2_modelff_wall50 | C_P2 | 5 | 2 | 0 | 11 | +0.41 |
| +0 | 90% | patent | C_P2_wall50 | C_P2 | 0 | 0 | 2 | 16 | +0.00 |
| +0 | 90% | patent | N_P2_modelff_hold | N_P2_hold | 6 | 0 | 0 | 12 | -0.42 |
| +0 | 90% | target_occluded | C_P2_exp23 | C_P2 | 0 | 0 | 0 | 18 | +0.16 |
| +0 | 90% | target_occluded | C_P2_modelff | C_P2 | 8 | 0 | 0 | 10 | -0.94 |
| +0 | 90% | target_occluded | C_P2_modelff_wall50 | C_P2 | 4 | 0 | 0 | 14 | +0.43 |
| +0 | 90% | target_occluded | C_P2_wall50 | C_P2 | 0 | 0 | 0 | 18 | -0.02 |
| +0 | 90% | target_occluded | N_P2_modelff_hold | N_P2_hold | 11 | 0 | 0 | 7 | -9.38 |
| +0 | 99% | patent | C_P2_exp23 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_exp23 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_wall50 | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
