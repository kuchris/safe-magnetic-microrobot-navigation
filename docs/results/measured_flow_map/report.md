# Experiment 26: measured flow map

Simulation only. Held-out seeds 3-5, both branches, all frame rates pooled. The controller's flow model is the plant's time-mean field on a voxel grid with per-voxel noise; route error is the mean |u_map - u_plant| along both routes over one cardiac period (noise realization of seed 3).

| Condition | Flow cut | Target | Arm | Route error mm/s | Success [95% CI] | Wall | Wrong |
|---|---:|---|---|---:|---|---:|---:|
| exact | 90% | patent | C_P2_modelff | 0.0 | 7/18 [20, 61] | 11 | 6 |
| exact | 90% | patent | N_P2_modelff_hold | 0.0 | 6/18 [16, 56] | 12 | 8 |
| exact | 90% | target_occluded | C_P2_modelff | 0.0 | 8/18 [25, 66] | 10 | 6 |
| exact | 90% | target_occluded | N_P2_modelff_hold | 0.0 | 11/18 [39, 80] | 7 | 6 |
| exact | 99% | patent | C_P2_modelff | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | patent | N_P2_modelff_hold | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | target_occluded | C_P2_modelff | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | target_occluded | N_P2_modelff_hold | 0.0 | 18/18 [82, 100] | 0 | 0 |
| map_0.25mm | 90% | patent | C_P2_modelff | 0.7 | 9/18 [29, 71] | 9 | 6 |
| map_0.25mm | 90% | patent | N_P2_modelff_hold | 0.7 | 6/18 [16, 56] | 12 | 8 |
| map_0.25mm | 90% | target_occluded | C_P2_modelff | 0.4 | 11/18 [39, 80] | 7 | 6 |
| map_0.25mm | 90% | target_occluded | N_P2_modelff_hold | 0.4 | 12/18 [44, 84] | 6 | 6 |
| map_0.5mm | 90% | patent | C_P2_modelff | 2.3 | 9/18 [29, 71] | 8 | 5 |
| map_0.5mm | 90% | patent | N_P2_modelff_hold | 2.3 | 9/18 [29, 71] | 9 | 5 |
| map_0.5mm | 90% | target_occluded | C_P2_modelff | 1.2 | 12/18 [44, 84] | 6 | 6 |
| map_0.5mm | 90% | target_occluded | N_P2_modelff_hold | 1.2 | 11/18 [39, 80] | 6 | 6 |
| map_0.5mm_noise10% | 90% | patent | C_P2_modelff | 6.0 | 4/18 [9, 45] | 13 | 7 |
| map_0.5mm_noise10% | 90% | patent | N_P2_modelff_hold | 6.0 | 4/18 [9, 45] | 11 | 6 |
| map_0.5mm_noise10% | 90% | target_occluded | C_P2_modelff | 5.7 | 5/18 [12, 51] | 11 | 6 |
| map_0.5mm_noise10% | 90% | target_occluded | N_P2_modelff_hold | 5.7 | 7/18 [20, 61] | 10 | 7 |
| map_0.5mm_noise5% | 90% | patent | C_P2_modelff | 3.5 | 8/18 [25, 66] | 9 | 5 |
| map_0.5mm_noise5% | 90% | patent | N_P2_modelff_hold | 3.5 | 8/18 [25, 66] | 9 | 5 |
| map_0.5mm_noise5% | 90% | target_occluded | C_P2_modelff | 3.1 | 9/18 [29, 71] | 8 | 6 |
| map_0.5mm_noise5% | 90% | target_occluded | N_P2_modelff_hold | 3.1 | 10/18 [34, 75] | 6 | 6 |
| map_1.0mm | 90% | patent | C_P2_modelff | 9.3 | 4/18 [9, 45] | 12 | 7 |
| map_1.0mm | 90% | patent | N_P2_modelff_hold | 9.3 | 4/18 [9, 45] | 14 | 6 |
| map_1.0mm | 90% | target_occluded | C_P2_modelff | 5.3 | 0/18 [0, 18] | 18 | 16 |
| map_1.0mm | 90% | target_occluded | N_P2_modelff_hold | 5.3 | 0/18 [0, 18] | 18 | 15 |
| map_1.0mm_noise10% | 90% | patent | C_P2_modelff | 11.0 | 3/18 [6, 39] | 8 | 7 |
| map_1.0mm_noise10% | 90% | patent | N_P2_modelff_hold | 11.0 | 1/18 [1, 26] | 10 | 9 |
| map_1.0mm_noise10% | 90% | target_occluded | C_P2_modelff | 9.1 | 0/18 [0, 18] | 17 | 17 |
| map_1.0mm_noise10% | 90% | target_occluded | N_P2_modelff_hold | 9.1 | 0/18 [0, 18] | 17 | 16 |
| map_1.0mm_noise10% | 99% | patent | C_P2_modelff | 1.1 | 18/18 [82, 100] | 0 | 0 |
| map_1.0mm_noise10% | 99% | patent | N_P2_modelff_hold | 1.1 | 18/18 [82, 100] | 0 | 0 |
| map_1.0mm_noise10% | 99% | target_occluded | C_P2_modelff | 0.9 | 18/18 [82, 100] | 0 | 0 |
| map_1.0mm_noise10% | 99% | target_occluded | N_P2_modelff_hold | 0.9 | 18/18 [82, 100] | 0 | 0 |

## Paired against the exact analytic model

| Condition | Flow cut | Target | Arm | Kept | Lost | Gained | Both fail |
|---|---:|---|---|---:|---:|---:|---:|
| map_0.25mm | 90% | patent | C_P2_modelff | 7 | 0 | 2 | 9 |
| map_0.25mm | 90% | patent | N_P2_modelff_hold | 6 | 0 | 0 | 12 |
| map_0.25mm | 90% | target_occluded | C_P2_modelff | 8 | 0 | 3 | 7 |
| map_0.25mm | 90% | target_occluded | N_P2_modelff_hold | 11 | 0 | 1 | 6 |
| map_0.5mm | 90% | patent | C_P2_modelff | 6 | 1 | 3 | 8 |
| map_0.5mm | 90% | patent | N_P2_modelff_hold | 6 | 0 | 3 | 9 |
| map_0.5mm | 90% | target_occluded | C_P2_modelff | 8 | 0 | 4 | 6 |
| map_0.5mm | 90% | target_occluded | N_P2_modelff_hold | 10 | 1 | 1 | 6 |
| map_0.5mm_noise10% | 90% | patent | C_P2_modelff | 2 | 5 | 2 | 9 |
| map_0.5mm_noise10% | 90% | patent | N_P2_modelff_hold | 2 | 4 | 2 | 10 |
| map_0.5mm_noise10% | 90% | target_occluded | C_P2_modelff | 2 | 6 | 3 | 7 |
| map_0.5mm_noise10% | 90% | target_occluded | N_P2_modelff_hold | 6 | 5 | 1 | 6 |
| map_0.5mm_noise5% | 90% | patent | C_P2_modelff | 5 | 2 | 3 | 8 |
| map_0.5mm_noise5% | 90% | patent | N_P2_modelff_hold | 5 | 1 | 3 | 9 |
| map_0.5mm_noise5% | 90% | target_occluded | C_P2_modelff | 5 | 3 | 4 | 6 |
| map_0.5mm_noise5% | 90% | target_occluded | N_P2_modelff_hold | 9 | 2 | 1 | 6 |
| map_1.0mm | 90% | patent | C_P2_modelff | 3 | 4 | 1 | 10 |
| map_1.0mm | 90% | patent | N_P2_modelff_hold | 3 | 3 | 1 | 11 |
| map_1.0mm | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| map_1.0mm | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| map_1.0mm_noise10% | 90% | patent | C_P2_modelff | 1 | 6 | 2 | 9 |
| map_1.0mm_noise10% | 90% | patent | N_P2_modelff_hold | 0 | 6 | 1 | 11 |
| map_1.0mm_noise10% | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| map_1.0mm_noise10% | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| map_1.0mm_noise10% | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| map_1.0mm_noise10% | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| map_1.0mm_noise10% | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| map_1.0mm_noise10% | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
