"""Toy flow fields for the simulation.

This is deliberately not a patient-specific blood-flow model.
"""

import numpy as np


def centerline_flow(position_m, junction_x_m=10e-3, speed_m_s=1e-3):
    """Piecewise flow following the inlet then nearest Y branch direction."""
    p = np.asarray(position_m, dtype=float)
    if p[0] < junction_x_m:
        direction = np.array([1.0, 0.0, 0.0])
    elif p[1] >= 0:
        direction = np.array([10.0, 6.0, 3.0])
    else:
        direction = np.array([10.0, -6.0, -3.0])
    direction /= np.linalg.norm(direction)
    return speed_m_s * direction
