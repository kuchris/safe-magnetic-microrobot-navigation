from dataclasses import replace

import numpy as np
import pytest

from src.experiment import TrialConfig, controller_flow_function, plant_flow_function, run_trial
from src.flow import poiseuille_flow, prescribed_flow
from src.flow_model_error_study import CONDITIONS, cell_config, cells, paired_against_exact, route_velocity_error

U, R = 0.03, 1.5e-3


@pytest.mark.parametrize("n", [2.0, 4.0, 9.0])
def test_profile_exponent_keeps_the_mean_and_sets_the_centerline(n):
    radial = (np.arange(400) + 0.5) / 400 * R
    axial = np.array([poiseuille_flow([5e-3, rho, 0], U, profile_exponent=n)[0] for rho in radial])
    mean = np.sum(axial * 2 * np.pi * radial * (R / 400)) / (np.pi * R ** 2)
    assert mean == pytest.approx(U, rel=1e-4)
    assert poiseuille_flow([5e-3, 0, 0], U, profile_exponent=n)[0] == pytest.approx(U * (n + 2) / n)


def test_profile_exponent_two_is_the_original_field_and_needs_poiseuille():
    for point in ([5e-3, 0.4e-3, 0.1e-3], [12e-3, 1e-3, 0.5e-3]):
        np.testing.assert_array_equal(poiseuille_flow(point, U, profile_exponent=2.0), poiseuille_flow(point, U))
    with pytest.raises(ValueError):
        prescribed_flow([5e-3, 0, 0], U, "smooth", profile_exponent=4.0)
    with pytest.raises(ValueError):
        poiseuille_flow([5e-3, 0, 0], U, profile_exponent=0.0)


def test_controller_model_errors_leave_the_plant_unchanged():
    base = TrialConfig(flow_model="poiseuille", flow_speed_m_s=U, flow_pulsatility=0.45,
                       model_flow_feedforward=True)
    point = np.array([5e-3, 0.3e-3, 0])
    exact_model = controller_flow_function(base)
    assert np.allclose(exact_model(point, 0.3), plant_flow_function(base)(point, 0.3))
    for change in ({"flow_model_phase_error": 0.25}, {"flow_model_pulsatility": 0.0},
                   {"flow_model_profile_exponent": 9.0}, {"flow_model_junction_scale": 2.0}):
        config = replace(base, **change)
        np.testing.assert_array_equal(plant_flow_function(config)(point, 0.3), plant_flow_function(base)(point, 0.3))
    # A quarter-period phase error puts the model's peak where the plant is at its mean.
    shifted = controller_flow_function(replace(base, flow_model_phase_error=0.25))
    assert np.linalg.norm(shifted(point, 0.0)) == pytest.approx(np.linalg.norm(plant_flow_function(base)(point, 0.25)))
    steady = controller_flow_function(replace(base, flow_model_pulsatility=0.0))
    assert np.linalg.norm(steady(point, 0.25)) == pytest.approx(np.linalg.norm(plant_flow_function(base)(point, 0.0)))


@pytest.mark.parametrize("change", [{"flow_model_pulsatility": 1.5}, {"flow_model_profile_exponent": 0.0},
                                    {"flow_model_junction_scale": -1.0}, {"flow_model_phase_error": float("inf")}])
def test_invalid_flow_model_errors_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, flow_model="poiseuille", **change))


def test_route_error_is_zero_for_the_exact_model_and_ordered_for_phase():
    assert route_velocity_error("exact", 0.9, "patent") == 0.0
    errors = [route_velocity_error(c, 0.9, "patent") for c in ("phase_+0.1", "phase_+0.25", "phase_+0.5")]
    assert errors == sorted(errors) and errors[0] > 0
    # A +/-20% scale error is symmetric in magnitude.
    assert route_velocity_error("scale_-20%", 0.9, "patent") == pytest.approx(
        route_velocity_error("scale_+20%", 0.9, "patent"))


def test_condition_configs_and_grid():
    exact = cell_config(0.9, 15.0, "patent", "N_P2_modelff_hold", "upper", 3, "exact")
    assert exact.model_flow_feedforward and exact.flow_model_phase_error == 0.0
    phase = cell_config(0.9, 15.0, "patent", "C_P2_modelff", "upper", 3, "phase_+0.25")
    assert phase.flow_model_phase_error == 0.25 and phase.particle_density_kg_m3 == 2000.0
    assert len(cells()) == len(CONDITIONS) * 2 * 3 * 2 * 2 * 2 * 3
    with pytest.raises(ValueError):
        cell_config(0.9, 15.0, "patent", "C_P2", "upper", 3, "exact")  # not a model-feedforward arm


def test_paired_against_exact_counts_kept_and_lost():
    base = dict(arm="C_P2_modelff", flow_reduction=0.9, frame_rate_hz=15.0, occlusion="patent", branch="upper")
    records = [dict(base, seed=3, condition="exact", target_success=True),
               dict(base, seed=4, condition="exact", target_success=False),
               dict(base, seed=3, condition="phase_+0.5", target_success=False),
               dict(base, seed=4, condition="phase_+0.5", target_success=True)]
    (row,) = paired_against_exact(records)
    assert (row["kept"], row["lost"], row["gained"], row["both_fail"]) == (0, 1, 1, 0)


def _archive():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parents[1] / "docs/results/flow_model_errors/trials.json").read_text())


def test_exact_condition_matches_experiment_24_archive():
    import json
    from pathlib import Path
    exp24 = json.loads((Path(__file__).parents[1] / "docs/results/feedforward_and_hold/heldout/trials.json").read_text())
    key = ("arm", "flow_reduction", "frame_rate_hz", "occlusion", "branch", "seed")
    reference = {tuple(r[k] for k in key): r for r in exp24 if r["arm"] in ("C_P2_modelff", "N_P2_modelff_hold")}
    exact = [r for r in _archive() if r["condition"] == "exact"]
    assert len(exact) == len(reference) == 144
    for r in exact:
        old = reference[tuple(r[k] for k in key)]
        for field in ("target_success", "wall_collision", "wrong_branch", "frames_used"):
            assert r[field] == old[field], field
        assert r["closest_target_approach_m"] == pytest.approx(old["closest_target_approach_m"], rel=1e-8)


def test_archived_junction_error_cell_reproduces():
    from src.flow_model_error_study import trial_record
    cell = dict(flow_reduction=0.9, frame_rate_hz=15.0, occlusion="target_occluded", arm="N_P2_modelff_hold",
                branch="upper", seed=3, condition="junction_x2")
    reference = next(r for r in _archive() if all(r[k] == v for k, v in cell.items()))
    record = trial_record(cell)
    for key in ("target_success", "wall_collision", "wrong_branch", "timeout", "frames_used",
                "terminal_wall_feature", "reason_counts"):
        assert record[key] == reference[key], key
    for key in ("elapsed_time_s", "closest_target_approach_m", "peak_force_fraction"):
        assert record[key] == pytest.approx(reference[key], rel=1e-8, abs=1e-15), key
