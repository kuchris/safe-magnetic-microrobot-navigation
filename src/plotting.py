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


def frame_timeline(result):
    """Nominal capture/delivery times and the valid frames the controller actually used.

    Nominal times follow the configured frame rate and latency (dropouts are not
    reconstructed). Delivered frames are recovered from the logged measurement
    age, so they include only valid observations that reached the estimator.
    """
    h, c = result["history"], result["config"]
    end = float(h["time_s"][-1])
    period = 1 / c["frame_rate_hz"]
    captures = np.arange(0, end + 1e-12, period)
    age = h["measurement_age_s"]
    finite = np.isfinite(age)
    capture_of_latest = np.round(h["time_s"][finite] - age[finite], 12)
    used, first = np.unique(capture_of_latest, return_index=True)
    return {"end_s": end, "nominal_capture_s": captures,
            "nominal_delivery_s": captures + c["latency_s"],
            "delivered_capture_s": used, "delivered_at_s": h["time_s"][finite][first]}


def plot_physics_trial(result, output_path, grid_step_m=0.1e-3):
    """Diagnostics for physiological-scale trials: flow map, frame timing, profile, force.

    The flow map is the plane z = y/2, which contains all three centerlines,
    projected onto x-y. Legacy toy figures keep using plot_trial.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patheffects
    from src.feasibility import Material, magnetic_force_cap
    from src.flow import prescribed_flow

    h, c, s = result["history"], result["config"], result["summary"]
    vessel = YVessel()
    t_ms = h["time_s"] * 1e3
    truth = h["true_position_m"]
    radius = c.get("particle_radius_m", 0.1e-3)
    speed = c["flow_speed_m_s"]

    def flow_at(point):
        return prescribed_flow(point, speed, c["flow_model"], c["flow_transition_length_m"],
                               c["flow_branch_width_m"])

    fig = plt.figure(figsize=(14, 11), layout="constrained")
    grid = fig.add_gridspec(3, 2)

    # Flow map with the particle path.
    ax = fig.add_subplot(grid[:2, 0])
    xs = np.arange(0, 22e-3 + grid_step_m / 2, grid_step_m)
    ys = np.arange(-8e-3, 8e-3 + grid_step_m / 2, grid_step_m)
    field = np.full((len(ys), len(xs)), np.nan)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            point = np.array([x, y, y / 2])
            if vessel.clearance(point) >= 0:
                field[j, i] = np.linalg.norm(flow_at(point))
    mesh = ax.pcolormesh(xs * 1e3, ys * 1e3, field, shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, label="Flow speed [m/s]", orientation="horizontal", shrink=0.8)
    ax.plot(truth[:, 0] * 1e3, truth[:, 1] * 1e3, color="white", linewidth=2, label="True path",
            path_effects=[patheffects.withStroke(linewidth=4, foreground="black")])
    estimate = h["estimated_position_m"]
    if np.isfinite(estimate).all(axis=1).any():
        ax.plot(estimate[:, 0] * 1e3, estimate[:, 1] * 1e3, "--", color="tab:orange", label="Estimated")
    ax.scatter(*truth[0, :2] * 1e3, color="white", edgecolor="black", zorder=3, label="Start")
    end_marker = "o" if s["target_success"] else "X"
    ax.scatter(*truth[-1, :2] * 1e3, s=120, marker=end_marker, color="tab:red", edgecolor="white",
               zorder=3, label="End")
    target = vessel.upper_target if c["branch"] == "upper" else vessel.lower_target
    ax.scatter(*target[:2] * 1e3, marker="*", s=180, color="gold", edgecolor="black", zorder=3,
               label="Target")
    ax.set(xlabel="x [mm]", ylabel="y [mm]", xlim=(0, 22), ylim=(-8, 8),
           title="Flow speed, centerline plane z = y/2 (projected)")
    ax.set_aspect("equal")
    ax.legend(loc="lower left", fontsize=8, ncol=2)

    # Frame timing against progress: shows whether any observation arrives in time.
    ax = fig.add_subplot(grid[0, 1])
    frames = frame_timeline(result)
    progress = np.r_[0, np.cumsum(np.linalg.norm(np.diff(truth, axis=0), axis=1))] * 1e3
    ax.plot(t_ms, progress, color="tab:blue", label="Distance travelled")
    rug = ax.get_xaxis_transform()
    ax.scatter(frames["nominal_capture_s"] * 1e3, np.full(len(frames["nominal_capture_s"]), 0.04),
               marker="|", s=80, color="gray", transform=rug, label="Nominal capture")
    ax.scatter(frames["nominal_delivery_s"] * 1e3, np.full(len(frames["nominal_delivery_s"]), 0.1),
               marker="|", s=80, color="tab:purple", transform=rug, label="Nominal delivery")
    ax.axvline(frames["nominal_delivery_s"][0] * 1e3, color="tab:purple", linestyle="--",
               label=f"First delivery ({frames['nominal_delivery_s'][0] * 1e3:g} ms)")
    if len(frames["delivered_at_s"]):
        ax.scatter(frames["delivered_at_s"] * 1e3, np.interp(frames["delivered_at_s"], h["time_s"], progress),
                   color="tab:green", zorder=3, label="Frame used by controller")
        note = f"first frame used at {frames['delivered_at_s'][0] * 1e3:.1f} ms"
    else:
        note = "no frame reached the controller"
    outcome = ("target reached" if s["target_success"] else "wall collision" if s["wall_collision"]
               else "wrong branch" if s["wrong_branch"] else "time limit")
    if s["maximum_force_n"] == 0:
        outcome += " (no actuation)"
    ax.axvline(frames["end_s"] * 1e3, color="tab:red", linewidth=2, label=f"End: {outcome}")
    right = max(frames["end_s"], frames["nominal_delivery_s"][0]) * 1e3 * 1.08
    ax.set(xlabel="Time [ms]", ylabel="Distance [mm]", xlim=(0, right),
           title=f"Imaging timeline: {note}")
    ax.legend(fontsize=8, loc="upper left")

    # Velocity profile across the parent segment, with the reachable band for the center.
    ax = fig.add_subplot(grid[1, 1])
    parent = vessel.segments[0]
    rho = np.linspace(-parent.radius_m, parent.radius_m, 301)
    x_mid = 0.5 * (parent.start_m[0] + parent.end_m[0])
    profile = np.array([np.linalg.norm(flow_at([x_mid, r, 0])) for r in rho])
    amplitude = c.get("flow_pulsatility", 0.0)
    ax.plot(rho * 1e3, profile, color="tab:blue", label="Time mean" if amplitude > 0 else None)
    if amplitude > 0:
        ax.fill_between(rho * 1e3, profile * (1 - amplitude), profile * (1 + amplitude), color="tab:blue",
                        alpha=0.15, label=f"Cardiac range (A = {amplitude:g})")
    reach = parent.radius_m - radius
    ax.axvspan(-reach * 1e3, reach * 1e3, color="tab:blue", alpha=0.08,
               label=f"Reachable by center (r = {radius * 1e6:.0f} µm)")
    start_rho = np.linalg.norm(truth[0, 1:])
    ax.axvline(start_rho * 1e3, color="black", linestyle=":", label="Start offset")
    ax.set(xlabel="Radial position ρ [mm]", ylabel="Flow speed [m/s]",
           title=f"Parent-segment profile at x = {x_mid * 1e3:.0f} mm ({c['flow_model']})")
    ax.legend(fontsize=8)

    # Clearance.
    ax = fig.add_subplot(grid[2, 0])
    for key, label in (("true_clearance_m", "True proxy"), ("estimated_clearance_m", "Estimated proxy"),
                       ("robust_clearance_m", "Robust proxy")):
        if np.isfinite(h[key]).any():
            ax.plot(t_ms, h[key] * 1e3, label=label)
    ax.axhline(c["safety_margin_m"] * 1e3, color="tab:red", linestyle="--", label="Margin")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(xlabel="Time [ms]", ylabel="Clearance [mm]", title="Wall clearance")
    ax.legend(fontsize=8)

    # Force in physical units, with the equivalent gradient when capped in T/m.
    ax = fig.add_subplot(grid[2, 1])
    physics = s.get("physics", {})
    cap = physics.get("force_cap_n", c["max_force_n"])
    scale, unit = (1e6, "µN") if cap >= 1e-7 else (1e9, "nN")
    magnitude = np.linalg.norm(h["force_n"], axis=1)
    ax.plot(t_ms, magnitude * scale, color="black", label="Applied |F|")
    ax.axhline(cap * scale, color="tab:red", linestyle="--", label="Cap")
    peak = magnitude.max()
    share = f"{100 * peak / cap:.2g}% of cap" if cap > 0 else "no cap"
    ax.set(xlabel="Time [ms]", ylabel=f"Force [{unit}]",
           title=f"Magnetic force: peak {peak * 1e9:.3g} nN ({share})")
    ax.set_ylim(-0.05 * cap * scale, 1.15 * cap * scale)
    if c.get("max_gradient_t_m", 0) > 0:
        per_gradient = magnetic_force_cap(radius, 1.0, Material(
            magnetization_a_m=c["magnetization_a_m"],
            magnetic_volume_fraction=c["magnetic_volume_fraction"])) * scale
        ax.secondary_yaxis("right", functions=(lambda f: f / per_gradient, lambda g: g * per_gradient)) \
            .set_ylabel("Equivalent gradient [T/m]")
    ax.legend(fontsize=8)

    details = [f"U = {speed:g} m/s ({c['flow_model']})", f"r = {radius * 1e6:.0f} µm",
               f"cap = {cap * scale:.3g} {unit}", f"{c['frame_rate_hz']:g} Hz, latency {c['latency_s'] * 1e3:g} ms"]
    if "dt_s" in physics:
        details.append(f"dt = {physics['dt_s'] * 1e6:.1f} µs")
    if physics.get("maximum_step_radius_fraction") is not None:
        details.append(f"max step/R = {physics['maximum_step_radius_fraction']:.2g}")
    if c.get("flow_pulsatility", 0.0) > 0:
        details.append(f"pulsatile A = {c['flow_pulsatility']:g}, T = {c['cardiac_period_s']:g} s, "
                       f"phase {c.get('cardiac_phase', 0.0):g}, α = {physics['womersley_number']:.2g}")
    if "stokes_number" in physics:
        details.append(f"inertial: St = {physics['stokes_number']:.2g}, "
                       f"max Re_slip = {physics['maximum_slip_reynolds']:.2g}"
                       + (", +Du/Dt" if c.get("fluid_acceleration_force") else ""))
    else:
        details.append("overdamped")
    lines = [""]
    for item in details:
        lines[-1] = f"{lines[-1]} · {item}" if lines[-1] else item
        if len(lines[-1]) > 95:
            lines.append("")
    fig.suptitle(f"Seed {c['seed']} | {c['branch']} target | {outcome} at {frames['end_s'] * 1e3:.1f} ms"
                 f" | simulation only, no clinical validation\n" + "\n".join(l for l in lines if l), fontsize=11)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
