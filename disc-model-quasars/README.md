# Disc model quasar test (WIP)

> **Work in progress, subject to change.** First pass with approximate quasar coordinates and a 24-city observer set. Method, data and conclusions may all be revised.

Tests a stationary-disc layout with two rotating star fields against the sky positions of 30 real quasars, seen from 24 cities over a sidereal day. Positions only: no brightness or extinction yet.

Page: https://rooster-ninja.github.io/simulations/disc-model-quasars/

## The diagram and how it works

From the original sketch (`images/original-sketch.jpeg`):

- **Disc (grey), stationary.** Radius 10 002 km (pole to equator). S is the top rim point, N the bottom. Equator is the horizontal diameter; 0° E on the left edge, 0° W on the right, 180° down the centre. Meridians are arcs through both rim points; parallels are evenly spaced arcs.
- **Two star fields** turn over it: green about the S point, blue about the N point, in opposite senses, one turn per sidereal day.
- **Tangent lines** through S and N bound the visible band. Beyond them is the unknown zone, where a star may move at any speed, including instantly.
- **Quasars** sit at (90° − |Dec|) × 111 km from their pole point: northern on the blue field, southern on the green.
- **Red error bars** run from the disc position to the point that best matches what the 24 cities actually see at that moment. An arrowhead at the canvas edge means the best point is off the map.
- **Hidden-time slider** sets how long each quasar spends crossing the unknown zone; the cards show the rate this forces on the visible arc.

## Degrees of freedom allowed for each star

| # | Freedom | Range allowed | Tested in |
| --- | --- | --- | --- |
| 1 | Position across the plane (x, y) | anywhere, ±10 000 000 km | free-position fit, free-layout fit |
| 2 | Height above the disc | 1 m to 100 000 000 km | pole-height test, both fits |
| 3 | Height changing with time | independent every 2 sidereal hours | both fits |
| 4 | Rotation centre | N/S rim point by declination; any point in the fits | circle sims, both fits |
| 5 | Circle radius | by declination in sims; any in the fits | circle sims, both fits |
| 6 | Launch (start) angle | ±90° offset | arc sim |
| 7 | Launch baseline (tangent line position) | 0 to 11 000 km beyond the pole point | baseline sim |
| 8 | Visible arc span | 180° to 360° | arc and baseline sims |
| 9 | Speed on the visible arc | whatever arc and timing require | all sims |
| 10 | Speed and path in the unknown zone | anything, including instantaneous | hidden-zone sim (fits ignore path) |
| 11 | Observer layout (each city's x, y, local north) | free, scale free | free-layout fit only |

**Held fixed:** each city's real observed altitude/azimuth (from catalogue RA/Dec and sidereal time), sightings above 5° only. No refraction model (under 0.2° above 5°).

## Results so far

| Test | Result |
| --- | ---: |
| Measured rotation rate | 15.04°/h; only uniform rotation reproduces it |
| Pole-star height needed (altitude = latitude) | 36 km (Quito) to 8 289 km (London) |
| Minimum error, disc layout fixed, 360 fits | best 9.4° rms, median 25.0° |
| Minimum error, layout also free | 17.3° rms, median 9.6°, 90th pct 26° |
| Distances in the best free layout vs globe | 0.53× to 2.89× |
| Best residual vs 1′ coordinate accuracy | ~560σ |

These are fallible, inductive findings from a first pass.

## Files

| Path | What |
| --- | --- |
| `index.html` | Report and interactive simulation (self-contained) |
| `images/original-sketch.jpeg` | The original disc sketch |
| `data/quasars.csv` | Quasar RA/Dec used (approximate) |
| `data/disc_best_fit.csv` | Best-fit position and error per quasar per 2 sidereal hours, disc layout fixed |
| `data/free_layout_fit.json` | Free-layout fit: city positions, quasar positions, distance pairs |
| `scripts/model.py` | Disc projection, observers, quasars, sight lines |
| `scripts/rate_tests.py` | Rates, pole heights, hidden-zone speeds |
| `scripts/fit_disc.py` | Minimum-error fit on the fixed disc layout (~1 min) |
| `scripts/fit_free_layout.py` | Fit with layout free (~3 min) |

Requires Python 3 with NumPy and SciPy. Run from `scripts/`.

## Known limits / to do

- Replace typed quasar coordinates (±1′) with ICRF3 or Milliquas values.
- Replace synthetic city sightings with real plate-solved frames (Seestar at Nanton first).
- Fits use 12 instants per day; motion between them is unconstrained.
- Horizon behaviour (rise, set, extinction) only covered by the rate and pole-height checks.
- Free-layout fit stopped at 4 000 evaluations while still creeping down slowly.
