# Moon, Earth's shadow and the gegenschein

Live: https://rooster-ninja.github.io/simulations/moon-shadow/

Single self-contained HTML file (`index.html`). No dependencies except the
optional Google Font Jost, which falls back to system fonts. Has `og:title` /
`og:description` meta tags for Discord link previews.

## What it shows

- **Top-down orbit view:** Sun, Earth orbit, enlarged Moon orbit around Earth
  (solid half = north of ecliptic, dashed = south), ☊ node line, shadow wedge,
  gegenschein oval, red ticks at Earth positions of eclipses.
- **What the Moon looks like:** per-pixel rendered disk (north up, east left),
  phase lighting, rough maria, penumbral grey / umbral red shading.
- **Sky panel** toward the antisolar point (±24° × ±12°): gegenschein ovals
  (~20°×10° outer, 10°×5° inner), shadow, Moon, moonlight washout near full.
- **Close-up** of the shadow at Moon distance (±4°), true scale; arrow when the
  Moon is off-panel.
- **Readout:** phase name, % lit, separation from shadow centre, edge vs
  penumbra, distance (km), angular size.
- **Clickable eclipse list** (tap to jump).

## Controls

Play/pause, speed (1 h/s … 15 d/s), ±1 day, next full Moon, next eclipse, reset
to T0, slider over 0–1461 days. T0 = 2026-10-01 00:00 UTC. All times UTC.

## Ephemeris (in `<script id="core">`)

- **Sun:** low-precision longitude (mean anomaly + 2 equation-of-centre terms).
- **Moon:** mean elements + main periodic terms (Meeus-style) for longitude,
  latitude (~10 terms, all positive signs in latitude series), distance.
- **Node:** `125.045 − 0.0529538·d`.
- **Shadow radii:** umbra = `1.02(πM + πS − s☉)`, penumbra = `1.02(πM + πS + s☉)`.
- **Classification** at minimum separation: Total / Partial / Penumbral.
- `nextFullFrom(t)`: 3 h scan until separation starts falling, then ternary refine.
- `scanEclipses(t0, t1)`: iterates full Moons, classifies each.

## Validation

Matches real eclipse types and dates 2025–2030 (e.g. total 2026-03-03, partial
2026-08-28, penumbral ×3 in 2027, total 2029-06-26), timing within ~15 min.
Next full Moon after T0 → 2026-10-26 ~04:20 UTC (real: 04:12).
Accuracy ~0.1°; intended for intuition, not observing schedules.

## Known simplifications

- No aberration/nutation; sun direction in the Moon render treated as horizontal.
- Gegenschein drawn as fixed ovals (no brightness model).
- Moon orbit in the top view is not to scale.
