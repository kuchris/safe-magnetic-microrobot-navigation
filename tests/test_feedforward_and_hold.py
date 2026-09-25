from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.feedforward_hold_study import ARMS, BASELINES, WALL_HORIZON_S, cell_config, cells, paired_changes
from src.localization import StateEstimate
from src.navigation import BiplaneNavigation
from src.presets import physiological_config
from src.vessel import YVessel

GAMMA = 6 * np.pi * 3.5e-3 * 100e-6
NDFEB_WEIGHT = (7500 - 1060) * 4 / 3 * np.pi * (100e-6) ** 3 * 9.81


class StubEstimator:
    def __init__(self, position):
        self.position = np.asarray(position, dtype=float)
        self.last_capture_s = 0.0

    def estimate(self, now_s):
        return StateEstimate(self.position, np.zeros(3), np.eye(6) * 1e-12)


def test_model_feedforward_cancels_the_controller_flow_model():
    def flow_model(position, time_s):
        return np.array([0.03, 0.0, 0.0]) * (1 + position[1])
    navigation = BiplaneNavigation(YVessel(), 100e-6, gain_n_per_m=0.0, max_force_n=1e-6, flow_model=flow_model)
    navigation.estimator, navigation.tracking_valid = StubEstimator([5e-3, 0, 0]), True
    np.testing.assert_allclose(navigation.step(0.01, []).force_n, [-GAMMA * 0.03, 0, 0], rtol=1e-12)


def test_known_input_adds_weight_and_modeled_flow_for_the_estimator():
    navigation = BiplaneNavigation(YVessel(), 100e-6, estimator_mode="command_aware",
                                   flow_model=lambda p, t: np.array([0.01, 0, 0]),
                                   known_weight_n=[0, 0, -2e-7])
    command = np.array([1e-8, 0, 3e-7])
    np.testing.assert_allclose(navigation._known_input(command, 0.1, np.zeros(3)),
                               command + [GAMMA * 0.01, 0, -2e-7])
    # Before the first estimate there is no position, so only the weight is added.
    np.testing.assert_allclose(navigation._known_input(command), command + [0, 0, -2e-7])


def test_release_hold_acts_before_the_first_frame():
    config = physiological_config(flow_speed_m_s=0.0, duration_s=0.08, start_m=(5e-3, 0.0, 0.0),
                                  gravity_compensation=True, gravity_hold_from_release=True,
                                  estimator_mode="command_aware", estimator_knows_weight=True)
    h = run_trial(config)["history"]
    early = h["time_s"] < 0.05
    assert set(h["reason"][early]) == {"gravity_hold"}
    np.testing.assert_allclose(h["force_n"][early][-1], [0, 0, NDFEB_WEIGHT], rtol=1e-9)
    # Held from release, the particle no longer sinks at ~40 mm/s before any frame arrives.
    assert abs(h["true_position_m"][early][-1, 2]) < 1e-5
    tracking_gated = run_trial(replace(config, gravity_hold_from_release=False))["history"]
    assert tracking_gated["true_position_m"][tracking_gated["time_s"] < 0.05][-1, 2] < -1e-3


def test_weight_aware_estimator_removes_phantom_hold_motion():
    # Zero steering gain isolates the hold: any estimate drift is phantom commanded motion.
    config = physiological_config(flow_speed_m_s=0.0, duration_s=0.15, start_m=(5e-3, 0.0, 0.0),
                                  gravity_compensation=True, gravity_hold_from_release=True,
                                  estimator_mode="command_aware", estimator_knows_weight=True,
                                  gain_saturation_distance_m=0.0, gain_n_per_m=0.0)

    def worst_error(result):
        h = result["history"]
        valid = np.isfinite(h["estimated_position_m"]).all(axis=1)
        return np.abs(h["estimated_position_m"][valid, 2] - h["true_position_m"][valid, 2]).max()
    assert worst_error(run_trial(config)) < 0.2e-3
    # Without the weight, the held 265 nN reads as ~40 mm/s of upward commanded motion.
    assert worst_error(run_trial(replace(config, estimator_knows_weight=False))) > 1e-3


@pytest.mark.parametrize("change", [
    {"gravity_hold_from_release": True},                                    # needs compensation
    {"estimator_knows_weight": True},                                       # needs gravity + command_aware
    {"flow_model_error": -1.0},
    {"estimator_mode": "command_aware", "flow_feedforward": True, "model_flow_feedforward": True},
])
def test_invalid_feedforward_and_hold_options_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, **change))


def test_flow_model_error_scales_the_controller_model_only():
    base = TrialConfig(duration_s=0.3, flow_model="poiseuille", model_flow_feedforward=True)
    physics = run_trial(replace(base, flow_model_error=0.2))["summary"]["physics"]
    assert physics["flow_model_error"] == 0.2
    plant = [run_trial(replace(base, flow_model_error=e, control_mode="passive"))["history"]["flow_velocity_m_s"]
             for e in (0.0, 0.2)]
    np.testing.assert_array_equal(plant[0], plant[1])  # the plant flow never changes


def test_arm_configs():
    unchanged = cell_config(0.99, 15.0, "patent", "C_P2_exp23", "upper", 0)
    assert unchanged.estimator_mode == "command_aware" and not unchanged.estimator_knows_weight
    ndfeb = cell_config(0.9, 7.5, "target_occluded", "N_P2_modelff_hold", "lower", 4, -0.2)
    assert ndfeb.particle_density_kg_m3 == 7500.0 and ndfeb.gravity_hold_from_release
    assert ndfeb.model_flow_feedforward and ndfeb.flow_model_error == -0.2 and ndfeb.estimator_knows_weight
    assert ndfeb.gain_n_per_m == pytest.approx(0.5 * GAMMA / 0.01)
    wall = cell_config(0.9, 7.5, "patent", "C_P2_wall50", "upper", 0)
    assert wall.prediction_horizon_s == WALL_HORIZON_S and not wall.model_flow_feedforward
    assert len(cells((0, 1, 2))) == 2 * 3 * 2 * len(ARMS) * 2 * 3
    assert set(BASELINES.values()) <= set(ARMS)


def test_paired_changes_use_each_materials_baseline():
    base = dict(flow_model_error=0.0, flow_reduction=0.9, frame_rate_hz=15.0, occlusion="patent",
                branch="upper", seed=0)
    records = [dict(base, arm="C_P2", material="composite", target_success=False, closest_target_approach_m=9e-3),
               dict(base, arm="N_P2_hold", material="ndfeb", target_success=True, closest_target_approach_m=4e-4),
               dict(base, arm="C_P2_modelff", material="composite", target_success=True,
                    closest_target_approach_m=4e-4),
               dict(base, arm="N_P2_modelff_hold", material="ndfeb", target_success=False,
                    closest_target_approach_m=1e-3)]
    rows = {r["arm"]: r for r in paired_changes(records)}
    assert rows["C_P2_modelff"]["rescued"] == 1 and rows["C_P2_modelff"]["baseline"] == "C_P2"
    assert rows["N_P2_modelff_hold"]["regressed"] == 1 and rows["N_P2_modelff_hold"]["baseline"] == "N_P2_hold"


RESULTS = __import__("pathlib").Path(__file__).parents[1] / "docs/results"


def _archived(stage, **factors):
    import json
    records = json.loads((RESULTS / "feedforward_and_hold" / stage / "trials.json").read_text())
    return next(r for r in records if all(r[k] == v for k, v in factors.items()))


def test_unchanged_arm_matches_experiment_23_archive():
    import json
    exp23 = json.loads((RESULTS / "delay_aware_control/heldout/trials.json").read_text())
    exp24 = json.loads((RESULTS / "feedforward_and_hold/heldout/trials.json").read_text())
    key = ("flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in exp23 if r["policy"] == "P2_predictor_fast_gain"}
    unchanged = [r for r in exp24 if r["arm"] == "C_P2_exp23"]
    assert len(unchanged) == len(reference) == 72
    for r in unchanged:
        old = reference[tuple(r[k] for k in key)]
        for field in ("target_success", "wall_collision", "wrong_branch", "frames_used"):
            assert r[field] == old[field], field
        assert r["closest_target_approach_m"] == pytest.approx(old["closest_target_approach_m"], rel=1e-8)


@pytest.mark.parametrize("stage, cell", [
    # Held-out: pure NdFeB with release hold and model feedforward enters an occluded branch at 90%.
    ("heldout", dict(flow_reduction=0.9, frame_rate_hz=15.0, occlusion="target_occluded", arm="N_P2_modelff_hold",
                     branch="upper", seed=3, flow_model_error=0.0)),
    # A +20% flow-model error removes that benefit for the composite arm.
    ("flow_error", dict(flow_reduction=0.9, frame_rate_hz=7.5, occlusion="target_occluded", arm="C_P2_modelff",
                        branch="upper", seed=3, flow_model_error=0.2)),
])
def test_archived_experiment_24_cells_reproduce(stage, cell):
    from src.feedforward_hold_study import trial_record
    reference, record = _archived(stage, **cell), trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used",
                "terminal_wall_feature", "reason_counts"):
        assert record[key] == reference[key], key
    for key in ("elapsed_time_s", "closest_target_approach_m", "peak_force_fraction"):
        assert record[key] == pytest.approx(reference[key], rel=1e-8, abs=1e-15), key
