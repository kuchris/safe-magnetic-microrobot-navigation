from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from src.experiment import TrialConfig, effective_max_force_n, run_trial
from src.feasibility import Material, magnetic_force_cap, required_gradient_branch_entry, Vessel, volume
from src.flow_sensitivity import trial_record


def assert_summary_matches(actual, expected):
    """Exact on keys and non-float fields; floats allow cross-platform round-off."""
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        if isinstance(value, float):
            assert actual[key] == pytest.approx(value, rel=1e-8, abs=1e-15), key
        else:
            assert actual[key] == value, key


def legacy_equivalent_gradient(config=TrialConfig()):
    return config.max_force_n / (volume(config.particle_radius_m) * config.magnetization_a_m)


def test_force_cap_is_volume_times_magnetization_times_gradient():
    assert magnetic_force_cap(1e-4, 1.0) == pytest.approx(4 / 3 * np.pi * 1e-12 * 1e6)
    assert magnetic_force_cap(2e-4, 1.0) == pytest.approx(8 * magnetic_force_cap(1e-4, 1.0))
    assert magnetic_force_cap(1e-4, 0.4) == pytest.approx(0.4 * magnetic_force_cap(1e-4, 1.0))
    half = Material(magnetic_volume_fraction=0.5)
    assert magnetic_force_cap(1e-4, 1.0, half) == pytest.approx(0.5 * magnetic_force_cap(1e-4, 1.0))
    with pytest.raises(ValueError):
        magnetic_force_cap(1e-4, -1.0)
    with pytest.raises(ValueError):
        magnetic_force_cap(0.0, 1.0)


def test_force_cap_inverts_feasibility_requirement():
    result = required_gradient_branch_entry(8e-5, Vessel())
    assert magnetic_force_cap(8e-5, result["gradient_t_m"]) == pytest.approx(result["force_n"])


def test_zero_gradient_keeps_legacy_cap_and_summary_keys():
    config = TrialConfig(duration_s=0.5)
    assert effective_max_force_n(config) == config.max_force_n
    assert "physics" not in run_trial(config)["summary"]


def test_equivalent_gradient_reproduces_archived_dropout_trial():
    pilot = json.loads((Path(__file__).parents[1] / "docs/results/benchmark_pilot.json").read_text())
    reference = next(r for r in pilot["trials"] if r["scenario"] == "dropout_burst"
                     and r["config"]["branch"] == "lower" and r["config"]["control_mode"] == "gated"
                     and r["config"]["seed"] == 0)
    config = TrialConfig(**reference["config"])
    gradient = legacy_equivalent_gradient(config)
    assert gradient == pytest.approx(7.16e-4, rel=1e-3)  # 3 nN on a 0.1 mm NdFeB sphere
    summary = run_trial(replace(config, max_gradient_t_m=gradient))["summary"]
    physics = summary.pop("physics")
    assert physics["force_cap_n"] == pytest.approx(config.max_force_n, rel=1e-12)
    assert_summary_matches(summary, reference["summary"])


def test_gradient_cap_bounds_applied_force_and_reports_gradient():
    config = TrialConfig(duration_s=2.0, max_gradient_t_m=2e-4)
    result = run_trial(config)
    physics = result["summary"]["physics"]
    cap = magnetic_force_cap(config.particle_radius_m, 2e-4)
    assert physics["force_cap_n"] == pytest.approx(cap)
    assert result["summary"]["maximum_force_n"] <= cap * (1 + 1e-12)
    assert 0 < physics["maximum_gradient_t_m"] <= 2e-4 * (1 + 1e-12)
    # Saturation statistics use the enforced cap, not the unused legacy field.
    assert trial_record(result)["force_saturation_fraction"] > 0


def test_physiological_scale_cap():
    config = TrialConfig(particle_radius_m=100e-6, max_gradient_t_m=1.0)
    assert effective_max_force_n(config) == pytest.approx(4.19e-6, rel=1e-3)
    composite = replace(config, magnetic_volume_fraction=0.3)
    assert effective_max_force_n(composite) == pytest.approx(0.3 * 4.19e-6, rel=1e-3)


def test_particle_radius_reaches_the_clearance_model():
    base = TrialConfig(duration_s=1.0, control_mode="passive")
    small = run_trial(base)["summary"]
    large = run_trial(replace(base, particle_radius_m=0.2e-3))["summary"]
    # Passive overdamped motion is radius independent, so only the eroded wall moves.
    assert small["minimum_wall_clearance_m"] - large["minimum_wall_clearance_m"] == pytest.approx(0.1e-3)


@pytest.mark.parametrize("change", [{"max_gradient_t_m": -1.0}, {"particle_radius_m": 0.0},
                                    {"particle_radius_m": 1.5e-3}, {"magnetic_volume_fraction": 0.0},
                                    {"magnetization_a_m": 0.0}])
def test_invalid_gradient_and_material_are_rejected(change):
    with pytest.raises(ValueError):
        run_trial(TrialConfig(duration_s=0.1, **change))
