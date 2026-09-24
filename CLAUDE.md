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
- Later: viz B (slowed GIF), viz C (interactive page from the sweep data)
One commit per stage; full suite green at each.

## Open questions for the user (Step 3 candidates)
- Delay-aware control at physiological scale (existing prediction module, feedforward, MPC).
- Open-loop gravity hold from release (gravity direction known a priori) for pure NdFeB.
- Any strategy for occluded targets (currently 0/432); needs better flow model at the stump.
- Note: `poiseuille_flow` was vectorized in 2f (profile values unchanged up to round-off).
