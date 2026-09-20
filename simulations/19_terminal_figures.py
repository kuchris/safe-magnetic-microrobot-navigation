"""Summarize held-out terminal-guidance outcomes and selected trajectory replays."""

import argparse
from collections import Counter
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.vessel import YVessel


def plot_counts(data, output):
    columns = [(speed, sigma, branch) for speed in (.6e-3, 1.2e-3)
               for sigma in (0, .3e-3) for branch in ("upper", "lower")]
    rows = [(model, mode) for model in data for mode in ("kinematic", "command_aware")]
    before, after = [], []
    for model, mode in rows:
        counts = []
        for suffix in ("off", "on"):
            groups = data[model]["aggregates_by_variant"][f"{mode}_{suffix}"]
            counts.append([next(g["outcomes"]["target_success"]["count"] for g in groups
                          if (g["flow_speed_m_s"], g["flow_disturbance_m_s"], g["branch"]) == key) for key in columns])
        before.append(counts[0])
        after.append(counts[1])
    before, after = np.array(before), np.array(after)
    n = len(data["piecewise"]["seeds"])
    fig, ax = plt.subplots(figsize=(14, 5), layout="constrained")
    plot = ax.imshow(after - before, cmap="RdYlGn", vmin=-n, vmax=n, aspect="auto")
    for i in range(4):
        for j in range(8):
            ax.text(j, i, f"{before[i, j]} → {after[i, j]}", ha="center", va="center", weight="bold", fontsize=13)
    ax.set(xticks=range(8), xticklabels=[f"{s * 1000:g} mm/s\nsigma {d * 1000:g}\n{b}" for s, d, b in columns],
           yticks=range(4), yticklabels=[f"{m.title()}\n{'Kinematic' if e == 'kinematic' else 'Command-aware'}" for m, e in rows])
    ax.axhline(1.5, color="white", linewidth=3)
    ax.axvline(3.5, color="white", linewidth=3)
    fig.colorbar(plot, ax=ax, label="Change in success count")
    seeds = ", ".join(map(str, data["piecewise"]["seeds"]))
    fig.suptitle(f"Terminal guidance: off → on | {n} trials per cell | seeds {seeds}\n"
                 "Fixed 0.4 mm success radius, 3 nN cap and current safety gates. Sigma: mm/s per velocity axis.\n"
                 "Counts are descriptive; paired rescues and regressions are reported separately.", fontsize=13)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_replay(pair, records, root, output):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained")
    vessel = YVessel()
    target = vessel.upper_target if records[pair["baseline"]]["config"]["branch"] == "upper" else vessel.lower_target
    target_mm = target * 1000
    colors = ("#7E8792", "#007F86")
    first_times = []
    maximum_distance = 0.0
    for index, key in enumerate(("baseline", "terminal")):
        record = records[pair[key]]
        label = "Off" if index == 0 else "On"
        label += " (success)" if record["summary"]["target_success"] else " (failed)"
        with np.load(root / "traces" / f"{pair[key]}.npz") as h:
            t, p = h["time_s"], h["true_position_m"]
            distance = np.linalg.norm(p - target, axis=1) * 1000
            maximum_distance = max(maximum_distance, float(distance.max()))
            near = np.flatnonzero(distance <= 2.5)
            if len(near):
                first_times.append(t[near[0]])
            axes[0].plot(p[:, 0] * 1000, p[:, 1] * 1000, color=colors[index], label=label)
            axes[0].scatter(*p[-1, :2] * 1000, color=colors[index], marker="o" if record["summary"]["target_success"] else "x")
            axes[1].plot(t, distance, color=colors[index], label=label)
            if index == 1:
                axes[2].plot(t, h["baseline_target_miss_m"] * 1000, color="#7E8792", label="Wall-only candidate")
                axes[2].plot(t, h["selected_target_miss_m"] * 1000, color="#007F86", label="Selected candidate")
                if not h["terminal_active"].any():
                    axes[2].text(.5, .5, "Terminal mode never active", transform=axes[2].transAxes, ha="center")
                    axes[2].set_axis_off()
    axes[0].add_patch(plt.Circle(target_mm[:2], .4, color="#007F86", fill=False, linestyle="--", label="Target sphere (XY projection)"))
    axes[0].scatter(*target_mm[:2], marker="*", color="black", s=70)
    axes[0].set(title="True trajectory near target", xlabel="x [mm]", ylabel="y [mm]",
                xlim=(target_mm[0] - 2.5, target_mm[0] + 1.5), ylim=(target_mm[1] - 2, target_mm[1] + 2))
    axes[0].set_aspect("equal", adjustable="box")
    axes[1].set(title="Actual 3D target distance", xlabel="Time [s]", ylabel="Distance [mm]", ylim=(0, 2.5))
    axes[1].axhline(.4, color="black", linestyle="--", linewidth=.8, label="Success radius")
    axes[2].set(title="Within guided run: predicted miss", xlabel="Time [s]", ylabel="Closest 3D distance [mm]")
    if first_times:
        for ax in axes[1:]:
            ax.set_xlim(left=min(first_times))
    else:
        axes[0].set(title="True paths: target region not reached", xlim=(0, 23), ylim=(-8, 8))
        axes[1].set_ylim(0, maximum_distance * 1.05)
        for segment in vessel.segments:
            line = np.vstack([segment.start_m, segment.end_m]) * 1000
            axes[0].plot(line[:, 0], line[:, 1], "--", color="#A6AEB7", linewidth=1)
    for ax in axes:
        if ax.axison:
            ax.legend(fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{pair['change'].title()} | {pair['case_id']}\n"
                 "First matching case in fixed experiment order. Prediction assumes a constant candidate force over 0.5 s.", fontsize=12)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="outputs/18_terminal_guidance")
    parser.add_argument("--output", default="outputs/19_terminal_figures")
    args = parser.parse_args()
    root, output = Path(args.input), Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    data = {m: json.loads((root / f"{m}.json").read_text()) for m in ("piecewise", "smooth")}
    if data["piecewise"]["seeds"] != data["smooth"]["seeds"]:
        raise ValueError("Both fields must use matching seeds")
    plot_counts(data, output / "success_counts.png")
    records = {r["trace_id"]: r for d in data.values() for r in d["trials"]}
    summary = []
    lines = ["# Paired terminal-guidance results", "",
             "| Field | Estimator | Flow mm/s | Sigma mm/s | Branch | N | Off success | On success | Rescued | Regressed |",
             "|---|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for model, d in data.items():
        for mode in ("kinematic", "command_aware"):
            pairs = [p for p in d["pairs"] if p["estimator_mode"] == mode]
            for pair in pairs:
                a, b = records[pair["baseline"]], records[pair["terminal"]]
                assert {k: v for k, v in a["config"].items() if k != "terminal_guidance_distance_m"} == {
                    k: v for k, v in b["config"].items() if k != "terminal_guidance_distance_m"}
            row = {"flow_model": model, "estimator_mode": mode,
                   "pair_changes": dict(Counter(p["change"] for p in pairs))}
            for suffix in ("off", "on"):
                trials = [r for r in d["trials"] if r["variant"] == f"{mode}_{suffix}"]
                row[suffix] = {"trials": len(trials), "outcomes": {k: sum(r["summary"][k] for r in trials)
                    for k in ("target_success", "wall_collision", "wrong_branch")},
                    "timeouts": sum(r["timeout"] for r in trials),
                    "terminal_features": dict(Counter(r["terminal_wall_feature"] for r in trials))}
            for key in ("wall_collision", "wrong_branch"):
                row[f"new_{key}"] = sum(not records[p["baseline"]]["summary"][key] and records[p["terminal"]]["summary"][key] for p in pairs)
            deltas = np.array([records[p["terminal"]]["summary"]["minimum_wall_clearance_m"] -
                               records[p["baseline"]]["summary"]["minimum_wall_clearance_m"] for p in pairs])
            row["clearance_decreased_over_1um"] = int(np.sum(deltas < -1e-6))
            row["worst_clearance_change_m"] = float(deltas.min())
            summary.append(row)
            for a, b in zip(d["aggregates_by_variant"][f"{mode}_off"], d["aggregates_by_variant"][f"{mode}_on"]):
                keys = ("flow_speed_m_s", "flow_disturbance_m_s", "branch")
                assert all(a[k] == b[k] for k in keys)
                selected = [p for p in pairs if all(records[p["baseline"]]["config"][k] == a[k] for k in keys)]
                lines.append(f"| {model} | {mode} | {a['flow_speed_m_s'] * 1000:g} | {a['flow_disturbance_m_s'] * 1000:g} | "
                             f"{a['branch']} | {a['trials']} | {a['outcomes']['target_success']['count']} | "
                             f"{b['outcomes']['target_success']['count']} | {sum(p['change']=='rescued' for p in selected)} | "
                             f"{sum(p['change']=='regressed' for p in selected)} |")
    examples = []
    pairs = [p for d in data.values() for p in d["pairs"]]
    for change in ("rescued", "regressed", "unchanged"):
        matching = [p for p in pairs if p["change"] == change and
                    (change != "unchanged" or not records[p["terminal"]]["summary"]["target_success"])]
        if matching:
            plot_replay(matching[0], records, root, output / f"{change}.png")
            examples.append(matching[0])
    for name, content in (("summary", summary), ("replay_examples", examples)):
        (output / f"{name}.json").write_text(json.dumps(content, indent=2) + "\n")
    (output / "comparison.md").write_text("\n".join(lines) + "\n")
    print(f"Saved comparison, summary and {1 + len(examples)} figures to {output}")


if __name__ == "__main__":
    main()
