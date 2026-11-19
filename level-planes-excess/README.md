# Three level planes and the angle excess

**Page:** https://rooster-ninja.github.io/simulations/level-planes-excess/

A perfect, error-free equilateral triangle. Each angle is read in its own
station's horizontal (level) plane, square to that station's vertical. Both
the sphere's radius (10 km to 10⁸ km, then ∞ for a plane) and the triangle's
side (1 km to 200,000 km) can be changed.

## What it shows

- **3D view.** The triangle, the three level planes, the verticals (which
  meet at the centre, or never meet on the plane), the straight sight lines
  and the angle measured in each plane.
- **Theodolite dials.** Each station's level plane seen along its own vertical,
  with the two projected sight lines and the angle read.
- **Overhead, zoomed.** Looking straight down the planar axis: the triangle
  with an arrow at each station showing the direction of its correction, and
  a zoomed bullseye per station with the planar axis at the centre and the
  station's own plumb line as a dot. The gap is Δ (auto-scaled rings), always
  straight toward the triangle's centre with no sideways part.
- **Show the math (collapsed by default).** Under the overhead view: the
  nine steps from three plumb lines to one planar plane, each with live
  numbers for the current radius and side: plumb directions, the planar axis,
  Δ exactly and as d/R, the rotation axis, the Rodrigues rotation matrix for
  A (with a check that it maps A's plumb line onto the planar axis), the
  corrected readings, and the change per station (E/3).
- **Side view.** The cross-section along one side. The angle between the two
  stations' horizontals equals the angle between their verticals, and each
  sight line dips half that angle below its own horizontal. An optional
  exaggeration makes small angles visible and is labelled with its factor.
- **Correct plumbs to one horizontal plane.** A toggle that tips every
  station's zenith axis toward the triangle's centre by Δ, the station's
  angular distance from the centre (Δ = d / R, 32.4″ per km on Earth). The
  instruments are turned in 3D; no angle is corrected. The three horizontals
  become one plane through A, B, C, every sight line has zero dip, and the
  readings sum to exactly 180° on any sphere. Δ is shown at each station; it
  is the convergence of the plumb lines, so the correction needs the
  curvature it removes.
- **Excess against area.** Log-log plot: straight lines of slope 1 whose height
  is K. A table runs the same side length on spheres from 1,000 km to ∞.

## How it works

- Stations sit on a circle of angular radius ρ, sin ρ = (2/√3) sin(s/2R).
- The vertical at a station is the sphere's unit normal. Each sight line is
  projected onto the level plane, and the angle is taken between the two
  projected directions (atan2 of their cross and dot products).
- Area is measured independently by tiling the surface with flat facets whose
  corners lie on the sphere (2,304 and 9,216 facets, Richardson-extrapolated).
- Measured K = E / A. The page never uses E = A / R²; the ratio to 1/R² is
  shown as a check and comes out 1.000000.
- Corrected plumbs: each station's frame (axis, plane basis) is replaced by
  the centroid's vertical and horizontal, and sight lines are the chords projected onto that plane.
  Δ = angle between plumb line and axis; dip = asin(chord · axis / |chord|).
- Arithmetic is arranged to avoid cancellation, so excesses down to about
  10⁻¹⁴ rad are reliable.

## Errors used

None, by design: no σ is attached. Angle reading error, deflection of the
vertical, refraction and ellipsoidal shape are all set to zero; the errors
panel lists their real-survey sizes and points to the triangulation-chain and
Gauss's great triangle pages, which carry them.

## Simplifications

- Sphere only; the verticals are the sphere's normals by construction. The page
  shows what a perfect sphere would give, not that Earth is one.
- Sight lines are straight chords, even where they would run below the horizon.
- Equilateral triangle only, limited to a quarter of the sphere (side ≤ 109.47°
  of arc).

## Sources

- C. F. Gauss (1827), *Disquisitiones generales circa superficies curvas*,
  Art. 20, in the Morehead & Hiltebeitel translation:
  [Project Gutenberg #36856](https://www.gutenberg.org/ebooks/36856)
- H. Moritz, [Geodetic Reference System 1980](https://iag.dgfi.tum.de/media/archives/HB2000/part4/grs80_corr.htm):
  mean radius R₁ = 6 371 008.7714 m (Earth preset)
