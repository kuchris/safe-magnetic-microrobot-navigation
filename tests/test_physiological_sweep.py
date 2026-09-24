import json
from pathlib import Path

import numpy as np
import pytest

from src.physiological_sweep import (DELAY_GAIN_FRACTION, DURATION_S, POLICIES, aggregate, all_cells,
                                     cell_config, delay_limited_gain, render_report, trial_record)

ARCHIVE = Path(__file__).parents[1] / "docs/results/physiological_sweep/trials.json"
FACTORS = ("flow_reduction", "frame_rate_hz", "material", "occlusion", "policy", "branch", "seed")


def archived(**factors):
    records = json.loads(ARCHIVE.read_text())
    return next(r for r in records if all(r[k] == v for k, v in factors.items()))


def test_cell_config_maps_each_factor():
    config = cell_config(0.99, 7.5, "composite", "target_occluded", "gated_delay_gain_hold", "lower", 2)
    assert config.flow_speed_m_s == pytest.approx(0.003)
    assert config.frame_rate_hz == 7.5 and config.seed == 2 and config.branch == "lower"
    assert config.occluded_branch == "lower" and config.gravity_compensation
    assert config.particle_density_kg_m3 == 2000.0 and config.duration_s == DURATION_S[0.99]
    assert config.gain_saturation_distance_m == 0 and config.gain_n_per_m == pytest.approx(
        delay_limited_gain(config))
    toy = cell_config(0.0, 15.0, "ndfeb", "patent", "gated_toy_gain", "upper", 0)
    assert toy.gain_saturation_distance_m == 1.5e-3 and toy.occluded_branch == ""
    assert cell_config(0.0, 15.0, "ndfeb", "patent", "passive", "upper", 0).control_mode == "passive"
    with pytest.raises(ValueError):
        cell_config(0.0, 15.0, "ndfeb", "patent", "mpc", "upper", 0)


def test_delay_limited_gain_formula():
    config = cell_config(0.9, 15.0, "ndfeb", "patent", "gated_delay_gain", "upper", 0)
    drag = 6 * np.pi * 3.5e-3 * 100e-6
    assert delay_limited_gain(config) == pytest.approx(DELAY_GAIN_FRACTION * drag / (0.05 + 1 / 15))


def test_full_grid_size():
    assert len(all_cells((0, 1, 2))) == 3 * 3 * 2 * 2 * len(POLICIES) * 2 * 3


@pytest.mark.parametrize("factors", [
    # Pure NdFeB sediments to the wall before the first frame.
    dict(flow_reduction=0.9, frame_rate_hz=15.0, material="ndfeb", occlusion="patent",
         policy="gated_delay_gain_hold", branch="upper", seed=0),
    # Occluded target: the flow carries the particle into the patent branch.
    dict(flow_reduction=0.9, frame_rate_hz=30.0, material="composite", occlusion="target_occluded",
         policy="gated_toy_gain", branch="lower", seed=1),
])
def test_archived_sweep_cells_reproduce(factors):
    record, reference = trial_record(factors), archived(**factors)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used",
                "terminal_wall_feature", "reason_counts"):
        assert record[key] == reference[key], key
    for key in ("elapsed_time_s", "closest_target_approach_m", "peak_force_fraction"):
        assert record[key] == pytest.approx(reference[key], rel=1e-8, abs=1e-15), key


def test_archived_success_cell_reproduces():
    factors = dict(flow_reduction=0.99, frame_rate_hz=30.0, material="composite", occlusion="patent",
                   policy="gated_delay_gain_hold", branch="upper", seed=1)
    record, reference = trial_record(factors), archived(**factors)
    assert record["target_success"] and reference["target_success"]
    assert record["elapsed_time_s"] == pytest.approx(reference["elapsed_time_s"], rel=1e-8)
    assert record["frames_used"] == reference["frames_used"] > 20


def test_aggregate_and_report_on_synthetic_records():
    base = dict(flow_reduction=0.9, frame_rate_hz=15.0, material="composite", occlusion="patent",
                policy="passive", branch="upper", wrong_branch=False, timeout=False, frames_used=3,
                peak_force_fraction=0.0, elapsed_time_s=0.2, terminal_wall_feature="none")
    records = [dict(base, seed=0, target_success=True, wall_collision=False, closest_target_approach_m=4e-4),
               dict(base, seed=1, target_success=False, wall_collision=True, closest_target_approach_m=2e-3)]
    (row,) = aggregate(records)
    assert row["trials"] == 2 and row["outcomes"]["target_success"]["count"] == 1
    assert row["closest_target_approach_m"] == {"median": pytest.approx(1.2e-3), "min": pytest.approx(4e-4)}
    report = render_report([row], (0, 1))
    assert "| 90% | 15 | composite | patent | passive | 2 | 50 [" in report
