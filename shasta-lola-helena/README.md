# Shasta · Lola · Helena

Live page: https://rooster-ninja.github.io/simulations/shasta-lola-helena/

## What it shows

The largest triangle observed by the US Coast and Geodetic Survey: Mount Shasta,
Mount Lola and Mount Saint Helena, observed by Benjamin Colonna from Shasta in
1878 with George Davidson on Lola. Its longest side, Shasta → Helena (306.5 km),
is drawn to true scale against a flat chord, with a vertical-stretch slider
(1× to 40×).

## How it works

- Geodesic lengths, azimuths, angles and polygon area on WGS84 with GeographicLib.
- Curvature radius per side: Gaussian mean √(MN) at the side's mid-latitude.
- Sagitta = R(1 − cos(s/2R)); tangent drop = s²/2R; spherical excess ε = A/R².
- Summit-to-summit sightline clearance computed geometrically and with k = 0.13.
- Vertical stretch is an affine map: straight lines stay straight.

## Results

| Quantity | Value |
| --- | ---: |
| Shasta–Helena arc | 306.514 km |
| Arc − chord | 29.5 m |
| Sagitta | 1 842 ± 29 m (1σ) |
| Angle sum | 180° 02′ 22.7″ |
| Spherical excess | 142.7″ |
| Sightline clearance (min) | 674 m geometric, 868 m with k = 0.13 |

## Errors used

| Source | 1σ | Effect on sagitta |
| --- | ---: | ---: |
| Station positions (summit coords, not NGS marks) | ±100 m | ±1.2 m |
| Side length, 1878 reported vs computed | ±2.4 km | ±29 m |
| Ellipsoid choice (WGS84 vs Clarke 1866) | ΔR ≈ 100 m | ±0.03 m |

## Simplifications

- Station positions are summit coordinates, not the published 1878 station
  positions. Replacing them with NGS datasheet values is the open item, and may
  explain why computed lengths (167.0 / 190.5 mi) run ~1.5 mi short of the
  reported 169 / 192 mi.
- Mountains in the cross-section are schematic profiles (12 km base).

## Visibility today

Modern accounts (California State Parks, Modern Hiker) say Shasta's top can be
seen from Mount Saint Helena on very clear days. These are anecdotal: no
published photograph, historic or recent, was found of Shasta from Saint Helena
or Lola, or of either from Shasta.

## Sources

- "The Longest Line", The American Surveyor (2012):
  https://amerisurv.com/2012/10/27/the-longest-line/
- "The Longest Line", Hydro International:
  https://www.hydro-international.com/content/article/the-longest-line
- Robert Louis Stevenson State Park, California State Parks:
  https://www.parks.ca.gov/?page_id=472
- Mount Saint Helena, Modern Hiker: https://modernhiker.com/hike/mount-saint-helena/
- Mount Saint Helena, SummitPost: https://www.summitpost.org/mount-saint-helena/150521
- C. F. F. Karney, GeographicLib.
