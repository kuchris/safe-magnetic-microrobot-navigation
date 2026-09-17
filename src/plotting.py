"""Static research diagnostics, aligned at the same simulation timestamps."""

import numpy as np
from src.vessel import YVessel


def plot_trial(result, output_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    h = result["history"]
    t = h["time_s"]
    truth, estimate = h["true_position_m"] * 1e3, h["estimated_position_m"] * 1e3
    stop = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    fig = plt.figure(figsize=(13, 10), layout="constrained")
    grid = fig.add_gridspec(3, 2)
    ax = fig.add_subplot(grid[:2, 0], projection="3d")
    vessel = YVessel()
    for i, segment in enumerate(vessel.segments):
        line = np.vstack([segment.start_m, segment.end_m]) * 1e3
        ax.plot(*line.T, ":", color="gray", label="Centerline" if i == 0 else None)
    ax.plot(*truth.T, label="True", color="tab:blue")
    ax.plot(*estimate.T, "--", label="Estimated", color="tab:orange", alpha=0.85)
    ax.scatter(*truth[stop].T, s=8, color="tab:red", label="Actuation stopped")
    target = vessel.upper_target if result["config"]["branch"] == "upper" else vessel.lower_target
    ax.scatter(*(target * 1e3), marker="*", s=100, color="black", label="Target")
    ax.set(xlabel="x [mm]", ylabel="y [mm]", zlabel="z [mm]", title="Toy Y-vessel navigation")
    ax.legend(fontsize=8)
    ax = fig.add_subplot(grid[0, 1])
    ax.plot(t, np.linalg.norm(truth - estimate, axis=1), color="tab:orange")
    ax.set(ylabel="Position error [mm]", title="Same-time localization error")
    ax = fig.add_subplot(grid[1, 1])
    ax.plot(t, h["sigma_m"] * 1e3, label="Largest-axis sigma")
    ax.axhline(result["config"]["max_sigma_m"] * 1e3, color="tab:red", linestyle="--", label="Stop threshold")
    ax.set(ylabel="Uncertainty [mm]", xlabel="Time [s]")
    ax.legend(fontsize=8)
    ax = fig.add_subplot(grid[2, 0])
    for key, label in (("true_clearance_m", "True proxy"), ("estimated_clearance_m", "Estimated proxy"),
                       ("robust_clearance_m", "Robust proxy")):
        ax.plot(t, h[key] * 1e3, label=label)
    ax.axhline(result["config"]["safety_margin_m"] * 1e3, color="tab:red", linestyle="--", label="Margin")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(ylabel="Clearance [mm]", xlabel="Time [s]")
    ax.legend(fontsize=8)
    ax = fig.add_subplot(grid[2, 1])
    for i, label in enumerate(("Fx", "Fy", "Fz")):
        ax.plot(t, h["force_n"][:, i] * 1e9, label=label, alpha=0.7)
    ax.plot(t, np.linalg.norm(h["force_n"], axis=1) * 1e9, color="black", label="Magnitude")
    ax.set(ylabel="Applied force [nN]", xlabel="Time [s]")
    ax.legend(fontsize=8, ncol=4)
    fig.suptitle(f"Seed {result['config']['seed']} | simulation only | no clinical validation")
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
