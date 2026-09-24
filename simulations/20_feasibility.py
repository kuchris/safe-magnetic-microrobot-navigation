"""Analytical feasibility map for steering into an occluded cerebral branch.

Sweeps particle radius and reports the magnetic gradient required to reach the
target-side wall before a bifurcation, the gradient needed to hold against
gravity, and dimensionless checks of the overdamped Stokes model.
No closed-loop simulation is run. Toy research estimate, not clinical guidance.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.feasibility import (Fluid, Material, Vessel, gravity_hold_gradient,
                             required_gradient_branch_entry, sedimentation_speed, validity)

SYSTOLIC_FACTOR = 1.6          # assumed peak/mean ratio, see docs
FLOW_REDUCTION = 0.1           # hypothetical 90% proximal flow reduction
STOKES_LIMIT = 0.1             # chosen threshold for the overdamped approximation
DIAMETER_RATIO_LIMIT = 0.25    # chosen threshold for "small relative to lumen"
SYSTEMS_T_M = {                # reported peak or typical gradients, see docs
    "Clinical MRI imaging gradients": 0.04,
    "Research MRI gradient platform": 0.40,
    "eMNS (double Navion, up to)": 1.0,
    "Permanent-magnet systems (up to)": 2.9,
}


def sweep(radii, vessel, material, fluid):
    gravity = gravity_hold_gradient(material, fluid)
    systolic = Vessel(vessel.radius_m, SYSTOLIC_FACTOR * vessel.mean_speed_m_s, vessel.approach_length_m)
    reduced = Vessel(vessel.radius_m, FLOW_REDUCTION * vessel.mean_speed_m_s, vessel.approach_length_m)
    rows = []
    for radius in radii:
        nominal = required_gradient_branch_entry(radius, vessel, material, fluid)
        worst = required_gradient_branch_entry(radius, systolic, material, fluid, start="far_wall")
        low = required_gradient_branch_entry(radius, reduced, material, fluid, start="far_wall")
        checks = validity(radius, vessel, material, fluid, nominal["lateral_speed_m_s"])
        rows.append({
            "radius_m": float(radius),
            "nominal_gradient_t_m": nominal["gradient_t_m"],
            "worst_gradient_t_m": worst["gradient_t_m"] + gravity,
            "reduced_flow_worst_gradient_t_m": low["gradient_t_m"] + gravity,
            "nominal_lateral_speed_m_s": nominal["lateral_speed_m_s"],
            "sedimentation_speed_m_s": sedimentation_speed(radius, material, fluid),
            **checks,
        })
    return rows, gravity


def windows(rows):
    """Smallest radius meeting each system's gradient and the model-validity limits."""
    result = {}
    for name, gradient in SYSTEMS_T_M.items():
        entry = {}
        for key in ("nominal_gradient_t_m", "worst_gradient_t_m", "reduced_flow_worst_gradient_t_m"):
            ok = [r["radius_m"] for r in rows if r[key] <= gradient]
            valid = [r for r in ok if validity_ok(rows, r)]
            entry[key] = {"min_radius_m": float(min(ok)) if ok else None,
                          "valid_radii_m": [float(min(valid)), float(max(valid))] if valid else None}
        result[name] = {"gradient_t_m": gradient, **entry}
    return result


def validity_ok(rows, radius):
    row = next(r for r in rows if r["radius_m"] == radius)
    return row["stokes_number"] <= STOKES_LIMIT and row["diameter_ratio"] <= DIAMETER_RATIO_LIMIT


def plot(rows, gravity, path):
    r_um = np.array([r["radius_m"] for r in rows]) * 1e6
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(8, 9), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 2]})
    ax.loglog(r_um, [r["nominal_gradient_t_m"] for r in rows], "k-", lw=2,
              label="Nominal: mean flow, centre start")
    ax.loglog(r_um, [r["worst_gradient_t_m"] for r in rows], "r-", lw=2,
              label=f"Worst: {SYSTOLIC_FACTOR}x mean, far-wall start, + gravity")
    ax.loglog(r_um, [r["reduced_flow_worst_gradient_t_m"] for r in rows], "b--", lw=1.5,
              label=f"Worst case with {int((1 - FLOW_REDUCTION) * 100)}% flow reduction (hypothetical)")
    ax.axhline(gravity, color="grey", ls=":", label=f"Gravity hold only ({gravity:.3f} T/m)")
    for (name, g), color in zip(SYSTEMS_T_M.items(), ["#8c564b", "#9467bd", "#2ca02c", "#ff7f0e"]):
        ax.axhline(g, color=color, lw=1)
        ax.text(r_um[0] * 1.1, g * 1.08, f"{name}: {g:g} T/m", color=color, fontsize=8)
    invalid = [r["stokes_number"] > STOKES_LIMIT or r["diameter_ratio"] > DIAMETER_RATIO_LIMIT
               for r in rows]
    first_invalid = r_um[np.argmax(invalid)] if any(invalid) else None
    if first_invalid is not None:
        for axis in (ax, bx):
            axis.axvspan(first_invalid, r_um[-1], color="grey", alpha=0.15)
        ax.text(first_invalid * 1.05, ax.get_ylim()[0] * 3, "Overdamped model\nnot valid here",
                fontsize=8, color="0.3")
    ax.set_ylabel("Required gradient |∇B| [T/m]")
    ax.set_title("Lateral steering into an occluded branch: NdFeB sphere, M1-like parent vessel")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, which="both", alpha=0.3)

    bx.loglog(r_um, [r["stokes_number"] for r in rows], label="Stokes number (inertia)")
    bx.loglog(r_um, [r["slip_reynolds"] for r in rows], label="Slip Reynolds (nominal steering)")
    bx.loglog(r_um, [r["shear_reynolds"] for r in rows], label="Wall-shear Reynolds")
    bx.axhline(STOKES_LIMIT, color="C0", ls=":", lw=1)
    bx.axhline(1.0, color="k", ls=":", lw=1)
    bx.set_xlabel("Particle radius [µm]")
    bx.set_ylabel("Dimensionless")
    bx.legend(fontsize=8)
    bx.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/20_feasibility")
    parser.add_argument("--vessel-radius-mm", type=float, default=1.5)
    parser.add_argument("--mean-speed-m-s", type=float, default=0.30)
    parser.add_argument("--approach-mm", type=float, default=10.0)
    args = parser.parse_args()
    vessel = Vessel(args.vessel_radius_mm * 1e-3, args.mean_speed_m_s, args.approach_mm * 1e-3)
    material, fluid = Material(), Fluid()
    radii = np.geomspace(5e-6, 500e-6, 121)
    rows, gravity = sweep(radii, vessel, material, fluid)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    data = {"vessel": vars(vessel), "material": vars(material), "fluid": vars(fluid),
            "systolic_factor": SYSTOLIC_FACTOR, "flow_reduction": FLOW_REDUCTION,
            "stokes_limit": STOKES_LIMIT, "diameter_ratio_limit": DIAMETER_RATIO_LIMIT,
            "gravity_hold_gradient_t_m": gravity, "windows": windows(rows), "rows": rows}
    (out / "feasibility.json").write_text(json.dumps(data, indent=2))
    plot(rows, gravity, out / "feasibility_map.png")
    print(f"gravity hold: {gravity:.4f} T/m")
    for name, w in data["windows"].items():
        print(name, {k: v for k, v in w.items() if k != "gradient_t_m"})
    print(f"saved to {out}")


if __name__ == "__main__":
    main()
