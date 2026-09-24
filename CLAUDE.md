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
- [ ] 2e Gravity + sedimentation gate: diagnostic by default, opt-in gravity compensation
- [x] Viz A: `plot_physics_trial` + `simulations/21_physiological_trial.py` (single trial).
      At 99% flow reduction frames arrive but peak force is ~0.06% of cap: gain needs rescaling.
- [ ] 2f `physiological` preset, flow-reduction factor, `occluded_branch` option,
      imaging sweep 7.5–30 fps (assumed), sweep experiment = 22 (21 is the single-trial viz), docs/15
- Later: viz B (slowed GIF), viz C (interactive page from the 2f sweep data)
One commit per stage; full suite green at each.
