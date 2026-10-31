"""Discord/report figure: the dome render plus the size of the DOV change against the angle noise."""
import json, csv, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "..")
render = sys.argv[1]; out = sys.argv[2]
R = json.load(open(f"{B}/data/dov_results.json")); ov = json.load(open(f"{B}/model/overlay_dov.json"))
rows = list(csv.DictReader(open(f"{B}/data/dov_triangles.csv")))
bg, ink, mut, rule, blue = "#f6f1e7", "#1d1d1b", "#5a5650", "#ddd5c4", "#2a5fa8"
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 13, "text.color": ink, "axes.labelcolor": mut,
                     "xtick.color": mut, "ytick.color": mut, "axes.edgecolor": mut})
fig = plt.figure(figsize=(13, 13.4), dpi=150); fig.patch.set_facecolor(bg)
fig.text(.05, .968, "THEOREMA EGREGIUM · DEFLECTION OF THE VERTICAL", color=blue, family="DejaVu Sans Mono", fontsize=12)
fig.text(.05, .935, "Plumb-line correction applied to every US triangle", fontsize=22, weight="bold")
fig.text(.05, .91, "NGS DEFLEC18 at all 456 stations · Schott 1900 heights for the 57 western mountain stations · same triangles, same rule",
         fontsize=11.5, color=mut)
ax = fig.add_axes([.05, .41, .90, .48]); ax.imshow(plt.imread(render)); ax.axis("off")
handles = [Patch(fc=c, ec=ink, lw=.5, label=l) for l, c in ov["bins"].items()]
ax.legend(handles=handles, title="Change in triangle excess\n(corrected − raw)", loc="lower left", fontsize=10.5, title_fontsize=11,
          frameon=True, facecolor=bg, edgecolor=rule, ncol=1, bbox_to_anchor=(0.005, 0.01))
# histogram
hx = fig.add_axes([.07, .09, .50, .27]); hx.set_facecolor(bg)
d = np.array([float(r["d_main"]) for r in rows]); sig = 1.26
hx.axvspan(-sig, sig, color="#c9d6ea", alpha=.6, lw=0); hx.axvspan(-2 * sig, 2 * sig, color="#c9d6ea", alpha=.3, lw=0)
hx.hist(d, bins=np.arange(-1.0, 1.0001, 0.025), color="#8a5a2b", edgecolor=bg, lw=.4)
hx.set_yscale("log"); hx.set_xlim(-2.8, 2.8)
hx.set_xlabel("Change in a triangle's angle excess (arcseconds)"); hx.set_ylabel("Triangles (log scale)")
hx.text(-2.7, hx.get_ylim()[1] * .5, "shaded: angle-closure noise\n±1.26″ (1σ), ±2.5″ (2σ)", ha="left", fontsize=10.5, color=blue)
for s in ("top", "right"): hx.spines[s].set_visible(False)
hx.set_title(f"All {len(d)} triangles: rms {R['by_case']['main']['rms']:.2f}″, largest {R['by_case']['main']['max']:.2f}″", fontsize=12.5, loc="left")
# numbers
F = R["fits"]
lines = [("", "raw", "corrected"),
         ("39th parallel, q", f"{F['US 39th parallel']['raw']['q']:.4f}", f"{F['US 39th parallel']['d_main']['q']:.4f}"),
         ("  ± 1σ", f"{F['US 39th parallel']['raw']['sq']:.4f}", f"{F['US 39th parallel']['d_main']['sq']:.4f}"),
         ("Eastern Oblique, q", f"{F['US Eastern Oblique']['raw']['q']:.4f}", f"{F['US Eastern Oblique']['d_main']['q']:.4f}"),
         ("  ± 1σ", f"{F['US Eastern Oblique']['raw']['sq']:.4f}", f"{F['US Eastern Oblique']['d_main']['sq']:.4f}"),
         ("39th chain Σ excess", f"{F['US 39th parallel']['chain']['raw']:.1f}″", f"{F['US 39th parallel']['chain']['main']:.1f}″"),
         ("  expected (ellipsoid)", f"{F['US 39th parallel']['chain']['pred']:.1f}″", ""),
         ("E. Oblique Σ excess", f"{F['US Eastern Oblique']['chain']['raw']:.1f}″", f"{F['US Eastern Oblique']['chain']['main']:.1f}″"),
         ("  expected (ellipsoid)", f"{F['US Eastern Oblique']['chain']['pred']:.1f}″", "")]
y = .355
for i, (a, b, c) in enumerate(lines):
    w = "bold" if i == 0 else "normal"
    fig.text(.62, y, a, fontsize=12, weight=w, color=ink if i else mut)
    fig.text(.86, y, b, fontsize=12, ha="right", family="DejaVu Sans Mono", weight=w, color=ink if i else mut)
    fig.text(.97, y, c, fontsize=12, ha="right", family="DejaVu Sans Mono", weight=w, color=ink if i else mut)
    y -= .028
fig.text(.62, y - .01, "q = K measured ÷ K ellipsoid. A flat plane needs\nevery excess = 0; the correction moves sums by ~1″.",
         fontsize=10.5, color=mut, va="top")
fig.text(.05, .018, "Correction per direction = −(ξ sin α − η cos α)·tan e, summed over each triangle's three angles (Laplace zenith-distance term). "
         "Checked against a 3-D\nprojection to 0.002″. DEFLEC18 values from NGS Interactive Computation, 31 Oct 2026. Heights elsewhere from the 10′ ETOPO1 grid (20 km peak).",
         fontsize=9.3, color=mut)
fig.savefig(out, facecolor=bg)
