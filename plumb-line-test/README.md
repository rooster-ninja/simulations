# Plumb line curvature test

A shareable summary of a proposed field experiment that tests whether the ground is curved, set up as a null-hypothesis test.

## What it shows

- **Hypotheses:** H₀ flat (κ = 0, plumb lines parallel) against H₁ curved (κ > 0, plumb lines converge, γ = d / R).
- **Method:** a fixed zenith camera at each station plate-solves the stars overhead to find the local vertical. Radio time-of-flight ranging (SX1280, "Alpha" and "Chimp") gives the distance between stations. Curvature along the line is κ = γ / d.
- **Diagrams:** flat vs curved zenith directions under parallel starlight, the L-shaped station layout (north and east legs, giving K = κ_NS × κ_EW), and the camera rig with inclinometer and 180° reversal.
- **Equipment list:** what's on hand and what to buy.
- **Field procedure and pre-registered decision rule:** reject H₀ at z > 3.3 (α = 0.001, one-sided), check globe consistency, check that γ is the same for every star, and blind the distances until the zenith reduction is done.
- **Expected numbers:** γ and z for baselines from 20 to 150 km.

## Model and simplifications

- Globe values use WGS-84 radii of curvature at 50° N: 6,373 km (meridian) and 6,391 km (prime vertical). The predicted signal is about 32.4″ per km of baseline.
- Error budget assumes about 20″ per station for a MEMS inclinometer after reversal, and about 5″ for a good machinist level. TOF error is treated as negligible.
- Deflection of the vertical (roughly 5–30″) and zenith refraction are noted but not modelled.
- Curvature in the diagrams is exaggerated for visibility.

This page is static: it has no interactive controls.
