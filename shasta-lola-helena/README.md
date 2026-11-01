# Shasta · Lola · Helena

Live page: https://rooster-ninja.github.io/simulations/shasta-lola-helena/

## What it shows

The largest triangle observed by the US Coast and Geodetic Survey: Mount Shasta,
Mount Lola and Mount Saint Helena, observed by Benjamin Colonna from Shasta in
1879 with George Davidson on Lola. Its longest side, Shasta → Helena (306.5 km),
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
| Side length, 1879 reported vs computed | ±2.4 km | ±29 m |
| Ellipsoid choice (WGS84 vs Clarke 1866) | ΔR ≈ 100 m | ±0.03 m |

## Simplifications

- Station positions are summit coordinates, not the published 1879 station
  positions. Replacing them with NGS datasheet values is the open item, and may
  explain why computed lengths (167.0 / 190.5 mi) run ~1.5 mi short of the
  reported 169 / 192 mi.
- Mountains in the cross-section are schematic profiles (12 km base).

## Visibility today

Modern accounts (California State Parks, Modern Hiker) say Shasta's top can be
seen from Mount Saint Helena on very clear days. These are anecdotal: no
published photograph, historic or recent, was found of Shasta from Saint Helena
or Lola, or of either from Shasta.

## Field record (primary source)

U.S. Coast and Geodetic Survey, Report of the Superintendent for the fiscal year
ending June 1880, pp. 37–39 and 43–44 (NOAA file CSC-0079):

- 25 Jul 1879: Colonna ascends Shasta; nine days and nights on the summit.
- 29 Jul: Lola heliotrope glimpsed from Shasta, no pointing. Davidson at Lola
  observes the Shasta heliotrope in five positions of 20-inch theodolite No. 115.
- 1 Aug: Helena seen from Shasta; four sets of six repetitions. Repeated 2 Aug.
- Only two angles of the triangle were measured that season, so the triangle was
  not closed by observation; the 142.7″ excess here is computed.
- Sides reported as approximately 136, 169 and 192 miles.
- Refraction coefficient observed at Lola (14 days, 3 nights) and Round Top.

Page extract: `sources/USCGS_1880_report_pp37-39_43-44.pdf` (and `.txt`, raw OCR).

## Terrain check (HeyWhatsThat)

Panorama from Saint Helena: https://www.heywhatsthat.com/?view=JUUTXI1Q
(screenshot in `images/heywhatsthat-st-helena-to-shasta.jpg`). Along bearing 7°
the skyline is at −0.64°, set by a Coast Range saddle ~40 mi out. Shasta's top
in the SRTM model reads −0.65° (no LOS); the true 14 179 ft summit works out to
about −0.63°. At standard refraction (k ≈ 0.14) the summit grazes the horizon,
±0.02°, so visibility depends on the day's refraction.

## Date

The observation is dated 1 August 1879. Colonna's own account (The Californian,
March 1880) gives "Friday, August 1", and 1 August was a Friday in 1879, not
1878. Some secondary sources (NOAA heliotrope page, JPR) say 1878. The 1880
Superintendent's report confirms 25 July – 2 August 1879.

## Sources

- "The Longest Line", The American Surveyor (2012):
  https://amerisurv.com/2012/10/27/the-longest-line/
- "The Longest Line", Hydro International:
  https://www.hydro-international.com/content/article/the-longest-line
- Robert Louis Stevenson State Park, California State Parks:
  https://www.parks.ca.gov/?page_id=472
- Mount Saint Helena, Modern Hiker: https://modernhiker.com/hike/mount-saint-helena/
- Mount Saint Helena, SummitPost: https://www.summitpost.org/mount-saint-helena/150521
- U.S. Coast and Geodetic Survey, Report of the Superintendent… fiscal year
  ending June 1880, pp. 37–39, 43–44: https://library.noaa.gov/coast-geodetic-survey/annual-reports (CSC-0079)
- B. A. Colonna, "Nine Days on the Summit of Mount Shasta", The Californian,
  March 1880, v. 1 no. 3, pp. 242–8 (cited in College of the Siskiyous Mount
  Shasta bibliography, ch. 11: https://www.siskiyous.edu/library/shasta/documents/AB_Ch11.pdf)
- NOAA 200th, Heliotrope: https://celebrating200years.noaa.gov/theodolites/heliotrope.html
- C. F. F. Karney, GeographicLib.
