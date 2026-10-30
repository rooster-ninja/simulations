# Peak chord curvature

Single straight Giga-Ranger chords between Nanton, Mount Head and Plateau
Mountain, plus a centre station inside that triangle, give a radius of
curvature with error bars. No angles, bearings or GPS.

## What it shows

- **Three chords fit any surface.** Three stations on a surface have three
  unknowns after removing slide and turn; three chords fill them exactly.
- **A centre station decides.** Four stations have five unknowns and six
  chords, leaving one condition that only the right curvature satisfies.
  Placement matters: a fourth station outside the triangle (High River) puts
  flat ~0.1σ away; a centre station near 50.36° N, 114.25° W puts it ~20σ
  away at the default errors. Tap the map to move it; shading shows test
  strength.
- **Chords need heights.** A chord runs through the air, so converting it to a
  ground distance uses each station's height above the reference surface,
  from simultaneous barometric levelling. Only height differences matter.

## How it works

- Truth: a sphere of the GRS 80 mean radius; stations at their published
  positions and heights (Nanton approximate; centre-station height a
  placeholder, slider).
- Model: a sphere of signed curvature u = 1/R (u > 0 convex, 0 flat, u < 0
  concave). Chord to ground distance:
  c² = (h₁ − h₂)² + 2(1 + u h₁)(1 + u h₂)·V_{u²}(s).
- Four-point condition on a surface of curvature K: 1ᵀ V⁻¹ 1 = K with
  V_ij = V_K(s_ij) = (1 − cos √K s_ij)/K. Solve F(u) = 1ᵀV⁻¹1 − u² = 0.
  This form needs no side-of-line decisions.
- Error bars: 1,500 simulated campaigns. Map shading: linearized error
  propagation for a centre station at each grid point.

## Errors used (defaults, adjustable)

| Source | 1σ | Basis | Flat excluded at |
| --- | --- | --- | --- |
| Chord, random | 0.05 m | 0.021 m exchange floor + corrected thermal drift (assumed) | 0.2 m → ~8σ |
| Air correction residual | 1 ppm per chord | Assumed, after GRIN removes ≈ 15 m per 60 km | 3 ppm → ~12σ, 10 ppm → ~4σ |
| Station heights | 2 m | Simultaneous barometric levelling (assumed) | 5 m → ~11σ, 10 m → ~6σ |
| Common offset | 0.03 m | Size of the −27 mm calibration residual | 0.5 m → ~5σ |
| Ray bending | ≈ 1.6 cm on 63 km | L³κ²/24, κ = R/4 radio ray; left uncorrected | < 1 % in û |

Defaults: û = 1.00 ± 0.05 (units of 1/6,371 km), flat ~20σ away. With all
four stations at equal height the test still gives ~3σ (chord-versus-ground
difference alone); the peak–prairie height difference multiplies it ~6×.

## Simplifications

- Sphere, no flattening. Line of sight on every chord is assumed, not checked
  against terrain. Nanton coordinates are approximate (town centre).

## Sources

- PeakVisor, Mount Head: https://peakvisor.com/peak/mount-head-canada.html
- PeakVisor, Plateau Mountain: https://peakvisor.com/peak/plateau-mountain-canada.html
- RoadsideThoughts, Nanton: https://roadsidethoughts.com/ab/nanton-profile.htm
- latlong.net, High River: https://www.latlong.net/place/high-river-ab-canada-13027.html ; RoadsideThoughts, High River: https://roadsidethoughts.com/ab/high-river-profile.htm
- rooster.ninja, Giga Ranger project overview: https://www.rooster.ninja/skunk_werks/giga_ranger/project_overview/
- rooster.ninja, SX1280 ranging calibration: https://www.rooster.ninja/moon_sensors/calibration/Giga_Ranger_Calibration/sx1280_ranging_calibration.html
- Semtech SX1280/SX1281 datasheet, p. 13: https://www.mouser.com/datasheet/2/761/DS_SX1280-1_V2.2-1511144.pdf
- H. Moritz, Geodetic Reference System 1980, §4: https://iag.dgfi.tum.de/media/archives/HB2000/part4/grs80_corr.htm
