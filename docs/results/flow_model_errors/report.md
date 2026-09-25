# Experiment 25: controller flow-model errors

Simulation only. Held-out seeds 3-5, both branches, all frame rates pooled. The plant never changes; only the controller's flow model is wrong. Route error is the mean |u_model - u_plant| over both routes (centerline and 0.5 mm off-axis) and one cardiac period.

| Condition | Flow cut | Target | Arm | Route error mm/s | Success [95% CI] | Wall | Wrong |
|---|---:|---|---|---:|---|---:|---:|
| double_pulsation | 90% | patent | C_P2_modelff | 15.7 | 0/18 [0, 18] | 18 | 0 |
| double_pulsation | 90% | patent | N_P2_modelff_hold | 15.7 | 0/18 [0, 18] | 18 | 3 |
| double_pulsation | 90% | target_occluded | C_P2_modelff | 8.3 | 0/18 [0, 18] | 18 | 6 |
| double_pulsation | 90% | target_occluded | N_P2_modelff_hold | 8.3 | 0/18 [0, 18] | 18 | 6 |
| double_pulsation | 99% | patent | C_P2_modelff | 1.6 | 18/18 [82, 100] | 0 | 0 |
| double_pulsation | 99% | patent | N_P2_modelff_hold | 1.6 | 18/18 [82, 100] | 0 | 0 |
| double_pulsation | 99% | target_occluded | C_P2_modelff | 0.8 | 18/18 [82, 100] | 0 | 0 |
| double_pulsation | 99% | target_occluded | N_P2_modelff_hold | 0.8 | 18/18 [82, 100] | 0 | 0 |
| exact | 90% | patent | C_P2_modelff | 0.0 | 7/18 [20, 61] | 11 | 6 |
| exact | 90% | patent | N_P2_modelff_hold | 0.0 | 6/18 [16, 56] | 12 | 8 |
| exact | 90% | target_occluded | C_P2_modelff | 0.0 | 8/18 [25, 66] | 10 | 6 |
| exact | 90% | target_occluded | N_P2_modelff_hold | 0.0 | 11/18 [39, 80] | 7 | 6 |
| exact | 99% | patent | C_P2_modelff | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | patent | N_P2_modelff_hold | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | target_occluded | C_P2_modelff | 0.0 | 18/18 [82, 100] | 0 | 0 |
| exact | 99% | target_occluded | N_P2_modelff_hold | 0.0 | 18/18 [82, 100] | 0 | 0 |
| junction_x0.5 | 90% | patent | C_P2_modelff | 0.5 | 2/18 [3, 33] | 16 | 11 |
| junction_x0.5 | 90% | patent | N_P2_modelff_hold | 0.5 | 1/18 [1, 26] | 17 | 14 |
| junction_x0.5 | 90% | target_occluded | C_P2_modelff | 0.4 | 10/18 [34, 75] | 7 | 6 |
| junction_x0.5 | 90% | target_occluded | N_P2_modelff_hold | 0.4 | 12/18 [44, 84] | 6 | 6 |
| junction_x0.5 | 99% | patent | C_P2_modelff | 0.1 | 18/18 [82, 100] | 0 | 0 |
| junction_x0.5 | 99% | patent | N_P2_modelff_hold | 0.1 | 18/18 [82, 100] | 0 | 0 |
| junction_x0.5 | 99% | target_occluded | C_P2_modelff | 0.0 | 18/18 [82, 100] | 0 | 0 |
| junction_x0.5 | 99% | target_occluded | N_P2_modelff_hold | 0.0 | 18/18 [82, 100] | 0 | 0 |
| junction_x2 | 90% | patent | C_P2_modelff | 1.0 | 11/18 [39, 80] | 7 | 4 |
| junction_x2 | 90% | patent | N_P2_modelff_hold | 1.0 | 10/18 [34, 75] | 8 | 5 |
| junction_x2 | 90% | target_occluded | C_P2_modelff | 0.7 | 0/18 [0, 18] | 18 | 6 |
| junction_x2 | 90% | target_occluded | N_P2_modelff_hold | 0.7 | 0/18 [0, 18] | 18 | 6 |
| junction_x2 | 99% | patent | C_P2_modelff | 0.1 | 18/18 [82, 100] | 0 | 0 |
| junction_x2 | 99% | patent | N_P2_modelff_hold | 0.1 | 18/18 [82, 100] | 0 | 0 |
| junction_x2 | 99% | target_occluded | C_P2_modelff | 0.1 | 18/18 [82, 100] | 0 | 0 |
| junction_x2 | 99% | target_occluded | N_P2_modelff_hold | 0.1 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.1 | 90% | patent | C_P2_modelff | 9.7 | 6/18 [16, 56] | 4 | 3 |
| phase_+0.1 | 90% | patent | N_P2_modelff_hold | 9.7 | 6/18 [16, 56] | 7 | 6 |
| phase_+0.1 | 90% | target_occluded | C_P2_modelff | 5.1 | 8/18 [25, 66] | 10 | 6 |
| phase_+0.1 | 90% | target_occluded | N_P2_modelff_hold | 5.1 | 7/18 [20, 61] | 11 | 6 |
| phase_+0.1 | 99% | patent | C_P2_modelff | 1.0 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.1 | 99% | patent | N_P2_modelff_hold | 1.0 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.1 | 99% | target_occluded | C_P2_modelff | 0.5 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.1 | 99% | target_occluded | N_P2_modelff_hold | 0.5 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.25 | 90% | patent | C_P2_modelff | 22.4 | 0/18 [0, 18] | 6 | 3 |
| phase_+0.25 | 90% | patent | N_P2_modelff_hold | 22.4 | 0/18 [0, 18] | 9 | 3 |
| phase_+0.25 | 90% | target_occluded | C_P2_modelff | 11.9 | 0/18 [0, 18] | 16 | 12 |
| phase_+0.25 | 90% | target_occluded | N_P2_modelff_hold | 11.9 | 0/18 [0, 18] | 11 | 7 |
| phase_+0.25 | 99% | patent | C_P2_modelff | 2.2 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.25 | 99% | patent | N_P2_modelff_hold | 2.2 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.25 | 99% | target_occluded | C_P2_modelff | 1.2 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.25 | 99% | target_occluded | N_P2_modelff_hold | 1.2 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.5 | 90% | patent | C_P2_modelff | 31.3 | 0/18 [0, 18] | 18 | 8 |
| phase_+0.5 | 90% | patent | N_P2_modelff_hold | 31.3 | 0/18 [0, 18] | 18 | 7 |
| phase_+0.5 | 90% | target_occluded | C_P2_modelff | 16.6 | 0/18 [0, 18] | 18 | 18 |
| phase_+0.5 | 90% | target_occluded | N_P2_modelff_hold | 16.6 | 0/18 [0, 18] | 18 | 18 |
| phase_+0.5 | 99% | patent | C_P2_modelff | 3.1 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.5 | 99% | patent | N_P2_modelff_hold | 3.1 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.5 | 99% | target_occluded | C_P2_modelff | 1.7 | 18/18 [82, 100] | 0 | 0 |
| phase_+0.5 | 99% | target_occluded | N_P2_modelff_hold | 1.7 | 18/18 [82, 100] | 0 | 0 |
| profile_n4 | 90% | patent | C_P2_modelff | 10.5 | 3/18 [6, 39] | 15 | 8 |
| profile_n4 | 90% | patent | N_P2_modelff_hold | 10.5 | 1/18 [1, 26] | 17 | 6 |
| profile_n4 | 90% | target_occluded | C_P2_modelff | 5.3 | 0/18 [0, 18] | 18 | 18 |
| profile_n4 | 90% | target_occluded | N_P2_modelff_hold | 5.3 | 0/18 [0, 18] | 18 | 15 |
| profile_n4 | 99% | patent | C_P2_modelff | 1.0 | 18/18 [82, 100] | 0 | 0 |
| profile_n4 | 99% | patent | N_P2_modelff_hold | 1.0 | 18/18 [82, 100] | 0 | 0 |
| profile_n4 | 99% | target_occluded | C_P2_modelff | 0.5 | 18/18 [82, 100] | 0 | 0 |
| profile_n4 | 99% | target_occluded | N_P2_modelff_hold | 0.5 | 18/18 [82, 100] | 0 | 0 |
| profile_n9 | 90% | patent | C_P2_modelff | 18.4 | 0/18 [0, 18] | 18 | 7 |
| profile_n9 | 90% | patent | N_P2_modelff_hold | 18.4 | 0/18 [0, 18] | 18 | 7 |
| profile_n9 | 90% | target_occluded | C_P2_modelff | 9.5 | 0/18 [0, 18] | 18 | 18 |
| profile_n9 | 90% | target_occluded | N_P2_modelff_hold | 9.5 | 0/18 [0, 18] | 18 | 18 |
| profile_n9 | 99% | patent | C_P2_modelff | 1.8 | 18/18 [82, 100] | 0 | 0 |
| profile_n9 | 99% | patent | N_P2_modelff_hold | 1.8 | 18/18 [82, 100] | 0 | 0 |
| profile_n9 | 99% | target_occluded | C_P2_modelff | 1.0 | 18/18 [82, 100] | 0 | 0 |
| profile_n9 | 99% | target_occluded | N_P2_modelff_hold | 1.0 | 18/18 [82, 100] | 0 | 0 |
| scale_+20% | 90% | patent | C_P2_modelff | 11.0 | 1/18 [1, 26] | 17 | 4 |
| scale_+20% | 90% | patent | N_P2_modelff_hold | 11.0 | 0/18 [0, 18] | 18 | 7 |
| scale_+20% | 90% | target_occluded | C_P2_modelff | 5.8 | 0/18 [0, 18] | 18 | 6 |
| scale_+20% | 90% | target_occluded | N_P2_modelff_hold | 5.8 | 0/18 [0, 18] | 18 | 6 |
| scale_+20% | 99% | patent | C_P2_modelff | 1.1 | 18/18 [82, 100] | 0 | 0 |
| scale_+20% | 99% | patent | N_P2_modelff_hold | 1.1 | 18/18 [82, 100] | 0 | 0 |
| scale_+20% | 99% | target_occluded | C_P2_modelff | 0.6 | 18/18 [82, 100] | 0 | 0 |
| scale_+20% | 99% | target_occluded | N_P2_modelff_hold | 0.6 | 18/18 [82, 100] | 0 | 0 |
| scale_-20% | 90% | patent | C_P2_modelff | 11.0 | 3/18 [6, 39] | 15 | 7 |
| scale_-20% | 90% | patent | N_P2_modelff_hold | 11.0 | 3/18 [6, 39] | 15 | 7 |
| scale_-20% | 90% | target_occluded | C_P2_modelff | 5.8 | 0/18 [0, 18] | 18 | 16 |
| scale_-20% | 90% | target_occluded | N_P2_modelff_hold | 5.8 | 0/18 [0, 18] | 18 | 15 |
| scale_-20% | 99% | patent | C_P2_modelff | 1.1 | 18/18 [82, 100] | 0 | 0 |
| scale_-20% | 99% | patent | N_P2_modelff_hold | 1.1 | 18/18 [82, 100] | 0 | 0 |
| scale_-20% | 99% | target_occluded | C_P2_modelff | 0.6 | 18/18 [82, 100] | 0 | 0 |
| scale_-20% | 99% | target_occluded | N_P2_modelff_hold | 0.6 | 18/18 [82, 100] | 0 | 0 |
| steady_model | 90% | patent | C_P2_modelff | 15.7 | 3/18 [6, 39] | 15 | 8 |
| steady_model | 90% | patent | N_P2_modelff_hold | 15.7 | 1/18 [1, 26] | 17 | 8 |
| steady_model | 90% | target_occluded | C_P2_modelff | 8.3 | 0/18 [0, 18] | 18 | 18 |
| steady_model | 90% | target_occluded | N_P2_modelff_hold | 8.3 | 0/18 [0, 18] | 18 | 18 |
| steady_model | 99% | patent | C_P2_modelff | 1.6 | 18/18 [82, 100] | 0 | 0 |
| steady_model | 99% | patent | N_P2_modelff_hold | 1.6 | 18/18 [82, 100] | 0 | 0 |
| steady_model | 99% | target_occluded | C_P2_modelff | 0.8 | 18/18 [82, 100] | 0 | 0 |
| steady_model | 99% | target_occluded | N_P2_modelff_hold | 0.8 | 18/18 [82, 100] | 0 | 0 |

## Paired against the exact model

| Condition | Flow cut | Target | Arm | Kept | Lost | Gained | Both fail |
|---|---:|---|---|---:|---:|---:|---:|
| double_pulsation | 90% | patent | C_P2_modelff | 0 | 7 | 0 | 11 |
| double_pulsation | 90% | patent | N_P2_modelff_hold | 0 | 6 | 0 | 12 |
| double_pulsation | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| double_pulsation | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| double_pulsation | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| double_pulsation | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| double_pulsation | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| double_pulsation | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| junction_x0.5 | 90% | patent | C_P2_modelff | 2 | 5 | 0 | 11 |
| junction_x0.5 | 90% | patent | N_P2_modelff_hold | 1 | 5 | 0 | 12 |
| junction_x0.5 | 90% | target_occluded | C_P2_modelff | 6 | 2 | 4 | 6 |
| junction_x0.5 | 90% | target_occluded | N_P2_modelff_hold | 11 | 0 | 1 | 6 |
| junction_x0.5 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| junction_x0.5 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| junction_x0.5 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| junction_x0.5 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| junction_x2 | 90% | patent | C_P2_modelff | 7 | 0 | 4 | 7 |
| junction_x2 | 90% | patent | N_P2_modelff_hold | 6 | 0 | 4 | 8 |
| junction_x2 | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| junction_x2 | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| junction_x2 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| junction_x2 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| junction_x2 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| junction_x2 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.1 | 90% | patent | C_P2_modelff | 0 | 7 | 6 | 5 |
| phase_+0.1 | 90% | patent | N_P2_modelff_hold | 0 | 6 | 6 | 6 |
| phase_+0.1 | 90% | target_occluded | C_P2_modelff | 6 | 2 | 2 | 8 |
| phase_+0.1 | 90% | target_occluded | N_P2_modelff_hold | 7 | 4 | 0 | 7 |
| phase_+0.1 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.1 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.1 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.1 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.25 | 90% | patent | C_P2_modelff | 0 | 7 | 0 | 11 |
| phase_+0.25 | 90% | patent | N_P2_modelff_hold | 0 | 6 | 0 | 12 |
| phase_+0.25 | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| phase_+0.25 | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| phase_+0.25 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.25 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.25 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.25 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.5 | 90% | patent | C_P2_modelff | 0 | 7 | 0 | 11 |
| phase_+0.5 | 90% | patent | N_P2_modelff_hold | 0 | 6 | 0 | 12 |
| phase_+0.5 | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| phase_+0.5 | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| phase_+0.5 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.5 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| phase_+0.5 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| phase_+0.5 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| profile_n4 | 90% | patent | C_P2_modelff | 3 | 4 | 0 | 11 |
| profile_n4 | 90% | patent | N_P2_modelff_hold | 1 | 5 | 0 | 12 |
| profile_n4 | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| profile_n4 | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| profile_n4 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| profile_n4 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| profile_n4 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| profile_n4 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| profile_n9 | 90% | patent | C_P2_modelff | 0 | 7 | 0 | 11 |
| profile_n9 | 90% | patent | N_P2_modelff_hold | 0 | 6 | 0 | 12 |
| profile_n9 | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| profile_n9 | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| profile_n9 | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| profile_n9 | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| profile_n9 | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| profile_n9 | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| scale_+20% | 90% | patent | C_P2_modelff | 0 | 7 | 1 | 10 |
| scale_+20% | 90% | patent | N_P2_modelff_hold | 0 | 6 | 0 | 12 |
| scale_+20% | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| scale_+20% | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| scale_+20% | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| scale_+20% | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| scale_+20% | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| scale_+20% | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| scale_-20% | 90% | patent | C_P2_modelff | 3 | 4 | 0 | 11 |
| scale_-20% | 90% | patent | N_P2_modelff_hold | 3 | 3 | 0 | 12 |
| scale_-20% | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| scale_-20% | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| scale_-20% | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| scale_-20% | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| scale_-20% | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| scale_-20% | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| steady_model | 90% | patent | C_P2_modelff | 3 | 4 | 0 | 11 |
| steady_model | 90% | patent | N_P2_modelff_hold | 1 | 5 | 0 | 12 |
| steady_model | 90% | target_occluded | C_P2_modelff | 0 | 8 | 0 | 10 |
| steady_model | 90% | target_occluded | N_P2_modelff_hold | 0 | 11 | 0 | 7 |
| steady_model | 99% | patent | C_P2_modelff | 18 | 0 | 0 | 0 |
| steady_model | 99% | patent | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
| steady_model | 99% | target_occluded | C_P2_modelff | 18 | 0 | 0 | 0 |
| steady_model | 99% | target_occluded | N_P2_modelff_hold | 18 | 0 | 0 | 0 |
