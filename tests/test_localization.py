import numpy as np

from src.localization import PositionKalmanFilter
from src.safety import SafetySupervisor
from src.vessel import YVessel


def test_kalman_update_moves_toward_measurement():
    kf = PositionKalmanFilter(np.zeros(3))
    before = kf.x.copy()
    measurement = np.array([1e-3, 0.0, 0.0])
    after = kf.update(measurement)
    assert after[0] > before[0]
    assert after[0] < measurement[0]


def test_safety_stops_on_large_uncertainty():
    vessel = YVessel()
    supervisor = SafetySupervisor(max_sigma_m=0.3e-3)
    allowed, reason, _ = supervisor.evaluate(
        np.array([5e-3, 0.0, 0.0]), 0.5e-3, vessel, 0.1e-3
    )
    assert not allowed
    assert reason == "localization_uncertain"


def test_safety_allows_well_localized_centerline_state():
    vessel = YVessel()
    supervisor = SafetySupervisor(max_sigma_m=0.3e-3, min_clearance_m=0.2e-3)
    allowed, reason, _ = supervisor.evaluate(
        np.array([5e-3, 0.0, 0.0]), 0.1e-3, vessel, 0.1e-3
    )
    assert allowed
    assert reason == "safe"
