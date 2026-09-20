"""Render flow-field and sampled performance maps from experiment 11."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.flow import prescribed_flow
from src.benchmark import wilson_interval


def plot_fields(output):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained", sharey=True)
    x, y = np.meshgrid(np.linspace(7, 14, 15), np.linspace(-2.4, 2.4, 13))
    for ax, model in zip(axes, ("piecewise", "smooth")):
        values = np.array([prescribed_flow([a * 1e-3, b * 1e-3, 0], 0.6e-3, model)
                           for a, b in zip(x.flat, y.flat)]) * 1000
        u, v = values[:, 0].reshape(x.shape), values[:, 1].reshape(y.shape)
        ax.quiver(x, y, u, v, v, cmap="coolwarm", clim=(-0.3, 0.3),
                  angles="xy", scale_units="xy", scale=1, width=0.003)
        ax.axvline(10, color="#7F8790", linestyle=":")
        ax.axhline(0, color="#7F8790", linestyle=":")
        ax.set(title="Original sign switch" if model == "piecewise" else "Continuous direction blend",
               xlabel="x [mm]", ylabel="y [mm]", xlim=(6.7, 14.7), ylim=(-2.8, 2.8))
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Prescribed flow, 0.6 mm/s | XY components at z = 0\n"
                 "One-second arrow scale; synthetic field, not wall-conforming or flux-conserving", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_map(data, outcome, title, output):
    metric = outcome in ("safety_stop_rate", "flow_holding_limit_exceeded_fraction")
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    fig.subplots_adjust(left=0.08, right=0.90, top=0.79, bottom=0.18, wspace=0.26, hspace=0.55)
    for row, model in enumerate(("piecewise", "smooth")):
        results = data[model]
        speeds, sigmas = results["speeds_m_s"], results["disturbances_m_s"]
        for col, (branch, offset) in enumerate((("upper", 0), ("upper", 0.4e-3), ("lower", 0), ("lower", 0.4e-3))):
            ax = axes[row, col]
            groups = {(r["flow_speed_m_s"], r["flow_disturbance_m_s"]): r for r in results["aggregates"]
                      if r["branch"] == branch and r["approach_offset_m"] == offset}
            bucket, field = ("metrics", "mean") if metric else ("outcomes", "rate")
            cells = [[groups[(speed, sigma)][bucket][outcome][field] * 100 for speed in speeds] for sigma in sigmas]
            plot = ax.imshow(cells, origin="lower", vmin=0, vmax=100, aspect="auto",
                             cmap="YlGnBu" if outcome == "target_success" else "YlOrRd")
            for i, sigma in enumerate(sigmas):
                for j, speed in enumerate(speeds):
                    group = groups[(speed, sigma)]
                    label = f"{cells[i][j]:.1f}%" if metric else f"{group['outcomes'][outcome]['count']}/{group['trials']}"
                    ax.text(j, i, label,
                            ha="center", va="center", weight="bold", color="white" if cells[i][j] > 65 else "#172D3D")
            route = "Original route" if offset == 0 else "Early guidance"
            ax.set(title=f"{model.title()} | {branch}\n{route}",
                   xticks=range(len(speeds)), xticklabels=[f"{s * 1000:g}" for s in speeds],
                   yticks=range(len(sigmas)), yticklabels=[f"{s * 1000:g}" for s in sigmas])
            if row == 1:
                ax.set_xlabel("Mean flow [mm/s]")
            if col == 0:
                ax.set_ylabel("Disturbance sigma [mm/s]")
    cax = fig.add_axes((0.92, 0.25, 0.015, 0.5))
    fig.colorbar(plot, cax=cax, label="Mean per-trial fraction [%]" if metric else "Observed trial rate [%]")
    fig.suptitle(title, fontsize=18, weight="bold", y=0.97)
    seeds = data["piecewise"]["seeds"]
    fig.text(0.08, 0.89, f"Gated control | seeds {', '.join(map(str, seeds))} | 60 s horizon | disturbance correlation: 0.25 s", fontsize=11)
    n = len(seeds)
    lower, upper = wilson_interval(n, n)
    note = (f"Means across {n} trials per cell, not event probabilities. Correlated time samples have no binomial interval.\n"
            "Holding demand above the force cap prevents instantaneous station keeping, not necessarily downstream navigation.") if metric else (
            f"Cells show counts, not certified operating limits. {n} trials per cell; even {n}/{n} has a 95% Wilson interval of {lower * 100:.1f}%-{upper * 100:.1f}%.\n"
            "Disturbance sigma is per velocity axis. Geometry, force cap and nominal imaging are fixed; both fields remain synthetic.")
    fig.text(0.08, 0.06, note, fontsize=9)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="outputs/11_flow_sensitivity")
    parser.add_argument("--output", default="outputs/11_flow_sensitivity/figures")
    args = parser.parse_args()
    root, path = Path(args.input), Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    data = {model: json.loads((root / f"{model}.json").read_text()) for model in ("piecewise", "smooth")}
    if data["piecewise"]["seeds"] != data["smooth"]["seeds"]:
        raise ValueError("Flow comparison requires the same seeds")
    plot_fields(path / "flow_fields.png")
    for outcome, title in (("target_success", "Target success across tested flow conditions"),
                           ("wrong_branch", "Wrong-branch events across tested flow conditions"),
                           ("wall_collision", "Wall-proxy violations across tested flow conditions"),
                           ("safety_stop_rate", "Safety-gate inhibition | mean stopped-sample fraction"),
                           ("flow_holding_limit_exceeded_fraction", "Flow-holding demand above force cap | mean interval fraction")):
        plot_map(data, outcome, title, path / f"{outcome}.png")
    print(f"Saved field comparison and five performance/diagnostic maps to {path}")


if __name__ == "__main__":
    main()
