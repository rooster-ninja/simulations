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
- **Drop between stations.** Readouts for how far B sits below A's level
  plane over the side s (2R sin²(s/2R) along A's vertical, ≈ s²/2R: 785 m
  over 100 km on Earth), how far A's plane is above B measured up B's own
  plumb line (R(sec(s/R) − 1)), and how far the straight sight line A–B runs
  below the surface at the midpoint (≈ s²/8R). The drop is also marked at B
  in the 3D view and stated in its caption.
- **Theodolite dials.** Each station's level plane seen along its own vertical,
  with the two projected sight lines and the angle read.
- **Overhead, zoomed.** Looking straight down the planar axis: the triangle
  with an arrow at each station showing the direction of its correction, and
  a zoomed bullseye per station with the planar axis at the centre and the
  station's own plumb line as a dot. The gap is Δ (auto-scaled rings), always
  straight toward the triangle's centre with no sideways part.
- **Error circles (overhead view).** 1σ circles drawn around each plumb
  line: digital zenith camera 0.1″ (Hirt et al. 2010), total-station
  compensator 0.5″ (Leica TS10 datasheet), and deflection of the vertical
  10″ (Brocken) and 60″ (NGS: can reach an arcminute). Each can be switched
  off; "Zoom to the error circles" centres the bullseye on the plumb line and
  scales the rings to the errors, with the planar axis shown by an arrow when
  it is off the edge. A table gives Δ ÷ each error. The first two are
  measurement errors; deflections are real departures of gravity from a
  smooth surface.
- **Show the math (collapsed by default).** Under the overhead view: the
  nine steps from three plumb lines to one planar plane, each with live
  numbers for the current radius and side: plumb directions, the planar axis,
  Δ exactly and as d/R, the rotation axis, the Rodrigues rotation matrix for
  A (with a check that it maps A's plumb line onto the planar axis), the
  corrected readings, the change per station (E/3), and an expanded "what it
  takes": what a bubble can and can't give, the six tilts the rotation needs,
  why comparing plumb lines is first order in curvature (δ = s/R) while the
  excess is second order, the ways to compare plumb lines and what each
  assumes, and the zenith-camera error budget.
- **The planes extended: a three-sided pyramid.** Each level plane is extended
  until it meets the other two. Overhead, the three ridges run along the
  medians, crossing each side's midpoint, and meet at an apex above the
  triangle's centre; a vertical cut along A's median shows A's plane rising to
  the apex and the B–C ridge falling away (heights exaggerated, with the
  factor shown). Readouts give the apex and ridge heights above the surface,
  the fold at each ridge (= δ), the face angles at the apex, and the angle
  defect 360° − sum, which equals the excess E (ratio 1.000000 at every size;
  the octant gives a cube corner, 270°, defect 90°). The same faces can be
  drawn in the 3D view with "Extend planes to pyramid".
  The three face pieces (station → ridge over each midpoint → apex) are
  highlighted in both views, with their areas: each is a flat kite with
  right angles at the ridges, area R² tan(s/2R) √(tan²ρ − tan²(s/2R)).
  For 100 km on Earth each piece is 1,443.49 km²; the three total
  4,330.48 km², 0.22 km² more than the sphere's triangle, while the flat
  triangle through A, B, C is 0.22 km² less.
  A rotatable, zoomable 3D view of the pyramid alone sits under the
  diagrams: the three flat planes, the face pieces, ridges, apex, straight
  sight lines, the plane through A, B, C as a reference grid, and each
  station's vertical square to its face (optionally extended downward). No
  sphere is drawn. Heights follow the same exaggeration setting.
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

- **Where is the sphere?** A closing part of the pyramid section: a table of
  every ingredient (sight lines, level planes, angles, ridges, apex, face
  areas) marked as plain Euclidean, with the sphere entering only in the
  direction given to each vertical, and the straight-line test that would
  make it a finding (do the plumb lines of many stations meet in one point?).

- **Conclusion.** Every reading is Euclidean; the excess comes from the
  directions given to the verticals; it fixes only a total; K = E / A divides
  by an unmeasured area and adds nothing; the convergence of the verticals is
  inferred by triangulation, not measured. The closure cannot be the evidence
  that the verticals converge.
- **Appendix A · Measuring the verticals directly.** Shared star field,
  ranged targets, reciprocal vertical angles and a carried gyro direction,
  each with its assumption and how to test it; the convergence as measured
  angle per ranged chord; the common-centre test (closest approach of the
  measured plumb lines); limits (0.1″ zenith camera, deflections, and
  near-ground refraction k from −4 to +16, Hirt et al. 2010 JGR).

Styling: the page is set as an 1800s treatise (Old Standard TT and IM Fell
English, ruled plates, § numerals, figure numbers) rather than the repo's
usual Surface Lab look, at the author's request.

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
- Pyramid: plane i is u_i · x = 1 on the unit sphere. The apex is at
  1/cos ρ on the centre's vertical; the ridge over a side's midpoint is at
  1/cos(s/2R) along the midpoint's vertical, with the midpoint at angular
  distance μ from the centre, tan μ = tan ρ / 2. Heights use 1/cos x − 1 =
  2 sin²(x/2) / cos x to avoid cancellation; face angles use atan2 of the
  cross and dot products of the ridge directions.
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

- C. Hirt et al. (2010), [Monitoring of the refraction coefficient in the lower atmosphere](https://ddfe.curtin.edu.au/models/ERTM2160/pdf/Hirt2010_JGR_D21102_refraction_av.pdf), J. Geophys. Res. 115, D21102

- C. Hirt et al. (2010), [Modern Determination of Vertical Deflections Using Digital Zenith Cameras](https://espace.curtin.edu.au/handle/20.500.11937/34194), J. Surveying Eng. 136(1)
- NOAA, [comparison of four astrogeodetic systems](https://repository.library.noaa.gov/view/noaa/72066/noaa_72066_DS1.pdf)
- Leica Geosystems, [FlexLine TS10 datasheet](https://dr.leica-geosystems.com/-/media/files/leicageosystems/products/datasheets/leica_flexline_ts10_lr.ashx)
- NOAA NGS, [DMEX97 deflection model page](https://webarchive.library.unt.edu/eot2008/20090116065704/http://www.ngs.noaa.gov/GEOID/DMEX97)

- C. F. Gauss (1827), *Disquisitiones generales circa superficies curvas*,
  Art. 20, in the Morehead & Hiltebeitel translation:
  [Project Gutenberg #36856](https://www.gutenberg.org/ebooks/36856)
- H. Moritz, [Geodetic Reference System 1980](https://iag.dgfi.tum.de/media/archives/HB2000/part4/grs80_corr.htm):
  mean radius R₁ = 6 371 008.7714 m (Earth preset)
