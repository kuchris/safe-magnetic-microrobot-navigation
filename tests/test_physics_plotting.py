import numpy as np
import pytest

from src.experiment import TrialConfig, run_trial
from src.plotting import frame_timeline, plot_physics_trial


@pytest.fixture(scope="module")
def physiological():
    return run_trial(TrialConfig(duration_s=0.2, flow_model="poiseuille", flow_speed_m_s=0.3,
                                 particle_radius_m=100e-6, max_gradient_t_m=1.0))


@pytest.fixture(scope="module")
def slow():
    return run_trial(TrialConfig(duration_s=0.6, flow_model="poiseuille", flow_speed_m_s=0.003,
                                 particle_radius_m=100e-6, max_gradient_t_m=1.0))


def test_timeline_reports_no_frame_before_early_collision(physiological):
    frames = frame_timeline(physiological)
    assert physiological["summary"]["wall_collision"]
    assert frames["end_s"] < frames["nominal_delivery_s"][0] == pytest.approx(0.05)
    assert len(frames["delivered_capture_s"]) == 0 and len(frames["delivered_at_s"]) == 0


def test_timeline_recovers_used_frames_from_measurement_age(slow):
    frames = frame_timeline(slow)
    captures, delivered = frames["delivered_capture_s"], frames["delivered_at_s"]
    assert len(captures) >= 8
    # Captures sit on the 20 Hz schedule (quantized to ticks) and arrive after the 50 ms latency.
    np.testing.assert_allclose(captures, np.round(captures / 0.05) * 0.05, atol=slow["summary"]["physics"]["dt_s"])
    assert np.all(delivered - captures >= 0.05 - 1e-9)
    assert np.all(delivered - captures <= 0.05 + slow["summary"]["physics"]["dt_s"] + 1e-9)


@pytest.mark.parametrize("case", ["physiological", "slow"])
def test_physics_figure_is_written(case, request, tmp_path):
    path = tmp_path / "physics.png"
    plot_physics_trial(request.getfixturevalue(case), path, grid_step_m=0.4e-3)
    assert path.stat().st_size > 10_000


def test_physics_figure_handles_legacy_toy_trial(tmp_path):
    path = tmp_path / "toy.png"
    plot_physics_trial(run_trial(TrialConfig(duration_s=0.3)), path, grid_step_m=0.4e-3)
    assert path.stat().st_size > 10_000
