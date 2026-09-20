# Flow sensitivity: piecewise

Gated control, 60 s horizon, 0.25 s disturbance correlation time. Counts are per trial.

| Flow mm/s | Disturbance sigma mm/s | Branch | Offset mm | N | Success | Wrong branch | Wall proxy | Timeout |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 0.3 | 0 | upper | 0 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0 | lower | 0 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0 | lower | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0.1 | upper | 0 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0.1 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0.1 | lower | 0 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0.1 | lower | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.3 | 0.3 | upper | 0 | 5 | 3 | 0 | 1 | 1 |
| 0.3 | 0.3 | upper | 0.4 | 5 | 3 | 0 | 1 | 1 |
| 0.3 | 0.3 | lower | 0 | 5 | 4 | 1 | 1 | 0 |
| 0.3 | 0.3 | lower | 0.4 | 5 | 4 | 0 | 1 | 0 |
| 0.6 | 0 | upper | 0 | 5 | 5 | 0 | 0 | 0 |
| 0.6 | 0 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.6 | 0 | lower | 0 | 5 | 4 | 1 | 1 | 0 |
| 0.6 | 0 | lower | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.6 | 0.1 | upper | 0 | 5 | 2 | 3 | 3 | 0 |
| 0.6 | 0.1 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.6 | 0.1 | lower | 0 | 5 | 4 | 1 | 1 | 0 |
| 0.6 | 0.1 | lower | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 0.6 | 0.3 | upper | 0 | 5 | 1 | 4 | 4 | 0 |
| 0.6 | 0.3 | upper | 0.4 | 5 | 3 | 1 | 2 | 0 |
| 0.6 | 0.3 | lower | 0 | 5 | 2 | 1 | 3 | 0 |
| 0.6 | 0.3 | lower | 0.4 | 5 | 2 | 1 | 3 | 0 |
| 1.2 | 0 | upper | 0 | 5 | 5 | 0 | 0 | 0 |
| 1.2 | 0 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 1.2 | 0 | lower | 0 | 5 | 4 | 1 | 1 | 0 |
| 1.2 | 0 | lower | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 1.2 | 0.1 | upper | 0 | 5 | 3 | 2 | 2 | 0 |
| 1.2 | 0.1 | upper | 0.4 | 5 | 5 | 0 | 0 | 0 |
| 1.2 | 0.1 | lower | 0 | 5 | 3 | 2 | 2 | 0 |
| 1.2 | 0.1 | lower | 0.4 | 5 | 4 | 1 | 1 | 0 |
| 1.2 | 0.3 | upper | 0 | 5 | 2 | 3 | 3 | 0 |
| 1.2 | 0.3 | upper | 0.4 | 5 | 2 | 3 | 3 | 0 |
| 1.2 | 0.3 | lower | 0 | 5 | 3 | 2 | 2 | 0 |
| 1.2 | 0.3 | lower | 0.4 | 5 | 3 | 2 | 2 | 0 |

JSON includes Wilson intervals, per-trial configurations and summaries, continuous-metric distributions and terminal feature counts. Flow-holding demand is diagnostic only: exceeding the force cap prevents instantaneous full cancellation, not necessarily forward navigation.
