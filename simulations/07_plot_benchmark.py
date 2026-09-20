"""Plot saved benchmark success rates without rerunning the simulations."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.benchmark import MODES


def plot_benchmark(result, output_path):
    scenarios = result["scenarios"]
    labels = {"nominal": "Nominal imaging", "dropout_burst": "Tracking-loss burst",
              "stale_imaging": "Stale imaging (250 ms)", "high_noise": "High noise (12 px)"}
    policies = {"passive": ("Passive drift", "#788491"),
                "ungated": ("Without safety gate", "#D68A12"),
                "gated": ("With safety gate", "#007F86")}
    groups = {(g["scenario"], g["branch"], g["control_mode"]): g
              for g in result["aggregates"]}
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), sharey=True)
    fig.subplots_adjust(left=0.20, right=0.97, top=0.77, bottom=0.19, wspace=0.17)
    y = np.arange(len(scenarios))[::-1]
    for ax, branch in zip(axes, ("upper", "lower")):
        for index, mode in enumerate(MODES):
            name, color = policies[mode]
            selected = [groups[(scenario, branch, mode)] for scenario in scenarios]
            rates = np.array([g["outcomes"]["target_success"]["rate"] for g in selected]) * 100
            intervals = np.array([g["outcomes"]["target_success"]["wilson_95"]
                                  for g in selected]) * 100
            positions = y + (1 - index) * 0.23
            ax.errorbar(rates, positions, xerr=np.maximum(0, np.array([
                rates - intervals[:, 0], intervals[:, 1] - rates])),
                fmt="o", color=color, markersize=7, capsize=4, linewidth=2, label=name)
            for row, position in zip(selected, positions):
                count = row["outcomes"]["target_success"]["count"]
                ax.text(111, position, f"{count}/{row['trials']}", color=color,
                        fontsize=10, va="center", weight="bold")
        ax.set(title=f"{branch.title()} target", xlabel="Target success (%)",
               xlim=(-5, 129), xticks=[0, 25, 50, 75, 100],
               yticks=y, yticklabels=[labels[s] for s in scenarios])
        ax.set_ylim(-0.55, len(scenarios) - 0.45)
        ax.grid(axis="x", color="#E2E7EC", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=0, labelsize=10)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#CBD2D9")
        ax.text(111, len(scenarios) - 0.43, "Reached", fontsize=9, color="#56616C")
    fig.suptitle("Can the robot reach the requested branch?", x=0.04, y=0.97,
                 ha="left", fontsize=20, weight="bold", color="#172D3D")
    fig.text(0.04, 0.90, f"{len(result['trials'])} toy simulation trials  |  "
             f"{len(result['seeds'])} paired seeds per policy / branch / scenario",
             fontsize=11, color="#56616C")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", bbox_to_anchor=(0.55, 0.08),
               ncol=3, frameon=False, fontsize=10)
    fig.text(0.04, 0.035, "Dots: observed success rates. Lines: 95% Wilson intervals. "
             "Small groups leave substantial uncertainty.\n"
             "Upper-target arrival may be passive drift. Zero magnetic force does not stop flow-driven motion.",
             fontsize=9, color="#56616C", linespacing=1.6)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="docs/results/benchmark_pilot.json")
    parser.add_argument("--output", default="outputs/06_benchmark_pilot/success_rates.png")
    args = parser.parse_args()
    plot_benchmark(json.loads(Path(args.input).read_text()), args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
