"""Retrospective forecast diagnostics; never used to select control commands."""

import numpy as np


def forecast_metrics(history, drag_n_s_m, horizons_s=(0.1, 0.5)):
    """Compare held-command and recorded-command forecasts against realized paths.

    Score every tenth physics sample after 1 s, only with an exact available
    endpoint. Recorded future commands remove a known intervention confound;
    they are an offline diagnostic, not information available to a forecast.
    """
    h = history
    t, force = h["time_s"], h["command_force_n"]
    previous = np.vstack([np.zeros(3), force[:-1]])
    flow = h["estimated_velocity_m_s"] - previous / drag_n_s_m
    integral = np.vstack([np.zeros(3), np.cumsum(np.diff(t)[:, None] * force[:-1] / drag_n_s_m, axis=0)])
    starts = np.arange(0, len(t), 10)
    starts = starts[(t[starts] >= 1) & np.isfinite(flow[starts]).all(axis=1)]
    rows = []
    for horizon in horizons_s:
        ends = np.searchsorted(t, t[starts] + horizon - 1e-12)
        valid = ends < len(t)
        i, j = starts[valid], ends[valid]
        exact = np.isclose(t[j] - t[i], horizon, atol=1e-10, rtol=0)
        i, j = i[exact], j[exact]
        held = h["estimated_position_m"][i] + horizon * (flow[i] + force[i] / drag_n_s_m)
        recorded = h["estimated_position_m"][i] + horizon * flow[i] + integral[j] - integral[i]
        past = np.searchsorted(t, t[i] - 0.1, side="right") - 1
        changed = np.linalg.norm(force[i] - force[past], axis=1) >= 0.5e-9
        for name, mask in (("all", np.ones(len(i), dtype=bool)), ("recent_command_change", changed)):
            def rmse(error):
                return float(np.sqrt(np.mean(np.sum(error[mask] ** 2, axis=1)))) if mask.any() else None
            rows.append({"horizon_s": horizon, "subset": name, "samples": int(mask.sum()),
                         "held_command_RMSE_m": rmse(held - h["true_position_m"][j]),
                         "recorded_command_RMSE_m": rmse(recorded - h["true_position_m"][j]),
                         "flow_RMSE_m_s": rmse(flow[i] - h["flow_velocity_m_s"][i])})
    return rows
