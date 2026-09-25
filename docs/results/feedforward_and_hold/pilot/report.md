# Experiment 24 (pilot)

Simulation only. Seeds 0, 1, 2; rates pool both branches and all frame rates; brackets are 95% Wilson intervals. Paired changes compare each arm with its material's baseline (C_P2 or N_P2_hold) on every other factor.

| Flow error | Flow cut | Target | Arm | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | Closest mm (median / min) |
|---:|---:|---|---|---:|---|---:|---:|---:|---|
| +0 | 90% | patent | C_P2 | 18 | 11 [3, 33] | 78 | 50 | 6 | 6.93 / 0.40 |
| +0 | 90% | patent | C_P2_exp23 | 18 | 11 [3, 33] | 83 | 50 | 0 | 9.85 / 0.39 |
| +0 | 90% | patent | C_P2_modelff | 18 | 33 [16, 56] | 61 | 39 | 6 | 3.78 / 0.40 |
| +0 | 90% | patent | C_P2_modelff_wall50 | 18 | 17 [6, 39] | 83 | 56 | 0 | 11.01 / 0.40 |
| +0 | 90% | patent | C_P2_wall50 | 18 | 17 [6, 39] | 72 | 50 | 6 | 6.93 / 0.39 |
| +0 | 90% | patent | N_P2_hold | 18 | 0 [0, 18] | 94 | 50 | 0 | 9.80 / 0.77 |
| +0 | 90% | patent | N_P2_modelff_hold | 18 | 28 [12, 51] | 72 | 50 | 0 | 9.20 / 0.40 |
| +0 | 90% | target_occluded | C_P2 | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.08 / 9.81 |
| +0 | 90% | target_occluded | C_P2_exp23 | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.17 / 9.81 |
| +0 | 90% | target_occluded | C_P2_modelff | 18 | 44 [25, 66] | 56 | 33 | 0 | 9.51 / 0.40 |
| +0 | 90% | target_occluded | C_P2_modelff_wall50 | 18 | 11 [3, 33] | 89 | 33 | 0 | 11.26 / 0.40 |
| +0 | 90% | target_occluded | C_P2_wall50 | 18 | 0 [0, 18] | 94 | 100 | 0 | 10.06 / 9.77 |
| +0 | 90% | target_occluded | N_P2_hold | 18 | 0 [0, 18] | 100 | 100 | 0 | 10.34 / 9.76 |
| +0 | 90% | target_occluded | N_P2_modelff_hold | 18 | 61 [39, 80] | 39 | 33 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2_exp23 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | patent | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | patent | C_P2_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | N_P2_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | patent | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | C_P2_exp23 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | target_occluded | C_P2_modelff | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | target_occluded | C_P2_modelff_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.39 |
| +0 | 99% | target_occluded | C_P2_wall50 | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | N_P2_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |
| +0 | 99% | target_occluded | N_P2_modelff_hold | 18 | 100 [82, 100] | 0 | 0 | 0 | 0.40 / 0.40 |

## Paired changes

| Flow error | Flow cut | Target | Arm | Baseline | Rescued | Regressed | Both success | Both fail | Median closest change mm |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|
| +0 | 90% | patent | C_P2_exp23 | C_P2 | 0 | 0 | 2 | 16 | +0.05 |
| +0 | 90% | patent | C_P2_modelff | C_P2 | 4 | 0 | 2 | 12 | +0.00 |
| +0 | 90% | patent | C_P2_modelff_wall50 | C_P2 | 1 | 0 | 2 | 15 | +1.58 |
| +0 | 90% | patent | C_P2_wall50 | C_P2 | 1 | 0 | 2 | 15 | +0.00 |
| +0 | 90% | patent | N_P2_modelff_hold | N_P2_hold | 5 | 0 | 0 | 13 | -0.16 |
| +0 | 90% | target_occluded | C_P2_exp23 | C_P2 | 0 | 0 | 0 | 18 | +0.06 |
| +0 | 90% | target_occluded | C_P2_modelff | C_P2 | 8 | 0 | 0 | 10 | -0.93 |
| +0 | 90% | target_occluded | C_P2_modelff_wall50 | C_P2 | 2 | 0 | 0 | 16 | +1.31 |
| +0 | 90% | target_occluded | C_P2_wall50 | C_P2 | 0 | 0 | 0 | 18 | -0.02 |
| +0 | 90% | target_occluded | N_P2_modelff_hold | N_P2_hold | 11 | 0 | 0 | 7 | -9.40 |
| +0 | 99% | patent | C_P2_exp23 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | patent | C_P2_wall50 | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | patent | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_exp23 | C_P2 | 0 | 0 | 18 | 0 | -0.00 |
| +0 | 99% | target_occluded | C_P2_modelff | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | target_occluded | C_P2_modelff_wall50 | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | target_occluded | C_P2_wall50 | C_P2 | 0 | 0 | 18 | 0 | +0.00 |
| +0 | 99% | target_occluded | N_P2_modelff_hold | N_P2_hold | 0 | 0 | 18 | 0 | -0.00 |
