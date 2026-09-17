# Six-state estimation and latency

The biplane experiments use `KinematicKalmanFilter` with state
`x = [px, py, pz, vx, vy, vz]`. The original `PositionKalmanFilter` is retained
for the direct-sensor baseline. Both use separate prediction and update.

## Prediction

$$
F(\Delta t)=\begin{bmatrix}I&\Delta t I\\0&I\end{bmatrix},\quad
Q(\Delta t)=q\begin{bmatrix}\Delta t^3 I/3&\Delta t^2 I/2\\
\Delta t^2 I/2&\Delta t I\end{bmatrix}.
$$

`q` is a continuous white-acceleration spectral density [m^2/s^3], not an
acceleration standard deviation. Position covariance has units m^2,
velocity covariance m^2/s^2, and cross covariance m^2/s.

The biplane estimator is a constant-velocity model. It does not receive true
flow/force or oracle displacement. Changes of force, flow and branch are
model mismatch covered only approximately by process noise. A future
control-input-aware model should use commanded inputs and estimated flow.

## Update and public state

Use `H = [I,0]`, reconstructed position and random-noise covariance in a linear
Kalman update. Solve the innovation system without an explicit inverse and
use the Joseph covariance update to preserve numerical symmetry and PSD.

Public copies expose `estimated_position`, `estimated_velocity`, full 6x6
`covariance`, and `position_uncertainty = sqrt(lambda_max(P_position))`.
The latter includes the separate fixed calibration floor. These copies do
not provide a mutable reference to the filter's internal state.

## Delayed observation handling

1. Before the first valid delivered reconstruction there is no estimate;
   active force is zero. No initialization uses true particle position.
2. Keep an anchor filter at the capture time of the last accepted image.
3. When the next ordered observation arrives, predict that anchor to the
   new capture time, then update with its reconstruction.
4. To control at the current time, predict a copy from the anchor to now.
   Repeated polling never advances or updates the anchor twice.

This exactly separates filtering at measurement time from prediction to
control time for ordered, synchronized, fixed-latency observations. Covariance
grows with elapsed time even when no valid image arrives. It avoids updating
the current state with an old position as though it were current.

`DelayedStateEstimator` rejects duplicate/out-of-order observations and
future capture timestamps. The navigation wrapper ignores duplicate/old
frames without letting them re-enable tracking. Delivered future frames
raise an error. Variable-latency reordering would require a replay/smoothing
buffer and is not implemented.

## Limits

Filter covariance is model-based uncertainty, not a guaranteed error bound.
Non-Gaussian outliers, mismatched calibration priors and unmodeled dynamics
can make it overconfident. Reconstruction residuals are exposed, but no
innovation/outlier gate is implemented in this milestone. A `k_sigma=3`
largest-axis margin is not a claim of 99.7% simultaneous 3D containment or
a proven collision probability bound.
