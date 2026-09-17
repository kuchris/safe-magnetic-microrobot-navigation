"""Deterministic stress scenarios; not a Monte Carlo study."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
from src.experiment import TrialConfig, run_trial, save_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/05_latency")
    args = parser.parse_args()
    base = TrialConfig()
    scenarios = {
        "nominal": base,
        "dropout_burst": replace(base, dropout_intervals=((8.0, 8.75),)),
        "stale_imaging": replace(base, latency_s=0.25),
        "stale_lower_target": replace(base, latency_s=0.25, branch="lower"),
        "high_noise": replace(base, noise_sigma_px=12.0),
    }
    summaries = {}
    for name, config in scenarios.items():
        result = run_trial(config)
        save_trial(result, Path(args.output) / name)
        summaries[name] = result["summary"]
    text = json.dumps(summaries, indent=2, allow_nan=False)
    (Path(args.output) / "comparison.json").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
