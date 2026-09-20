"""Fixed-grid comparison of original and guided routes under flow uncertainty."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

from src.experiment import TrialConfig, run_trial
from src.flow_sensitivity import aggregate_records, trial_record


SPEEDS_M_S = (0.3e-3, 0.6e-3, 1.2e-3)
DISTURBANCES_M_S = (0.0, 0.1e-3, 0.3e-3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("piecewise", "smooth"), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(10, 15)))
    parser.add_argument("--output", default="outputs/11_flow_sensitivity")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    base = TrialConfig(duration_s=60, flow_model=args.model, flow_correlation_s=0.25)
    records = []
    total = len(SPEEDS_M_S) * len(DISTURBANCES_M_S) * 2 * 2 * len(args.seeds)
    for speed in SPEEDS_M_S:
        for sigma in DISTURBANCES_M_S:
            for branch in ("upper", "lower"):
                for seed in args.seeds:
                    for offset in (0.0, 0.4e-3):
                        config = replace(base, seed=seed, branch=branch, flow_speed_m_s=speed,
                                         flow_disturbance_m_s=sigma, approach_offset_m=offset)
                        result = run_trial(config)
                        records.append(trial_record(result))
                print(f"{args.model}: {len(records)}/{total} trials", flush=True)
    data = {"seeds": args.seeds, "speeds_m_s": SPEEDS_M_S, "disturbances_m_s": DISTURBANCES_M_S,
            "trials": records, "aggregates": aggregate_records(records)}
    (path / f"{args.model}.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    lines = [f"# Flow sensitivity: {args.model}", "",
             "Gated control, 60 s horizon, 0.25 s disturbance correlation time. Counts are per trial.", "",
             "| Flow mm/s | Disturbance sigma mm/s | Branch | Offset mm | N | Success | Wrong branch | Wall proxy | Timeout |",
             "|---:|---:|---|---:|---:|---:|---:|---:|---:|"]
    for row in data["aggregates"]:
        counts = [str(row["outcomes"][k]["count"]) for k in ("target_success", "wrong_branch", "wall_collision", "timeout")]
        lines.append(f"| {row['flow_speed_m_s'] * 1000:g} | {row['flow_disturbance_m_s'] * 1000:g} | "
                     f"{row['branch']} | {row['approach_offset_m'] * 1000:g} | {row['trials']} | "
                     + " | ".join(counts) + " |")
    lines += ["", "JSON includes Wilson intervals, per-trial configurations and summaries, continuous-metric "
              "distributions and terminal feature counts. Flow-holding demand is diagnostic only: exceeding "
              "the force cap prevents instantaneous full cancellation, not necessarily forward navigation.", ""]
    (path / f"{args.model}.md").write_text("\n".join(lines))
    print(f"Saved {args.model} sensitivity results to {path}")


if __name__ == "__main__":
    main()
