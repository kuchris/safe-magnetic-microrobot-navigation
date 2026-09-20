"""Compare passive, ungated and gated navigation across paired seeds and branches."""

import argparse

from src.benchmark import SCENARIOS, run_benchmark, save_benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=list(SCENARIOS))
    parser.add_argument("--output", default="outputs/06_benchmark")
    args = parser.parse_args()

    def progress(done, total):
        if done % 6 == 0 or done == total:
            print(f"Completed {done}/{total} trials", flush=True)

    result = run_benchmark(args.seeds, args.scenarios, progress=progress)
    save_benchmark(result, args.output)
    print(f"Saved benchmark.json, trials.csv and report.md to {args.output}")


if __name__ == "__main__":
    main()
