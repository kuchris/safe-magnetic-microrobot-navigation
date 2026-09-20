"""Ground-truth replay diagnostics; never used to select control actions."""

import numpy as np

from src.flow import centerline_flow
from src.particle import Particle
from src.planner import wrong_branch
from src.vessel import YVessel


def wall_feature(position_m, vessel, particle_radius_m=0.1e-3):
    """Identify the capsule feature responsible for a sampled proxy violation.

    This labels the existing proxy, not exact union contact. An outlet cap is
    isolated only when the point would fit inside that outlet's extended tube.
    """
    clearances = [s.wall_clearance(position_m, particle_radius_m) for s in vessel.segments]
    if max(clearances) > 0:
        return "none"
    index = int(np.argmax(clearances))
    segment = vessel.segments[index]
    axis = segment.end_m - segment.start_m
    fraction = np.dot(position_m - segment.start_m, axis) / np.dot(axis, axis)
    radial = np.linalg.norm(position_m - segment.start_m - fraction * axis)
    if index > 0 and fraction > 1 and radial <= segment.radius_m - particle_radius_m:
        return "closed_outlet_cap_proxy"
    if index == 0 and fraction < 0:
        return "closed_inlet_cap_proxy"
    if 0 <= fraction <= 1:
        return "capsule_sidewall_proxy"
    return "endcap_or_overlap_proxy"


def analyze_trial(result):
    h, config = result["history"], result["config"]
    vessel = YVessel()
    particle = Particle(0.1e-3, 3.5e-3)
    p, time = h["true_position_m"], h["time_s"]
    junction_x = vessel.segments[0].end_m[0]

    def snapshot(mask):
        indices = np.flatnonzero(mask)
        if not len(indices):
            return None
        i = indices[0]
        estimate = h["estimated_position_m"][i]
        flow = centerline_flow(p[i], speed_m_s=config["flow_speed_m_s"])
        return {"time_s": float(time[i]), "position_m": p[i].tolist(),
                "estimated_position_m": estimate.tolist() if np.isfinite(estimate).all() else None,
                "waypoint_index": int(h["waypoint_index"][i]),
                "waypoint_m": h["waypoint_m"][i].tolist(),
                "force_n": h["force_n"][i].tolist(), "reason": str(h["reason"][i]),
                "clearance_m": float(h["true_clearance_m"][i]),
                "prescribed_flow_m_s": flow.tolist(),
                "nominal_net_velocity_m_s": particle.velocity(flow, h["force_n"][i]).tolist()}

    wrong = np.array([wrong_branch(point, vessel, config["branch"]) for point in p])
    stop = np.isin(h["reason"], ["tracking_lost", "localization_uncertain", "wall_margin_low"])
    last_active = np.flatnonzero(~stop)
    persistent_stop = float(time[last_active[-1] + 1] if len(last_active) else time[0]) if stop[-1] else None
    return {
        "junction_crossing": snapshot(p[:, 0] >= junction_x),
        "branch_waypoint_selected": snapshot(h["waypoint_m"][:, 0] > junction_x),
        "wrong_branch_confirmed": snapshot(wrong),
        "first_wall_stop_after_junction": snapshot((p[:, 0] >= junction_x) & (h["reason"] == "wall_margin_low")),
        "first_wall_violation": snapshot(h["true_clearance_m"] <= 0),
        "terminal_wall_feature": wall_feature(p[-1], vessel),
        "persistent_stop_from_s": persistent_stop,
        "target_success": result["summary"]["target_success"],
        "elapsed_time_s": float(time[-1]),
    }
