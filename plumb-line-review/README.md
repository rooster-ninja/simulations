# Plumb line test review

Companion to [plumb-line-test](../plumb-line-test/). A review of what the zenith test measures and what it can and cannot conclude.

## What it covers

- **Measurements and outputs:** radio time-of-flight distance, zenith per station (camera + tilt sensor + reversal turntable), and the angle γ between zeniths, with example JSON output formats.
- **Celestial navigation link:** 1′ of zenith shift = 1 nautical mile; 55 km = 29.7′ ≈ 1,782″. The observer-centred celestial sphere uses directions only, so its radius never enters.
- **Fairness critique:** γ is measured relative to the star field. Flat ground with a star dome at H ≈ 6,400 km predicts the same γ as a globe with distant stars, so γ alone rules out only "flat ground, distant stars". γ is extrinsic, not Gaussian curvature.
- **Where the models diverge:** globe x/R vs flat-dome atan(x/H) with H = R: 0.04″ at 55 km, 4.4′ at 1,000 km, 106′ at 3,000 km, 410′ at 5,000 km.
- **Open items:** star distance (to revisit), longer baselines, a star-free radio-ranging test.

## Simplifications

- The flat-dome comparison uses the simplest case: a flat star layer at height H directly above the plane.
- JSON blocks are example values showing the format, not measurements.

This page is static: it has no interactive controls.
