"""Paired-seed benchmark of toy navigation policies, with per-trial statistics."""

from collections import defaultdict
from dataclasses import replace
import csv
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np

from src.experiment import TrialConfig, run_trial
from src.failure_analysis import wall_feature
from src.vessel import YVessel


MODES = ("passive", "ungated", "gated")
SCENARIOS = {
    "nominal": {},
    "dropout_burst": {"dropout_intervals": ((8.0, 8.75),)},
    "stale_imaging": {"latency_s": 0.25},
    "high_noise": {"noise_sigma_px": 12.0},
}
OUTCOMES = ("target_success", "wall_collision", "wrong_branch")
METRICS = ("minimum_wall_clearance_m", "navigation_time_s", "localization_RMSE_m",
           "safety_stop_rate", "position_3sigma_coverage", "localization_availability")


def wilson_interval(successes, trials):
    """Two-sided 95% Wilson score interval for independent Bernoulli trials."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("counts must satisfy 0 <= successes <= trials and trials > 0")
    z = NormalDist().inv_cdf(0.975)
    p = successes / trials
    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    radius = z * np.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator
    return [max(0.0, float(center - radius)), min(1.0, float(center + radius))]


def aggregate_trials(records):
    groups = defaultdict(list)
    for record in records:
        groups[(record["scenario"], record["config"]["branch"],
                record["config"]["control_mode"])].append(record["summary"])
    aggregates = []
    for (scenario, branch, mode), summaries in groups.items():
        n = len(summaries)
        outcomes = {}
        for key in OUTCOMES:
            count = sum(s[key] for s in summaries)
            outcomes[key] = {"count": count, "rate": count / n,
                             "wilson_95": wilson_interval(count, n)}
        metrics = {}
        for key in METRICS:
            values = [s[key] for s in summaries if s[key] is not None]
            metrics[key] = {"n": len(values), "mean": float(np.mean(values)) if values else None,
                            "p05": float(np.quantile(values, 0.05)) if values else None,
                            "median": float(np.median(values)) if values else None,
                            "p95": float(np.quantile(values, 0.95)) if values else None}
        aggregates.append({"scenario": scenario, "branch": branch, "control_mode": mode,
                           "trials": n, "outcomes": outcomes, "metrics": metrics})
    return aggregates


def run_benchmark(seeds=range(10), scenarios=tuple(SCENARIOS), base_config=TrialConfig(),
                  progress=None):
    seeds, scenarios = tuple(seeds), tuple(scenarios)
    if not seeds or len(set(seeds)) != len(seeds) or any(
            not isinstance(seed, int) or seed < 0 for seed in seeds):
        raise ValueError("seeds must be distinct nonnegative integers")
    if not scenarios or len(set(scenarios)) != len(scenarios) or any(
            name not in SCENARIOS for name in scenarios):
        raise ValueError("scenarios must be distinct known scenario names")
    records = []
    total = len(seeds) * len(scenarios) * 2 * len(MODES)
    for scenario in scenarios:
        for branch in ("upper", "lower"):
            for seed in seeds:
                for mode in MODES:
                    config = replace(base_config, **SCENARIOS[scenario], seed=seed,
                                     branch=branch, control_mode=mode)
                    result = run_trial(config)
                    records.append({"scenario": scenario, "config": result["config"],
                                    "summary": result["summary"],
                                    "terminal_wall_feature": wall_feature(
                                        result["history"]["true_position_m"][-1], YVessel(),
                                        result["config"]["particle_radius_m"])})
                    if progress is not None:
                        progress(len(records), total)
    return {"seeds": seeds, "scenarios": scenarios, "trials": records,
            "aggregates": aggregate_trials(records)}


def render_report(result):
    lines = ["# Toy navigation benchmark", "",
             f"Seeds: {', '.join(map(str, result['seeds']))}. Trials: {len(result['trials'])}.", "",
             "Policies share seeds, sensor settings, estimator, waypoints and force limits. "
             "Passive always applies zero force. Ungated requires an initial estimate, then "
             "continues steering despite stale/lost observations or low robust clearance. "
             "Gated uses the existing uncertainty, freshness and clearance supervisor.", "",
             "Rates below are per trial. Brackets show two-sided 95% Wilson score intervals "
             "across seeds within each scenario, branch and policy. These are marginal "
             "intervals, not simultaneous bounds or tests of paired policy differences. "
             "Small seed counts produce wide intervals even with no observed failures.", "",
             "| Scenario | Branch | Policy | N | Success % [95% CI] | Wall proxy violation % [95% CI] | Wrong branch % [95% CI] |",
             "|---|---|---|---:|---|---|---|"]
    for group in result["aggregates"]:
        cells = []
        for key in OUTCOMES:
            outcome = group["outcomes"][key]
            low, high = outcome["wilson_95"]
            cells.append(f"{outcome['rate'] * 100:.1f} [{low * 100:.1f}, {high * 100:.1f}]")
        lines.append(f"| {group['scenario']} | {group['branch']} | {group['control_mode']} | "
                     f"{group['trials']} | " + " | ".join(cells) + " |")
    lines += ["", "## Per-trial metric distributions", "",
              "Values are medians [5th, 95th percentiles] across trials, not confidence intervals. "
              "Arrival time includes successful trials only. Missing estimates are excluded from "
              "RMSE and coverage; availability includes all control samples. JSON includes the "
              "valid trial count for each metric. Trials receive equal weight.", "",
              "| Scenario / branch / policy | Min clearance mm | Arrival s | RMSE mm | Inhibited samples % | 3-sigma coverage % | Estimate availability % |",
              "|---|---|---|---|---|---|---|"]
    for group in result["aggregates"]:
        cells = []
        for key, scale in zip(METRICS, (1000, 1, 1000, 100, 100, 100)):
            metric = group["metrics"][key]
            cells.append("N/A" if metric["n"] == 0 else
                         f"{metric['median'] * scale:.3f} "
                         f"[{metric['p05'] * scale:.3f}, {metric['p95'] * scale:.3f}]")
        lines.append(f"| {group['scenario']} / {group['branch']} / {group['control_mode']} | "
                     + " | ".join(cells) + " |")
    lines += ["", "## Interpretation and limits", "",
              "- Passive upper-branch arrival can be caused entirely by flow. Inspect both branches.",
              "- Zero force does not immobilize the particle. With default parameters, cancelling "
              "0.6 mm/s flow requires approximately 3.96 nN, above the 3 nN force cap.",
              "- Wall violations use the sampled capsule-clearance proxy. Closed rounded outlets "
              "can register as violations; no swept collision or anatomical outlet model is used.",
              "- Coverage is the fraction of localized samples whose Euclidean position error is "
              "at most three times the largest-axis position sigma. This is a descriptive ball "
              "coverage metric, not a calibrated 3D confidence level or collision-risk bound. "
              "Time samples are correlated; no sample-level binomial interval is reported.",
              "- Inhibited samples include startup without an estimate and gate-triggered stops. "
              "Passive force is zero by design and is not counted as a gate-triggered stop.",
              "- Seeds are paired between policies. Random draws are shared while observation "
              "positions and termination times can differ. Results are conditional on these toy "
              "settings; variation across anatomy, physics, or real data is not measured.", ""]
    return "\n".join(lines)


def save_benchmark(result, output_dir):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "benchmark.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (path / "report.md").write_text(render_report(result))
    fields = ["scenario", "branch", "control_mode", "seed", *OUTCOMES, *METRICS]
    with (path / "trials.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in result["trials"]:
            writer.writerow({"scenario": record["scenario"],
                             "branch": record["config"]["branch"],
                             "control_mode": record["config"]["control_mode"],
                             **{key: record["summary"][key] for key in fields[3:]}})
