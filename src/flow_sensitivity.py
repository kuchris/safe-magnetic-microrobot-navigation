"""Trial-level summaries for a fixed-grid flow sensitivity study."""

from collections import Counter, defaultdict

import numpy as np

from src.benchmark import wilson_interval
from src.failure_analysis import wall_feature
from src.particle import Particle
from src.vessel import YVessel


def trial_record(result):
    h, c, s = result["history"], result["config"], result["summary"]
    weights = np.diff(h["time_s"])
    gamma = Particle(0.1e-3, 3.5e-3).drag_coefficient
    demand = gamma * np.linalg.norm(h["flow_velocity_m_s"][:-1], axis=1)
    force = np.linalg.norm(h["force_n"][:-1], axis=1)
    return {"config": c, "summary": s,
            "timeout": not s["target_success"] and not s["wall_collision"],
            "terminal_wall_feature": wall_feature(h["true_position_m"][-1], YVessel()),
            "flow_holding_limit_exceeded_fraction": float(np.average(
                demand > c["max_force_n"], weights=weights)) if len(weights) else None,
            "force_saturation_fraction": float(np.average(
                (force > 0) & (force >= c["max_force_n"] * (1 - 1e-12)), weights=weights)) if len(weights) else None}


def aggregate_records(records):
    groups = defaultdict(list)
    for r in records:
        c = r["config"]
        groups[(c["flow_model"], c["flow_speed_m_s"], c["flow_disturbance_m_s"],
                c["branch"], c["approach_offset_m"])].append(r)
    rows = []
    for (model, speed, sigma, branch, offset), trials in groups.items():
        n = len(trials)
        outcomes = {}
        for key in ("target_success", "wrong_branch", "wall_collision", "timeout"):
            count = sum(r["timeout"] if key == "timeout" else r["summary"][key] for r in trials)
            outcomes[key] = {"count": count, "rate": count / n, "wilson_95": wilson_interval(count, n)}
        metrics = {}
        for key in ("minimum_wall_clearance_m", "safety_stop_rate", "navigation_time_s",
                    "flow_holding_limit_exceeded_fraction", "force_saturation_fraction"):
            values = [r["summary"][key] if key in r["summary"] else r[key] for r in trials]
            values = [v for v in values if v is not None]
            metrics[key] = {"n": len(values), "mean": float(np.mean(values)) if values else None,
                            "p05": float(np.quantile(values, 0.05)) if values else None,
                            "median": float(np.median(values)) if values else None,
                            "p95": float(np.quantile(values, 0.95)) if values else None}
        rows.append({"flow_model": model, "flow_speed_m_s": speed, "flow_disturbance_m_s": sigma,
                     "branch": branch, "approach_offset_m": offset, "trials": n,
                     "outcomes": outcomes, "metrics": metrics,
                     "terminal_features": dict(Counter(r["terminal_wall_feature"] for r in trials))})
    return rows
