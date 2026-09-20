"""Replay identical observations and commands through two estimators, offline."""

import argparse
import json
from pathlib import Path
import numpy as np

from src.flow_estimation import CommandAwareEstimator
from src.imaging import BiplaneImager
from src.localization import BiplaneTriangulator, DelayedStateEstimator
from src.prediction_audit import forecast_metrics


def replay_estimators(config, history):
    sensor_seed, calibration_seed, _ = np.random.SeedSequence(config["seed"]).spawn(3)
    bias = np.random.default_rng(calibration_seed).normal(0, config["calibration_sigma_px"], (2, 2))
    imager = BiplaneImager(noise_sigma_px=config["noise_sigma_px"], frame_rate_hz=config["frame_rate_hz"],
        latency_s=config["latency_s"], dropout_probability=config["dropout_probability"],
        dropout_intervals=config["dropout_intervals"], calibration_bias_px=bias, rng=np.random.default_rng(sensor_seed))
    triangulator = BiplaneTriangulator(noise_sigma_px=config["noise_sigma_px"],
                                     calibration_sigma_px=config["calibration_sigma_px"])
    drag = 6 * np.pi * 3.5e-3 * 0.1e-3
    estimators = {"kinematic": DelayedStateEstimator(), "command_aware": CommandAwareEstimator(drag)}
    states = {mode: {"estimated_position_m": np.full_like(history["true_position_m"], np.nan),
                     "estimated_velocity_m_s": np.full_like(history["true_position_m"], np.nan)} for mode in estimators}
    for i, now in enumerate(history["time_s"]):
        # Truth regenerates the simulated camera only. Both filters receive the
        # same reconstructed observations and emitted commands from the archive.
        for frame in imager.advance(now, history["true_position_m"][i]):
            if frame.detector_px is not None:
                rec = triangulator.reconstruct(frame.detector_px)
                for estimator in estimators.values():
                    estimator.observe(rec, frame.captured_at_s, now)
        if i % 10 == 0:
            for mode, estimator in estimators.items():
                estimate = estimator.estimate(now)
                if estimate is not None:
                    states[mode]["estimated_position_m"][i] = estimate.estimated_position
                    states[mode]["estimated_velocity_m_s"][i] = estimate.estimated_velocity
        estimators["command_aware"].command(now, history["command_force_n"][i])
    np.testing.assert_allclose(states["kinematic"]["estimated_position_m"][::10],
                               history["estimated_position_m"][::10], atol=1e-15, rtol=0, equal_nan=True)
    return {mode: forecast_metrics(dict(history, **state), drag) for mode, state in states.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("piecewise", "smooth"), required=True)
    parser.add_argument("--input", default="outputs/13_predictive_control")
    parser.add_argument("--output", default="outputs/15_estimation_audit")
    args = parser.parse_args()
    root, output = Path(args.input), Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    source = json.loads((root / f"{args.model}.json").read_text())
    trials = [r for r in source["trials"] if r["config"]["prediction_horizon_s"] == 0.5]
    records = []
    for trial in trials:
        with np.load(root / "traces" / f"{trial['trace_id']}.npz") as history:
            metrics = replay_estimators(trial["config"], dict(history))
        records.append({"source_trace_id": trial["trace_id"], "config": trial["config"], "metrics": metrics})
        if len(records) % 10 == 0:
            print(f"{args.model}: audited {len(records)}/{len(trials)} fixed histories", flush=True)
    (output / f"{args.model}.json").write_text(json.dumps(
        {"source": str(root), "seeds": source["seeds"], "trials": records}, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
