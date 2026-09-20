"""Plot original/guided comparisons and replay the same gated dropout case."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.experiment import TrialConfig, run_trial
from src.planner import YWaypointPlanner
from src.replay_plotting import animate_pair, plot_pair
from src.vessel import YVessel


def plot_rates(root, output):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.19, right=0.97, top=0.85, bottom=0.16, hspace=0.38, wspace=0.15)
    scenario_labels = ["Nominal", "Tracking-loss burst", "Stale imaging", "High noise"]
    for row, cohort in enumerate(("pilot", "heldout")):
        results = {name: json.loads((root / cohort / name / "benchmark.json").read_text())
                   for name in ("baseline", "guided")}
        scenarios = results["baseline"]["scenarios"]
        y = np.arange(len(scenarios))[::-1]
        for col, branch in enumerate(("upper", "lower")):
            ax = axes[row, col]
            for index, (name, color) in enumerate((("baseline", "#788491"), ("guided", "#007F86"))):
                groups = {g["scenario"]: g for g in results[name]["aggregates"]
                          if g["branch"] == branch and g["control_mode"] == "gated"}
                outcomes = [groups[s]["outcomes"]["target_success"] for s in scenarios]
                rates = np.array([o["rate"] for o in outcomes]) * 100
                ci = np.array([o["wilson_95"] for o in outcomes]) * 100
                positions = y + (0.13 if index == 0 else -0.13)
                ax.errorbar(rates, positions, xerr=np.maximum(0, [rates - ci[:, 0], ci[:, 1] - rates]),
                            fmt="o", capsize=4, color=color, linewidth=2, label="Original route" if index == 0 else "Early guidance")
                for scenario, o, position in zip(scenarios, outcomes, positions):
                    ax.text(110, position, f"{o['count']}/{groups[scenario]['trials']}", color=color, va="center", fontsize=10)
            seeds = ",".join(map(str, results["baseline"]["seeds"]))
            ax.set(title=f"{branch.title()} target | seeds {seeds}", xlim=(-5, 128),
                   ylim=(-0.5, 3.5), xticks=[0, 25, 50, 75, 100], yticks=y, yticklabels=scenario_labels)
            ax.grid(axis="x", color="#E2E7EC")
            ax.spines[["top", "right", "left"]].set_visible(False)
            if row == 1:
                ax.set_xlabel("Target success (%)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=2, loc="lower center", bbox_to_anchor=(0.55, 0.065), frameon=False)
    fig.suptitle("Earlier branch guidance | same safety gate and force cap", fontsize=17, weight="bold", y=0.97)
    fig.text(0.04, 0.91, "Top: original pilot seeds. Bottom: validation seeds not used to select the 0.4 mm offset.", fontsize=11)
    fig.text(0.04, 0.025, "Dots: observed rates. Lines: 95% Wilson intervals. Five trials per cell; no general safety guarantee.\n"
             "Stale-data inhibition is unchanged: the lower target remains unreachable when active force stays zero.", fontsize=9)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_routes(output):
    vessel = YVessel()
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    for offset, label, color in ((0, "Original route", "#788491"), (0.4e-3, "Early guidance", "#007F86")):
        planner = YWaypointPlanner(vessel, "lower", approach_offset_m=offset)
        p = planner.waypoints * 1000
        ax.plot(p[:, 0], p[:, 1], ".-", color=color, label=label)
    ax.axvline(10, linestyle=":", color="#C54B43", label="Flow branch switch")
    ax.set(xlim=(6, 14), ylim=(-2.5, 0.3), xlabel="x [mm]", ylabel="y [mm]",
           title="Selected waypoints near the junction | lower target (XY projection)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="outputs/09_approach_guidance")
    parser.add_argument("--output", default="outputs/09_approach_guidance/figures")
    args = parser.parse_args()
    root, path = Path(args.input), Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    plot_rates(root, path / "success_rates.png")
    plot_routes(path / "waypoints.png")
    config = TrialConfig(seed=0, branch="lower", dropout_intervals=((8.0, 8.75),))
    cases = [run_trial(config), run_trial(replace(config, approach_offset_m=0.4e-3))]
    labels = ("Original route (gated)", "Early guidance (gated)")
    plot_pair(cases, labels, path / "dropout_seed_0.png", "Earlier guidance | dropout seed 0 | lower target",
              comparison_note="Same seed, scenario and safety gate; waypoint route differs.")
    animate_pair(cases, labels, path / "dropout_seed_0.gif")
    print(f"Saved success-rate comparison, waypoints, replay diagnostics and animation to {path}")


if __name__ == "__main__":
    main()
