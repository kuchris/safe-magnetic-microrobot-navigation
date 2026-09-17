"""Closed-loop navigation with noisy localization and fail-safe actuation."""

import numpy as np
import matplotlib.pyplot as plt

from src.controller import bounded_target_force
from src.flow import centerline_flow
from src.localization import NoisyPositionSensor, PositionKalmanFilter
from src.particle import Particle
from src.safety import SafetySupervisor
from src.vessel import YVessel


def main():
    rng = np.random.default_rng(7)
    vessel = YVessel(radius_m=1.5e-3)
    particle = Particle(
        radius_m=0.10e-3,
        viscosity_pa_s=3.5e-3,
        position_m=np.array([0.5e-3, 0.0, 0.0]),
    )
    target = vessel.upper_target
    sensor = NoisyPositionSensor(sigma_m=0.15e-3, rng=rng)
    kf = PositionKalmanFilter(sensor.measure(particle.position_m))
    safety = SafetySupervisor(max_sigma_m=0.35e-3, min_clearance_m=0.20e-3)

    dt = 0.005
    true_path = [particle.position_m.copy()]
    estimated_path = [kf.x.copy()]
    stop_count = 0
    min_true_clearance = float("inf")

    for _ in range(6000):
        # Use only the current estimate to choose the next action.
        flow_est = centerline_flow(kf.x)
        estimate = kf.x.copy()

        requested_force = bounded_target_force(estimate, target)
        allowed, reason, _ = safety.evaluate(
            estimate, kf.sigma_max_m, vessel, particle.radius_m
        )
        force = safety.filter_force(requested_force, allowed)
        if not allowed:
            stop_count += 1

        true_flow = centerline_flow(particle.position_m)
        particle.step(dt, true_flow, force)
        # Predict including commanded magnetic drift; update at the new time.
        kf.predict(displacement_m=(flow_est + force / particle.drag_coefficient) * dt)
        estimate = kf.update(sensor.measure(particle.position_m))
        true_path.append(particle.position_m.copy())
        estimated_path.append(estimate.copy())

        true_clearance = vessel.clearance(particle.position_m, particle.radius_m)
        min_true_clearance = min(min_true_clearance, true_clearance)
        if true_clearance < 0:
            print("STOP: true wall violation")
            break
        if np.linalg.norm(particle.position_m - target) < 0.4e-3:
            break

    true_xyz = np.asarray(true_path) * 1e3
    est_xyz = np.asarray(estimated_path) * 1e3
    reached = np.linalg.norm(particle.position_m - target) < 0.4e-3

    print("target reached:", reached)
    print("safety stop frames:", stop_count)
    print("minimum true clearance [mm]:", min_true_clearance * 1e3)
    print("final localization sigma [mm]:", kf.sigma_max_m * 1e3)

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.plot(true_xyz[:, 0], true_xyz[:, 1], true_xyz[:, 2], label="true")
    ax.plot(est_xyz[:, 0], est_xyz[:, 1], est_xyz[:, 2], linestyle="--", label="estimated")
    for segment in vessel.segments:
        line = np.vstack([segment.start_m, segment.end_m]) * 1e3
        ax.plot(line[:, 0], line[:, 1], line[:, 2], linestyle=":")
    ax.scatter(*(target * 1e3), marker="x", s=80, label="target")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_zlabel("z [mm]")
    ax.legend()
    plt.show()


if __name__ == "__main__":
    main()
