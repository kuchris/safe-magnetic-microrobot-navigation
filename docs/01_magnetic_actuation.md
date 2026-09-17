# Lesson 01 — Magnetic Actuation

## Goal

Understand the difference between using a magnetic field to **orient** a magnetic particle and using a magnetic-field gradient to **translate** it.

## 1. Intuition first

A magnetic particle can be modeled, initially, as a magnetic dipole with magnetic moment vector **m**.

A roughly uniform external field **B** tries to align the particle with the field. That is primarily a rotational effect.

A spatially varying field can also pull the particle toward a region of different magnetic energy. That is the translational effect we need for navigation.

This distinction matters: **a strong field is not automatically a strong pulling force**. Translation depends on how the field changes with position.

## 2. Torque

For a magnetic dipole,

```text
tau = m x B
```

Magnitude:

```text
|tau| = |m| |B| sin(theta)
```

where:

- `tau`: torque [N m]
- `m`: magnetic dipole moment [A m^2]
- `B`: magnetic flux density [T]
- `theta`: angle between m and B

Check your intuition:

- theta = 0 deg -> torque = 0
- theta = 90 deg -> torque is maximal

So a uniform B field can act like a compass-aligning field.

## 3. Translational force

For a fixed dipole approximation,

```text
F_m = grad(m . B)
```

The dot product `m . B` has units of energy [J]. Taking its spatial gradient gives force [N].

In one simplified dimension, if m is aligned with B,

```text
F_x ~= m dB/dx
```

This immediately tells us something important:

```text
dB/dx = 0  ->  no translational force in this simplified model
```

Even if B itself is large.

## 4. Why multiple external coils?

In 3D we want to control a desired force vector

```text
F_des = [Fx, Fy, Fz]
```

using coil currents

```text
I = [I1, I2, ..., IN]
```

A useful local approximation is

```text
F ~= A(x) I
```

where `A(x)` is a position-dependent actuation matrix obtained from the coil geometry/field model.

Then control becomes an inverse problem:

```text
Given F_des and current position x,
find coil currents I subject to current/field/safety limits.
```

Later we will solve constrained versions of this problem rather than blindly inverting A.

## 5. The first dynamics model

At small scales in a viscous fluid, inertia often becomes much less important than drag. For a spherical particle in the Stokes regime,

```text
F_drag = 6 pi eta r (u - v)
```

At quasi-steady force balance,

```text
F_m + F_drag ~= 0
```

therefore

```text
v ~= u + F_m / (6 pi eta r)
```

This is our first simulation equation.

It says the particle velocity is approximately:

```text
local fluid velocity + magnetic drift velocity
```

## 6. Why this is useful for safety

Suppose the controller commands a magnetic force toward a target. Blood/fluid flow may push sideways. The actual motion is therefore not necessarily parallel to the magnetic force.

That is why a safe system needs repeated localization and feedback rather than a single open-loop command.

## Exercise A

A magnetic moment is exactly parallel to a uniform magnetic field.

1. What is the magnetic torque?
2. Does the equation `F = grad(m.B)` guarantee a translational force merely because B is large?
3. What physical property of B is required for translation?

Try answering these without looking back.

## Exercise B

In the overdamped approximation,

```text
v = u + F_m / gamma
```

with

```text
gamma = 6 pi eta r
```

If `u = [1, 0, 0] mm/s` and magnetic drift `F_m/gamma = [0, 0.5, 0] mm/s`, what is the resulting velocity vector?

## Next lesson

We will study why the Reynolds number becomes small, derive Stokes drag intuition, and decide when this overdamped model is reasonable and when it breaks down.
