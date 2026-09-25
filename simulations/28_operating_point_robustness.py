"""Run with python -m simulations.28_operating_point_robustness --help.

Robustness of the 99% operating point to latency, dropout, actuation gain error,
weaker gradients, a wrong gravity direction, calibration and detector noise; and
a check of the stale-measurement gate at 90% reduction. Simulation only.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np

from src.benchmark import wilson_interval
from src.robustness_study import (ARMS, CONDITIONS, FRAME_RATES_HZ, FOLLOWUP, GATE_CHECK_ARMS, OCCLUSIONS, cells,
                                  followup_cells, trial_record)


def table(records, stage, conditions, arms):
    rows = []
    for condition in conditions:
        for arm in arms:
            for occlusion in OCCLUSIONS:
                for fps in (*FRAME_RATES_HZ, None):
                    t = [r for r in records if r["stage"] == stage and r["condition"] == condition and r["arm"] == arm
                         and r["occlusion"] == occlusion and (fps is None or r["frame_rate_hz"] == fps)]
                    s = sum(r["target_success"] for r in t)
                    rows.append({"condition": condition, "arm": arm, "occlusion": occlusion, "frame_rate_hz": fps,
                                 "trials": len(t), "success": s, "wilson_95": wilson_interval(s, len(t)),
                                 "wall": sum(r["wall_collision"] for r in t),
                                 "wrong": sum(r["wrong_branch"] for r in t), "timeout": sum(r["timeout"] for r in t),
                                 "median_elapsed_s": float(np.median([r["elapsed_time_s"] for r in t]))})
    return rows


def paired(records, stage, reference, conditions):
    key = ("arm", "frame_rate_hz", "occlusion", "branch", "seed")
    base = {tuple(r[k] for k in key): r for r in records if r["stage"] == stage and r["condition"] == reference}
    out = defaultdict(lambda: {"kept": 0, "lost": 0, "gained": 0, "both_fail": 0})
    for r in records:
        if r["stage"] != stage or r["condition"] == reference or r["condition"] not in conditions:
            continue
        b = base[tuple(r[k] for k in key)]
        out[r["condition"]][{(True, True): "kept", (True, False): "lost", (False, True): "gained",
                             (False, False): "both_fail"}[(b["target_success"], r["target_success"])]] += 1
    return dict(out)


def render(robust, gate, robust_pairs, gate_rows, gate_pairs):
    lines = ["# Experiment 28: operating-point robustness and gate check", "",
             "Simulation only. Held-out seeds 3-5 and both branches. Robustness runs at 99% flow reduction;",
             "the gate check at 90%. 'All' pools the three frame rates.", "",
             "## Robustness at 99% (successes / trials, all frame rates)", "",
             "| Condition | Arm | Target | Success [95% CI] | Wall | Wrong | Timeout | Median time s |",
             "|---|---|---|---|---:|---:|---:|---:|"]
    for r in robust:
        if r["frame_rate_hz"] is None:
            low, high = r["wilson_95"]
            lines.append(f"| {r['condition']} | {r['arm']} | {r['occlusion']} | {r['success']}/{r['trials']} "
                         f"[{low * 100:.0f}, {high * 100:.0f}] | {r['wall']} | {r['wrong']} | {r['timeout']} | "
                         f"{r['median_elapsed_s']:.2f} |")
    lines += ["", "Paired against the matched-gate nominal (kept / lost / gained / both fail):", ""]
    for condition, p in robust_pairs.items():
        lines.append(f"- {condition}: {p['kept']} / {p['lost']} / {p['gained']} / {p['both_fail']}")
    lines += ["", "## Gate check at 90% (model feedforward arms)", "",
              "| Gate | Arm | Target | fps | Success | Wall | Wrong |", "|---|---|---|---:|---:|---:|---:|"]
    for r in gate_rows:
        fps = "all" if r["frame_rate_hz"] is None else f"{r['frame_rate_hz']:g}"
        lines.append(f"| {r['condition']} | {r['arm']} | {r['occlusion']} | {fps} | {r['success']}/{r['trials']} | "
                     f"{r['wall']} | {r['wrong']} |")
    lines += ["", "Matched gate paired against the fixed gate (kept / lost / gained / both fail):", ""]
    for condition, p in gate_pairs.items():
        lines.append(f"- {condition}: {p['kept']} / {p['lost']} / {p['gained']} / {p['both_fail']}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/28_operating_point_robustness")
    parser.add_argument("--followup-only", action="store_true",
                        help="run only the exploratory open-loop-hold follow-up (written to <output>/followup)")
    args = parser.parse_args()
    if args.followup_only:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(trial_record, followup_cells(), chunksize=2))
        rows = table(records, "followup", FOLLOWUP, ("C_P2",))
        path = Path(args.output) / "followup"
        path.mkdir(parents=True, exist_ok=True)
        (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
        (path / "aggregates.json").write_text(json.dumps(rows, indent=1, allow_nan=False) + "\n")
        print(f"{len(records)} follow-up trials -> {path}", file=sys.stderr, flush=True)
        return
    grid = cells()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(trial_record, grid, chunksize=2))
    robust = table(records, "robustness", CONDITIONS, ARMS)
    gate_rows = table(records, "gate_check", ("fixed_gate", "matched_gate"), GATE_CHECK_ARMS)
    robust_pairs = paired(records, "robustness", "nominal", CONDITIONS)
    gate_pairs = paired(records, "gate_check", "fixed_gate", ("matched_gate",))
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps(
        {"robustness": robust, "gate_check": gate_rows, "robustness_paired": robust_pairs,
         "gate_paired": gate_pairs}, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render(robust, None, robust_pairs, gate_rows, gate_pairs))
    print(f"{len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
