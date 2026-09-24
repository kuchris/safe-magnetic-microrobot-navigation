"""One physiological-scale trial with diagnostics. Run with python -m simulations.21_physiological_trial --help.

Defaults follow docs/14: M1-like mean flow 0.3 m/s (sourced), a 100 µm NdFeB
sphere (material assumed) and a best-case 1 T/m gradient cap (eMNS reference).
Simulation only; not a device model and not a clinical claim.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from src.experiment import TrialConfig, run_trial
from src.plotting import plot_physics_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speed", type=float, default=0.3, help="cross-sectional mean flow [m/s]")
    parser.add_argument("--radius-um", type=float, default=100.0, help="particle radius [µm]")
    parser.add_argument("--gradient", type=float, default=1.0, help="gradient cap [T/m]")
    parser.add_argument("--frame-rate", type=float, default=20.0, help="imaging frame rate [Hz]")
    parser.add_argument("--latency", type=float, default=0.05, help="imaging latency [s]")
    parser.add_argument("--duration", type=float, default=0.2, help="time limit [s]")
    parser.add_argument("--branch", choices=["upper", "lower"], default="upper")
    parser.add_argument("--inertia", action="store_true", help="reduced Maxey-Riley particle (stage 2c)")
    parser.add_argument("--fluid-acceleration", action="store_true",
                        help="add the (3/2) m_f Du/Dt force; requires --inertia (stage 2d)")
    parser.add_argument("--pulsatility", type=float, default=0.0, help="amplitude A, PI = 2A (stage 2d)")
    parser.add_argument("--period", type=float, default=1.0, help="cardiac period [s] (assumed 60 bpm)")
    parser.add_argument("--phase", type=float, default=0.0, help="release phase in [0, 1); 0.25 = peak")
    parser.add_argument("--gravity", type=float, default=0.0, help="gravity [m/s^2]; 9.81 enables (stage 2e)")
    parser.add_argument("--gravity-dir", type=float, nargs=3, default=(0.0, 0.0, -1.0),
                        help="gravity direction in the vessel frame (assumed)")
    parser.add_argument("--density", type=float, default=7500.0, help="particle density [kg/m^3] (assumed)")
    parser.add_argument("--magnetic-fraction", type=float, default=1.0,
                        help="NdFeB volume fraction of a composite (assumed)")
    parser.add_argument("--sedimentation-check", action="store_true", help="diagnostic flag (stage 2e)")
    parser.add_argument("--gravity-compensation", action="store_true", help="hold against weight (stage 2e)")
    parser.add_argument("--start-mm", type=float, nargs=3, default=(0.5, 0.0, 0.0), help="release point [mm]")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="outputs/21_physiological_trial")
    args = parser.parse_args()
    result = run_trial(TrialConfig(
        seed=args.seed, branch=args.branch, duration_s=args.duration,
        flow_model="poiseuille", flow_speed_m_s=args.speed,
        particle_radius_m=args.radius_um * 1e-6, max_gradient_t_m=args.gradient,
        frame_rate_hz=args.frame_rate, latency_s=args.latency, particle_inertia=args.inertia,
        fluid_acceleration_force=args.fluid_acceleration, flow_pulsatility=args.pulsatility,
        cardiac_period_s=args.period, cardiac_phase=args.phase,
        gravity_m_s2=args.gravity, gravity_direction=tuple(args.gravity_dir),
        particle_density_kg_m3=args.density, magnetic_volume_fraction=args.magnetic_fraction,
        sedimentation_check=args.sedimentation_check,
        gravity_compensation=args.gravity_compensation,
        start_m=tuple(v * 1e-3 for v in args.start_mm)))
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(json.dumps(
        {"config": result["config"], "summary": result["summary"]}, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(path / "history.npz", **result["history"])
    plot_physics_trial(result, path / "physics_diagnostics.png")
    print(json.dumps(result["summary"], indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
