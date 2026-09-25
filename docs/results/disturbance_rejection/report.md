# Experiment 30: disturbance rejection

Simulation only. Held-out seeds 3-5, both branches and targets, 7.5/15/30 fps, 99% flow reduction, open-loop hold and matched gate for both materials.

| Estimator | Bundle | Arm | Success [95% CI] | 7.5 / 15 / 30 fps | Wall | Wrong | Timeout | Kept / lost / gained vs baseline |
|---|---|---|---|---|---:|---:|---:|---|
| baseline | nominal | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | — |
| baseline | nominal | N_P2_hold | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | — |
| baseline | mild | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | — |
| baseline | mild | N_P2_hold | 32/36 [75, 96] | 8 / 12 / 12 | 4 | 0 | 0 | — |
| baseline | moderate | C_P2 | 33/36 [78, 97] | 10 / 11 / 12 | 3 | 2 | 0 | — |
| baseline | moderate | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | — |
| drift_ff | nominal | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| drift_ff | nominal | N_P2_hold | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| drift_ff | mild | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| drift_ff | mild | N_P2_hold | 32/36 [75, 96] | 8 / 12 / 12 | 4 | 0 | 0 | 32 / 0 / 0 |
| drift_ff | moderate | C_P2 | 35/36 [86, 100] | 12 / 11 / 12 | 1 | 1 | 0 | 32 / 1 / 3 |
| drift_ff | moderate | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 0 / 0 |
| fast_residual | nominal | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| fast_residual | nominal | N_P2_hold | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| fast_residual | mild | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| fast_residual | mild | N_P2_hold | 20/36 [40, 70] | 0 / 8 / 12 | 16 | 0 | 0 | 20 / 12 / 0 |
| fast_residual | moderate | C_P2 | 21/36 [42, 73] | 3 / 6 / 12 | 15 | 5 | 0 | 21 / 12 / 0 |
| fast_residual | moderate | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 0 / 0 |
| fast_residual_ff | nominal | C_P2 | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| fast_residual_ff | nominal | N_P2_hold | 36/36 [90, 100] | 12 / 12 / 12 | 0 | 0 | 0 | 36 / 0 / 0 |
| fast_residual_ff | mild | C_P2 | 35/36 [86, 100] | 11 / 12 / 12 | 1 | 0 | 0 | 35 / 1 / 0 |
| fast_residual_ff | mild | N_P2_hold | 20/36 [40, 70] | 0 / 8 / 12 | 16 | 0 | 0 | 20 / 12 / 0 |
| fast_residual_ff | moderate | C_P2 | 19/36 [37, 68] | 2 / 5 / 12 | 17 | 4 | 0 | 19 / 14 / 0 |
| fast_residual_ff | moderate | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 0 / 0 |
| faster_residual_ff | nominal | C_P2 | 7/36 [10, 35] | 0 / 3 / 4 | 29 | 23 | 0 | 7 / 29 / 0 |
| faster_residual_ff | nominal | N_P2_hold | 6/36 [8, 32] | 0 / 2 / 4 | 26 | 26 | 0 | 6 / 30 / 0 |
| faster_residual_ff | mild | C_P2 | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 36 / 0 |
| faster_residual_ff | mild | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 32 / 0 |
| faster_residual_ff | moderate | C_P2 | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 33 / 0 |
| faster_residual_ff | moderate | N_P2_hold | 0/36 [0, 10] | 0 / 0 / 0 | 36 | 0 | 0 | 0 / 0 / 0 |
