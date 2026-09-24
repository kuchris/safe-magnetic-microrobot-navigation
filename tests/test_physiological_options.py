from dataclasses import fields, replace

import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.flow import poiseuille_flow
from src.plotting import frame_timeline
from src.presets import COMPOSITE, PHYSIOLOGICAL, physiological_config, provenance
from src.vessel import YVessel

U = 0.3
LOWER_MID = YVessel().segments[2].start_m + 0.6 * (YVessel().segments[2].end_m - YVessel().segments[2].start_m)
UPPER_MID = YVessel().segments[1].start_m + 0.6 * (YVessel().segments[1].end_m - YVessel().segments[1].start_m)


def test_occluded_branch_is_stagnant_and_flow_turns_to_patent_branch():
    np.testing.assert_allclose(poiseuille_flow(LOWER_MID, U, occluded_branch="lower"), 0, atol=1e-15)
    np.testing.assert_allclose(np.linalg.norm(poiseuille_flow(UPPER_MID, U, occluded_branch="lower")), 2 * U)
    # Just past the junction even the lower half of the lumen turns toward the patent upper branch.
    below = poiseuille_flow([11e-3, -0.3e-3, -0.15e-3], U, occluded_branch="lower")
    assert below[1] > 0 and below[2] > 0
    # Parent segment upstream of the junction is unchanged up to the ~1e-6 relative tanh tail.
    np.testing.assert_allclose(poiseuille_flow([3e-3, 0.4e-3, 0], U, occluded_branch="upper"),
                               poiseuille_flow([3e-3, 0.4e-3, 0], U), atol=1e-5 * U)
    with pytest.raises(ValueError):
        poiseuille_flow([3e-3, 0, 0], U, occluded_branch="middle")


def test_passive_particle_cannot_enter_an_occluded_target_branch():
    config = TrialConfig(duration_s=0.2, flow_model="poiseuille", flow_speed_m_s=U, control_mode="passive",
                         branch="lower", occluded_branch="lower", start_m=(0.5e-3, -0.4e-3, -0.2e-3))
    summary = run_trial(config)["summary"]
    assert not summary["target_success"]
    assert summary["wrong_branch"] or summary["wall_collision"]
    assert summary["physics"]["occluded_branch"] == "lower"


@pytest.mark.parametrize("change", [{"occluded_branch": "lower"},  # piecewise model
                                    {"flow_model": "poiseuille", "occluded_branch": "left"},
                                    {"actuation_period_s": -0.01}, {"gain_saturation_distance_m": -1.0}])
def test_invalid_physiological_options_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, **change))


def test_zero_order_hold_updates_only_on_the_actuation_period():
    config = TrialConfig(duration_s=1.0, actuation_period_s=0.02)
    result = run_trial(config)
    h = result["history"]
    changes = h["time_s"][1:][np.any(np.diff(h["force_n"], axis=0) != 0, axis=1)]
    assert len(changes) > 5
    np.testing.assert_allclose(changes / 0.02, np.round(changes / 0.02), atol=1e-6)
    # Measurement age keeps growing during a hold, so frame captures are still recovered exactly.
    frames = frame_timeline(result)
    np.testing.assert_allclose(frames["delivered_capture_s"], np.round(frames["delivered_capture_s"] / 0.05) * 0.05,
                               atol=1e-9)
    assert result["summary"]["physics"]["actuation_period_s"] == 0.02


def test_gain_from_saturation_distance_reproduces_the_toy_gain():
    base = TrialConfig(duration_s=3.0)
    legacy = run_trial(base)["summary"]
    scaled = run_trial(replace(base, gain_saturation_distance_m=1.5e-3))["summary"]
    physics = scaled.pop("physics")
    assert physics["gain_n_per_m"] == pytest.approx(2e-6)
    for key, value in legacy.items():
        assert scaled[key] == (pytest.approx(value, rel=1e-8) if isinstance(value, float) else value), key


def test_closest_target_approach_is_reported_with_physics():
    result = run_trial(TrialConfig(duration_s=0.5, flow_model="poiseuille"))
    closest = result["summary"]["physics"]["closest_target_approach_m"]
    target = YVessel().upper_target
    assert closest == pytest.approx(np.linalg.norm(result["history"]["true_position_m"] - target, axis=1).min())
    assert closest <= np.linalg.norm(result["history"]["true_position_m"][-1] - target)


def test_preset_values_all_have_provenance_and_valid_fields():
    names = {f.name for f in fields(TrialConfig)}
    for table in (PHYSIOLOGICAL, COMPOSITE):
        for name, (value, note) in table.items():
            assert name in names and isinstance(note, str) and note
    notes = provenance("composite")
    assert "assumed" in notes["particle_density_kg_m3"] and "assumed" in notes["cardiac_period_s"]


def test_preset_overrides_and_materials():
    ndfeb = physiological_config()
    assert ndfeb.flow_speed_m_s == 0.30 and ndfeb.max_gradient_t_m == 1.0 and ndfeb.particle_inertia
    composite = physiological_config("composite", flow_speed_m_s=0.003, frame_rate_hz=30.0)
    assert composite.particle_density_kg_m3 == 2000.0 and composite.magnetic_volume_fraction == 0.14
    assert composite.flow_speed_m_s == 0.003 and composite.frame_rate_hz == 30.0
    with pytest.raises(ValueError):
        physiological_config("steel")
    with pytest.raises(ValueError):
        physiological_config(flow_speed=0.3)


def test_preset_trial_runs_with_every_physics_option():
    result = run_trial(physiological_config(duration_s=0.03))
    physics = result["summary"]["physics"]
    for key in ("force_cap_n", "dt_s", "stokes_number", "womersley_number", "net_weight_n",
                "sedimentation_risk_fraction", "gain_n_per_m", "actuation_period_s", "closest_target_approach_m"):
        assert key in physics, key
