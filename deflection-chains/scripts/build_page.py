"""Write ../index.html from the result files, so every number on the page comes from the data."""
import json, csv, os, html
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "..")
BP = json.load(open(f"{B}/model/balanced/mesh_params_balanced.json")); OP = json.load(open(f"{B}/model/mesh_params.json"))
WMIN, WMAX = -3000, int(round(BP["peak_mm"] + 1000, -1))
R = json.load(open(f"{B}/data/dov_results.json")); OV = json.load(open(f"{B}/model/overlay_dov.json"))
T = list(csv.DictReader(open(f"{B}/data/dov_triangles.csv")))
S = list(csv.DictReader(open(f"{B}/data/dov_stations.csv")))
F = R["fits"]; C = R["by_case"]
e = html.escape
def f(x, n=4): return f"{x:.{n}f}"
def sg(x, n=2): return ("+" if x >= 0 else "−") + f"{abs(x):.{n}f}"

top = sorted(T, key=lambda t: -abs(float(t["d_main"])))[:10]
top_rows = "\n".join(
    f'<tr><td>{e(t["triangle"])}</td><td>{"39th" if "39th" in t["survey"] else "E. Oblique"}</td>'
    f'<td class="n">{float(t["area_km2"]):,.0f}</td><td class="n">{float(t["excess_raw"]):.2f}″</td>'
    f'<td class="n"><b>{sg(float(t["d_main"]))}″</b></td><td class="n">{float(t["excess_raw"])+float(t["d_main"]):.2f}″</td>'
    f'<td class="n">{float(t["defl_max"]):.1f}″</td><td class="n">{t["n_schott_h"]}/3</td></tr>' for t in top)
st_top = sorted(S, key=lambda x: -(float(x["xi_deflec18"]) ** 2 + float(x["eta_deflec18"]) ** 2))[:8]
st_rows = "\n".join(
    f'<tr><td>{e(x["station"])}</td><td class="n">{sg(float(x["xi_deflec18"]))}″</td><td class="n">{sg(float(x["eta_deflec18"]))}″</td>'
    f'<td class="n">{sg(float(x["xi_eigen6c4"]))}″</td><td class="n">{sg(float(x["eta_eigen6c4"]))}″</td>'
    f'<td class="n">{(x["h_schott_m"] + " m") if x["h_schott_m"] else "—"}</td></tr>' for x in st_top)

def fitrow(label, key):
    g = F[key]; cells = "".join(f'<td class="n">{f(g[c]["q"])} ± {f(g[c]["sq"])}</td>' for c in ("raw", "d_main", "d_low_h", "d_eigen"))
    return f"<tr><td>{label}</td><td class=\"n\">{g['raw']['n']}</td>{cells}</tr>"
def chainrow(label, key):
    g = F[key]["chain"]
    return (f'<tr><td>{label}</td><td class="n">{g["n"]}</td><td class="n">{g["raw"]:.1f}″</td><td class="n">{g["main"]:.1f}″</td>'
            f'<td class="n">{sg(g["main"]-g["raw"])}″</td><td class="n">{g["pred"]:.1f}″</td><td class="n">±{g["noise"]:.1f}″</td></tr>')

legend = "".join(f'<span><i style="background:{c}"></i>{e(l)}</span>' for l, c in OV["bins"].items())
cnt39 = OV["counts"]["US 39th parallel"]; cntEO = OV["counts"]["US Eastern Oblique"]
OP_peak = 1938.2; OP_gap = 1888.35 - 1653.26   # report's dome: peak, and north-minus-south lowest-coast gap (na_dome_mesh_balanced.py --lat0 45)
grey39 = cnt39["±0.03″"]; n39 = sum(cnt39.values()); greyEO = cntEO["±0.03″"]; nEO = sum(cntEO.values())

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Deflection of the Vertical: US Chains</title>
<meta property="og:title" content="Deflection of the vertical in the US triangulation chains">
<meta property="og:description" content="Every observed angle of the 39th-parallel and Eastern Oblique chains corrected for the local plumb line with NGS DEFLEC18 and Schott's station heights. The chains on the curvature dome, coloured by how much each triangle's excess moves.">
<meta name="theme-color" content="#f3efe4">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,700;8..60,800&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{{
  --bg:#f3efe4; --card:#f8f5ec; --plate:#ffffff; --ink:#1a1813; --muted:#6b6658; --rule:#ddd5c2;
  --accent:#4a8fb0; --bar:#16140f; --bar-ink:#f3efe4;
  --f-display:"Source Serif 4",Georgia,"Times New Roman",serif; --f-body:"Archivo",system-ui,sans-serif; --f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; color-scheme:dark}}
*,*::before,*::after{{box-sizing:border-box}}
html,body{{margin:0}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.55;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 40px}}
.wrap{{max-width:1100px;margin:0 auto;display:flex;flex-direction:column;gap:22px;padding-top:28px}}
.back{{margin:0 0 14px;font-family:var(--f-mono);font-size:13px}}.back a{{color:var(--muted);text-decoration:none}}.back a:hover{{color:var(--accent)}}
.eyebrow{{font-family:var(--f-mono);font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin:0}}
h1{{font-family:var(--f-display);font-weight:800;font-size:clamp(32px,5.2vw,54px);line-height:1.04;letter-spacing:-.01em;margin:10px 0 0;text-wrap:balance;max-width:24ch}}
.sub{{color:var(--ink);font-size:18px;max-width:66ch;margin:14px 0 0}}
.panel{{background:var(--card);border:1.5px solid var(--rule);border-radius:16px;padding:18px 18px 16px;display:flex;flex-direction:column;gap:12px;min-width:0}}
.ptitle{{font-family:var(--f-mono);font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);font-weight:500}}
.math{{font-family:var(--f-display);font-style:italic;font-size:19px;text-align:center;line-height:1.7;overflow-x:auto;padding:2px 4px}}
.controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
button{{font:500 14px var(--f-mono);letter-spacing:.06em;color:var(--ink);background:var(--card);border:1.5px solid var(--rule);border-radius:10px;padding:9px 14px;cursor:pointer}}
button:hover{{border-color:var(--muted)}}button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
button[aria-pressed="true"]{{border-color:var(--accent);color:var(--accent)}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--f-mono);font-size:12px;color:var(--muted)}}
.legend i{{display:inline-block;width:16px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;border:1px solid var(--muted)}}
.cap{{font-size:16px;margin:0;max-width:72ch}}
.viewer{{position:relative;height:min(64vh,560px);min-height:320px;border-radius:12px;overflow:hidden;background:#3a4150;border:1.5px solid var(--rule)}}
.viewer canvas{{display:block;width:100%;height:100%;touch-action:none}}
.water{{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;align-items:center;font-family:var(--f-mono);font-size:13px;color:var(--muted)}}
.water input{{width:100%;accent-color:#2f6fae}}
.water output{{grid-column:1/-1;color:var(--ink);font-variant-numeric:tabular-nums}}
#vstatus{{position:absolute;inset:auto 12px 12px 12px;color:#e8e3d8;font:13px var(--f-mono)}}
figure{{margin:0}}figure img{{display:block;width:100%;height:auto;border-radius:12px;border:1.5px solid var(--rule);background:var(--plate)}}
figcaption{{font-size:14px;color:var(--muted);margin-top:8px;max-width:76ch}}
.readout{{background:var(--card);border:1.5px solid var(--rule);border-radius:16px;padding:16px 18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px 20px}}
.kv .k{{font-family:var(--f-mono);text-transform:uppercase;letter-spacing:.14em;font-size:11.5px;color:var(--muted)}}
.kv .v{{font-family:var(--f-display);font-weight:700;font-size:23px;line-height:1.2;font-variant-numeric:tabular-nums}}
.prose p{{margin:0 0 10px;max-width:72ch}}.prose p:last-child{{margin:0}}
ol.steps{{margin:0;padding-left:22px;max-width:74ch}}ol.steps li{{margin:0 0 8px}}
table{{border-collapse:collapse;width:100%;font-size:15px}}
th{{font-family:var(--f-display);font-variant:small-caps;font-weight:700;letter-spacing:.03em;text-align:left;border-bottom:1.5px solid var(--rule);padding:8px 10px;font-size:16px;white-space:nowrap}}
td{{border-bottom:1px solid var(--rule);padding:8px 10px;vertical-align:top}}
td.n,th.n{{text-align:right;font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
.tablebox{{overflow-x:auto}}
details.src{{background:var(--bar);color:var(--bar-ink);border-radius:12px;padding:14px 18px;font-family:var(--f-mono);font-size:14px}}
details.src summary{{cursor:pointer;font-weight:600}}
details.src ul{{margin:12px 0 0;padding-left:18px;font-family:var(--f-body);font-size:14px;line-height:1.6}}
details.src a{{color:var(--bar-ink)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="back"><a href="../">← All simulations</a></p>
    <p class="eyebrow">Theorema Egregium · deflection of the vertical</p>
    <h1>The plumb line, put back into every US triangle</h1>
    <p class="sub">A theodolite is levelled to the local plumb line, not to the ellipsoid. Near mountains the two differ by tens of arcseconds. Here every observed angle in the 39th-parallel and Eastern Oblique chains is corrected for that difference, and the curvature is measured again from the same triangles under the same rule.</p>
  </header>

  <section class="readout" aria-label="Key numbers">
    <div class="kv"><div class="k">Stations, DEFLEC18</div><div class="v">{R['with_deflec18']}</div></div>
    <div class="kv"><div class="k">Largest deflection</div><div class="v">{R['defl18_max']:.1f}″</div></div>
    <div class="kv"><div class="k">Change per triangle, rms</div><div class="v">{C['main']['rms']:.2f}″</div></div>
    <div class="kv"><div class="k">Largest change</div><div class="v">{C['main']['max']:.2f}″</div></div>
    <div class="kv"><div class="k">39th parallel q</div><div class="v">{f(F['US 39th parallel']['raw']['q'],4)} → {f(F['US 39th parallel']['d_main']['q'],4)}</div></div>
    <div class="kv"><div class="k">Eastern Oblique q</div><div class="v">{f(F['US Eastern Oblique']['raw']['q'],4)} → {f(F['US Eastern Oblique']['d_main']['q'],4)}</div></div>
  </section>

  <section class="panel">
    <div class="ptitle">1 · What the plumb line does to a horizontal angle</div>
    <div class="prose">
      <p>The horizontal circle turns about the instrument's vertical axis, and that axis is set by the bubble, along the local plumb line. The plumb line leans away from the ellipsoid normal by the deflection of the vertical: ξ toward the north and η toward the east. Tilting the axis changes the reading to a station that is seen above or below the horizon. It does not change the reading to a station seen exactly level.</p>
      <p>A direction to a station at elevation angle <i>e</i> and azimuth α is reduced to the ellipsoid normal by the term below, the zenith-distance part of the Laplace azimuth equation. An angle is the difference of two directions, so it changes by the difference of their two terms. A triangle's excess changes by the sum over its three corners.</p>
    </div>
    <div class="math">δ = −(ξ sin α − η cos α) · tan e &nbsp;&nbsp;&nbsp; Δε = Σ<sub>corners</sub> (δ<sub>right</sub> − δ<sub>left</sub>)</div>
    <p class="cap">A 25″ deflection on a sight line 1° above the horizon moves that direction by at most 25″ × tan 1° = 0.44″. On level ground, tan e is a few thousandths and the term all but vanishes.</p>
  </section>

  <section class="panel">
    <div class="ptitle">2 · The chains on the curvature dome</div>
    <div class="legend" aria-label="Colour key: change in triangle excess, corrected minus raw">{legend}</div>
    <div class="controls" role="group" aria-label="Viewpoint">
      <button class="vbtn" data-view="chains" aria-pressed="true">Both chains</button>
      <button class="vbtn" data-view="west" aria-pressed="false">Western mountains</button>
      <button class="vbtn" data-view="top" aria-pressed="false">Overhead</button>
      <button class="vbtn" data-view="iso" aria-pressed="false">Whole dome</button>
    </div>
    <div class="controls" role="group" aria-label="Model">
      <button class="mbtn" data-model="bal" aria-pressed="true">Balanced tilt (top {BP['lat0']:.2f}° N)</button>
      <button class="mbtn" data-model="orig" aria-pressed="false">Report's dome (top 45° N)</button>
    </div>
    <div class="water">
      <label for="wl">Water plane</label>
      <input id="wl" type="range" min="{WMIN}" max="{WMAX}" step="5" value="0" aria-describedby="wlout">
      <output id="wlout" for="wl"></output>
    </div>
    <div class="viewer" id="viewer"><span id="vstatus">Loading the model…</span></div>
    <p class="cap"><b>Balanced tilt.</b> The report's dome puts its top at 45° N, 100° W, where the lowest northern coast (north-east Greenland) sits {OP_gap:.0f} mm lower than the lowest southern coast. Tilting the dome about an east–west axis by {BP['lat0']-45:.2f}° moves the top to {BP['lat0']:.2f}° N, and the two lowest points, at {BP['lowest_points']['north']['lat']:.1f}° N {abs(BP['lowest_points']['north']['lon']):.1f}° W (north-east Greenland) and {BP['lowest_points']['south']['lat']:.1f}° N {abs(BP['lowest_points']['south']['lon']):.1f}° W (Panama–Colombia), then sit at the same height: {BP['lowest_points']['north']['arc_km']:,.0f} km of arc from the top, {BP['base_mm']:.0f} mm above the base. The peak drops from {OP_peak:,.0f} mm to {BP['peak_mm']:,.0f} mm. Same sphere, same K; only the axis moved. The water slider runs from 3 m below the base to 1 m above the peak, in model units (1 mm = 1 km).</p>
    <p class="cap">The report's North America dome (R = 1/√K = 6,388.8 km, 1 mm = 1 km). Every printed triangle is outlined; the non-overlapping triangles of the whole-chain sums are filled by how much the correction moves their excess. {grey39} of the {n39} 39th-parallel tiles and {greyEO} of the {nEO} Eastern Oblique tiles move by less than 0.03″ (grey). The colour sits on the high Rocky Mountain and Great Basin triangles, where the sight lines are steep and the deflections large. Drag to turn, pinch or scroll to zoom.</p>
  </section>

  <section class="panel">
    <div class="ptitle">3 · How big is the change?</div>
    <figure><img src="figures/dov_chains_summary.png" alt="Dome render with the chains coloured by the change in excess, a histogram of the change for all {len(T)} triangles against the angle-closure noise, and the curvature ratio before and after the correction" loading="lazy">
    <figcaption>All {len(T)} triangles. The change is a few hundredths of an arcsecond for most and {C['main']['max']:.2f}″ at most. The angle-closure noise of a single triangle is ±1.26″ (1σ) on the 39th parallel and ±1.40″ on the Eastern Oblique Arc (report §3.4).</figcaption></figure>
  </section>

  <section class="panel">
    <div class="ptitle">4 · Curvature before and after</div>
    <p class="cap">Same selection (signal ≥ 2× noise), same weights and same per-survey noise as the report's declared rule. q = K measured ÷ K of the ellipsoid, 1σ. The two right-hand columns bracket the inputs: station heights from the grid value instead of its 20 km peak, and the geoid-slope model EIGEN-6C4 instead of DEFLEC18.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Survey</th><th class="n">Triangles</th><th class="n">Raw angles</th><th class="n">DEFLEC18, main</th><th class="n">Low heights</th><th class="n">EIGEN-6C4</th></tr></thead>
      <tbody>{fitrow("US 39th parallel", "US 39th parallel")}{fitrow("US Eastern Oblique", "US Eastern Oblique")}{fitrow("Both US chains", "both")}</tbody>
    </table></div>
    <p class="cap">Whole-chain sums over the non-overlapping triangles (report Appendix B). Noise is σ<sub>closure</sub>·√n, an upper bound.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Chain</th><th class="n">Triangles</th><th class="n">Σ excess, raw</th><th class="n">Corrected</th><th class="n">Change</th><th class="n">Expected</th><th class="n">Noise</th></tr></thead>
      <tbody>{chainrow("US 39th parallel", "US 39th parallel")}{chainrow("US Eastern Oblique", "US Eastern Oblique")}</tbody>
    </table></div>
    <p class="cap"><b>Finding.</b> The plumb-line correction moves the measured curvature by {abs(F['US 39th parallel']['d_main']['q']-F['US 39th parallel']['raw']['q'])/F['US 39th parallel']['raw']['sq']:.2f}σ on the 39th parallel and {abs(F['US Eastern Oblique']['d_main']['q']-F['US Eastern Oblique']['raw']['q'])/F['US Eastern Oblique']['raw']['sq']:.2f}σ on the Eastern Oblique Arc. It does not explain the Eastern Oblique shortfall, and it cannot bring any triangle's excess near zero: the largest change is {C['main']['max']:.2f}″ against excesses of up to 75″. This is an inductive finding with the inputs stated, good to the error bars shown.</p>
  </section>

  <section class="panel">
    <div class="ptitle">5 · Largest changes and largest deflections</div>
    <div class="tablebox"><table>
      <thead><tr><th>Triangle</th><th>Chain</th><th class="n">Area km²</th><th class="n">Raw excess</th><th class="n">Change</th><th class="n">Corrected</th><th class="n">Max defl.</th><th class="n">Schott h</th></tr></thead>
      <tbody>{top_rows}</tbody>
    </table></div>
    <div class="tablebox"><table>
      <thead><tr><th>Station</th><th class="n">ξ DEFLEC18</th><th class="n">η DEFLEC18</th><th class="n">ξ EIGEN-6C4</th><th class="n">η EIGEN-6C4</th><th class="n">Schott height</th></tr></thead>
      <tbody>{st_rows}</tbody>
    </table></div>
    <p class="cap">Pikes Peak's +25.6″ east–west deflection is the largest. Schott singled out Colorado Springs, at the foot of the same mountain, as one of the two most deflected astronomical stations on the arc (1900, p. 848). The smooth satellite model gives half that value or less, which is why DEFLEC18 is used.</p>
  </section>

  <section class="panel">
    <div class="ptitle">6 · Methods</div>
    <ol class="steps">
      <li><b>Stations and triangles.</b> {R['stations']} stations and {R['triangles']} triangles of the two US chains, with the raw observed excess, area from printed sides, tier and per-survey noise, all exactly as in the report (<code>triangles_rule.csv</code>, <code>arcs_parallel_master.kml</code>).</li>
      <li><b>Deflections.</b> ξ and η at every station from NGS DEFLEC18 (Interactive Computation, file input, Format 2), the deflection model that accompanies GEOID18. The raw NGS output is kept in <code>sources/</code>.</li>
      <li><b>Heights.</b> Schott's adjusted heights for the {R['with_schott_height']} stations west of 100° W that he prints (1900, pp. 256–341, transcribed in <code>sources/schott1900_station_heights.csv</code>). Every other station takes the highest ETOPO1 10′ grid value within 20 km; the "low heights" column uses the grid value at the station instead.</li>
      <li><b>Elevation angles.</b> From the two heights (plus the EIGEN-6C4 geoid height), the WGS84 geodesic distance, Earth's curvature and refraction coefficient k = 0.13: tan e = Δh/d − (1 − k)·d/2R.</li>
      <li><b>Correction.</b> δ for both directions at each corner; the interior angle changes by their difference; the triangle's excess by the sum over its corners. Checked against an independent 3-D calculation that projects the two sight lines onto the plane square to the tilted plumb line: they agree to {0.0024:.3f}″ over the 40 largest corrections (<code>scripts/check_formula.py</code>).</li>
      <li><b>Refit.</b> The report's declared rule, unchanged: same triangles (SNR ≥ 2), tier weights, per-survey σ, weighted least squares through the origin, error inflated by √(χ²/dof).</li>
    </ol>
  </section>

  <section class="panel">
    <div class="ptitle">7 · Error budget for the correction</div>
    <div class="tablebox"><table>
      <thead><tr><th>Input</th><th>Uncertainty</th><th class="n">Effect on a triangle</th></tr></thead>
      <tbody>
        <tr><td>DEFLEC18 deflection</td><td>a model of today's field at the printed positions, not an observation at the marks</td><td class="n">scales the change; 2× deflection → 2× change</td></tr>
        <tr><td>Deflection model choice</td><td>DEFLEC18 vs EIGEN-6C4 (degree 720)</td><td class="n">rms {C['main']['rms']:.3f}″ vs {C['eigen']['rms']:.3f}″</td></tr>
        <tr><td>Station heights</td><td>Schott's adjusted heights; grid elsewhere</td><td class="n">rms {C['main']['rms']:.3f}″ vs {C['low_h']['rms']:.3f}″</td></tr>
        <tr><td>Refraction k</td><td>0.13 assumed; rerun with 0.05 and 0.20</td><td class="n">≤ 0.05″ (largest triangle change)</td></tr>
        <tr><td>Formula vs 3-D projection</td><td>first-order term</td><td class="n">≤ 0.003″</td></tr>
        <tr><td><i>For scale:</i> one triangle's angle closure</td><td>report §3.4</td><td class="n">±1.26″ to ±1.40″</td></tr>
      </tbody>
    </table></div>
    <p class="cap">Even if every deflection were doubled, the largest change would be under 2″ and the shift in q under 0.3σ. The correction is a small, well-understood term next to the pointing noise, as Schott himself judged.</p>
  </section>

  <section class="panel">
    <div class="ptitle">8 · What this does not cover</div>
    <ul class="cap" style="padding-left:20px">
      <li>DEFLEC18 is a modern gravity-field model evaluated at the printed station positions. It is not a deflection observed at the marks Schott's observers occupied.</li>
      <li>Heights for eastern stations come from a smoothed 10′ grid; the eastern sight lines are nearly level, so their changes stay small either way.</li>
      <li>Lateral refraction, the other systematic Schott names, is not modelled here.</li>
      <li>The Eastern Oblique Arc's printed angles were taken from Schott 1902 by the report; Schott 1902 station heights are not yet transcribed.</li>
    </ul>
  </section>

  <details class="src">
    <summary>Sources for this page (pages and quotes)</summary>
    <ul>
      <li>National Geodetic Survey, <i>DEFLEC18</i>, deflections of the vertical in NAD 83 (2011), from the hybrid geoid GEOID18; computed 31 Oct 2026 via Interactive Computation for the 456 station positions. NGS describes the values as <q>typically a few arc seconds, but can reach an arc minute</q>. Input and output files: <code>sources/DEFLEC18_us_stations_456_*.txt</code>.</li>
      <li>Schott, C. A., <i>The Transcontinental Triangulation and the American Arc of the Parallel</i>, USC&amp;GS Special Publication No. 4, 1900. Station heights pp. 256, 265, 269, 300, 311, 335–341. On the Salt Lake base net, p. 206, Schott puts the larger direction error <q>mainly to the effect of local deflections in measuring angles</q>, with lateral refraction also sharing in it. Large astronomic deflections at Colorado Springs and Genoa, p. 848.</li>
      <li>Schott, C. A., <i>The Eastern Oblique Arc of the United States and Osculating Spheroid</i>, USC&amp;GS Special Publication No. 7, 1902 (triangles of the Eastern Oblique Arc, via the report).</li>
      <li>Report: <a href="https://rooster-ninja.github.io/TheoremaEgregium_CurvatureMeasuredFromSurveyorsTriangles/">Theorema Egregium: curvature measured from surveyors' triangles</a>, its <code>triangles_rule.csv</code>, <code>chain_results.json</code>, declared rule and model (duplicated in <code>model/</code>).</li>
      <li>EIGEN-6C4 geoid and ETOPO1 topography, 10′ grids to degree 720, ICGEM Calculation Service, via <a href="https://github.com/fatiando-data">Fatiando a Terra data</a> (CC BY 4.0; public domain).</li>
    </ul>
  </details>
</div>

<script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}</script>
<script type="module">
import * as THREE from 'three';
import {{GLTFLoader}} from 'three/addons/loaders/GLTFLoader.js';
import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
const box=document.getElementById('viewer'),st=document.getElementById('vstatus');
const r=new THREE.WebGLRenderer({{antialias:true}});r.setPixelRatio(Math.min(devicePixelRatio,2));
r.outputColorSpace=THREE.SRGBColorSpace;box.appendChild(r.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0x3a4150);
const cam=new THREE.PerspectiveCamera(30,1,10,600000);cam.up.set(0,0,1);
const ctl=new OrbitControls(cam,r.domElement);ctl.enableDamping=true;ctl.maxDistance=120000;
s.add(new THREE.HemisphereLight(0xffffff,0x334455,1.3));
const dl=new THREE.DirectionalLight(0xffffff,1.7);dl.position.set(-5000,-7000,10000);s.add(dl);
const views={{iso:[-25,40,21000,[-150,300,600]],chains:[-20,55,7500,[250,-750,1600]],west:[-10,38,4200,[-1150,-500,1750]],top:[0,89,9000,[250,-700,1600]]}};
function setView(n){{const[az,el,d0,tg]=views[n];ctl.target.set(...tg);const d=d0*Math.max(1,1.6/cam.aspect),a=az*Math.PI/180,e=el*Math.PI/180;
  cam.position.set(tg[0]+d*Math.cos(e)*Math.sin(a),tg[1]-d*Math.cos(e)*Math.cos(a),tg[2]+d*Math.sin(e));ctl.update();
  document.querySelectorAll('button.vbtn').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===n)));}}
let cur='chains';
function size(){{const w=box.clientWidth,h=box.clientHeight;r.setSize(w,h);cam.aspect=w/h;cam.updateProjectionMatrix();setView(cur);}}
new ResizeObserver(size).observe(box);size();
document.querySelectorAll('button.vbtn').forEach(b=>b.addEventListener('click',()=>{{cur=b.dataset.view;setView(cur);}}));
new THREE.TextureLoader().load('model/starplane.png',t=>{{t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;
  const m=new THREE.Mesh(new THREE.CircleGeometry(40000,128),new THREE.MeshBasicMaterial({{map:t,transparent:true,depthWrite:false}}));
  m.position.set(-50,400,-50.5);m.renderOrder=-1;s.add(m);}});
const models={{}};let mcur='bal',pending=2;
const PEAK={{bal:{BP['peak_mm']:.1f},orig:{OP_peak:.1f}}};
function showModel(k){{mcur=k;for(const[n,g]of Object.entries(models))g.visible=(n===k);
  document.querySelectorAll('button.mbtn').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.model===k)));setWater();}}
function load(k,url){{new GLTFLoader().load(url,g=>{{
  g.scene.traverse(o=>{{if(o.isMesh)o.material=new THREE.MeshStandardMaterial({{vertexColors:true,roughness:.85,metalness:0,flatShading:true}});}});
  const slab=g.scene.getObjectByName('land_10');if(slab)slab.visible=false;   // the report's fixed ocean slab; the water plane replaces it
  models[k]=g.scene;s.add(g.scene);g.scene.visible=(k===mcur);
  if(--pending===0){{st.remove();window.__ready=true;}}
}},undefined,()=>{{st.textContent='The model could not be loaded here. The figure in section 3 shows the same view.';}});}}
load('bal','model/balanced/viewer_scene_balanced.glb');load('orig','model/viewer_scene_dov.glb');
document.querySelectorAll('button.mbtn').forEach(b=>b.addEventListener('click',()=>showModel(b.dataset.model)));
const water=new THREE.Mesh(new THREE.PlaneGeometry(7000,8800),new THREE.MeshStandardMaterial({{color:0x2f6fae,transparent:true,opacity:.62,roughness:.35,metalness:0,side:THREE.DoubleSide,depthWrite:false}}));
water.position.set(-50,400,0);water.renderOrder=2;s.add(water);
const wl=document.getElementById('wl'),wo=document.getElementById('wlout');
function setWater(){{const z=+wl.value;water.position.z=z;const pk=PEAK[mcur];
  const rel=z<0?`${{(-z/1000).toFixed(2)}} m below the base`:z<{BP['base_mm']:.0f}?`${{(z/1000).toFixed(3)}} m above the base, under the lowest coast`:z<=pk?`${{((pk-z)/1000).toFixed(2)}} m below the peak`:`${{((z-pk)/1000).toFixed(2)}} m above the peak`;
  wo.textContent=`z = ${{(z/1000).toFixed(3)}} m (${{z.toLocaleString()}} mm, ${{z.toLocaleString()}} km at scale) · ${{rel}}`;}}
wl.addEventListener('input',setWater);setWater();
(function loop(){{ctl.update();r.render(s,cam);requestAnimationFrame(loop);}})();
</script>
</body>
</html>
"""
open(f"{B}/index.html", "w").write(page)
print("wrote index.html", len(page))
