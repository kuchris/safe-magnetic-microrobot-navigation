import inspect
import numpy as np
import pytest

from src.controller import bounded_target_force
from src.imaging import BiplaneFrame, default_views
from src.navigation import BiplaneNavigation
from src.safety import SafetySupervisor
from src.vessel import YVessel


@pytest.mark.parametrize("sigma,tracking,age,expected", [
    (0.5e-3, True, 0, "localization_uncertain"),
    (np.nan, True, 0, "localization_uncertain"),
    (-1, True, 0, "localization_uncertain"),
    (0.01e-3, False, 0, "tracking_lost"),
    (0.01e-3, True, 0.2, "tracking_lost"),
    (0.01e-3, True, np.inf, "tracking_lost"),
])
def test_fail_closed_conditions(sigma, tracking, age, expected):
    supervisor = SafetySupervisor()
    allowed, reason, _ = supervisor.evaluate([5e-3, 0, 0], sigma, YVessel(), 0.1e-3, tracking, age)
    assert not allowed and reason == expected
    np.testing.assert_array_equal(supervisor.filter_force([1, 2, 3], allowed), np.zeros(3))


def test_robust_margin_can_stop_even_when_estimated_margin_is_positive():
    allowed, reason, clearance = SafetySupervisor(min_clearance_m=0.2e-3).evaluate(
        [5e-3, 0.9e-3, 0], 0.11e-3, YVessel(), 0.1e-3)
    assert clearance > 0.2e-3
    assert not allowed and reason == "wall_margin_low"


def test_force_saturation_direction_zero_and_supervisor_limit():
    force = bounded_target_force([0, 0, 0], [3, 4, 0], 1, 2)
    np.testing.assert_allclose(force, [1.2, 1.6, 0])
    np.testing.assert_array_equal(bounded_target_force([1, 2, 3], [1, 2, 3]), [0, 0, 0])
    np.testing.assert_allclose(SafetySupervisor(max_force_n=1).filter_force([3, 4, 0], True), [.6, .8, 0])
    with pytest.raises(ValueError):
        bounded_target_force([0, 0, 0], [1, 0, 0], max_force_n=-1)


def frame(captured, delivery=None, lost=False):
    pixels = None if lost else np.stack([v.project([5e-3, 0, 0]) for v in default_views()])
    return BiplaneFrame(captured, captured if delivery is None else delivery, pixels)


def test_dropout_stale_timeout_recovery_and_duplicates_cannot_reenable():
    navigation = BiplaneNavigation(YVessel(), 0.1e-3)
    assert navigation.step(0, []).reason == "tracking_lost"
    assert navigation.step(.01, [frame(.01)]).reason == "safe"
    assert navigation.step(.06, [frame(.06, lost=True)]).reason == "tracking_lost"
    assert navigation.step(.07, [frame(.01)]).reason == "tracking_lost"
    assert navigation.step(.11, [frame(.11)]).reason == "safe"
    result = navigation.step(.3, [])
    assert result.reason == "tracking_lost"
    np.testing.assert_array_equal(result.force_n, [0, 0, 0])


def test_no_future_frame_or_truth_control_argument():
    navigation = BiplaneNavigation(YVessel(), 0.1e-3)
    with pytest.raises(ValueError):
        navigation.step(0, [frame(0, .1)])
    assert list(inspect.signature(BiplaneNavigation.step).parameters) == ["self", "now_s", "frames"]
    assert not any(hasattr(navigation, name) for name in ("particle", "true_position", "true_position_m"))


def test_invalid_pixels_stop_tracking():
    navigation = BiplaneNavigation(YVessel(), 0.1e-3)
    result = navigation.step(0, [BiplaneFrame(0, 0, np.full((2, 2), np.nan))])
    assert result.reason == "tracking_lost"


def test_saturation_is_reported_without_claiming_a_safety_stop():
    navigation = BiplaneNavigation(YVessel(), 0.1e-3, max_force_n=1e-12)
    result = navigation.step(0, [frame(0)])
    assert result.reason == "actuation_limit" and result.actuation_limited
    np.testing.assert_allclose(np.linalg.norm(result.force_n), 1e-12, rtol=1e-12, atol=0)


def test_invalid_position_shape_fails_closed():
    allowed, reason, _ = SafetySupervisor().evaluate([0, 0], 0, YVessel(), 0.1e-3)
    assert not allowed and reason == "localization_uncertain"
