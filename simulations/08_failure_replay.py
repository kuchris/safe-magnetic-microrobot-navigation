"""Replay selected benchmark seeds and export event evidence, plots and a GIF."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

from src.experiment import TrialConfig, run_trial
from src.failure_analysis import analyze_trial
from src.replay_plotting import animate_pair, plot_pair


PAIRS = (("dropout_burst", 0), ("dropout_burst", 2), ("high_noise", 0), ("stale_imaging", 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="docs/results/benchmark_pilot.json")
    parser.add_argument("--output", default="outputs/08_failure_analysis")
    args = parser.parse_args()
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    pilot = json.loads(Path(args.input).read_text())
    selected = {("nominal", "lower", 0, "gated"), *[
        (scenario, "lower", seed, mode) for scenario, seed in PAIRS for mode in ("ungated", "gated")]}
    cases, evidence = {}, {}
    for trial in pilot["trials"]:
        c = trial["config"]
        key = (trial["scenario"], c["branch"], c["seed"], c["control_mode"])
        if key not in selected:
            continue
        result = run_trial(TrialConfig(**c))
        if result["summary"] != trial["summary"]:
            raise RuntimeError(f"Replay differs from recorded benchmark: {key}")
        name = "_".join(map(str, key))
        trial_path = path / name
        trial_path.mkdir(exist_ok=True)
        np.savez_compressed(trial_path / "history.npz", **result["history"])
        (trial_path / "summary.json").write_text(json.dumps(
            {"config": result["config"], "summary": result["summary"]}, indent=2, allow_nan=False) + "\n")
        cases[key] = result
        evidence[name] = {"config": result["config"], "analysis": analyze_trial(result)}
        print(f"Reproduced {name}", flush=True)
    if set(cases) != selected:
        raise ValueError("Input benchmark does not contain all selected replay cases")
    (path / "analysis.json").write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    lines = ["# Selected replay events", "",
             "All nine replay summaries exactly match the saved pilot. Times are sampled at 5 ms. "
             "Wall labels identify capsule proxy features, not exact anatomical contact.", "",
             "| Case | Success | Junction s | True y at junction (um) | Wrong branch s | Terminal s | Terminal feature |",
             "|---|---|---:|---:|---:|---:|---|"]
    for name, record in evidence.items():
        a = record["analysis"]
        j, w = a["junction_crossing"], a["wrong_branch_confirmed"]
        wrong_time = f"{w['time_s']:.3f}" if w else "N/A"
        lines.append(f"| {name} | {a['target_success']} | {j['time_s']:.3f} | "
                     f"{j['position_m'][1] * 1e6:.3f} | {wrong_time} | "
                     f"{a['elapsed_time_s']:.3f} | {a['terminal_wall_feature']} |")
    (path / "events.md").write_text("\n".join(lines) + "\n")
    # Control also runs every physics tick: this varies both resolutions.
    sensitivity = []
    for seed, mode in ((0, "gated"), (2, "ungated")):
        base = cases[("dropout_burst", "lower", seed, mode)]
        for dt in (0.005, 0.0025, 0.001):
            result = base if dt == 0.005 else run_trial(replace(TrialConfig(**base["config"]), dt_s=dt))
            sensitivity.append({"seed": seed, "control_mode": mode, "dt_s": dt,
                                "summary": result["summary"], "analysis": analyze_trial(result)})
            print(f"Resolution check: seed {seed}, {mode}, dt={dt}", flush=True)
    (path / "resolution_sensitivity.json").write_text(json.dumps(sensitivity, indent=2, allow_nan=False) + "\n")
    labels = ("Without safety gate", "With safety gate")
    for scenario, seed in PAIRS:
        pair = [cases[(scenario, "lower", seed, mode)] for mode in ("ungated", "gated")]
        plot_pair(pair, labels, path / f"{scenario}_seed_{seed}.png",
                  f"{scenario.replace('_', ' ').title()} | lower target | seed {seed}")
    pair = [cases[("dropout_burst", "lower", 0, mode)] for mode in ("ungated", "gated")]
    print("Rendering paired replay animation", flush=True)
    animate_pair(pair, labels, path / "dropout_seed_0.gif")
    print(f"Saved replay evidence, four diagnostic figures and animation to {path}")


if __name__ == "__main__":
    main()
