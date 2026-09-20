"""Held-out paired terminal-guidance study for both estimator baselines."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import numpy as np

from src.experiment import TrialConfig, run_trial
from src.flow_sensitivity import aggregate_records, trial_record
from src.vessel import YVessel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("piecewise", "smooth"), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(25, 30)))
    parser.add_argument("--output", default="outputs/18_terminal_guidance")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    root = Path(args.output)
    traces = root / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    base = TrialConfig(duration_s=60, flow_model=args.model, flow_correlation_s=.25,
                       approach_offset_m=.4e-3, prediction_horizon_s=.5)
    records, pairs = [], []
    for mode in ("kinematic", "command_aware"):
        for speed in (.6e-3, 1.2e-3):
            for sigma in (0.0, .3e-3):
                for branch in ("upper", "lower"):
                    for seed in args.seeds:
                        case_id = f"{args.model}_{mode}_{speed * 1000:g}_{sigma * 1000:g}_{branch}_{seed}"
                        pair = []
                        for distance in (0.0, 2e-3):
                            config = replace(base, seed=seed, branch=branch, flow_speed_m_s=speed,
                                             flow_disturbance_m_s=sigma, estimator_mode=mode,
                                             terminal_guidance_distance_m=distance)
                            result = run_trial(config)
                            h = result["history"]
                            stopped = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
                            assert np.all(h["force_n"][stopped] == 0)
                            assert not h["terminal_active"][stopped].any()
                            assert result["summary"]["maximum_force_n"] <= config.max_force_n * (1 + 1e-12)
                            record = trial_record(result)
                            vessel = YVessel()
                            target = vessel.upper_target if branch == "upper" else vessel.lower_target
                            record["closest_target_distance_m"] = float(np.linalg.norm(h["true_position_m"] - target, axis=1).min())
                            record["terminal_active_fraction"] = float(h["terminal_active"].mean())
                            record["terminal_adjusted_fraction"] = float(h["terminal_adjusted"].mean())
                            record["variant"] = f"{mode}_{'off' if distance == 0 else 'on'}"
                            record["trace_id"] = f"{case_id}_{'off' if distance == 0 else 'on'}"
                            np.savez_compressed(traces / f"{record['trace_id']}.npz", **h)
                            records.append(record)
                            pair.append(record)
                        before, after = [r["summary"]["target_success"] for r in pair]
                        pairs.append({"case_id": case_id, "estimator_mode": mode, "baseline": pair[0]["trace_id"],
                                      "terminal": pair[1]["trace_id"], "change": "rescued" if after and not before else
                                      "regressed" if before and not after else "unchanged"})
                    print(f"{args.model}: {len(records)}/{32 * len(args.seeds)} trials", flush=True)
    variants = ("kinematic_off", "kinematic_on", "command_aware_off", "command_aware_on")
    data = {"seeds": args.seeds, "trials": records, "pairs": pairs,
            "aggregates_by_variant": {v: aggregate_records([r for r in records if r["variant"] == v]) for v in variants}}
    (root / f"{args.model}.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    for mode in ("kinematic", "command_aware"):
        selected = [p for p in pairs if p["estimator_mode"] == mode]
        print(f"Saved {args.model}/{mode}: " + ", ".join(f"{label}={sum(p['change'] == label for p in selected)}"
              for label in ("rescued", "regressed", "unchanged")), flush=True)


if __name__ == "__main__":
    main()
