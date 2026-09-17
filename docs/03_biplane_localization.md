# Simulated biplane localization

## Implemented projection model

Each configurable `OrthographicView` has two orthonormal detector axes in
world coordinates, an origin [m], a pixel size [m/px], and a detector offset
[px]. It maps arbitrary finite 3D points to two detector coordinates:

$$
y_i=H_i p+b_i+\epsilon_i+c_i,\qquad
H_i=U_i/s_i,\quad b_i=o_i-H_i a_i.
$$

`U_i` holds the two axes, `s_i` the pixel size, `a_i` the origin, `o_i` the
offset, `epsilon_i` random detection noise, and `c_i` a fixed calibration
offset error. The default pair observes (x,y) and (x,z). Arbitrary rotations,
translations, pixel sizes, and offsets are supported and tested with points
throughout 3D space. There is no trajectory-specific inversion.

These are two virtual parallel-projection coordinate measurements, not
raster images or a realistic X-ray/fluoroscopy system. There is no finite
detector extent, perspective, occlusion, radiation, image segmentation,
multiple-particle correspondence, or independently timed exposure model.

## Weighted triangulation

Stack both views to form `y = H p + b + error`, with four observations and
three unknowns. Whiten by the detector noise standard deviations and use an
SVD pseudoinverse:

$$
L=(R^{-1/2}H)^+R^{-1/2},\qquad
\hat p=L(y-b),\qquad P_{noise}=LRL^T.
$$

The implementation exposes residual detector error, full 3x3 covariance and
largest-principal-axis standard deviation. Singular/poorly conditioned
geometry raises an error instead of returning a falsely precise position.
The default condition-number ceiling is 1e6. Nonzero declared measurement
noise is required for weighting; noiseless synthetic observations can still
be reconstructed exactly with that positive declared noise.

## Calibration error and uncertainty

The trial draws one fixed 4D detector-offset error per run, each component
with configured `calibration_sigma_px`. Repeated frames share this error.
The triangulator propagates the prior as
`P_calibration = calibration_sigma_px**2 * L @ L.T`.

The filter assimilates only independent measurement-noise covariance. The
constant calibration-position covariance is carried as a separate floor
when exposing total uncertainty. Repeated observations cannot remove it.
This is appropriate to this linear, fixed-geometry additive-offset model;
it is not a calibration solver. An individual fixed bias can exceed its
prior standard deviation. Rotation/scale calibration mismatch or changing
geometry would require a richer error state and covariance model.

## Frame timing and dropout

`BiplaneImager.advance(now, true_position)` is part of the simulated plant.
It captures a synchronized pair at most once each physics tick. It skips
missed acquisition slots instead of inventing historical positions. The
actual capture time is stored; arbitrary frame periods are quantized to
physics ticks. Use `dt <= 1/frame_rate_hz`, enforced by the trial runner.

Frames become available after `latency_s`, rounded up to a physics tick.
Both valid pairs and dropout notifications use this queue. Dropouts can be
independent Bernoulli events or explicitly configured [start,end) bursts.
A dropout represents failure to localize the pair; single-view recovery is
not implemented. Zero latency is supported.

Only delivered `BiplaneFrame` objects enter the navigation loop. It receives
neither true position nor actual calibration bias. Loss cannot be detected
before its delayed report arrives; the independent capture-age timeout also
prevents indefinite actuation while waiting for feedback.
