"""Run with python -m simulations.29_combined_perturbations --help.

Combined imperfections (latency, actuation gain, gravity direction, calibration,
detector noise, weaker gradient, dropout) at the 99% operating point, with the
open-loop gravity hold for both materials. Simulation only.
"""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

from src.benchmark import wilson_interval
from src.combined_study import ARMS, BUNDLES, MILD_TO_MODERATE, ablation_cells, cells, raise_cells, trial_record
from src.robustness_study import FRAME_RATES_HZ, OCCLUSIONS


def summarize(records):
    rows = []
    for bundle in BUNDLES:
        t = [r for r in records if r["bundle"] == bundle]
        s = sum(r["target_success"] for r in t)
        rows.append({
            "bundle": bundle, "trials": len(t), "success": s, "wilson_95": wilson_interval(s, len(t)),
            "by_arm_target": {f"{a}|{o}": sum(r["target_success"] for r in t if r["arm"] == a and r["occlusion"] == o)
                              for a in ARMS for o in OCCLUSIONS},
            "by_fps": {str(f): sum(r["target_success"] for r in t if r["frame_rate_hz"] == f) for f in FRAME_RATES_HZ},
            "outcomes": dict(Counter("success" if r["target_success"] else "wall" if r["wall_collision"]
                                     else "wrong" if r["wrong_branch"] else "timeout" for r in t)),
        })
    return rows


def render(rows):
    lines = ["# Experiment 29: combined perturbations at the 99% operating point", "",
             "Simulation only. Held-out seeds 3-5, both branches and targets, 7.5/15/30 fps. Both materials use the "
             "open-loop gravity hold and the matched gate.", "",
             "| Bundle | Success [95% CI] | Composite patent / occluded | NdFeB patent / occluded | "
             "7.5 / 15 / 30 fps (of 24) | Outcomes |", "|---|---|---|---|---|---|"]
    for r in rows:
        low, high = r["wilson_95"]
        a = r["by_arm_target"]
        f = r["by_fps"]
        lines.append(f"| {r['bundle']} | {r['success']}/{r['trials']} [{low * 100:.0f}, {high * 100:.0f}] | "
                     f"{a['C_P2|patent']} / {a['C_P2|target_occluded']} | {a['N_P2_hold|patent']} / "
                     f"{a['N_P2_hold|target_occluded']} | {f['7.5']} / {f['15.0']} / {f['30.0']} | "
                     f"{', '.join(f'{k} {v}' for k, v in sorted(r['outcomes'].items()))} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/29_combined_perturbations")
    parser.add_argument("--raise-only", action="store_true",
                        help="run only the exploratory mild-plus-one analysis (pure NdFeB)")
    parser.add_argument("--ablation-only", action="store_true",
                        help="run only the exploratory one-at-a-time ablation of the moderate bundle (pure NdFeB)")
    args = parser.parse_args()
    if args.raise_only:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(trial_record, raise_cells(), chunksize=2))
        rows = {f: {"success": sum(r["target_success"] for r in records if r["raised"] == f),
                    "trials": sum(1 for r in records if r["raised"] == f),
                    "by_fps": {str(x): sum(r["target_success"] for r in records if r["raised"] == f
                                           and r["frame_rate_hz"] == x) for x in FRAME_RATES_HZ}}
                for f in MILD_TO_MODERATE}
        path = Path(args.output) / "mild_plus_one"
        path.mkdir(parents=True, exist_ok=True)
        (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
        (path / "aggregates.json").write_text(json.dumps(rows, indent=1, allow_nan=False) + "\n")
        print(json.dumps(rows), file=sys.stderr, flush=True)
        return
    if args.ablation_only:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(trial_record, ablation_cells(), chunksize=2))
        rows = {w: {"success": sum(r["target_success"] for r in records if r["without"] == w),
                    "trials": sum(1 for r in records if r["without"] == w),
                    "by_fps": {str(f): sum(r["target_success"] for r in records if r["without"] == w
                                           and r["frame_rate_hz"] == f) for f in FRAME_RATES_HZ}}
                for w in BUNDLES["moderate"]}
        path = Path(args.output) / "ablation"
        path.mkdir(parents=True, exist_ok=True)
        (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
        (path / "aggregates.json").write_text(json.dumps(rows, indent=1, allow_nan=False) + "\n")
        print(json.dumps(rows), file=sys.stderr, flush=True)
        return
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(trial_record, cells(), chunksize=2))
    rows = summarize(records)
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps(rows, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render(rows))
    print(f"{len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
