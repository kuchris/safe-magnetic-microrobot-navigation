# CLAUDE.md

## Rules
- Before writing any code, give me a detailed plan and wait for my confirmation.
- All new features are disabled by default; the existing experiments (01–20) must remain reproducible.
- Every parameter must cite its source or be marked as assumed; never claim clinical efficacy.
- Run `python -m pytest -q`; new changes must not introduce new failures.

## Status
- docs/14_feasibility.md: at M1-level blood flow (~0.3 m/s), a ~1 T/m eMNS requires a
  radius ≳80 µm, which is exactly where the overdamped Stokes assumption breaks down (St > 0.1);
  pure NdFeB needs 0.063 T/m to counter gravity; reducing proximal blood flow is more
  effective than increasing the gradient.
- Resolved: the 2 archived-equality tests (test_flow_models, test_terminal_guidance) now compare
  float summary fields with rel=1e-8 via `assert_summary_matches`; all other fields stay exact.
- Experiments 01–20 = `simulations/01_*.py` … `simulations/20_*.py`.
- Adding keys to `run_trial`'s summary breaks archived comparisons; new physics metrics go
  under `summary["physics"]`, present only when a new feature is enabled.

## Step 2 (approved plan): physiological scale, not toy
Toy defaults stay for 01–20 reproducibility; new work builds a `physiological` preset.
At 0.3 m/s the 10 mm approach is ~33 ms (< 1 imaging frame): show closed-loop failure
honestly, do not tune the controller to hide it.
- [x] 2a Gradient cap T/m + material (`max_gradient_t_m`, `particle_radius_m`,
      `magnetization_a_m`, `magnetic_volume_fraction`); `gain_n_per_m` not yet rescaled
- [x] 2b Poiseuille profile (`flow_model="poiseuille"`, U = cross-sectional mean) + auto dt
      (`max_step_radius_fraction=0.02`, assumed). Controller runs every physics tick, so the
      control rate rises as dt shrinks: add an actuation update period (ZOH) in 2f.
      First real-scale run: collides at 23 ms, before the first frame arrives (50 ms latency).
- [x] 2c Inertial particle (`particle_inertia`, `particle_density_kg_m3`, `fluid_density_kg_m3`):
      reduced Maxey–Riley, exact-per-step exponential integrator, released at local flow.
      Omits fluid-acceleration term, Basset, lift. Off-axis 100 µm at 0.3 m/s: St 0.15,
      Re_slip ~10, cross-stream shift 0.2–0.5 mm vs overdamped (both passive).
- [x] 2d Quasi-steady pulsatility (`flow_pulsatility`, `cardiac_period_s`, `cardiac_phase`),
      α reported; `fluid_acceleration_force` ((3/2) m_f Du/Dt, inertial only). PI/A still unsourced.
      Finding: transit ~40 ms ≈ 4% of a cycle; success vs outlet-cap collision flipped on 9 µm
      around the 0.4 mm tolerance → 2f should report closest approach as a continuous metric.
      Toy replay helpers (failure_analysis, flow_sensitivity) ignore pulsation.
- [x] 2e Gravity (`gravity_m_s2`, `gravity_direction`), `sedimentation_check` (diagnostic,
      horizon 0.1 s assumed), `gravity_compensation` (−W within cap, only while tracking valid).
      Finding: pure NdFeB at 99% flow reduction hits the wall at 47 ms, before the first frame,
      so tracking-gated compensation never engages. Composite (2000 kg/m³, 14% NdFeB, assumed):
      unheld → wall at 260 ms after a gate stop; held → no contact in 3 s.
      Open question for the user: open-loop hold from release (gravity direction known a priori).
- [x] Viz A: `plot_physics_trial` + `simulations/21_physiological_trial.py` (single trial).
      At 99% flow reduction frames arrive but peak force is ~0.06% of cap: gain needs rescaling.
- [x] 2f `src/presets.py` (`physiological_config`, per-value provenance; PI 0.6–1.2 from a search
      summary of Sci Rep 2020, full text unverified), `occluded_branch` (poiseuille only),
      `actuation_period_s` (ZOH), `gain_saturation_distance_m`, `closest_target_approach_m`.
      Experiment 22 = `src/physiological_sweep.py` + `simulations/22_*` (864 trials, ~75 s on 8 cores),
      archived in docs/results/physiological_sweep, write-up docs/15.
      Deviation: flow reduction lives in the physiological sweep, not the toy benchmark (toy
      scenario timings are seconds; real transits are tens of ms).
      Findings: pure NdFeB 0/432 (sediments before first frame); no success at 0% reduction;
      composite + 99% + delay-limited gain (0.5·γ/τ_d, assumed) + gravity hold 18/18 patent;
      toy-equivalent gain overshoots (delay·cap/γ = 5–11 R); occluded target 0/432.
- Viz C done: private artifact "Microrobot Steering Atlas" (https://claude.ai/artifact/FpUbV7Yhc51w2Nz1Avgumo),
  built from docs/results of experiments 22–28 (v2 flow-model errors, v3 measured map, v4 robustness).
- Viz B done: `simulations/27_steering_animation.py` (P0 vs P2, occluded cell, ~2× slow-motion GIF,
  docs/figures/steering_occluded_p0_vs_p2.gif).
One commit per stage; full suite green at each.

## Step 3.1: delay-aware control (experiment 23, docs/16)
- New opt-in options: `flow_feedforward` (needs command_aware; subtracts known weight when a
  hold is on), `model_drag_error` (controller drag scale). Study: `src/delay_aware_study.py`,
  P0 = exp-22 policy (archives match), pilot seeds 0–2, held-out 3–5, ±20% drag on held-out.
- Held-out: P2 (command-aware + gain 0.5·γ/T_a, T_a = 10 ms) reaches occluded targets at 99%
  in 18/18 (P0 1/18), robust to ±20% drag; patent median 0.79 s vs 2.78 s. 90% still ≤ 5/18.
  H1 partly, H2 and H3 not supported. Wall prediction (P4/P5) regresses at 7.5 fps
  (horizon τ_d = 183 ms over-constrains; ends at closed-outlet-cap proxy or times out).

## Step 3.2 (decided by Claude under "you decide everything"): experiment 24
- Options (opt-in): `model_flow_feedforward` + `flow_model_error` (controller uses the prescribed
  flow model, nominal U scaled, cardiac phase and occlusion known: assumed), and
  `gravity_hold_from_release` (open-loop hold before/without tracking; gravity direction known).
- Arms: composite C_P2 (baseline), +model FF, +wall prediction with 50 ms horizon, both;
  NdFeB N_P2 + release hold (baseline), + model FF. 90%/99% × 7.5/15/30 fps × patent/occluded.
- Pre-registered: H4 release hold lets pure NdFeB reach patent targets at 99%; H5 model FF
  lifts 90% above P2 and survives ±20% flow-model error; H6 50 ms horizon removes the 7.5 fps
  wall-prediction regression and keeps its 90% benefit. Pilot seeds 0–2, held-out 3–5.

- Done (docs/17, held-out): H4 supported (pure NdFeB + release hold 18/18 patent and occluded
  at 99%); H5 half (model FF at 90%: composite 7/18 patent, 8/18 occluded; NdFeB 6/18, 11/18;
  needs ≥15 fps; ±20% flow-model error removes most of it); H6 half (50 ms horizon: no 99%
  regression, no 90% benefit). Found/fixed (opt-in `estimator_knows_weight`): exp-23 estimator
  read a held weight as commanded motion. Model FF also feeds u_model to the estimator.
  Limitation noted: Stokes command model vs Re_slip ~10 for NdFeB commands.

## Step 3.3 (user request): flow-model shape and phase errors, experiment 25
- Plant unchanged; only the controller's flow model is wrong. Conditions: exact, scale ±20%,
  phase +0.1/0.25/0.5 period, pulsation A_model 0/0.9, profile exponent n 4/9 (flux-equivalent),
  junction transition/width ×0.5/×2 (all assumed). Arms C_P2_modelff, N_P2_modelff_hold;
  90%/99%; held-out seeds 3–5 only (robustness test, no tuning).
- Pre-registered: H7 phase ≤0.1 keeps ≥ half the exact successes, 0.25/0.5 lose most; H8 blunt
  profiles (centerline −25%/−39%) lose most; H9 steady model (A=0) keeps < half; H10 success at
  90% falls with route-averaged model velocity error, > ~10 mm/s loses most; 99% stays 18/18.

- Done (docs/18): exact reproduces exp 24 (32/72 at 90%); 99% is 72/72 under every error.
  H7, H8, H9 supported; H10 not as a single predictor: junction ×2/×0.5 (route error ≤ 1 mm/s)
  swing occluded success 19/36 → 0/36 or 22/36; phase +0.1 is gentler than equal-size bias.
  Reading: the 90% result is a knife edge set by flow shape at the split.

## Step 3.4 (goal "keep going", chosen by Claude): measured flow map, experiment 26
- Controller flow model = voxelized, noisy map of the plant's time-mean field (trilinear
  interpolation, fixed Gaussian noise per lumen voxel, pulsation waveform ECG-gated and exact).
  Voxel 0.25/0.5/1.0 mm, noise 5%/10% of centerline mean at 0.5 mm, plus 1.0 mm + 10% (assumed).
  Arms as exp 25; held-out seeds 3–5; 90% all conditions, 99% worst condition only.
- Pre-registered: H11 0.25 mm noiseless keeps ≥ 80% of exact successes; H12 success falls with
  voxel size, 1.0 mm loses most; H13 5% noise costs little, 10% more but keeps some; 99% stays 18/18.

- Done (docs/19): exact reproduces exp 25; 0.25/0.5 mm maps 38/41 of 72 at 90% (exact 32;
  0.25 mm loses none of the exact successes); 5% noise 35, 10% noise 20; 1.0 mm 8 (occluded 0);
  99% worst map 72/72. H11, H13 supported; H12 at 1.0 mm only. 7.5 fps: 0 in every condition.

## Step 3.5 (goal "keep going"): robustness of the operating point, experiment 28
- Found while designing: the gate's 0.15 s max measurement age is shorter than latency + frame
  period at 7.5 fps (0.183 s), so 7.5 fps loses tracking ~7% more of the time. The "7.5 fps
  floor" in docs/17–19 may be partly this gate setting. Exp 28 gate check re-runs the exp-24
  model-FF arms at 90% with max age = latency + 1/fps + 0.02 s (assumed margin), paired.
- Robustness at 99% (arms C_P2 and N_P2_hold, matched gate everywhere, plus fixed-gate nominal):
  latency 0.1/0.2 s, 0.3 s dropout, actuation gain ±20%, gradient 0.5/0.25 T/m, gravity-model
  tilt 15/30°, calibration 1 px, noise 3 px (all assumed). Held-out seeds 3–5.
- Pre-registered: H14 latency 0.1 keeps ≥ 80%, 0.2 ≥ 50%; H15 gain ±20% ≥ 80%; H16 0.5 and
  0.25 T/m ≥ 80%; H17 tilt 15° tolerable, 30° starts failing pure NdFeB; H18 0.3 s dropout ≥ 50%;
  H19 matched gate gives 7.5 fps successes at 90% (floor partly a gate artifact).

- Done (docs/20): nominal 72/72 either gate; latency 0.1 s, 0.5/0.25 T/m, 1 px calibration, 3 px
  noise: 72/72. Latency 0.2 s 59 (composite only); gain ±20% 60/64 and tilt 15° 60 (all NdFeB at
  7.5 fps); tilt 30° NdFeB 0/36; dropout 0.3 s 27 (composite 0/36: tracking-gated hold). H14–H16
  supported, H17 partly, H18 and H19 not (7.5 fps floor is real). Exploratory follow-up: composite
  with open-loop hold 36/36 nominal, 30/36 under dropout.

## Step 3.6 (goal "keep going"): combined perturbations, experiment 29
- Both materials with the open-loop hold (composite C_P2 + gravity_hold_from_release; N_P2_hold),
  matched gate, 99%, held-out seeds 3–5. Bundles (assumed): nominal; mild (latency 0.1, gain −10%,
  tilt 5°, calib 0.5 px, noise 2 px, 0.5 T/m); moderate (latency 0.1, gain −20%, tilt 10°, calib
  1 px, noise 3 px, 0.5 T/m, dropout 0.2 s); severe (latency 0.2, gain −20%, tilt 15°, calib 1 px,
  noise 3 px, 0.25 T/m, dropout 0.3 s).
- Pre-registered: H20 mild ≥ 90%; H21 moderate ≥ 70%; H22 severe < 50%, failures concentrated at
  7.5 fps and in pure NdFeB.

- Done (docs/21): nominal 72/72, mild 68 (H20 ok), moderate 33 (composite 33/36, NdFeB 0/36; H21
  not supported), severe 11 (H22 partly). Exploratory: removing any one moderate ingredient leaves
  NdFeB 0/36; mild + one raised: dropout 4/36, gain 12, tilt 20, noise 24, calibration 28.
  Mechanism: hold bias (gain/tilt) is unmodeled force; weight-aware Smith predictor stays
  confidently wrong until fresh frames reveal it. Next: disturbance-force estimation.

## Open questions for the user (Step 3 candidates)
- Make the open-loop hold the default for physiological runs? (changes the preset; would need
  re-running exp 22–28 comparisons or a new preset name).
- Combined perturbations; spatially correlated map noise; flow changes after measurement.
- Open-loop gravity hold from release (gravity direction known a priori) for pure NdFeB.
- Any strategy for occluded targets (currently 0/432); needs better flow model at the stump.
- Note: `poiseuille_flow` was vectorized in 2f (profile values unchanged up to round-off).
