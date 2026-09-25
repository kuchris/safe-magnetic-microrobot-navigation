"""Run with python -m simulations.24_feedforward_and_hold --help.

Model flow feedforward, a release-time gravity hold and a 50 ms wall-prediction
horizon on top of experiment 23's P2. Pilot seeds 0-2, held-out seeds 3-5, and
a +/-20% flow-model error on held-out seeds for the model-feedforward arms.
Simulation only.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np

from src.benchmark import wilson_interval
from src.delay_aware_study import aggregate
from src.feedforward_hold_study import (ARMS, FLOW_MODEL_ERRORS, FLOW_REDUCTIONS, HELDOUT_SEEDS, MODEL_FF_ARMS,
                                        OCCLUSIONS, PILOT_SEEDS, cells, paired_changes, trial_record)

POOLED = ("flow_model_error", "flow_reduction", "occlusion", "arm")
PER_FPS = ("flow_model_error", "flow_reduction", "frame_rate_hz", "occlusion", "arm")


def render(pooled, paired, title, seeds):
    lines = [f"# {title}", "", f"Simulation only. Seeds {', '.join(map(str, seeds))}; rates pool both branches "
             "and all frame rates; brackets are 95% Wilson intervals. Paired changes compare each arm with its "
             "material's baseline (C_P2 or N_P2_hold) on every other factor.", "",
             "| Flow error | Flow cut | Target | Arm | N | Success % [95% CI] | Wall % | Wrong % | Timeout % | "
             "Closest mm (median / min) |", "|---:|---:|---|---|---:|---|---:|---:|---:|---|"]
    for r in pooled:
        o = r["outcomes"]
        low, high = o["target_success"]["wilson_95"]
        lines.append(f"| {r['flow_model_error']:+g} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{r['trials']} | {o['target_success']['rate'] * 100:.0f} [{low * 100:.0f}, {high * 100:.0f}] | "
                     f"{o['wall_collision']['rate'] * 100:.0f} | {o['wrong_branch']['rate'] * 100:.0f} | "
                     f"{o['timeout']['rate'] * 100:.0f} | {r['closest_target_approach_m']['median'] * 1e3:.2f} / "
                     f"{r['closest_target_approach_m']['min'] * 1e3:.2f} |")
    lines += ["", "## Paired changes", "", "| Flow error | Flow cut | Target | Arm | Baseline | Rescued | Regressed | "
              "Both success | Both fail | Median closest change mm |", "|---:|---:|---|---|---|---:|---:|---:|---:|---:|"]
    for r in paired:
        lines.append(f"| {r['flow_model_error']:+g} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{r['baseline']} | {r['rescued']} | {r['regressed']} | {r['both_success']} | {r['both_fail']} | "
                     f"{r['median_closest_change_m'] * 1e3:+.2f} |")
    return "\n".join(lines) + "\n"


def plot(pooled, output_path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [(f, o) for f in FLOW_REDUCTIONS for o in OCCLUSIONS]
    grid = np.full((len(rows), len(ARMS)), np.nan)
    fig, ax = plt.subplots(figsize=(14, 4.8), layout="constrained")
    for r in pooled:
        i, j = rows.index((r["flow_reduction"], r["occlusion"])), list(ARMS).index(r["arm"])
        o = r["outcomes"]
        grid[i, j] = o["target_success"]["rate"]
        ax.text(j, i, f"{o['target_success']['count']}/{r['trials']}\nwall {o['wall_collision']['count']}\n"
                      f"{r['closest_target_approach_m']['median'] * 1e3:.2f} mm",
                ha="center", va="center", fontsize=8, color="black" if grid[i, j] >= 0.5 else "white")
    image = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(ARMS)), [a.replace("_", "\n", 1) for a in ARMS], fontsize=8)
    ax.set_yticks(range(len(rows)), [f"{f * 100:g}% cut, {o.replace('_', ' ')}" for f, o in rows])
    fig.colorbar(image, ax=ax, label="Target success rate")
    ax.set_title(f"{title}: successes / trials, wall contacts, median closest approach | simulation only",
                 fontsize=10)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stages", nargs="+", choices=("pilot", "heldout", "flow_error"),
                        default=["pilot", "heldout", "flow_error"])
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/24_feedforward_and_hold")
    args = parser.parse_args()
    root = Path(args.output)
    heldout_records = None
    for stage in args.stages:
        if stage == "flow_error":
            grid, seeds = cells(HELDOUT_SEEDS, FLOW_MODEL_ERRORS, MODEL_FF_ARMS), HELDOUT_SEEDS
        else:
            seeds = PILOT_SEEDS if stage == "pilot" else HELDOUT_SEEDS
            grid = cells(seeds)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(trial_record, grid, chunksize=2))
        if stage == "heldout":
            heldout_records = records
        baselines = None
        if stage == "flow_error":
            if heldout_records is None:
                heldout_records = json.loads((root / "heldout" / "trials.json").read_text())
            # Baselines never use the flow model, so their error-free held-out runs are the reference.
            baselines = [dict(r, flow_model_error=e) for r in heldout_records for e in FLOW_MODEL_ERRORS]
        pooled, per_fps = aggregate(records, POOLED), aggregate(records, PER_FPS)
        paired = paired_changes(records, baselines)
        path = root / stage
        path.mkdir(parents=True, exist_ok=True)
        (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
        (path / "aggregates.json").write_text(json.dumps(
            {"pooled": pooled, "per_frame_rate": per_fps, "paired": paired}, indent=1, allow_nan=False) + "\n")
        (path / "report.md").write_text(render(pooled, paired, f"Experiment 24 ({stage})", seeds))
        if stage != "flow_error":
            plot(pooled, path / "success.png", f"Experiment 24 ({stage})")
        print(f"{stage}: {len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
