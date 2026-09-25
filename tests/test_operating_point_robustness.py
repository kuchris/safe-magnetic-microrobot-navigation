from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.presets import physiological_config
from src.robustness_study import CONDITIONS, GATE_MARGIN_S, cell_config, cells


def test_gravity_model_tilt_rotates_the_held_weight_not_the_plant():
    base = physiological_config(flow_speed_m_s=0.0, duration_s=0.04, start_m=(5e-3, 0.0, 0.0),
                                gravity_compensation=True, gravity_hold_from_release=True,
                                estimator_mode="command_aware", estimator_knows_weight=True)
    level = run_trial(base)["history"]
    tilted = run_trial(replace(base, gravity_model_tilt_deg=30.0))["history"]
    weight = np.linalg.norm(level["force_n"][0])
    # The hold now points 30 degrees off vertical, so it leaves W sin(30) sideways and W(1 - cos 30) down.
    np.testing.assert_allclose(tilted["force_n"][0], [0, -weight * np.sin(np.radians(30)),
                                                      weight * np.cos(np.radians(30))], rtol=1e-9, atol=1e-18)
    assert abs(level["true_position_m"][-1, 1]) < 1e-9 < abs(tilted["true_position_m"][-1, 1])


def test_zero_tilt_is_the_default_and_invalid_tilt_is_rejected():
    config = physiological_config(duration_s=0.02, gravity_compensation=True)
    a, b = run_trial(config)["history"], run_trial(replace(config, gravity_model_tilt_deg=0.0))["history"]
    np.testing.assert_array_equal(a["true_position_m"], b["true_position_m"])
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, gravity_model_tilt_deg=float("nan")))


def test_matched_gate_exceeds_latency_plus_frame_period():
    for fps in (7.5, 15.0, 30.0):
        config = cell_config("robustness", fps, "patent", "C_P2", "upper", 3, "latency_0.2s")
        assert config.latency_s == 0.2
        assert config.max_measurement_age_s == pytest.approx(0.2 + 1 / fps + GATE_MARGIN_S)
    fixed = cell_config("robustness", 7.5, "patent", "C_P2", "upper", 3, "nominal_fixed_gate")
    assert fixed.max_measurement_age_s == 0.15
    gate = cell_config("gate_check", 7.5, "patent", "C_P2_modelff", "upper", 3, "matched_gate")
    assert gate.flow_speed_m_s == pytest.approx(0.03) and gate.model_flow_feedforward
    assert gate.max_measurement_age_s == pytest.approx(0.05 + 1 / 7.5 + GATE_MARGIN_S)


def test_conditions_map_to_config_fields():
    c = cell_config("robustness", 15.0, "target_occluded", "N_P2_hold", "lower", 4, "gradient_0.25")
    assert c.max_gradient_t_m == 0.25 and c.flow_speed_m_s == pytest.approx(0.003)
    assert cell_config("robustness", 15.0, "patent", "C_P2", "upper", 3, "dropout_0.3s").dropout_intervals == ((0.3, 0.6),)
    assert cell_config("robustness", 15.0, "patent", "C_P2", "upper", 3, "gain_-20%").actuation_gain_error == -0.2
    assert len(cells()) == len(CONDITIONS) * 72 + 2 * 72
    with pytest.raises(ValueError):
        cell_config("robustness", 15.0, "patent", "C_P2_modelff", "upper", 3, "nominal")
    with pytest.raises(ValueError):
        cell_config("sweep", 15.0, "patent", "C_P2", "upper", 3, "nominal")


def _archive(followup=False):
    import json
    from pathlib import Path
    root = Path(__file__).parents[1] / "docs/results/operating_point_robustness"
    return json.loads(((root / "followup") if followup else root).joinpath("trials.json").read_text())


def test_gate_check_matches_experiment_24_with_the_fixed_gate():
    import json
    from pathlib import Path
    exp24 = json.loads((Path(__file__).parents[1] / "docs/results/feedforward_and_hold/heldout/trials.json").read_text())
    key = ("arm", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in exp24
                 if r["arm"] in ("C_P2_modelff", "N_P2_modelff_hold") and r["flow_reduction"] == 0.9}
    fixed = [r for r in _archive() if r["stage"] == "gate_check" and r["condition"] == "fixed_gate"]
    assert len(fixed) == len(reference) == 72
    for r in fixed:
        assert r["target_success"] == reference[tuple(r[k] for k in key)]["target_success"]


@pytest.mark.parametrize("followup, cell", [
    (False, dict(stage="robustness", frame_rate_hz=15.0, occlusion="patent", arm="C_P2", branch="upper", seed=3,
                 condition="dropout_0.3s")),
    (False, dict(stage="robustness", frame_rate_hz=7.5, occlusion="patent", arm="N_P2_hold", branch="upper", seed=3,
                 condition="gravity_tilt_30deg")),
    (True, dict(stage="followup", frame_rate_hz=15.0, occlusion="patent", arm="C_P2", branch="upper", seed=3,
                condition="dropout_0.3s_open_loop_hold")),
])
def test_archived_robustness_cells_reproduce(followup, cell):
    from src.robustness_study import trial_record
    reference = next(r for r in _archive(followup) if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used", "reason_counts"):
        assert record[key] == reference[key], key
    assert record["elapsed_time_s"] == pytest.approx(reference["elapsed_time_s"], rel=1e-8)
