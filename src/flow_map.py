"""A measured flow map for the controller: the plant's time-mean field sampled on a
voxel grid, with fixed per-voxel noise, times the (assumed exact) cardiac waveform.

This stands in for an image-based flow measurement such as 4D flow MRI. Voxel
size and noise level are assumed values, not scanner specifications. Trilinear
interpolation blurs the parabolic profile and the flow split (partial volume).
"""

from dataclasses import replace

import numpy as np

from src.flow import pulsatile_speed
from src.validation import nonnegative, vector
from src.vessel import YVessel

# Bounding box of the default Y-vessel lumen, with one radius of margin [m].
BOX_MIN = np.array([-1.5e-3, -7.6e-3, -4.6e-3])
BOX_MAX = np.array([21.6e-3, 7.6e-3, 4.6e-3])


_NOISELESS_CACHE = {}


def measured_flow_map(config, voxel_m, noise_fraction=0.0):
    """Map for a trial. Noiseless maps depend only on the flow setup and are reused."""
    if noise_fraction > 0:
        # Its own stream (spawn key 3) so the sensor, calibration and flow draws are unchanged.
        rng = np.random.default_rng(np.random.SeedSequence(config.seed, spawn_key=(3,)))
        return MeasuredFlowMap(config, voxel_m, noise_fraction, rng)
    key = (voxel_m, config.flow_model, config.flow_speed_m_s, config.flow_pulsatility, config.cardiac_period_s,
           config.cardiac_phase, config.occluded_branch, config.flow_transition_length_m, config.flow_branch_width_m)
    if key not in _NOISELESS_CACHE:
        _NOISELESS_CACHE[key] = MeasuredFlowMap(config, voxel_m)
    return _NOISELESS_CACHE[key]


class MeasuredFlowMap:
    def __init__(self, config, voxel_m, noise_fraction=0.0, rng=None):
        from src.experiment import plant_flow_function  # local import avoids a cycle
        self.voxel = nonnegative(voxel_m, "voxel_m", positive=True)
        self.noise_fraction = nonnegative(noise_fraction, "noise_fraction")
        self.config = config
        steady = plant_flow_function(replace(config, flow_pulsatility=0.0, cardiac_phase=0.0))
        axes = [np.arange(lo, hi + self.voxel / 2, self.voxel) for lo, hi in zip(BOX_MIN, BOX_MAX)]
        self.origin = np.array([a[0] for a in axes])
        self.shape = np.array([len(a) for a in axes])
        grid = np.zeros((*self.shape, 3))
        vessel = YVessel()
        inside = np.zeros(self.shape, dtype=bool)
        for i, x in enumerate(axes[0]):
            for j, y in enumerate(axes[1]):
                for k, z in enumerate(axes[2]):
                    point = np.array([x, y, z])
                    if vessel.clearance(point) > -self.voxel:
                        grid[i, j, k] = steady(point, 0.0)
                        inside[i, j, k] = vessel.clearance(point) >= 0
        if self.noise_fraction > 0:
            rng = np.random.default_rng() if rng is None else rng
            sigma = self.noise_fraction * 2 * config.flow_speed_m_s  # fraction of the centerline mean
            grid[inside] += rng.normal(0.0, sigma, (int(inside.sum()), 3))
        self.grid = grid

    def steady(self, position_m):
        p = vector(position_m)
        index = np.clip((p - self.origin) / self.voxel, 0, self.shape - 1 - 1e-9)
        i0 = np.floor(index).astype(int)
        f = index - i0
        cube = self.grid[i0[0]:i0[0] + 2, i0[1]:i0[1] + 2, i0[2]:i0[2] + 2]
        wx = np.array([1 - f[0], f[0]])[:, None, None, None]
        wy = np.array([1 - f[1], f[1]])[None, :, None, None]
        wz = np.array([1 - f[2], f[2]])[None, None, :, None]
        return np.sum(cube * wx * wy * wz, axis=(0, 1, 2))

    def __call__(self, position_m, time_s):
        c = self.config
        factor = pulsatile_speed(1.0, time_s + c.cardiac_phase * c.cardiac_period_s, c.flow_pulsatility,
                                 c.cardiac_period_s)
        return factor * self.steady(position_m)
