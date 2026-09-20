"""Held-out closed-loop comparison of kinematic and command-aware estimation."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import numpy as np

from src.experiment import TrialConfig, run_trial
from src.flow_sensitivity import aggregate_records, trial_record
from src.prediction_audit import forecast_metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("piecewise", "smooth"), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(20, 25)))
    parser.add_argument("--output", default="outputs/16_flow_estimator_comparison")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    root = Path(args.output)
    traces = root / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    base = TrialConfig(duration_s=60, flow_model=args.model, flow_correlation_s=0.25,
                       approach_offset_m=0.4e-3, prediction_horizon_s=0.5)
    records, pairs = [], []
    for speed in (0.6e-3, 1.2e-3):
        for sigma in (0.0, 0.3e-3):
            for branch in ("upper", "lower"):
                for seed in args.seeds:
                    case_id = f"{args.model}_{speed * 1000:g}_{sigma * 1000:g}_{branch}_{seed}"
                    pair = []
                    for mode in ("kinematic", "command_aware"):
                        config = replace(base, seed=seed, branch=branch, flow_speed_m_s=speed,
                                         flow_disturbance_m_s=sigma, estimator_mode=mode)
                        result = run_trial(config)
                        h = result["history"]
                        stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
                        assert np.all(h["force_n"][stopped] == 0)
                        assert result["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
                        record = trial_record(result)
                        record["forecast_metrics"] = forecast_metrics(h, 6 * np.pi * 3.5e-3 * 0.1e-3)
                        record["prediction_adjusted_fraction"] = float(h["prediction_adjusted"].mean())
                        record["trace_id"] = f"{case_id}_{mode}"
                        np.savez_compressed(traces / f"{record['trace_id']}.npz", **h)
                        records.append(record)
                        pair.append(record)
                    before, after = [r["summary"]["target_success"] for r in pair]
                    pairs.append({"case_id": case_id, "baseline": pair[0]["trace_id"],
                                  "command_aware": pair[1]["trace_id"],
                                  "change": "rescued" if after and not before else
                                            "regressed" if before and not after else "unchanged"})
                print(f"{args.model}: {len(records)}/{16 * len(args.seeds)} trials", flush=True)
    aggregates = {mode: aggregate_records([r for r in records if r["config"]["estimator_mode"] == mode])
                  for mode in ("kinematic", "command_aware")}
    data = {"seeds": args.seeds, "trials": records, "pairs": pairs, "aggregates_by_estimator": aggregates}
    (root / f"{args.model}.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    print(f"Saved {args.model}: " + ", ".join(f"{label}={sum(p['change'] == label for p in pairs)}"
          for label in ("rescued", "regressed", "unchanged")), flush=True)


if __name__ == "__main__":
    main()
