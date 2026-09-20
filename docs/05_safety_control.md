# Uncertainty-aware control and evaluation

## Control boundary

`BiplaneNavigation.step(now_s, frames)` accepts only current time and delivered
imaging observations. Its dependencies are configured vessel geometry,
particle radius, a triangulator, estimator, waypoint planner and supervisor.
It has no particle object, true position, true velocity, or true flow input.

Ground truth is confined to plant physics (including the simulated imaging
boundary), evaluation/termination, and diagnostic plotting. The original
Y-vessel demo now obtains an explicit ideal sensor observation; the direct
noisy demo initializes from a measurement and aligns true/estimated samples.

## Branch selection and control

`YWaypointPlanner` explicitly chooses upper or lower at construction and
generates centerline waypoints along the inlet and requested branch. It
advances using only estimated position and a tolerance/passage check. This
is deterministic Y route following, not general graph path planning.

An optional `approach_offset_m` displaces waypoints toward the chosen branch
before the junction. The offset ramps linearly from zero at a distance of two
inlet radii to its configured maximum at the junction, then returns to zero
over the same centerline distance downstream. Its direction is the outgoing
branch component perpendicular to the inlet. The target endpoint is unchanged.
With the toy 1.5 mm vessel radius, experiment 09 uses a 3 mm approach span and
0.4 mm maximum offset. Zero remains the default to reproduce the original
route and recorded benchmarks. The planner still receives geometry and
estimated position only; it does not estimate flow or predict future safety.
See [the approach guidance evaluation](09_approach_guidance.md).

The proportional controller requests `F = gain * (waypoint - estimated_p)`
and caps its Euclidean magnitude. The supervisor re-enforces the force cap.
The toy plant can apply a scalar actuation gain error, then caps the actual
force again. Zero requested force stays zero for all configured gain errors.
There are no coil currents, actuator dynamics, or bounded least squares yet.

## Supervisor

`estimated_clearance = vessel.clearance(estimated_position, particle_radius)`

`robust_clearance = estimated_clearance - k_sigma * position_uncertainty`

Require `robust_clearance > safety_margin`. Check in this priority order:

| Condition | Logged reason | Action |
|---|---|---|
| No estimate, latest delivered pair lost/invalid, or capture age above timeout | `tracking_lost` | Zero active force |
| Invalid uncertainty/state or sigma above threshold | `localization_uncertain` | Zero active force |
| Robust margin <= configured margin | `wall_margin_low` | Zero active force |
| Desired magnitude exceeds bound, otherwise allowed | `actuation_limit` | Apply capped force |
| All checks pass | `safe` | Apply bounded force |

Only the highest-priority reason is recorded on a tick. `actuation_limit` is
a saturation event, not a stop. Tracking recovers upon a fresh valid frame,
provided age, covariance, and wall margin pass. There is no hysteresis.

This is a reactive stop gate, not an invariant safety guarantee. It does not
check predicted collision along the force direction or a reachable tube.
Zero actuation leaves fluid advection unchanged; it does not immobilize the
particle or guarantee that the selected branch is reached. Delayed dropout
reports cannot stop control retroactively. Startup and terminal samples are
included in the reported sample-based stop fraction.

## Metrics

Safety metrics are primary. The runner saves configuration, seed, JSON
summary and timestamp-aligned histories; startup missing estimates are NaN
in NPZ data and excluded from localization RMSE. JSON uses null when RMSE
or successful navigation time is unavailable.

| Field | Definition |
|---|---|
| `wall_collision` | Any sampled particle-clearance proxy <= 0; stops trial |
| `minimum_wall_clearance_m` | Minimum true-position capsule-union proxy, including initial sample |
| `wrong_branch` | Latched entry into nearer unintended branch beyond a 2 mm junction exclusion region |
| `target_success` | True distance <= 0.4 mm, with no wall violation or wrong-branch event |
| `navigation_time_s` | Time to success; null for failures/timeouts |
| `elapsed_time_s` | Actual trial duration |
| `safety_stop_rate` | Fraction of logged physics samples with one of the three stop reasons |
| `safety_stop_events` | Number of transitions into stopped state, including startup |
| `localization_RMSE_m` | sqrt(mean squared 3D position error at matching timestamps) |
| `maximum_force_n` | Maximum logged applied-force magnitude |
| `reason_counts` | Sample count by supervisor outcome |

The wrong-branch detector is a Y-specific nearest-centerline heuristic with
an ambiguity region, not a topological vessel-segment classifier. A graph
representation and branch-crossing surfaces remain future work.

The paired-seed benchmark reports success, wall-proxy and wrong-branch rates
with conditional Wilson intervals. Experiment 09 additionally compares
matched route outcomes and terminal capsule feature counts. These estimates
describe the configured toy scenarios, not broad physical parameter
distributions or a calibrated safety guarantee.
