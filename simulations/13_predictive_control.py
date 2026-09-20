"""Held-out matched comparison with the short-horizon correction off/on."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

from src.experiment import TrialConfig, run_trial
from src.flow_sensitivity import aggregate_records, trial_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("piecewise", "smooth"), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(15, 20)))
    parser.add_argument("--output", default="outputs/13_predictive_control")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    root = Path(args.output)
    traces = root / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    base = TrialConfig(duration_s=60, flow_model=args.model, flow_correlation_s=0.25,
                       approach_offset_m=0.4e-3)
    records, pairs = [], []
    for speed in (0.6e-3, 1.2e-3):
        for sigma in (0.0, 0.3e-3):
            for branch in ("upper", "lower"):
                for seed in args.seeds:
                    case_id = f"{args.model}_{speed * 1000:g}_{sigma * 1000:g}_{branch}_{seed}"
                    pair = []
                    for horizon in (0.0, 0.5):
                        config = replace(base, seed=seed, branch=branch, flow_speed_m_s=speed,
                                         flow_disturbance_m_s=sigma, prediction_horizon_s=horizon)
                        result = run_trial(config)
                        h = result["history"]
                        stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
                        assert np.all(h["force_n"][stopped] == 0)
                        assert result["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
                        record = trial_record(result)
                        evaluated = np.isfinite(h["predicted_selected_clearance_m"])
                        record["prediction_adjusted_fraction"] = float(h["prediction_adjusted"].mean())
                        record["prediction_evaluated_samples"] = int(evaluated.sum())
                        record["prediction_infeasible_fraction"] = float(np.mean(
                            h["predicted_selected_clearance_m"][evaluated] < config.safety_margin_m)) if evaluated.any() else None
                        record["trace_id"] = f"{case_id}_{horizon:g}"
                        np.savez_compressed(traces / f"{record['trace_id']}.npz", **h)
                        records.append(record)
                        pair.append(record)
                    before, after = [r["summary"]["target_success"] for r in pair]
                    pairs.append({"case_id": case_id, "baseline": pair[0]["trace_id"],
                                  "predictive": pair[1]["trace_id"],
                                  "change": "rescued" if after and not before else
                                            "regressed" if before and not after else "unchanged"})
                print(f"{args.model}: {len(records)}/{16 * len(args.seeds)} trials", flush=True)
    aggregates = {str(horizon): aggregate_records([r for r in records if r["config"]["prediction_horizon_s"] == horizon])
                  for horizon in (0.0, 0.5)}
    data = {"seeds": args.seeds, "trials": records, "pairs": pairs, "aggregates_by_horizon": aggregates}
    (root / f"{args.model}.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    print(f"Saved {args.model}: " + ", ".join(f"{label}={sum(p['change'] == label for p in pairs)}"
          for label in ("rescued", "regressed", "unchanged")), flush=True)


if __name__ == "__main__":
    main()
