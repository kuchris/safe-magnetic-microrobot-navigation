"""Run with python -m simulations.22_physiological_sweep --help.

Factorial sweep at physiological scale: flow reduction x frame rate x material x
target occlusion x control policy x branch x seed. Simulation only.
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np

from src.physiological_sweep import (FLOW_REDUCTIONS, FRAME_RATES_HZ, MATERIALS, POLICIES, aggregate,
                                     all_cells, render_report, run_sweep)


def plot_grid(rows, occlusion, output_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(MATERIALS), len(POLICIES), figsize=(15, 7), layout="constrained",
                             sharex=True, sharey=True)
    for i, material in enumerate(MATERIALS):
        for j, policy in enumerate(POLICIES):
            ax = axes[i, j]
            grid = np.full((len(FLOW_REDUCTIONS), len(FRAME_RATES_HZ)), np.nan)
            text = [["" for _ in FRAME_RATES_HZ] for _ in FLOW_REDUCTIONS]
            for r in rows:
                if (r["material"], r["policy"], r["occlusion"]) != (material, policy, occlusion):
                    continue
                a, b = FLOW_REDUCTIONS.index(r["flow_reduction"]), FRAME_RATES_HZ.index(r["frame_rate_hz"])
                grid[a, b] = r["outcomes"]["target_success"]["rate"]
                o = r["outcomes"]
                text[a][b] = (f"{o['target_success']['count']}/{r['trials']}\n"
                              f"{r['closest_target_approach_m']['median'] * 1e3:.2f} mm\n"
                              f"wall {o['wall_collision']['count']}")
            image = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
            for a in range(len(FLOW_REDUCTIONS)):
                for b in range(len(FRAME_RATES_HZ)):
                    ax.text(b, a, text[a][b], ha="center", va="center", fontsize=8,
                            color="white" if (np.isnan(grid[a, b]) or grid[a, b] < 0.5) else "black")
            ax.set_xticks(range(len(FRAME_RATES_HZ)), [f"{f:g}" for f in FRAME_RATES_HZ])
            ax.set_yticks(range(len(FLOW_REDUCTIONS)), [f"{f * 100:g}%" for f in FLOW_REDUCTIONS])
            ax.set_title(f"{material} | {policy}", fontsize=9)
            if i == len(MATERIALS) - 1:
                ax.set_xlabel("Frame rate [fps]")
            if j == 0:
                ax.set_ylabel("Proximal flow reduction")
    fig.colorbar(image, ax=axes, label="Target success rate", shrink=0.8)
    fig.suptitle(f"Experiment 22, target branch {occlusion.replace('_', ' ')}: successes / trials, "
                 "median closest approach, wall contacts | simulation only")
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--workers", type=int, default=None, help="process count (default: all cores)")
    parser.add_argument("--output", default="outputs/22_physiological_sweep")
    args = parser.parse_args()
    cells = all_cells(tuple(args.seeds))

    def progress(done, total):
        if done % 50 == 0 or done == total:
            print(f"{done}/{total} trials", file=sys.stderr, flush=True)

    records = run_sweep(cells, args.workers, progress)
    rows = aggregate(records)
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps(rows, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render_report(rows, args.seeds))
    for occlusion in ("patent", "target_occluded"):
        plot_grid(rows, occlusion, path / f"success_{occlusion}.png")
    print(f"{len(records)} trials -> {path}")


if __name__ == "__main__":
    main()
