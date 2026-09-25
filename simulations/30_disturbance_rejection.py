"""Run with python -m simulations.30_disturbance_rejection --help.

Estimated-drift feedforward and a faster residual filter against a biased gravity
hold, under experiment 29's nominal, mild and moderate bundles. Simulation only.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

from src.benchmark import wilson_interval
from src.disturbance_study import ARMS, BUNDLES, ESTIMATORS, cells, trial_record
from src.robustness_study import FRAME_RATES_HZ


def summarize(records):
    rows = []
    for estimator in ESTIMATORS:
        for bundle in BUNDLES:
            for arm in ARMS:
                t = [r for r in records if r["estimator"] == estimator and r["bundle"] == bundle and r["arm"] == arm]
                s = sum(r["target_success"] for r in t)
                rows.append({"estimator": estimator, "bundle": bundle, "arm": arm, "trials": len(t), "success": s,
                             "wilson_95": wilson_interval(s, len(t)),
                             "by_fps": {str(f): sum(r["target_success"] for r in t if r["frame_rate_hz"] == f)
                                        for f in FRAME_RATES_HZ},
                             "wall": sum(r["wall_collision"] for r in t), "wrong": sum(r["wrong_branch"] for r in t),
                             "timeout": sum(r["timeout"] for r in t)})
    return rows


def paired(records):
    key = ("bundle", "arm", "frame_rate_hz", "occlusion", "branch", "seed")
    base = {tuple(r[k] for k in key): r for r in records if r["estimator"] == "baseline"}
    out = {}
    for r in records:
        if r["estimator"] == "baseline":
            continue
        b = base[tuple(r[k] for k in key)]
        g = out.setdefault(f"{r['estimator']}|{r['bundle']}|{r['arm']}", {"kept": 0, "lost": 0, "gained": 0, "both_fail": 0})
        g[{(True, True): "kept", (True, False): "lost", (False, True): "gained",
           (False, False): "both_fail"}[(b["target_success"], r["target_success"])]] += 1
    return out


def render(rows, pairs):
    lines = ["# Experiment 30: disturbance rejection", "",
             "Simulation only. Held-out seeds 3-5, both branches and targets, 7.5/15/30 fps, 99% flow reduction, "
             "open-loop hold and matched gate for both materials.", "",
             "| Estimator | Bundle | Arm | Success [95% CI] | 7.5 / 15 / 30 fps | Wall | Wrong | Timeout | Kept / lost / gained vs baseline |",
             "|---|---|---|---|---|---:|---:|---:|---|"]
    for r in rows:
        low, high = r["wilson_95"]
        f = r["by_fps"]
        p = pairs.get(f"{r['estimator']}|{r['bundle']}|{r['arm']}")
        pair = "—" if p is None else f"{p['kept']} / {p['lost']} / {p['gained']}"
        lines.append(f"| {r['estimator']} | {r['bundle']} | {r['arm']} | {r['success']}/{r['trials']} "
                     f"[{low * 100:.0f}, {high * 100:.0f}] | {f['7.5']} / {f['15.0']} / {f['30.0']} | {r['wall']} | "
                     f"{r['wrong']} | {r['timeout']} | {pair} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/30_disturbance_rejection")
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(trial_record, cells(), chunksize=2))
    rows, pairs = summarize(records), paired(records)
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps({"rows": rows, "paired": pairs}, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render(rows, pairs))
    print(f"{len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
