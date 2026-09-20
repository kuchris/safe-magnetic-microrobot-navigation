"""Plot fixed-trace forecast errors and separate held-out navigation outcomes."""

import argparse
from collections import Counter
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.replay_plotting import plot_pair
from src.vessel import YVessel


MODES = ("kinematic", "command_aware")
LABELS = ("Kinematic", "Command-aware")
COLORS = ("#7E8792", "#007F86")


def mean_audit(trials, mode, horizon, subset, metric):
    values = [r[metric] for trial in trials for r in trial["metrics"][mode]
              if r["horizon_s"] == horizon and r["subset"] == subset and r[metric] is not None]
    return float(np.mean(values)) if values else None


def plot_audit(data, output):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained", sharey=True)
    metrics = ((0.1, "held_command_RMSE_m"), (0.5, "held_command_RMSE_m"), (0.5, "recorded_command_RMSE_m"))
    for ax, (model, d) in zip(axes, data.items()):
        for k, mode in enumerate(MODES):
            values = [mean_audit(d["trials"], mode, horizon, "all", metric) * 1e6 for horizon, metric in metrics]
            bars = ax.bar(np.arange(3) + (k - 0.5) * 0.34, values, width=0.34, color=COLORS[k], label=LABELS[k])
            ax.bar_label(bars, fmt="%.1f", padding=3)
        ax.set(title=f"{model.title()} | {len(d['trials'])} fixed traces", ylim=(0, 275), ylabel="Mean per-trial RMSE [micrometres]",
               xticks=range(3), xticklabels=["0.1 s\nheld command", "0.5 s\nheld command", "0.5 s\nrecorded commands"])
        ax.legend(loc="upper left", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Forecast audit on identical observations and commands | seeds 15-19\n"
                 "Recorded future commands are an offline diagnostic only. Lower is better; trial means mix tested conditions.", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_outcomes(data, output):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained", sharey=True)
    for row, (model, d) in enumerate(data.items()):
        n = len(d["seeds"])
        for col, speed in enumerate((0.6e-3, 1.2e-3)):
            ax = axes[row, col]
            for k, mode in enumerate(MODES):
                groups = d["aggregates_by_estimator"][mode]
                counts = [next(g["outcomes"]["target_success"]["count"] for g in groups
                               if g["flow_speed_m_s"] == speed and g["flow_disturbance_m_s"] == sigma and g["branch"] == branch)
                          for sigma in (0, 0.3e-3) for branch in ("upper", "lower")]
                bars = ax.bar(np.arange(4) + (k - 0.5) * 0.34, counts, width=0.34, color=COLORS[k], label=LABELS[k])
                ax.bar_label(bars, labels=[f"{c}/{n}" for c in counts], padding=3)
            ax.set(title=f"{model.title()} | {speed * 1000:g} mm/s", ylim=(0, n + 1), ylabel="Successful trials",
                   yticks=range(n + 1), xticks=range(4), xticklabels=["Upper\nsigma 0", "Lower\nsigma 0", "Upper\nsigma 0.3", "Lower\nsigma 0.3"])
            ax.legend(loc="upper right", fontsize=9)
            ax.spines[["top", "right"]].set_visible(False)
    seeds = ", ".join(map(str, data["piecewise"]["seeds"]))
    fig.suptitle(f"Closed-loop estimator comparison | held-out seeds {seeds}\n"
                 "Both use early guidance, 0.5 s correction, unchanged gates and 3 nN cap. Sigma: mm/s per axis.\n"
                 f"{n} trials per cell do not establish an operating range; raw records include Wilson intervals.", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default="outputs/15_estimation_audit")
    parser.add_argument("--comparison", default="outputs/16_flow_estimator_comparison")
    parser.add_argument("--output", default="outputs/17_estimation_figures")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    audit = {m: json.loads((Path(args.audit) / f"{m}.json").read_text()) for m in ("piecewise", "smooth")}
    data = {m: json.loads((Path(args.comparison) / f"{m}.json").read_text()) for m in audit}
    plot_audit(audit, output / "forecast_errors.png")
    plot_outcomes(data, output / "success_counts.png")
    summary = {}
    lines = ["# Command-aware estimation comparison", "",
             "Both policies use early guidance and 0.5 s prediction. Only estimator mode differs.", "",
             "| Field | Flow mm/s | Sigma mm/s | Branch | N | Kinematic success | Command-aware success | Rescued | Regressed |",
             "|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for model, d in data.items():
        records = {r["trace_id"]: r for r in d["trials"]}
        summary[model] = {"pair_changes": dict(Counter(p["change"] for p in d["pairs"]))}
        for mode in MODES:
            trials = [r for r in d["trials"] if r["config"]["estimator_mode"] == mode]
            summary[model][mode] = {"trials": len(trials),
                "outcomes": {key: sum(r["summary"][key] for r in trials) for key in ("target_success", "wall_collision", "wrong_branch")},
                "terminal_features": dict(Counter(r["terminal_wall_feature"] for r in trials)),
                "mean_stop_fraction": float(np.mean([r["summary"]["safety_stop_rate"] for r in trials]))}
        pairs = [(records[p["baseline"]], records[p["command_aware"]]) for p in d["pairs"]]
        for a, b in pairs:
            assert {k: v for k, v in a["config"].items() if k != "estimator_mode"} == {
                k: v for k, v in b["config"].items() if k != "estimator_mode"}
        for key in ("wall_collision", "wrong_branch"):
            summary[model][f"new_{key}"] = sum(not a["summary"][key] and b["summary"][key] for a, b in pairs)
        changes = np.array([b["summary"]["minimum_wall_clearance_m"] - a["summary"]["minimum_wall_clearance_m"] for a, b in pairs])
        summary[model]["clearance_decreased_over_1um"] = int(np.sum(changes < -1e-6))
        summary[model]["worst_clearance_change_m"] = float(changes.min())
        for base, changed in zip(d["aggregates_by_estimator"]["kinematic"], d["aggregates_by_estimator"]["command_aware"]):
            keys = ("flow_speed_m_s", "flow_disturbance_m_s", "branch")
            assert all(base[k] == changed[k] for k in keys)
            selected = [p for p in d["pairs"] if all(records[p["baseline"]]["config"][k] == base[k] for k in keys)]
            lines.append(f"| {model} | {base['flow_speed_m_s'] * 1000:g} | {base['flow_disturbance_m_s'] * 1000:g} | "
                         f"{base['branch']} | {base['trials']} | {base['outcomes']['target_success']['count']} | "
                         f"{changed['outcomes']['target_success']['count']} | {sum(p['change']=='rescued' for p in selected)} | "
                         f"{sum(p['change']=='regressed' for p in selected)} |")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "comparison.md").write_text("\n".join(lines) + "\n")
    records = {r["trace_id"]: r for d in data.values() for r in d["trials"]}
    regressions = [p for d in data.values() for p in d["pairs"] if p["change"] == "regressed"]
    if regressions:
        pair = regressions[0]  # Deterministic first regression in experiment order.
        cases = []
        for key in ("baseline", "command_aware"):
            with np.load(Path(args.comparison) / "traces" / f"{pair[key]}.npz") as history:
                cases.append(dict(records[pair[key]], history=dict(history)))
        plot_pair(cases, LABELS, output / "regression.png", f"First regressed pair | {pair['case_id']}",
                  comparison_note="Same seed and scenario; only estimator mode differs.")
        (output / "regression_example.json").write_text(json.dumps(pair, indent=2) + "\n")
    details = []
    for pair in regressions:
        detail = {"case_id": pair["case_id"]}
        for key in ("baseline", "command_aware"):
            record = records[pair[key]]
            vessel = YVessel()
            target = vessel.upper_target if record["config"]["branch"] == "upper" else vessel.lower_target
            with np.load(Path(args.comparison) / "traces" / f"{pair[key]}.npz") as h:
                distances = np.linalg.norm(h["true_position_m"] - target, axis=1)
                i = int(np.argmin(distances))
                detail[key] = {"closest_target_distance_m": float(distances[i]),
                               "closest_target_time_s": float(h["time_s"][i]),
                               "terminal_feature": record["terminal_wall_feature"]}
        details.append(detail)
    (output / "regression_details.json").write_text(json.dumps(details, indent=2) + "\n")
    print(f"Saved figures and comparison summaries to {output}")


if __name__ == "__main__":
    main()
