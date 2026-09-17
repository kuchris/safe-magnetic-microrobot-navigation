"""Lesson 01 experiment: flow + magnetic drift in free space."""

import numpy as np

from src.particle import Particle


def main():
    particle = Particle(
        radius_m=100e-6,
        viscosity_pa_s=3.5e-3,
        position_m=np.zeros(3),
    )

    # Toy values chosen for learning, not clinical design.
    flow = np.array([1.0e-3, 0.0, 0.0])

    # Choose force so magnetic drift is +0.5 mm/s in y.
    desired_magnetic_drift = np.array([0.0, 0.5e-3, 0.0])
    magnetic_force = particle.drag_coefficient * desired_magnetic_drift

    dt = 0.01
    duration = 2.0
    steps = int(duration / dt)

    for _ in range(steps):
        particle.step(dt, flow, magnetic_force)

    print("drag coefficient [N s/m]:", particle.drag_coefficient)
    print("final position [mm]:", particle.position_m * 1e3)
    print("expected approx [mm]: [2, 1, 0]")


if __name__ == "__main__":
    main()
