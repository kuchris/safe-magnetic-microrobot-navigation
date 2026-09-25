"""Static diagnostics and animation from saved replay histories."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyArrowPatch
import numpy as np

from src.vessel import YVessel


COLORS = ("#007F86", "#C54B43")
STOP_REASONS = ("tracking_lost", "localization_uncertain", "wall_margin_low")


def draw_route(ax, branch):
    vessel = YVessel()
    for segment in vessel.segments:
        line = np.vstack([segment.start_m, segment.end_m]) * 1000
        ax.plot(line[:, 0], line[:, 1], "--", color="#A6AEB7", linewidth=1)
    target = vessel.upper_target if branch == "upper" else vessel.lower_target
    ax.scatter(target[0] * 1000, target[1] * 1000, marker="*", s=140, color="#007F86", label="Target")
    ax.axvline(10, color="#A6AEB7", linewidth=0.8)
    ax.set(xlabel="x [mm]", ylabel="y [mm]", xlim=(0, 23), ylim=(-8, 8))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)


def plot_pair(cases, labels, output_path, title,
              comparison_note="Same seed and scenario; policy differs."):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), layout="constrained")
    draw_route(axes[0, 0], cases[0]["config"]["branch"])
    for index, (case, label, color) in enumerate(zip(cases, labels, COLORS)):
        h = case["history"]
        t, p, estimate = h["time_s"], h["true_position_m"] * 1000, h["estimated_position_m"] * 1000
        axes[0, 0].plot(p[:, 0], p[:, 1], color=color, label=label)
        axes[0, 0].scatter(*p[-1, :2], color=color, marker="o" if case["summary"]["target_success"] else "x")
        axes[0, 1].plot(t, np.linalg.norm(p - estimate, axis=1), color=color, label=label)
        axes[0, 1].plot(t, h["sigma_m"] * 3000, color=color, linestyle=":", alpha=0.7)
        crossing = np.flatnonzero(p[:, 0] >= 10)
        if len(crossing):
            i = crossing[0]
            near = (t >= t[i] - 0.5) & (t <= t[i] + 0.5)
            axes[0, 2].plot(t[near] - t[i], p[near, 1] * 1000, color=color, label=label)
            axes[0, 2].scatter(0, p[i, 1] * 1000, color=color)
        axes[1, 0].plot(t, h["true_clearance_m"] * 1000, color=color, label=label)
        axes[1, 0].plot(t, h["robust_clearance_m"] * 1000, color=color, linestyle=":", alpha=0.7)
        axes[1, 1].plot(t, h["force_n"][:, 1] * 1e9, color=color, label=label)
        axes[1, 1].plot(t, np.linalg.norm(h["force_n"], axis=1) * 1e9, color=color, linestyle=":", alpha=0.7)
        reasons = {"safe": 0, "ungated": 0, "passive": 0, "actuation_limit": 1,
                   "tracking_lost": 2, "localization_uncertain": 3, "wall_margin_low": 4,
                   "prediction_adjustment": 5}
        axes[1, 2].step(t, [reasons[r] + (index - 0.5) * 0.12 for r in h["reason"]],
                        where="post", color=color, label=label, linewidth=1)
    axes[0, 0].set_title("True trajectories (XY projection)")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].set(title="Localization: error / dotted 3-sigma", xlabel="Time [s]", ylabel="Distance [mm]")
    axes[0, 2].set(title="At the first x >= 10 mm sample", xlabel="Time from crossing [s]", ylabel="True y [micrometres]")
    axes[0, 2].axhline(0, color="black", linewidth=0.7)
    axes[0, 2].axvline(0, color="black", linewidth=0.7, linestyle=":")
    axes[1, 0].set(title="Clearance: true / dotted robust", xlabel="Time [s]", ylabel="Proxy clearance [mm]")
    axes[1, 0].axhline(0, color="black", linewidth=0.7)
    axes[1, 0].axhline(0.2, color="#8A8A8A", linewidth=0.7, linestyle="--")
    axes[1, 1].set(title="Applied force: Fy / dotted magnitude", xlabel="Time [s]", ylabel="Force [nN]")
    axes[1, 2].set(title="Controller state", xlabel="Time [s]", yticks=range(6),
                   yticklabels=["Steering", "Force cap", "Tracking lost", "Uncertain", "Wall margin", "Prediction"])
    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(title + "\n" + comparison_note + " Capsule proxy / toy flow only.", fontsize=14)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def animate_pair(cases, labels, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.79, bottom=0.25, wspace=0.25)
    artists = []
    for ax, case, label in zip(axes, cases, labels):
        draw_route(ax, case["config"]["branch"])
        ax.set_title(label, fontsize=12)
        trail, = ax.plot([], [], color="#007F86", linewidth=2)
        truth, = ax.plot([], [], "o", color="#007F86", markersize=7)
        estimate, = ax.plot([], [], "x", color="#D68A12", markersize=8)
        waypoint, = ax.plot([], [], "D", color="#7253A3", markersize=4)
        arrow = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=14, color="#C54B43", linewidth=2)
        ax.add_patch(arrow)
        status = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", fontsize=9,
                         bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
        artists.append((trail, truth, estimate, waypoint, arrow, status))
    clock = fig.text(0.5, 0.88, "", ha="center", fontsize=12)
    fig.suptitle("Tracking-loss burst | lower target | seed 0", fontsize=17, weight="bold")
    fig.text(0.06, 0.04, "Path / dot: truth (red dot = inhibited). Orange x: estimate. Purple diamond: waypoint.\n"
             "Red arrow: force (1 nN = 0.5 mm). Grey: centerlines; XY projection, not wall boundaries.\n"
             "Finished trials freeze at the terminal sample. Toy simulation only.", fontsize=9)
    end = max(case["history"]["time_s"][-1] for case in cases)

    def update(now):
        clock.set_text(f"Simulation time: {now:.2f} s")
        for case, group in zip(cases, artists):
            h = case["history"]
            i = max(0, np.searchsorted(h["time_s"], now, side="right") - 1)
            p, e, w = h["true_position_m"][i] * 1000, h["estimated_position_m"][i] * 1000, h["waypoint_m"][i] * 1000
            trail, truth, estimate, waypoint, arrow, status = group
            trail.set_data(h["true_position_m"][:i + 1:5, 0] * 1000, h["true_position_m"][:i + 1:5, 1] * 1000)
            truth.set_data([p[0]], [p[1]])
            truth.set_color("#C54B43" if h["reason"][i] in STOP_REASONS else "#007F86")
            estimate.set_data([e[0]], [e[1]])
            waypoint.set_data([w[0]], [w[1]])
            arrow.set_positions(p[:2], p[:2] + h["force_n"][i, :2] * 1e9 * 0.5)
            arrow.set_visible(np.linalg.norm(h["force_n"][i]) > 1e-14)
            finished = now >= h["time_s"][-1]
            outcome = "TARGET REACHED" if case["summary"]["target_success"] else "WALL-PROXY VIOLATION"
            status.set_text(f"{outcome if finished else h['reason'][i]}\n"
                            f"Sample: {h['time_s'][i]:.2f} s | waypoint {h['waypoint_index'][i]}\n"
                            f"Force: {np.linalg.norm(h['force_n'][i]) * 1e9:.2f} nN")
        return []

    animation = FuncAnimation(fig, update, frames=np.linspace(0, end, 140), interval=80, blit=False)
    animation.save(output_path, writer=PillowWriter(fps=12), dpi=90)
    plt.close(fig)


def animate_physiological_pair(cases, labels, output_path, title, frames=120, fps=12, grid_step_m=0.2e-3):
    """Side-by-side animation of two physiological-scale trials on the flow-speed map.

    Arrows are scaled to the force cap (full cap = 3 mm). Finished trials freeze.
    Simulation only.
    """
    from src.flow import prescribed_flow

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    fig.subplots_adjust(left=0.06, right=0.98, top=0.8, bottom=0.2, wspace=0.18)
    xs = np.arange(0, 22e-3, grid_step_m)
    ys = np.arange(-8e-3, 8e-3, grid_step_m)
    vessel = YVessel()
    artists = []
    for ax, case, label in zip(axes, cases, labels):
        c = case["config"]
        field = np.full((len(ys), len(xs)), np.nan)
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                point = np.array([x, y, y / 2])
                if vessel.clearance(point) >= 0:
                    field[j, i] = np.linalg.norm(prescribed_flow(
                        point, c["flow_speed_m_s"], c["flow_model"], c["flow_transition_length_m"],
                        c["flow_branch_width_m"], occluded_branch=c.get("occluded_branch") or None))
        # Shift the scale so stagnant lumen (an occluded branch) still reads as vessel, not background.
        top = np.nanmax(field) if np.isfinite(field).any() and np.nanmax(field) > 0 else 1.0
        ax.imshow(field, extent=(0, 22, -8, 8), origin="lower", cmap="Greys", alpha=0.55, aspect="equal",
                  vmin=-0.3 * top, vmax=top)
        target = vessel.upper_target if c["branch"] == "upper" else vessel.lower_target
        ax.scatter(target[0] * 1e3, target[1] * 1e3, marker="*", s=160, color="#E0A800", edgecolor="black", zorder=4)
        ax.set(xlim=(0, 22), ylim=(-8, 8), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_title(label, fontsize=11)
        trail, = ax.plot([], [], color=COLORS[0], linewidth=2)
        truth, = ax.plot([], [], "o", color=COLORS[0], markersize=7, zorder=5)
        estimate, = ax.plot([], [], "x", color="#D68A12", markersize=8, zorder=5)
        frame_mark, = ax.plot([], [], "o", markersize=16, markerfacecolor="none", markeredgecolor="#2F5BD3",
                              markeredgewidth=2, zorder=6)
        arrow = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=14, color="#C54B43", linewidth=2,
                                zorder=6)
        ax.add_patch(arrow)
        status = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", fontsize=9,
                         bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
        artists.append((trail, truth, estimate, frame_mark, arrow, status))
    end = max(case["history"]["time_s"][-1] for case in cases)
    slowdown = (frames / fps) / end
    clock = fig.text(0.5, 0.85, "", ha="center", fontsize=12)
    fig.suptitle(title, fontsize=14, weight="bold")
    fig.text(0.06, 0.04, "Dot: particle (red = actuation stopped). Orange x: controller's estimate. Blue ring: a new "
             "frame reached the controller.\nRed arrow: magnetic force (full length 3 mm = force cap). Grey shade: "
             f"flow speed; XY projection. Played about {slowdown:.1f}× slower than real time. Simulation only.",
             fontsize=8.5)

    def update(now):
        clock.set_text(f"t = {now * 1e3:.0f} ms")
        for case, group in zip(cases, artists):
            h, s = case["history"], case["summary"]
            cap = s.get("physics", {}).get("force_cap_n", case["config"]["max_force_n"])
            i = max(0, np.searchsorted(h["time_s"], now, side="right") - 1)
            p, e = h["true_position_m"][i] * 1e3, h["estimated_position_m"][i] * 1e3
            trail_, truth_, estimate_, frame_, arrow_, status_ = group
            step = max(1, i // 400)
            trail_.set_data(h["true_position_m"][:i + 1:step, 0] * 1e3, h["true_position_m"][:i + 1:step, 1] * 1e3)
            truth_.set_data([p[0]], [p[1]])
            truth_.set_color("#C54B43" if h["reason"][i] in STOP_REASONS else COLORS[0])
            estimate_.set_data([e[0]], [e[1]])
            age = h["measurement_age_s"][i]
            # A frame arrives when its age equals the latency; show the ring for one animation frame.
            fresh = np.isfinite(age) and age - case["config"]["latency_s"] < end / frames
            frame_.set_data([p[0]] if fresh else [], [p[1]] if fresh else [])
            force = h["force_n"][i, :2] / cap * 3.0
            arrow_.set_positions(p[:2], p[:2] + force)
            arrow_.set_visible(np.linalg.norm(h["force_n"][i]) > 1e-15)
            finished = now >= h["time_s"][-1]
            outcome = ("TARGET REACHED" if s["target_success"] else "WALL CONTACT" if s["wall_collision"]
                       else "WRONG BRANCH" if s["wrong_branch"] else "TIME LIMIT")
            status_.set_text(f"{outcome if finished else h['reason'][i]}\n"
                             f"t = {h['time_s'][i] * 1e3:.0f} ms | |F| = {np.linalg.norm(h['force_n'][i]) * 1e9:.0f} nN")
        return []

    animation = FuncAnimation(fig, update, frames=np.linspace(0, end, frames), interval=1000 / fps, blit=False)
    animation.save(output_path, writer=PillowWriter(fps=fps), dpi=80)
    plt.close(fig)
