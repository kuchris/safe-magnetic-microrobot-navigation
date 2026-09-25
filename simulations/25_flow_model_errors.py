"""Run with python -m simulations.25_flow_model_errors --help.

Controller flow-model errors (scale, phase, pulsation, profile, junction) for
experiment 24's model-feedforward arms, on held-out seeds 3-5. The plant never
changes. Simulation only.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np

from src.benchmark import wilson_interval
from src.delay_aware_study import aggregate
from src.flow_model_error_study import (ARMS, CONDITIONS, ERROR_TYPE, FLOW_REDUCTIONS, OCCLUSIONS, cells,
                                        paired_against_exact, route_velocity_error, trial_record)

POOLED = ("condition", "flow_reduction", "occlusion", "arm")
TYPE_COLOR = {"exact": "#16202A", "scale": "#2F5BD3", "phase": "#C2410C", "pulsation": "#7A4FBF",
              "profile": "#1B8A5A", "junction": "#8A6D1B"}


def plots(pooled, errors, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Success at 90% reduction: conditions x (arm, target).
    columns = [(a, o) for a in ARMS for o in OCCLUSIONS]
    grid = np.full((len(CONDITIONS), len(columns)), np.nan)
    fig, ax = plt.subplots(figsize=(10, 7), layout="constrained")
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
    ax.set_yticks(range(len(CONDITIONS)), [f"{c}  ({errors[(c, 0.9, 'patent')] * 1e3:.1f} mm/s)"
                                          for c in CONDITIONS])
    fig.colorbar(image, ax=ax, label="Target success rate")
    ax.set_title("Experiment 25, 90% flow reduction, held-out seeds: successes / trials\n"
                 "(route-averaged model velocity error on patent routes) | simulation only", fontsize=10)
    fig.savefig(path / "success_90.png", dpi=150)
    plt.close(fig)

    # Success vs route-averaged model error at 90% (both arms pooled, all frame rates).
    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    for occlusion, marker in (("patent", "o"), ("target_occluded", "s")):
        for condition in CONDITIONS:
            rows = [r for r in pooled if r["flow_reduction"] == 0.9 and r["occlusion"] == occlusion
                    and r["condition"] == condition]
            n = sum(r["trials"] for r in rows)
            s = sum(r["outcomes"]["target_success"]["count"] for r in rows)
            low, high = wilson_interval(s, n)
            x = errors[(condition, 0.9, occlusion)] * 1e3
            color = TYPE_COLOR[ERROR_TYPE[condition]]
            ax.errorbar(x, s / n, yerr=[[s / n - low], [high - s / n]], fmt=marker, color=color, ecolor=color,
                        alpha=0.85, capsize=3, markersize=6,
                        markerfacecolor=color if occlusion == "patent" else "white")
    for kind, color in TYPE_COLOR.items():
        ax.plot([], [], "o", color=color, label=kind)
    ax.plot([], [], "o", color="gray", label="patent target")
    ax.plot([], [], "s", color="gray", markerfacecolor="white", label="occluded target")
    ax.set(xlabel="Route-averaged |u_model − u_plant| [mm/s]", ylabel="Success rate (both arms, all fps)",
           ylim=(-0.03, 1.03), title="90% flow reduction: success vs flow-model error (95% Wilson) | simulation only")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, ncol=2)
    fig.savefig(path / "success_vs_error.png", dpi=150)
    plt.close(fig)


def render(pooled, paired, errors):
    lines = ["# Experiment 25: controller flow-model errors", "",
             "Simulation only. Held-out seeds 3-5, both branches, all frame rates pooled. The plant never changes; "
             "only the controller's flow model is wrong. Route error is the mean |u_model - u_plant| over both routes "
             "(centerline and 0.5 mm off-axis) and one cardiac period.", "",
             "| Condition | Flow cut | Target | Arm | Route error mm/s | Success [95% CI] | Wall | Wrong |",
             "|---|---:|---|---|---:|---|---:|---:|"]
    for r in pooled:
        o = r["outcomes"]
        low, high = o["target_success"]["wilson_95"]
        lines.append(f"| {r['condition']} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{errors[(r['condition'], r['flow_reduction'], r['occlusion'])] * 1e3:.1f} | "
                     f"{o['target_success']['count']}/{r['trials']} [{low * 100:.0f}, {high * 100:.0f}] | "
                     f"{o['wall_collision']['count']} | {o['wrong_branch']['count']} |")
    lines += ["", "## Paired against the exact model", "",
              "| Condition | Flow cut | Target | Arm | Kept | Lost | Gained | Both fail |", "|---|---:|---|---|---:|---:|---:|---:|"]
    for r in paired:
        lines.append(f"| {r['condition']} | {r['flow_reduction'] * 100:g}% | {r['occlusion']} | {r['arm']} | "
                     f"{r['kept']} | {r['lost']} | {r['gained']} | {r['both_fail']} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", default="outputs/25_flow_model_errors")
    args = parser.parse_args()
    grid = cells()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(trial_record, grid, chunksize=2))
    errors = {(c, f, o): route_velocity_error(c, f, o) for c in CONDITIONS for f in FLOW_REDUCTIONS for o in OCCLUSIONS}
    pooled, paired = aggregate(records, POOLED), paired_against_exact(records)
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trials.json").write_text(json.dumps(records, indent=1, allow_nan=False) + "\n")
    (path / "aggregates.json").write_text(json.dumps(
        {"pooled": pooled, "paired": paired,
         "route_error_m_s": [{"condition": c, "flow_reduction": f, "occlusion": o, "error": e}
                             for (c, f, o), e in errors.items()]}, indent=1, allow_nan=False) + "\n")
    (path / "report.md").write_text(render(pooled, paired, errors))
    plots(pooled, errors, path)
    print(f"{len(records)} trials -> {path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
