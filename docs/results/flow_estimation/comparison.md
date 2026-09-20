# Command-aware estimation comparison

Both policies use early guidance and 0.5 s prediction. Only estimator mode differs.

| Field | Flow mm/s | Sigma mm/s | Branch | N | Kinematic success | Command-aware success | Rescued | Regressed |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| piecewise | 0.6 | 0 | upper | 5 | 5 | 5 | 0 | 0 |
| piecewise | 0.6 | 0 | lower | 5 | 5 | 5 | 0 | 0 |
| piecewise | 0.6 | 0.3 | upper | 5 | 3 | 3 | 0 | 0 |
| piecewise | 0.6 | 0.3 | lower | 5 | 4 | 2 | 0 | 2 |
| piecewise | 1.2 | 0 | upper | 5 | 5 | 5 | 0 | 0 |
| piecewise | 1.2 | 0 | lower | 5 | 5 | 5 | 0 | 0 |
| piecewise | 1.2 | 0.3 | upper | 5 | 1 | 2 | 1 | 0 |
| piecewise | 1.2 | 0.3 | lower | 5 | 3 | 3 | 0 | 0 |
| smooth | 0.6 | 0 | upper | 5 | 5 | 5 | 0 | 0 |
| smooth | 0.6 | 0 | lower | 5 | 5 | 5 | 0 | 0 |
| smooth | 0.6 | 0.3 | upper | 5 | 3 | 3 | 0 | 0 |
| smooth | 0.6 | 0.3 | lower | 5 | 4 | 3 | 0 | 1 |
| smooth | 1.2 | 0 | upper | 5 | 5 | 5 | 0 | 0 |
| smooth | 1.2 | 0 | lower | 5 | 5 | 5 | 0 | 0 |
| smooth | 1.2 | 0.3 | upper | 5 | 2 | 2 | 0 | 0 |
| smooth | 1.2 | 0.3 | lower | 5 | 3 | 3 | 0 | 0 |
