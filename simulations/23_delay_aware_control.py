"""Run with python -m simulations.23_delay_aware_control --help.

Delay-aware control at physiological scale: pilot seeds 0-2, held-out seeds
3-5, and a +/-20% controller drag-model error on the held-out seeds.
Simulation only.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np

from src.delay_aware_study import (FLOW_REDUCTIONS, HELDOUT_SEEDS, MODEL_DRAG_ERRORS, OCCLUSIONS, PILOT_SEEDS,
                                   POLICIES, aggregate, cells, paired_changes, render_report, trial_record)

POOLED = ("model_drag_error", "flow_reduction", "occlusion", "policy")
STAGES = {
    "pilot": (PILOT_SEEDS, (0.0,)),
    "heldout": (HELDOUT_SEEDS, (0.0,)),
    "drag_error": (HELDOUT_SEEDS, MODEL_DRAG_ERRORS),
}


def plot(pooled, output_path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [(f, o) for f in FLOW_REDUCTIONS for o in OCCLUSIONS]
    grid = np.full((len(rows), len(POLICIES)), np.nan)
    fig, ax = plt.subplots(figsize=(14, 4.8), layout="constrained")
    for r in pooled:
        i, j = rows.index((r["flow_reduction"], r["occlusion"])), list(POLICIES).index(r["policy"])
        o = r["outcomes"]
        grid[i, j] = o["target_success"]["rate"]
        ax.text(j, i, f"{o['target_success']['count']}/{r['trials']}\n"
                      f"wall {o['wall_collision']['count']}\n"
                      f"{r['closest_target_approach_m']['median'] * 1e3:.2f} mm",
                ha="center", va="center", fontsize=8, color="black" if grid[i, j] >= 0.5 else "white")
    image = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(POLICIES)), [p.replace("_", "\n", 1) for p in POLICIES], fontsize=8)
    ax.set_yticks(range(len(rows)), [f"{f * 100:g}% cut, {o.replace('_', ' ')}" for f, o in rows])
    fig.colorbar(image, ax=ax, label="Target success rate")
    ax.set_title(f"{title}: successes / trials, wall contacts, median closest approach "
                 "(all frame rates, both branches) | simulation only", fontsize=10)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stages", nargs="+", choices=tuple(STAGES), default=list(STAGES))
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/23_delay_aware_control")
    args = parser.parse_args()
    root = Path(args.output)
    for stage in args.stages:
        seeds, errors = STAGES[stage]
        grid = cells(seeds, errors)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(trial_record, grid, chunksize=4))
        pooled, per_fps = aggregate(records, POOLED), aggregate(records)
        paired = paired_changes(records)
        path = root / stage
        path.mkdir(parents=True, exist_ok=True)
        (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
        (path / "aggregates.json").write_text(json.dumps(
            {"pooled": pooled, "per_frame_rate": per_fps, "paired": paired}, indent=1, allow_nan=False) + "\n")
        title = f"Experiment 23 ({stage})"
        (path / "report.md").write_text(render_report(pooled, paired, title, seeds))
        if stage != "drag_error":
            plot(pooled, path / "success.png", title)
        print(f"{stage}: {len(records)} trials -> {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
