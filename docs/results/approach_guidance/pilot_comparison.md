# Approach guidance comparison

Seeds: [0, 1, 2, 3, 4]. Original offset: 0 mm; guided offset: 0.4 mm.

Only waypoint geometry differs. Force limits, safety thresholds, physics and sensor settings are fixed.

| Scenario | Branch | Policy | Original success | Guided success | Rescued seeds | Regressed seeds | Sidewall proxy old/new | Outlet cap old/new |
|---|---|---|---:|---:|---|---|---|---|
| nominal | upper | passive | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| nominal | upper | ungated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| nominal | upper | gated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| nominal | lower | passive | 0/5 | 0/5 | [] | [] | 0/0 | 5/5 |
| nominal | lower | ungated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| nominal | lower | gated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| dropout_burst | upper | passive | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| dropout_burst | upper | ungated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| dropout_burst | upper | gated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| dropout_burst | lower | passive | 0/5 | 0/5 | [] | [] | 0/0 | 5/5 |
| dropout_burst | lower | ungated | 4/5 | 5/5 | [2] | [] | 1/0 | 0/0 |
| dropout_burst | lower | gated | 4/5 | 5/5 | [0] | [] | 0/0 | 1/0 |
| stale_imaging | upper | passive | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| stale_imaging | upper | ungated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| stale_imaging | upper | gated | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| stale_imaging | lower | passive | 0/5 | 0/5 | [] | [] | 0/0 | 5/5 |
| stale_imaging | lower | ungated | 4/5 | 5/5 | [0] | [] | 1/0 | 0/0 |
| stale_imaging | lower | gated | 0/5 | 0/5 | [] | [] | 0/0 | 5/5 |
| high_noise | upper | passive | 5/5 | 5/5 | [] | [] | 0/0 | 0/0 |
| high_noise | upper | ungated | 4/5 | 5/5 | [1] | [] | 1/0 | 0/0 |
| high_noise | upper | gated | 4/5 | 5/5 | [1] | [] | 0/0 | 1/0 |
| high_noise | lower | passive | 0/5 | 0/5 | [] | [] | 0/0 | 5/5 |
| high_noise | lower | ungated | 3/5 | 5/5 | [0, 4] | [] | 2/0 | 0/0 |
| high_noise | lower | gated | 3/5 | 5/5 | [0, 4] | [] | 0/0 | 2/0 |

Per-route reports include 95% Wilson intervals and metric distributions. Matched-seed changes are descriptive; no paired significance test or safety guarantee is claimed.
