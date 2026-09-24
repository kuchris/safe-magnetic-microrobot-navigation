# Order-of-magnitude feasibility at cerebral scale

Computational research/education only. This is an analytical estimate, not a
device design, not a safety claim and not clinical guidance.

## Question

The simulator so far uses toy flow (0.6 mm/s) and a 3 nN force cap. Before
adding realism, this note asks: **at physiological cerebral flow, what
particle size and magnetic gradient are needed to steer into an occluded
branch, and is the simulator's overdamped Stokes model valid there?**

## Scenario

A medium/large-vessel occlusion distal to a bifurcation: the parent segment is
M1-like and the target branch is occluded. Because the target branch carries
little or no outflow, essentially every streamline leaves through the patent
branch. The particle must therefore **cross streamlines** to the target-side
wall within an approach length `L`, instead of riding a favourable flow split.
This is the physical version of the repository's wrong-branch failure mode.

## Model

Parent flow is Poiseuille along a diameter: `u(y) = 2U(1 - y²/R²)`. A constant
gradient gives lateral force `F = V·M·|∇B|` on a saturated sphere of volume
`V`. With Stokes drag, the lateral drift speed is constant and the axial
distance needed to move from `y0` to `y1` is `∫ u(y) dy / v⊥`. From the axis to
the wall this integral is `4UR/3`, giving the closed form

$$
|\nabla B|_{req} = \frac{6\,\eta\,U R}{M\,r^2\,L}.
$$

The requirement scales as `1/r²`: halving the radius quadruples the gradient.
The implementation (`src/feasibility.py`) adds two corrections that can only
increase the requirement: a first-order Lorentz wall factor `1 + 9r/(8h)` for
motion toward the wall, and the empirical Schiller–Naumann drag factor
`1 + 0.15 Re^0.687` at the required slip speed. The end point keeps a gap of
one particle radius to the target-side wall.

Holding against net weight needs `|∇B| = Δρ g / M`, independent of size.

Model-validity checks, computed for every radius:

- Stokes number `St = τU/L`, with `τ = 2(ρp + ρf/2)r²/(9η)` including added mass.
  `St ≤ 0.1` is used here as the overdamped limit (a chosen threshold).
- Slip Reynolds number at the required lateral speed, and wall-shear Reynolds
  number `ρ(4U/R)r²/η`. Values above 1 mean Stokes drag and the neglect of
  shear-induced lift are not justified.
- Diameter ratio `r/R ≤ 0.25` (a chosen threshold).

## Parameters and provenance

| Quantity | Value | Source / status |
|---|---|---|
| M1 lumen diameter | 2.7–3.4 mm → R = 1.5 mm | MRI measurements: ~2.73 mm (AJNR, PMC8174897); ~3.3–3.4 mm (AJNR 18(10):1929) |
| MCA TCD mean velocity | ~58–60 cm/s | PubMed 2095006; PMC2913920 |
| Cross-sectional mean U | 0.30 m/s | TCD reports the spectral envelope (≈ centreline); halved for Poiseuille. Cross-check: ~170–180 mL/min MCA flow (Ultrasound Med Biol, 2014) over a 3.3 mm lumen gives ~0.34 m/s |
| Systolic factor | 1.6 × U | **Assumed**, not sourced |
| Approach length L | 10 mm | **Assumed**, swept via `--approach-mm` |
| Blood viscosity / density | 3.5 mPa·s / 1060 kg/m³ | **Assumed** typical high-shear values |
| NdFeB magnetization / density | 1.0×10⁶ A/m / 7500 kg/m³ | **Assumed** textbook values (Br ≈ 1.26 T) |
| Clinical MRI imaging gradients | 0.02–0.04 T/m | US patent 11181593 background |
| Research MRI gradient platform | ~0.3–0.4 T/m | Connectom 300 mT/m (Siemens 2020); 400 mT/m imaging (ISMRM 2025) |
| Clinical eMNS | up to 1 T/m at 30 mT | Double Navion, *Clinically ready magnetic microrobots for targeted therapies*; Navion: Gervasoni et al., Adv. Mater. 2024 |
| Permanent-magnet systems | 0.7–2.9 T/m reported | Comparison cited in *Robotically Adjustable Magnetic Navigation System for Medical Magnetic Milli/Microrobots* |

System gradients are **peak or best-case values**. At an M1 depth of roughly
4–6 cm (TCD insonation depth, PubMed 2095006) the deliverable gradient will
generally be lower. The reference lines are therefore optimistic.

## Results

Run: `python -m simulations.20_feasibility`

![Feasibility map](figures/feasibility_map.png)

| Actuation reference | Nominal: smallest radius | Worst case: smallest radius | Worst case, 90% flow reduction |
|---|---:|---:|---:|
| Clinical MRI (0.04 T/m) | ~215 µm, overdamped invalid | not reachable | not reachable |
| Research MRI (0.4 T/m) | ~58 µm | ~146 µm, overdamped invalid | ~25 µm |
| eMNS (1 T/m) | ~35 µm | ~79 µm | ~15 µm |
| Permanent magnets (2.9 T/m) | ~20 µm | ~41 µm | ~9 µm |

Worst case means 1.6 × mean flow, starting at the far wall, with gravity in the
least favourable direction. The overdamped model stops being valid (St > 0.1)
at a radius of about **82 µm**.

Findings:

1. **Pure NdFeB cannot be held against gravity by clinical MRI imaging
   gradients** (0.063 T/m required, 0.04 T/m available). A dead-end branch is
   also a sedimentation trap: an unsupported 100 µm-radius particle settles at
   roughly 30 mm/s and reaches the wall of a 3 mm lumen within about 0.1 s.
2. **With a ~1 T/m eMNS the worst-case window is a knife edge.** It needs
   r ≳ 80 µm, which is where the overdamped assumption fails. Useful steering
   happens at slip Reynolds numbers of 1–10, not in the Stokes regime.
3. **Reducing proximal flow is a larger lever than increasing gradient.**
   A hypothetical 90% flow reduction lowers the worst-case minimum radius from
   ~79 µm to ~15 µm at 1 T/m, back inside the overdamped regime. Clinically,
   proximal flow control during thrombectomy (for example, balloon guide
   catheters) exists; whether it would reduce flow this much in this setting
   is **not established here**.
4. **The toy simulator is dynamically closer to reality than its units
   suggest.** Its drift-to-flow ratio `Π = (F/γ)/U` is about 0.76
   (3 nN, r = 0.1 mm, 0.6 mm/s). A 100 µm-radius NdFeB sphere at 1 T/m in
   0.3 m/s flow gives a Stokes-estimate Π ≈ 2.1. What the toy misses is not
   the force-to-flow ratio but finite Reynolds number, inertia, the velocity
   profile and pulsatility.

## Implications for the simulator

- Replace the nN force cap with a **gradient cap in T/m** plus material and
  size, so limits map to real hardware.
- Add a Poiseuille (then pulsatile) velocity profile before any CFD work.
- For r ≳ 80 µm, add particle inertia and finite-Re drag
  (a reduced Maxey–Riley model) and shear-induced lift, or restrict
  experiments to the overdamped window.
- Add gravity and a sedimentation check to the safety gate. "Zero force"
  is not a hold state in a stagnant branch.
- Treat flow reduction as an explicit experimental factor.

## Limitations

- One-dimensional lateral path along a diameter. No 3D bifurcation geometry,
  no secondary flow, no recirculation at the occluded orifice.
- Uniform gradient over the approach length; real fields decay with depth
  and couple field magnitude, gradient and torque.
- Lorentz wall correction is first order and underestimates drag very close
  to the wall. Schiller–Naumann is an unbounded-fluid correlation.
- Blood is treated as a Newtonian continuum. The particle size is comparable
  to many red-cell diameters, and near-wall cell-free layers are ignored.
- No imaging constraint. Tracking a 50–200 µm particle through the skull at
  video rate is a separate, possibly harder, problem.
- No embolic-risk analysis. A lost particle of this size would lodge in a
  distal arteriole; retrieval or degradability is outside this model.
