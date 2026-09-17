"""MVP: navigate a simulated particle toward the upper branch of a 3D Y vessel."""

import numpy as np
import matplotlib.pyplot as plt

from src.controller import bounded_target_force
from src.flow import centerline_flow
from src.particle import Particle
from src.vessel import YVessel


def main():
    vessel = YVessel(radius_m=1.5e-3)
    particle = Particle(
        radius_m=0.10e-3,
        viscosity_pa_s=3.5e-3,
        position_m=np.array([0.5e-3, 0.0, 0.0]),
    )
    target = vessel.upper_target

    dt = 0.005
    max_steps = 6000
    trajectory = [particle.position_m.copy()]
    min_clearance = float("inf")
    collided = False

    for _ in range(max_steps):
        flow = centerline_flow(particle.position_m)
        force = bounded_target_force(particle.position_m, target)
        particle.step(dt, flow, force)
        trajectory.append(particle.position_m.copy())

        clearance = vessel.clearance(particle.position_m, particle.radius_m)
        min_clearance = min(min_clearance, clearance)
        if clearance < 0:
            collided = True
            break
        if np.linalg.norm(particle.position_m - target) < 0.4e-3:
            break

    xyz = np.asarray(trajectory) * 1e3
    print("target reached:", np.linalg.norm(particle.position_m - target) < 0.4e-3)
    print("wall violation:", collided)
    print("minimum clearance [mm]:", min_clearance * 1e3)
    print("steps:", len(trajectory) - 1)

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], label="particle")
    for segment in vessel.segments:
        line = np.vstack([segment.start_m, segment.end_m]) * 1e3
        ax.plot(line[:, 0], line[:, 1], line[:, 2], linestyle="--")
    ax.scatter(*(target * 1e3), marker="x", s=80, label="target")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_zlabel("z [mm]")
    ax.legend()
    plt.show()


if __name__ == "__main__":
    main()
