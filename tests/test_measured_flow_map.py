from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, plant_flow_function, run_trial
from src.flow_map import MeasuredFlowMap, measured_flow_map
from src.flow_map_study import CONDITIONS, WORST, cell_config, cells, route_velocity_error
from src.presets import physiological_config

CONFIG = physiological_config("composite", flow_speed_m_s=0.03, model_flow_feedforward=True)


def test_map_matches_the_plant_on_grid_nodes_and_scales_with_the_pulse():
    flow_map = MeasuredFlowMap(CONFIG, 1.0e-3)
    plant = plant_flow_function(CONFIG)
    steady = plant_flow_function(replace(CONFIG, flow_pulsatility=0.0))
    node = flow_map.origin + np.array([6, 7, 4]) * flow_map.voxel  # a lumen node near the parent axis
    np.testing.assert_allclose(flow_map.steady(node), steady(node, 0.0), rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(flow_map(node, 0.25), plant(node, 0.25), rtol=1e-12, atol=1e-15)


def test_finer_maps_are_closer_to_the_plant():
    errors = [route_velocity_error(c, 0.9, "patent") for c in ("map_0.25mm", "map_0.5mm", "map_1.0mm")]
    assert errors == sorted(errors) and errors[0] < 1e-3
    assert route_velocity_error("exact", 0.9, "patent") == 0.0


def test_noise_is_seeded_per_trial_and_zero_mean():
    a = measured_flow_map(replace(CONFIG, seed=3), 1.0e-3, 0.1)
    b = measured_flow_map(replace(CONFIG, seed=3), 1.0e-3, 0.1)
    c = measured_flow_map(replace(CONFIG, seed=4), 1.0e-3, 0.1)
    np.testing.assert_array_equal(a.grid, b.grid)
    assert not np.array_equal(a.grid, c.grid)
    clean = MeasuredFlowMap(CONFIG, 1.0e-3)
    noise = (a.grid - clean.grid)[np.any(a.grid != clean.grid, axis=-1)]
    assert abs(noise.mean()) < 0.1 * noise.std()
    assert noise.std() == pytest.approx(0.1 * 2 * 0.03, rel=0.1)


def test_noiseless_maps_are_cached():
    assert measured_flow_map(CONFIG, 1.0e-3) is measured_flow_map(replace(CONFIG, seed=9), 1.0e-3)


def test_map_leaves_the_sensor_and_flow_draws_unchanged():
    base = physiological_config("composite", flow_speed_m_s=0.03, duration_s=0.3, control_mode="passive",
                                model_flow_feedforward=True)
    plain = run_trial(base)["history"]
    mapped = run_trial(replace(base, flow_model_voxel_m=1.0e-3, flow_model_noise=0.1))["history"]
    np.testing.assert_array_equal(plain["true_position_m"], mapped["true_position_m"])
    np.testing.assert_array_equal(plain["estimated_position_m"], mapped["estimated_position_m"])


@pytest.mark.parametrize("change", [
    {"flow_model_noise": 0.1},                                                     # needs a map
    {"flow_model_voxel_m": 1e-3},                                                  # needs model feedforward
    {"flow_model_voxel_m": 1e-3, "model_flow_feedforward": True, "flow_model_error": 0.2},
    {"flow_model_voxel_m": -1e-3},
])
def test_invalid_map_options_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(replace(TrialConfig(duration_s=0.1, flow_model="poiseuille"), **change))


def test_study_grid_and_configs():
    config = cell_config(0.9, 15.0, "target_occluded", "N_P2_modelff_hold", "lower", 4, "map_0.5mm_noise5%")
    assert config.flow_model_voxel_m == 0.5e-3 and config.flow_model_noise == 0.05
    assert config.model_flow_feedforward and config.gravity_hold_from_release
    grid = cells()
    assert len(grid) == len(CONDITIONS) * 72 + 2 * 72
    assert {c["condition"] for c in grid if c["flow_reduction"] == 0.99} == {"exact", WORST}


def _archive(name):
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parents[1] / "docs/results" / name / "trials.json").read_text())


def test_exact_condition_matches_experiment_25_archive():
    key = ("arm", "flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in _archive("flow_model_errors") if r["condition"] == "exact"}
    exact = [r for r in _archive("measured_flow_map") if r["condition"] == "exact"]
    assert len(exact) == len(reference) == 144
    for r in exact:
        old = reference[tuple(r[k] for k in key)]
        for field in ("target_success", "wall_collision", "wrong_branch", "frames_used"):
            assert r[field] == old[field], field


def test_archived_noisy_map_cell_reproduces():
    from src.flow_map_study import trial_record
    cell = dict(flow_reduction=0.9, frame_rate_hz=30.0, occlusion="target_occluded", arm="C_P2_modelff",
                branch="lower", seed=4, condition="map_0.5mm_noise10%")
    reference = next(r for r in _archive("measured_flow_map") if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used",
                "terminal_wall_feature", "reason_counts"):
        assert record[key] == reference[key], key
    for key in ("elapsed_time_s", "closest_target_approach_m", "peak_force_fraction"):
        assert record[key] == pytest.approx(reference[key], rel=1e-8, abs=1e-15), key
