"""Run with python -m simulations.26_measured_flow_map --help.

Model feedforward with a measured (voxelized, noisy) flow map instead of the
analytic flow model, for experiment 24's feedforward arms on held-out seeds.
Simulation only.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np

from src.delay_aware_study import aggregate
from src.flow_map_study import ARMS, CONDITIONS, OCCLUSIONS, WORST, cells, route_velocity_error, trial_record
from src.flow_model_error_study import paired_against_exact

POOLED = ("condition", "flow_reduction", "occlusion", "arm")


def plot(pooled, errors, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    columns = [(a, o) for a in ARMS for o in OCCLUSIONS]
    grid = np.full((len(CONDITIONS), len(columns)), np.nan)
    fig, ax = plt.subplots(figsize=(10, 5.2), layout="constrained")
    for r in pooled:
        if r["flow_reduction"] != 0.9:
            continue
        i, j = list(CONDITIONS).index(r["condition"]), columns.index((r["arm"], r["occlusion"]))
        o = r["outcomes"]
        grid[i, j] = o["target_success"]["rate"]
        ax.text(j, i, f"{o['target_success']['count']}/{r['trials']}", ha="center", va="center", fontsize=9,
                color="black" if grid[i, j] >= 0.5 else "white")
    image = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(columns)), [f"{a}\n{o.replace('_', ' ')}" for a, o in columns], fontsize=8)
    ax.set_yticks(range(len(CONDITIONS)), [f"{c}  ({errors[(c, 0.9, 'patent')] * 1e3:.1f} mm/s)" for c in CONDITIONS])
    fig.colorbar(image, ax=ax, label="Target success rate")
    ax.set_title("Experiment 26, 90% flow reduction, held-out seeds: successes / trials\n"
                 "(route-averaged map error on patent routes) | simulation only", fontsize=10)
    fig.savefig(path / "success_90.png", dpi=150)
    plt.close(fig)


def render(pooled, paired, errors):
    lines = ["# Experiment 26: measured flow map", "",
             "Simulation only. Held-out seeds 3-5, both branches, all frame rates pooled. The controller's flow "
             "model is the plant's time-mean field on a voxel grid with per-voxel noise; route error is the mean "
             "|u_map - u_plant| along both routes over one cardiac period (noise realization of seed 3).", "",
             "| Condition | Flow cut | Target | Arm | Route error mm/s | Success [95% CI] | Wall | Wrong |",
             "|---|---:|---|---|---:|---|---:|---:|"]
    for r in pooled:
        o = r["outcomes"]
        low, high = o["target_success"]["wilson_95"]
        lines.append(f"| {r['condition']} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{errors[(r['condition'], r['flow_reduction'], r['occlusion'])] * 1e3:.1f} | "
                     f"{o['target_success']['count']}/{r['trials']} [{low * 100:.0f}, {high * 100:.0f}] | "
                     f"{o['wall_collision']['count']} | {o['wrong_branch']['count']} |")
    lines += ["", "## Paired against the exact analytic model", "",
              "| Condition | Flow cut | Target | Arm | Kept | Lost | Gained | Both fail |", "|---|---:|---|---|---:|---:|---:|---:|"]
    for r in paired:
        lines.append(f"| {r['condition']} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{r['kept']} | {r['lost']} | {r['gained']} | {r['both_fail']} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/26_measured_flow_map")
    args = parser.parse_args()
    grid = cells()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(trial_record, grid, chunksize=2))
    errors = {(c, f, o): route_velocity_error(c, f, o) for c in CONDITIONS for f in (0.9, 0.99)
              for o in OCCLUSIONS if f == 0.9 or c in ("exact", WORST)}
    pooled, paired = aggregate(records, POOLED), paired_against_exact(records)
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps(
        {"pooled": pooled, "paired": paired,
         "route_error_m_s": [{"condition": c, "flow_reduction": f, "occlusion": o, "error": e}
                             for (c, f, o), e in errors.items()]}, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render(pooled, paired, errors))
    plot(pooled, errors, path)
    print(f"{len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
