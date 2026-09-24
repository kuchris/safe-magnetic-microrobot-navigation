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
- [ ] 2c Inertial particle (reduced Maxey–Riley, added mass, Schiller–Naumann, exponential
      integrator; no Basset/lift); must reduce exactly to overdamped as τ→0
- [ ] 2d Quasi-steady pulsatility; report Womersley α (~2.1–2.3 at M1)
- [ ] 2e Gravity + sedimentation gate: diagnostic by default, opt-in gravity compensation
- [ ] 2f `physiological` preset, flow-reduction factor, `occluded_branch` option,
      imaging sweep 7.5–30 fps (assumed), experiment 21, docs/15
One commit per stage; full suite green at each.
