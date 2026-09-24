"""Physiological-scale trial preset for Step 2. Simulation only; not a device model.

Each value records its provenance: a source (mostly via docs/14_feasibility.md),
or "assumed". The toy defaults in TrialConfig are untouched, so experiments
01-20 still reproduce. Nothing here is a clinical claim.
"""

from dataclasses import fields, replace

from src.experiment import TrialConfig

# field: (value, provenance)
PHYSIOLOGICAL = {
    "flow_model": ("poiseuille", "parabolic profile (stage 2b); not CFD"),
    "flow_speed_m_s": (0.30, "M1 cross-sectional mean: TCD mean ~58-60 cm/s halved for Poiseuille (docs/14)"),
    "flow_pulsatility": (0.45, "A = PI/2 with PI 0.9, the midpoint of a reported normal MCA PI of 0.6-1.2 "
                               "(Sci Rep 2020, doi:10.1038/s41598-020-74056-2; range taken from a search "
                               "summary, full text not verified); sinusoidal waveform assumed"),
    "cardiac_period_s": (1.0, "60 bpm, assumed"),
    "particle_radius_m": (100e-6, "just above the ~80 um worst-case minimum at 1 T/m (docs/14); chosen"),
    "max_gradient_t_m": (1.0, "clinical eMNS best case, Navion (docs/14); deliverable at depth is lower"),
    "magnetization_a_m": (1.0e6, "NdFeB, Br ~ 1.26 T, textbook, assumed"),
    "particle_density_kg_m3": (7500.0, "sintered NdFeB, textbook, assumed"),
    "magnetic_volume_fraction": (1.0, "pure magnet, assumed"),
    "fluid_density_kg_m3": (1060.0, "whole blood, assumed (docs/14)"),
    "particle_inertia": (True, "St > 0.1 at this size (docs/14, stage 2c)"),
    "fluid_acceleration_force": (True, "junction turning gives ~90 m/s^2 (stage 2d)"),
    "gravity_m_s2": (9.81, "standard gravity"),
    "gravity_direction": ((0.0, 0.0, -1.0), "vessel-frame orientation, assumed"),
    "sedimentation_check": (True, "diagnostic only; never changes actions"),
    "frame_rate_hz": (15.0, "inside a 7.5-30 fps fluoroscopy range, assumed"),
    "latency_s": (0.05, "toy value retained, assumed"),
    "actuation_period_s": (0.01, "100 Hz field update with zero-order hold, assumed"),
    "gain_saturation_distance_m": (1.5e-3, "saturation distance of the toy controller "
                                           "(3 nN / 2e-6 N/m), assumed"),
    "duration_s": (1.0, "time limit; sweeps set it per flow condition"),
}

# Composite alternative: NdFeB powder in a ~1100 kg/m^3 polymer. 14 vol% gives
# ~2000 kg/m^3. Both numbers are assumed, chosen so settling is slow enough for
# frames to arrive.
COMPOSITE = {
    "particle_density_kg_m3": (2000.0, "NdFeB-polymer composite, assumed"),
    "magnetic_volume_fraction": (0.14, "(2000 - 1100) / (7500 - 1100), assumed"),
}


def physiological_config(material="ndfeb", **overrides):
    """TrialConfig at physiological scale; keyword overrides win over the preset."""
    if material not in ("ndfeb", "composite"):
        raise ValueError("material must be 'ndfeb' or 'composite'")
    known = {f.name for f in fields(TrialConfig)}
    unknown = set(overrides) - known
    if unknown:
        raise ValueError(f"unknown TrialConfig fields: {sorted(unknown)}")
    values = {name: value for name, (value, _) in PHYSIOLOGICAL.items()}
    if material == "composite":
        values.update({name: value for name, (value, _) in COMPOSITE.items()})
    values.update(overrides)
    return replace(TrialConfig(), **values)


def provenance(material="ndfeb"):
    """Field -> provenance string for every preset value."""
    notes = {name: note for name, (_, note) in PHYSIOLOGICAL.items()}
    if material == "composite":
        notes.update({name: note for name, (_, note) in COMPOSITE.items()})
    return notes
