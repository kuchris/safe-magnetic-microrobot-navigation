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
    parser.add_argument("--start-mm", type=float, nargs=3, default=(0.5, 0.0, 0.0), help="release point [mm]")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="outputs/21_physiological_trial")
    args = parser.parse_args()
    result = run_trial(TrialConfig(
        seed=args.seed, branch=args.branch, duration_s=args.duration,
        flow_model="poiseuille", flow_speed_m_s=args.speed,
        particle_radius_m=args.radius_um * 1e-6, max_gradient_t_m=args.gradient,
        frame_rate_hz=args.frame_rate, latency_s=args.latency, particle_inertia=args.inertia,
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
