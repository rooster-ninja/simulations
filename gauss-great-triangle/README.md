# Building Gauss's Great Triangle

**Page:** https://rooster-ninja.github.io/simulations/gauss-great-triangle/

A 13-step animation of the Hanoverian arc measurement (1820–1823), from the
5 875.219 m Braak base to Gauss's great triangle Hohehagen – Brocken –
Inselsberg, ending with what the triangle's observed excess says about the
radius.

## What it shows

- **Steps 1–8, the chain.** The map zooms in on the Braak base, then follows
  the chain south. For each triangle the known side flashes, the two new sides
  grow from its ends, and a ladder records the longest side so far
  (5.9 km → 106 km). Heliotrope flashes run between the three summits of the
  great triangle.
- **Steps 9–13, the great triangle.** Gauss's raw angles, his computed excess
  and per-vertex reductions, the closing error, the solved sides and area, and
  the radius implied by the observed excess.

## How it works

Law of sines down the chain; plane angles = observed angles − Gauss's
reductions − closing error / 3; area = ½ · b · c · sin A;
R = √(area / observed excess). Everything runs in one self-contained
`index.html`, with no build step.

## Values used

| Quantity | Value | Source |
| --- | ---: | --- |
| Braak base | 5 875.219 m | vermessungsgeschichte.de |
| Angle at Hohehagen | 86° 13′ 58.366″ | Gauss, as quoted in the Berkeley Physics Course vol. 1 |
| Angle at Brocken | 53° 06′ 45.642″ | same |
| Angle at Inselsberg | 40° 39′ 30.165″ | same |
| Observed sum − 180° | 14.173″ (Breitenberger: 14.211″) | same; Scholz |
| Computed excess | 14.85348″ | Gauss, Disquisitiones generales (1827) |
| Reductions H / B / I | −4.95113″ / −4.95104″ / −4.95131″ | same |
| Side Inselsberg – Brocken | 105 972.85 m | Jordan, Handbuch der Vermessungskunde (1896) |
| Mean error of a direction | 0.48″ | Gauss to Bessel, 1823 (Werke IX, 366) |

## Errors used

- One direction ± 0.48″, one angle ± 0.68″, angle sum ± 1.18″ (1σ).
- Observed excess 14.17 ± 1.18″, 12σ above zero.
- Closing error −0.68″ against Gauss's computed excess, 0.6σ.
- Implied radius from this one triangle: 6 533 km, 1σ range 6 277–6 823 km.
- Not included: deflection of the vertical (≈ 10″ on the Brocken) and
  sideways refraction, both systematic.

## Simplifications

- Chain station positions are approximate modern locations, and the triangle
  order between Braak and the Harz is a reconstruction. Gauss's angles for
  those triangles (Werke IV and IX) were not available, so chain lengths on
  steps 2–7 are illustrative only.
- The great-triangle closing error is split evenly over the three angles.
- Styled in warm browns at the owner's request, not the repo's standard
  research-note theme; light mode only.

## Sources

- [Dänische Basismessung in Braak 1820](https://www.vermessungsgeschichte.de/detail/daenische-basismessung-in-braak-1820)
- [Hannoversche Gradmessung 1821–1823](https://www.vermessungsgeschichte.de/detail/778-hannoversche-gradmessung-1821-1823)
- [E. Scholz, C.F. Gauß' Präzisionsmessungen terrestrischer Dreiecke](https://arxiv.org/html/math/0409578) (citing Breitenberger 1984)
- [arXiv:2208.12757](https://arxiv.org/pdf/2208.12757) (quoting Gauss's Disquisitiones generales)
- [W. Jordan, Handbuch der Vermessungskunde (1896)](https://digital.ub.uni-paderborn.de/download/pdf/7975294.pdf)
- [Brosche & Heckmann, Eine frühe Lotabweichungsbestimmung auf dem Brocken, zfv 2016](https://geodaesie.info/images/zfv/141-jahrgang-2016/downloads/zfv_2016_3_Brosche_Heckmann.pdf)
- [Carl Friedrich Gauß im Deister](https://www.myheimat.de/springe/c-freizeit/240-jahre-carl-friedrich-gauss-landvermessung-und-der-deister_a2827047)
- Berkeley Physics Course, vol. 1 (Kittel et al., 1973), ch. 1
