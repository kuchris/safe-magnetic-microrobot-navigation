"""Run with python -m simulations.04_biplane_localization --help."""

import argparse
import json
from src.experiment import TrialConfig, run_trial, save_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--latency", type=float, default=0.05)
    parser.add_argument("--noise", type=float, default=1.0, help="detector noise sigma [px]")
    parser.add_argument("--dropout", type=float, default=0.0, help="pair dropout probability")
    parser.add_argument("--branch", choices=["upper", "lower"], default="upper")
    parser.add_argument("--output", default="outputs/04_biplane")
    args = parser.parse_args()
    result = run_trial(TrialConfig(seed=args.seed, latency_s=args.latency,
        noise_sigma_px=args.noise, dropout_probability=args.dropout, branch=args.branch))
    save_trial(result, args.output)
    print(json.dumps(result["summary"], indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
