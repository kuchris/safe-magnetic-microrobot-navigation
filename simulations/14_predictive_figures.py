"""Render paired counts and deterministically selected prediction replays."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.replay_plotting import draw_route


COLORS = ("#7E8792", "#007F86")


def plot_counts(data, output):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained", sharey=True)
    for row, model in enumerate(("piecewise", "smooth")):
        n = len(data[model]["seeds"])
        for col, speed in enumerate((0.6e-3, 1.2e-3)):
            ax = axes[row, col]
            for index, horizon in enumerate(("0.0", "0.5")):
                groups = data[model]["aggregates_by_horizon"][horizon]
                counts = [next(g["outcomes"]["target_success"]["count"] for g in groups
                               if g["flow_speed_m_s"] == speed and g["flow_disturbance_m_s"] == sigma
                               and g["branch"] == branch)
                          for sigma in (0, 0.3e-3) for branch in ("upper", "lower")]
                bars = ax.bar(np.arange(4) + (index - 0.5) * 0.34, counts, width=0.34,
                              color=COLORS[index], label="Baseline" if index == 0 else "0.5 s prediction")
                ax.bar_label(bars, labels=[f"{count}/{n}" for count in counts], padding=3, fontsize=10)
            ax.set(title=f"{model.title()} flow | {speed * 1000:g} mm/s", ylim=(0, n + 1),
                   xticks=range(4), xticklabels=["Upper\nsigma 0", "Lower\nsigma 0", "Upper\nsigma 0.3", "Lower\nsigma 0.3"],
                   ylabel="Successful trials", yticks=range(n + 1))
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(fontsize=9, loc="upper right")
    seeds = ", ".join(map(str, data["piecewise"]["seeds"]))
    fig.suptitle(f"Short-horizon correction | matched target-success counts\n"
                 f"Seeds {seeds}; both use early guidance, unchanged gates and 3 nN cap\n"
                 f"Sigma: mm/s per axis, 0.25 s correlation. {n} trials per cell are not a certified operating range.", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_replay(pair, records, root, output):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), layout="constrained")
    draw_route(axes[0], records[pair["baseline"]]["config"]["branch"])
    for index, key in enumerate(("baseline", "predictive")):
        record = records[pair[key]]
        with np.load(root / "traces" / f"{pair[key]}.npz") as h:
            t = h["time_s"]
            p = h["true_position_m"] * 1000
            label = "Baseline" if index == 0 else "Prediction"
            label += " (success)" if record["summary"]["target_success"] else " (failed)"
            axes[0].plot(p[:, 0], p[:, 1], color=COLORS[index], label=label)
            axes[0].scatter(*p[-1, :2], color=COLORS[index], marker="o" if record["summary"]["target_success"] else "x")
            axes[1].plot(t, h["true_clearance_m"] * 1000, color=COLORS[index], label=label)
            if index == 1:
                axes[2].plot(t, h["predicted_nominal_clearance_m"] * 1000, color="#C54B43", label="Nominal force")
                axes[2].plot(t, h["predicted_selected_clearance_m"] * 1000, color=COLORS[index], label="Selected force")
                adjusted = h["prediction_adjusted"]
                axes[2].scatter(t[adjusted][::20], h["predicted_selected_clearance_m"][adjusted][::20] * 1000,
                                s=8, color="#D68A12", label="Adjustment (subsampled)")
    axes[0].set_title("True XY paths; dashed lines are centerlines")
    axes[1].set(title="Simulated true clearance proxy", xlabel="Time [s]", ylabel="Clearance [mm]")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[2].set(title="Predicted minimum robust clearance", xlabel="Time [s]", ylabel="Clearance [mm]")
    axes[2].axhline(0.2, color="black", linestyle="--", linewidth=0.8, label="0.2 mm margin")
    for ax in axes:
        ax.legend(fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{pair['change'].title()} | {pair['case_id']}\n"
                 "First matching case in fixed experiment order. Prediction gaps mean the current gate inhibited actuation.", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="outputs/13_predictive_control")
    args = parser.parse_args()
    root = Path(args.input)
    output = root / "figures"
    output.mkdir(parents=True, exist_ok=True)
    data = {model: json.loads((root / f"{model}.json").read_text()) for model in ("piecewise", "smooth")}
    if data["piecewise"]["seeds"] != data["smooth"]["seeds"]:
        raise ValueError("Flow models must use matching seeds")
    plot_counts(data, output / "success_counts.png")
    records = {r["trace_id"]: r for d in data.values() for r in d["trials"]}
    pairs = [p for d in data.values() for p in d["pairs"]]
    examples = []
    for change in ("rescued", "regressed", "unchanged"):
        matching = [p for p in pairs if p["change"] == change and
                    (change != "unchanged" or not records[p["predictive"]]["summary"]["target_success"])]
        if matching:
            pair = matching[0]
            plot_replay(pair, records, root, output / f"{change}.png")
            examples.append(pair)
    (root / "replay_examples.json").write_text(json.dumps(examples, indent=2) + "\n")
    lines = ["# Predictive control matched results", "",
             "Both controllers use 0.4 mm early guidance; only prediction horizon differs. Counts are per trial.", "",
             "| Field | Flow mm/s | Sigma mm/s | Branch | N | Baseline success | Prediction success | Rescued | Regressed |",
             "|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for model, d in data.items():
        for base, pred in zip(d["aggregates_by_horizon"]["0.0"], d["aggregates_by_horizon"]["0.5"]):
            keys = ("flow_speed_m_s", "flow_disturbance_m_s", "branch")
            assert all(base[k] == pred[k] for k in keys)
            selected = [p for p in d["pairs"] if all(records[p["baseline"]]["config"][k] == base[k] for k in keys)]
            lines.append(f"| {model} | {base['flow_speed_m_s'] * 1000:g} | {base['flow_disturbance_m_s'] * 1000:g} | "
                         f"{base['branch']} | {base['trials']} | {base['outcomes']['target_success']['count']} | "
                         f"{pred['outcomes']['target_success']['count']} | {sum(p['change'] == 'rescued' for p in selected)} | "
                         f"{sum(p['change'] == 'regressed' for p in selected)} |")
    (root / "comparison.md").write_text("\n".join(lines) + "\n")
    print(f"Saved comparison table and {1 + len(examples)} figures to {root}")


if __name__ == "__main__":
    main()
