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
  built from docs/results of experiments 22–24. Later: viz B (slowed GIF).
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

## Open questions for the user (Step 3 candidates)
- Local flow measurement at the split (not just mean speed); combined model errors.
- Open-loop gravity hold from release (gravity direction known a priori) for pure NdFeB.
- Any strategy for occluded targets (currently 0/432); needs better flow model at the stump.
- Note: `poiseuille_flow` was vectorized in 2f (profile values unchanged up to round-off).
