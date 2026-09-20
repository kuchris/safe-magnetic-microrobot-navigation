"""Compare the original route with a fixed 0.4 mm pre-junction approach offset."""

import argparse
from collections import Counter
import json
from pathlib import Path

from src.benchmark import run_benchmark, save_benchmark
from src.experiment import TrialConfig


def trial_key(record):
    c = record["config"]
    return record["scenario"], c["branch"], c["control_mode"], c["seed"]


def compare_routes(baseline, guided):
    before = {trial_key(r): r for r in baseline["trials"]}
    after = {trial_key(r): r for r in guided["trials"]}
    if before.keys() != after.keys():
        raise ValueError("Route comparisons require matching scenarios, branches, policies and seeds")
    rows = []
    for group in baseline["aggregates"]:
        key = group["scenario"], group["branch"], group["control_mode"]
        pairs = [(before[k], after[k]) for k in before if k[:3] == key]
        row = {"scenario": key[0], "branch": key[1], "control_mode": key[2], "trials": len(pairs)}
        for index, name in enumerate(("baseline", "guided")):
            records = [pair[index] for pair in pairs]
            row[name] = {"successes": sum(r["summary"]["target_success"] for r in records),
                         "wrong_branches": sum(r["summary"]["wrong_branch"] for r in records),
                         "wall_proxy_violations": sum(r["summary"]["wall_collision"] for r in records),
                         "terminal_features": dict(Counter(r["terminal_wall_feature"] for r in records)),
                         "minimum_clearance_m": min(r["summary"]["minimum_wall_clearance_m"] for r in records),
                         "maximum_force_n": max(r["summary"]["maximum_force_n"] for r in records)}
        row["rescued_seeds"] = [a["config"]["seed"] for a, b in pairs
                                if not a["summary"]["target_success"] and b["summary"]["target_success"]]
        row["regressed_seeds"] = [a["config"]["seed"] for a, b in pairs
                                  if a["summary"]["target_success"] and not b["summary"]["target_success"]]
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(5)))
    parser.add_argument("--output", default="outputs/09_approach_guidance/pilot")
    args = parser.parse_args()
    path = Path(args.output)
    pilot = json.loads(Path("docs/results/benchmark_pilot.json").read_text())
    reference = {trial_key(r): r for r in pilot["trials"]}
    results = {}
    for name, offset in (("baseline", 0.0), ("guided", 0.4e-3)):
        def progress(done, total):
            if done % 12 == 0 or done == total:
                print(f"{name}: {done}/{total}", flush=True)

        result = run_benchmark(args.seeds, base_config=TrialConfig(approach_offset_m=offset), progress=progress)
        if name == "baseline":
            for record in result["trials"]:
                old = reference.get(trial_key(record))
                if old is not None and record["summary"] != old["summary"]:
                    raise RuntimeError("Baseline summary differs from original pilot")
        save_benchmark(result, path / name)
        results[name] = result
    rows = compare_routes(results["baseline"], results["guided"])
    (path / "comparison.json").write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
    lines = ["# Approach guidance comparison", "",
             f"Seeds: {args.seeds}. Original offset: 0 mm; guided offset: 0.4 mm.", "",
             "Only waypoint geometry differs. Force limits, safety thresholds, physics and sensor settings are fixed.", "",
             "| Scenario | Branch | Policy | Original success | Guided success | Rescued seeds | Regressed seeds | Sidewall proxy old/new | Outlet cap old/new |",
             "|---|---|---|---:|---:|---|---|---|---|"]
    for row in rows:
        a, b, n = row["baseline"], row["guided"], row["trials"]
        feature = lambda r, key: r["terminal_features"].get(key, 0)
        lines.append(f"| {row['scenario']} | {row['branch']} | {row['control_mode']} | "
                     f"{a['successes']}/{n} | {b['successes']}/{n} | {row['rescued_seeds']} | "
                     f"{row['regressed_seeds']} | {feature(a, 'capsule_sidewall_proxy')}/{feature(b, 'capsule_sidewall_proxy')} | "
                     f"{feature(a, 'closed_outlet_cap_proxy')}/{feature(b, 'closed_outlet_cap_proxy')} |")
    lines += ["", "Per-route reports include 95% Wilson intervals and metric distributions. "
              "Matched-seed changes are descriptive; no paired significance test or safety guarantee is claimed.", ""]
    (path / "comparison.md").write_text("\n".join(lines))
    print(f"Saved matched route comparison to {path}")


if __name__ == "__main__":
    main()
