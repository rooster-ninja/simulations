# Survey triangles across America: Gauss vs Tarski

**Page:** https://rooster-ninja.github.io/simulations/survey-triangles-gauss-vs-tarski/

![The two US chains in the Gauss reading, coloured by excess over a flat triangle](figures/gauss_reading.png)

## What it shows

Every triangle of Schott's 39th-parallel arc (465) and Eastern Oblique arc (281) is read two ways.

- **Gauss reading (angles).** Excess ε = sum of observed angles − 180°, tested against closure noise. 220 triangles are curved beyond 3σ. Every one gets its curvature through angular excess. That route leaves the Theorema Egregium (Art. 12, curvature from lengths E, F, G) for Art. 20 (angle excess = integral curvature, stated through the normals), and it rests on plumb-levelled angles and on sight lines treated as shortest lines.
- **Tarski reading (lengths).** Only the three printed sides of each triangle are used, decided as plane geometry (Tarski: elementary plane geometry is complete and decidable). All 746 triangles exist as flat triangles, and their plane angles sum to 180° exactly.
- **Closed fans (lengths).** A station ringed by triangles is the one place lengths alone can show curvature. 62 fans were found. Each fails to close flat by its sides alone, with deficits of 0.3″ to 90.8″. But each deficit equals one third of the fan's printed ellipsoid excess, to +0.05″ ± 0.31″. That is the ε/3 that Legendre's theorem took off each angle to compute the sides. The curvature in the lengths was put there from the angles and the ellipsoid model; it was not measured.

## Result

| | 39th parallel | Eastern Oblique |
| --- | ---: | ---: |
| Triangles | 465 | 281 |
| Tested by angles | 449 | 267 |
| Curved beyond 3σ (angles) | 108 | 112 |
| Curvature via angular excess | 449 of 449 | 267 of 267 |
| Exist flat from their own sides | 465 | 281 |
| Triangles with a measured side | 0 | 3 |
| Legendre residual, median / 95% | 0.52″ / 1.51″ | 0.51″ / 1.38″ |
| Closed fans | 43 | 19 |
| Fan deficit − ⅓Σ printed ε | +0.01″ ± 0.19″ | +0.15″ ± 0.48″ |
| Fan deficit − ⅓Σ observed ε | +0.33″ ± 0.47″ (39) | +0.73″ ± 1.18″ (16) |

These are inductive findings from Schott's printed values at the stated noise. The excess is real at that noise; the finding is about the route: none of the curved triangles is a Theorema Egregium result.

## How it works

1. `scripts/build.py` reads Schott's printed angles, excess and sides (log metres) from the report's master KML extracts in `sources/`, with the observed excess and qc from `triangles_rule.csv` (3 degree misprints corrected from printed sides).
2. Gauss: ε and z = ε / σ (σ = ±1.261″ / ±1.397″ per triangle, the report's rule). Triangles with an angle printed "…." are not tested.
3. Tarski: triangle inequality and law-of-cosines plane angles from the three printed sides. Legendre residual = observed angle − printed ε/3 − plane angle.
4. Fans: for each station, neighbours are ordered by map bearing and the finest non-overlapping ring of triangles that wraps 360° is chosen; each wedge's plane angle must match its bearing gap within 2°. Deficit = 360° − Σ plane angles at the centre from sides only.
5. Measured sides: both ends are terminals of the same base line (Massachusetts, Dauphin Island).
6. `scripts/build_page.py` writes `index.html` from `data/gauss_tarski.json`.

Rebuild: `python3 scripts/build.py && python3 scripts/build_page.py`.

## Error budget

| Source | Size | Effect |
| --- | --- | --- |
| Angle-closure noise | ±1.261″ / ±1.397″ | the σ in every z |
| Printed sides, 7-place logs | ±1.2 × 10⁻⁷ relative | plane angles to ~±0.03″ for well-shaped triangles |
| Network adjustment | median 0.51″ per angle | spread of the Legendre residual |
| Fan deficit vs ⅓Σε | ±0.31″ | adjustment and log rounding round 3–8 triangles |
| Near-degenerate triangle | Humboldt–Reinhard–Erricssen, 179.87° corner | margin 2.4 cm against ~0.5 cm log rounding; still exists flat |
| Fan finder | map bearings | chooses the ring only; values use sides |
| Display map | azimuthal equidistant | none |

## Simplifications

- The fan test uses Schott's computed sides, so it cannot be independent of the angles. That is the finding, not a flaw: in this data no length is independent of the angles apart from 3 base sides.
- Tarski's result is cited from the RAND R-109 summary; the RAND scan is image-only.

## Files

| Path | What |
| --- | --- |
| `index.html` | The page |
| `scripts/build.py` | Both readings, closed fans, measured sides |
| `scripts/build_page.py` | Writes `index.html` |
| `data/triangles.csv` | Per triangle: sides, flat existence, angle sums, observed and printed excess, z, Legendre residual, measured sides |
| `data/fans.csv` | Per closed fan: centre, ring, deficit from sides, ⅓Σ printed and observed excess |
| `data/gauss_tarski.json` | Everything the page draws |
| `sources/kml_*_triangles.json` | Schott's printed angles, excess, sides and pages (from the report's master KML) |
| `sources/triangles_rule.csv`, `us_triangle_vertices.csv`, `na_outline_lonlat.json` | Copies from the report / flat-plane-chains |
| `sources/Schott_SP4_1900_pp25_51_206_612-614.pdf`, `sources/Schott_SP7_1902_p26.pdf` | Page extracts quoted on the page |

## Sources

- C. F. Gauss, *Disquisitiones generales circa superficies curvas* (1827), tr. Morehead & Hiltebeitel (1902), Project Gutenberg 36856: Art. 11 (p. 19), Art. 12 (p. 20), Art. 20 (p. 29), Arts. 27–28 (pp. 42–43).
- A. Tarski, *A Decision Method for Elementary Algebra and Geometry*, RAND R-109 (1948; 2nd ed. 1951).
- C. A. Schott, USC&GS Special Publication No. 4 (1900): pp. 25, 51, 206, 612–614.
- C. A. Schott, USC&GS Special Publication No. 7 (1902): p. 26.
- The Theorema Egregium report's master KML and `triangles_rule.csv`.
- Natural Earth 1:50m admin-0 countries (public domain).

## Appendix

The earlier page on these chains: [Flat plane, lumpy triangles](../flat-plane-chains/).
