import pytest

from src.combined_study import BUNDLES, cell_config, cells
from src.robustness_study import GATE_MARGIN_S


def test_bundles_apply_every_field_and_the_open_loop_hold():
    severe = cell_config(7.5, "target_occluded", "C_P2", "upper", 3, "severe")
    assert severe.gravity_hold_from_release and severe.gravity_compensation and severe.estimator_knows_weight
    assert (severe.latency_s, severe.actuation_gain_error, severe.gravity_model_tilt_deg) == (0.2, -0.2, 15.0)
    assert (severe.calibration_sigma_px, severe.noise_sigma_px, severe.max_gradient_t_m) == (1.0, 3.0, 0.25)
    assert severe.dropout_intervals == ((0.3, 0.6),)
    assert severe.max_measurement_age_s == pytest.approx(0.2 + 1 / 7.5 + GATE_MARGIN_S)
    assert severe.flow_speed_m_s == pytest.approx(0.003)
    nominal = cell_config(15.0, "patent", "N_P2_hold", "lower", 4, "nominal")
    assert nominal.latency_s == 0.05 and nominal.max_gradient_t_m == 1.0 and nominal.particle_density_kg_m3 == 7500.0


def test_grid_and_invalid_names():
    assert len(cells()) == len(BUNDLES) * 2 * 3 * 2 * 2 * 3
    with pytest.raises(ValueError):
        cell_config(15.0, "patent", "C_P2_modelff", "upper", 3, "mild")
    with pytest.raises(ValueError):
        cell_config(15.0, "patent", "C_P2", "upper", 3, "extreme")


def test_ablation_resets_one_ingredient_to_nominal():
    from src.combined_study import NOMINAL_VALUES, ablation_cells
    c = cell_config(15.0, "patent", "N_P2_hold", "upper", 3, "moderate", without="actuation_gain_error")
    assert c.actuation_gain_error == 0.0 and c.gravity_model_tilt_deg == 10.0 and c.latency_s == 0.1
    c = cell_config(15.0, "patent", "N_P2_hold", "upper", 3, "moderate", without="latency_s")
    assert c.latency_s == 0.05 and c.max_measurement_age_s == pytest.approx(0.05 + 1 / 15 + GATE_MARGIN_S)
    assert set(BUNDLES["moderate"]) <= set(NOMINAL_VALUES)
    assert len(ablation_cells()) == len(BUNDLES["moderate"]) * 36
    with pytest.raises(ValueError):
        cell_config(15.0, "patent", "N_P2_hold", "upper", 3, "mild", without="dropout_intervals")


def test_archived_combined_cell_reproduces():
    import json
    from pathlib import Path
    from src.combined_study import trial_record
    archive = json.loads((Path(__file__).parents[1] / "docs/results/combined_perturbations/trials.json").read_text())
    cell = dict(frame_rate_hz=30.0, occlusion="patent", arm="N_P2_hold", branch="upper", seed=3, bundle="moderate")
    reference = next(r for r in archive if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used", "reason_counts"):
        assert record[key] == reference[key], key
    assert record["elapsed_time_s"] == pytest.approx(reference["elapsed_time_s"], rel=1e-8)
