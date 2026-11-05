# Fiber ping and Earth shape (WIP)

**Work in progress.** Two measurement runs on 4 Nov 2026, one probe per pair, one run each.

## What it shows

A round trip over fiber can't be faster than light covering the distance twice; routing, queues and routers only add time. So the minimum ping between two cities is an upper bound on how far apart they can be. This page checks 25 measured round trips against that bound twice: once with globe (great-circle) distances, once with the north-pole azimuthal equidistant flat-map distances.

- **Run 1:** Vancouver to 19 coastal cities. All pass both models; from a northern source the flat map stretches distances only 0–14%, less than normal route slack.
- **Run 2:** southern-hemisphere pairs, where the flat map roughly doubles distances.
  - Auckland → Sydney: 23.6 ms, 14.4 ± 0.6 ms faster than light in vacuum could cover the flat-map distance (22.9σ).
  - Perth → Sydney: 53.2 ms, 2.2 ± 0.6 ms under the flat vacuum floor (3.6σ).
  - The other four pairs were routed through London, New York or Miami and don't discriminate.
- Every pair is above the globe fiber floor. The tightest, Auckland → Sydney, is 2.5 ms (7.2σ) above it, as a direct cable should be.

## How it works

- Measurements: Globalping probes (one per source city; ping and traceroute from the same probe) to single-site Vultr test hosts. Every traceroute ends at the labelled host, so anycast mislabelling is ruled out.
- Ping: 16 ICMP echoes per pair, minimum used.
- Globe distance: haversine, 6,371 km sphere. Flat distance: r = (90° − φ) × 111.195 km, d² = r₁² + r₂² − 2r₁r₂ cos Δλ.
- Floors: vacuum 2d/c (c exact); fiber 2d·n_g/c with n_g = 1.468.

## Errors used

- Endpoint position: 25 km (1σ) per end, city-level coordinates. Propagated to the floor by Monte Carlo (4,000 trials): 0.24–0.63 ms.
- Ping timestamp, fast side: 0.05 ms. Only clock error can make a ping read faster than the path allows.
- Fiber group index 1.462–1.468; the vacuum test doesn't depend on it.

## Simplifications

- Rejects one specific flat map (north-pole azimuthal equidistant), not every possible flat layout.
- One run per pair; Perth → Sydney needs repeats from other networks.
- Run 1 did not log probe coordinates; the Vancouver city centre is used.
- Spherical Earth for globe distances (no flattening; under 0.5%).

## Files

- `data/` raw results and traceroutes from both runs, plus `summary.json`.
- `scripts/vancouver_ping_test.py`, `scripts/southern_ping_test.py` — the measurement scripts (Python 3 stdlib, run from any machine).
- `scripts/analyze.py` — combines runs, computes distances, floors and σ → `data/summary.json`.
- `scripts/build_page.py` — embeds `summary.json` into `scripts/page.template.html` → `index.html`.

## Sources

- NIST, speed of light in vacuum: https://physics.nist.gov/cuu/Constants/Value/c.html
- Corning SMF-28e+ product information (group index 1.4682 at 1550 nm): https://img-en.fs.com/file/datasheet/corning-smf-28eplus-33175.pdf
- Corning SMF-28 ULL product information (group index 1.4620 at 1550 nm): https://www.corning.com/media/worldwide/coc/documents/Fiber/SMF-28%20ULL.pdf
- Globalping, ping and traceroute API guides: https://blog.globalping.io/run-ping-with-http-using-globalping-api/, https://blog.globalping.io/run-traceroute-with-http-using-globalping-api/
- Esri, azimuthal equidistant projection: https://pro.arcgis.com/en/pro-app/3.6/help/mapping/properties/azimuthal-equidistant.htm
