"""Run with python -m simulations.27_steering_animation --help.

Animates experiment 23's clearest contrast: the same held-out occluded-target cell
(99% flow reduction, 15 fps, lower branch, seed 3) under the baseline P0 and the
command-aware P2 policy. Simulation only.
"""

import argparse
from pathlib import Path

from src.delay_aware_study import cell_config
from src.experiment import run_trial
from src.replay_plotting import animate_physiological_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/27_steering_animation/occluded_p0_vs_p2.gif")
    parser.add_argument("--frames", type=int, default=120)
    args = parser.parse_args()
    cell = dict(flow_reduction=0.99, frame_rate_hz=15.0, occlusion="target_occluded", branch="lower", seed=3)
    cases = [run_trial(cell_config(policy=p, **cell)) for p in ("P0_kinematic_delay_gain", "P2_predictor_fast_gain")]
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    animate_physiological_pair(cases, ["P0: kinematic estimator, delay-limited gain",
                                       "P2: command-aware estimator, actuation-limited gain"], path,
                               "Occluded lower branch | 99% flow reduction | 15 fps | seed 3", frames=args.frames)
    print(path)


if __name__ == "__main__":
    main()
