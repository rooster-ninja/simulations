# Triangulation chain: baseline to check base

A step-through of first-order triangulation. A 10 km baseline is measured
with bars, carried through seven triangles (sides growing to 105 km, then
shrinking), and checked against a second bar-measured base at the far end.

## What it shows

- **Overhead chain.** Each triangle is shaded by its spherical excess once
  its three angles are observed. The theodolite's station, the two sight
  lines and the swept angle are drawn on the map.
- **Theodolite view.** At each station the eyepiece (10′ field) holds the
  first target on the crosshair, then swings to the second while the
  horizontal circle turns. The angle is the difference of the two readings.
  Targets by distance: a flag on a 4 m pole under 35 km (drawn at its true
  angular size), a signal lamp at 35–70 km, a heliotrope flash beyond.
- **Closure.** For each triangle: angle sum − 180°, excess `E = A / R²`, and
  the closure (sum − 180° − E), with the excess expressed in units of the
  angle-sum error.
- **Check base.** Computed length (Legendre's theorem, then the law of sines,
  triangle by triangle) compared with the measured check base, against the
  expected error.

## Errors used

| Quantity | 1σ |
| --- | --- |
| Each observed angle | 0.7″ |
| Angle sum | 1.2″ |
| Baseline and check base | 1 : 300,000 |

"New errors" draws a fresh set of random errors.

## Simplifications

- Geometry is laid out on a plane; the spherical excess is added to each true
  angle (Legendre's theorem), with R = 6,371 km.
- No flattening, refraction, deflection of the vertical or station centring.
- Each station's angle is shown as one averaged reading pair, not 16
  separate sets.

## Sources

- FGCC (1984), Standards and Specifications for Geodetic Control Networks,
  pp. 3-2 and 3-3.
- NOAA Special Publication NOS NGS 5, Geodetic Surveys in the United States.
- U.S. Coast and Geodetic Survey (1882), Yolo Base Line report excerpt.
- The American Surveyor (2007), Woodward's Ice Bar.
