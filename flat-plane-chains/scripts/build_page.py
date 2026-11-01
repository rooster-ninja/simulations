"""Write index.html from data/flat_chains.json (run build_flat.py first)."""
import json, math, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(ROOT, "data", "flat_chains.json")))
S = J["summary"]; A, B = S["US 39th parallel"], S["US Eastern Oblique"]
T = J["triangles"]; segs = J["segments"]; brk = J["breaks"]
esc = html.escape
f1 = lambda v: f"{v:,.1f}".replace(",", " ")
f0 = lambda v: f"{v:,.0f}".replace(",", " ")

# --- z histogram (SVG), both chains, resolved triangles ---
zs = [t["z"] for t in T if t["st"] == "r"]
lo, hi, w = -6, 62, 2
bins = [0] * ((hi - lo) // w)
for z in zs:
    k = int((min(max(z, lo), hi - 1e-9) - lo) // w); bins[k] += 1
W, H, ml, mb, mt = 720, 260, 44, 40, 14
pw, ph = W - ml - 12, H - mb - mt
ymax = max(max(bins), len(zs) * w * 0.3989) * 1.08
X = lambda v: ml + (v - lo) / (hi - lo) * pw
Y = lambda c: mt + ph - c / ymax * ph
bars = "".join(f'<rect x="{X(lo + i * w) + 0.5:.1f}" y="{Y(c):.1f}" width="{pw * w / (hi - lo) - 1:.1f}" height="{mt + ph - Y(c):.1f}" fill="var(--bar-fill)"/>' for i, c in enumerate(bins) if c)
n = len(zs)
gx = [lo + i * 0.1 for i in range(int((6 - lo) / 0.1))]
flat = " ".join(f"{X(x):.1f},{Y(n * w * math.exp(-x * x / 2) / math.sqrt(2 * math.pi)):.1f}" for x in gx if x <= 6)
ticks = "".join(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{mt + ph}" y2="{mt + ph + 5}" stroke="var(--muted)"/><text x="{X(v):.1f}" y="{mt + ph + 19}" text-anchor="middle">{v}</text>' for v in range(-5, 61, 10) if v >= lo)
yt = "".join(f'<line x1="{ml - 4}" x2="{ml + pw}" y1="{Y(c):.1f}" y2="{Y(c):.1f}" stroke="var(--rule)"/><text x="{ml - 8}" y="{Y(c) + 4:.1f}" text-anchor="end">{c}</text>' for c in range(0, int(ymax) + 1, 100))
hist = f'''<svg viewBox="0 0 {W} {H}" role="img" aria-label="Histogram of each triangle's excess over a flat triangle, in units of its closure noise">
{yt}{bars}<polyline points="{flat}" fill="none" stroke="var(--flatline)" stroke-width="2.5"/>
<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{mt}" y2="{mt + ph}" stroke="var(--flatline)" stroke-dasharray="4 4"/>
{ticks}<text x="{ml + pw / 2:.1f}" y="{H - 4}" text-anchor="middle">observed excess ÷ closure noise (σ above a flat triangle)</text>
<text x="{X(5) + 6:.1f}" y="{Y(n * w * 0.3989) + 14:.1f}" fill="var(--flatline)">flat plane: every triangle near 0</text></svg>'''

def seg_rows(sv):
    out = []
    for s in [s for s in segs if s["survey"] == sv]:
        out.append(f'<tr><td class="n">{s["segment"]}</td><td class="n">{s["lon_min"]:.1f}° to {s["lon_max"]:.1f}°</td><td class="n">{s["triangles"]}</td>'
                   f'<td class="n">{s["unresolved"] or "—"}</td><td class="n">{s["tiles"]}</td><td class="n">{f0(s["area_km2"])}</td>'
                   f'<td class="n">{s["sum_obs"]:.1f}″</td><td class="n">±{s["noise"]:.1f}″</td><td class="n">{s["z_flat"]:.1f}</td><td class="n">{s["sum_pred"]:.1f}″</td></tr>')
    return "".join(out)

brk_rows = "".join(
    f'<tr><td>{b["id"]}</td><td>{"39th parallel" if b["survey"].endswith("parallel") else "Eastern Oblique"}</td><td class="n">{b["between"].replace("-", " | ")}</td>'
    f'<td>{"one shared station" if b["kind"].startswith("shared") else "gap"}</td><td>{esc(b["station_a"])}{"" if b["station_a"] == b["station_b"] else " → " + esc(b["station_b"])}</td>'
    f'<td class="n">{"0" if b["gap_km"] == 0 else f1(b["gap_km"])}</td><td class="n">{b["lat"]:.2f}° N {-b["lon"]:.2f}° W</td></tr>'
    for i, b in enumerate(brk))
unres = sorted([t for t in T if t["st"] == "u"], key=lambda t: (t["s"], t["seg"], t["n"]))
unres_rows = "".join(f'<tr><td>{esc(t["n"])}</td><td>{"39th parallel" if t["s"] == 0 else "Eastern Oblique"}</td><td class="n">{t["seg"]}</td><td class="n">{f0(t["a"])}</td><td class="n">{t["ep"]:.2f}″</td></tr>' for t in unres)
nvx = sum(b["kind"].startswith("shared") for b in brk); ngap = len(brk) - nvx

big = sorted([t for t in T if t["st"] == "r"], key=lambda t: -t["eo"])[:8]
big_rows = "".join(f'<tr><td>{esc(t["n"])}</td><td class="n">{f0(t["a"])}</td><td class="n">{t["eo"]:.2f}″</td><td class="n">{t["z"]:.1f}</td><td class="n">{t["ep"]:.2f}″</td><td class="n">{f0(t["R"])} ± {t["sR"]}</td><td class="n">{f0(t["h"])}</td></tr>' for t in big)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Flat Plane, Lumpy Triangles</title>
<meta property="og:title" content="Flat plane, lumpy triangles: the US chains with no curve fitted">
<meta property="og:description" content="Every triangle of the 39th-parallel and Eastern Oblique chains tested on its own against a flat triangle, laid on a flat map of North America with its own measured excess drawn as a lump. Triangles with an unobserved angle are red. Breaks in the chain are flagged.">
<meta name="theme-color" content="#f3efe4">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,700;8..60,800&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
/* Surface Lab / triangulation-chain theme; layout: header, readout, viewer, numbered panels, sources */
:root{{
  --bg:#f3efe4; --card:#f8f5ec; --plate:#ffffff; --ink:#1a1813; --muted:#6b6658; --rule:#ddd5c2;
  --accent:#4a8fb0; --bar:#16140f; --bar-ink:#f3efe4; --unres:#c8342a; --bar-fill:#2b7bb0; --flatline:#c8342a;
  --f-display:"Source Serif 4",Georgia,"Times New Roman",serif; --f-body:"Archivo",system-ui,sans-serif; --f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; --unres:#ef6a5e; --bar-fill:#5fa6d6; --flatline:#ef6a5e; color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; --unres:#ef6a5e; --bar-fill:#5fa6d6; --flatline:#ef6a5e; color-scheme:dark}}
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
.controls{{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center}}
.controls .lab{{font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);min-width:7.5em}}
button{{font:500 14px var(--f-mono);letter-spacing:.04em;color:var(--ink);background:var(--card);border:1.5px solid var(--rule);border-radius:10px;padding:8px 12px;cursor:pointer}}
button:hover{{border-color:var(--muted)}}button:focus-visible,input:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
button[aria-pressed="true"]{{border-color:var(--accent);color:var(--accent)}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 16px;font-family:var(--f-mono);font-size:12px;color:var(--muted)}}
.legend i{{display:inline-block;width:16px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;border:1px solid var(--muted)}}
.cap{{font-size:16px;margin:0;max-width:72ch}}
.viewer{{position:relative;height:min(66vh,580px);min-height:340px;border-radius:12px;overflow:hidden;background:#3a4150;border:1.5px solid var(--rule)}}
.viewer canvas{{display:block;width:100%;height:100%;touch-action:none}}
.tag{{font:600 12px var(--f-mono);color:#1a1813;background:#f2c14e;border-radius:6px;padding:1px 5px;pointer-events:none}}
.tag.vx{{background:#f08c2b}}
#vstatus{{position:absolute;inset:auto 12px 12px 12px;color:#e8e3d8;font:13px var(--f-mono)}}
.info{{font-family:var(--f-mono);font-size:13px;color:var(--ink);min-height:3.2em;background:var(--plate);border:1px solid var(--rule);border-radius:10px;padding:8px 12px}}
.ex{{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;align-items:center;font-family:var(--f-mono);font-size:13px;color:var(--muted)}}
.ex input{{width:100%;accent-color:var(--accent)}}
.readout{{background:var(--card);border:1.5px solid var(--rule);border-radius:16px;padding:16px 18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px 20px}}
.kv .k{{font-family:var(--f-mono);text-transform:uppercase;letter-spacing:.14em;font-size:11.5px;color:var(--muted)}}
.kv .v{{font-family:var(--f-display);font-weight:700;font-size:23px;line-height:1.2;font-variant-numeric:tabular-nums}}
.kv .v.red{{color:var(--unres)}}
.prose p{{margin:0 0 10px;max-width:72ch}}.prose p:last-child{{margin:0}}
ol.steps{{margin:0;padding-left:22px;max-width:74ch}}ol.steps li{{margin:0 0 8px}}
.finding{{border-left:3px solid var(--accent);padding-left:14px;margin:0;max-width:74ch}}
.finding.red{{border-color:var(--unres)}}
table{{border-collapse:collapse;width:100%;font-size:15px}}
th{{font-family:var(--f-display);font-variant:small-caps;font-weight:700;letter-spacing:.03em;text-align:left;border-bottom:1.5px solid var(--rule);padding:8px 10px;font-size:16px;white-space:nowrap}}
td{{border-bottom:1px solid var(--rule);padding:7px 10px;vertical-align:top}}
td.n,th.n{{text-align:right;font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
.tablebox{{overflow-x:auto}}
.histbox{{overflow-x:auto}}.histbox svg{{display:block;width:100%;min-width:520px;height:auto}}
.histbox text{{font:12px var(--f-mono);fill:var(--muted)}}
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
    <p class="eyebrow">Theorema Egregium · no curve fitted</p>
    <h1>Flat plane, lumpy triangles</h1>
    <p class="sub">Each triangle of the two US chains is laid on a flat map and tested on its own: do its three observed angles add up to 180°, as a flat triangle must? Its measured excess is drawn as a lump over its own footprint. Nothing is fitted under the chain as a whole. Triangles with an angle that was never observed are red, and every place the chain is broken is flagged.</p>
  </header>

  <section class="readout" aria-label="Key numbers">
    <div class="kv"><div class="k">Triangles tested</div><div class="v">{A["resolved"] + B["resolved"]}</div></div>
    <div class="kv"><div class="k">Unresolved (angle not observed)</div><div class="v red">{A["unresolved"] + B["unresolved"]}</div></div>
    <div class="kv"><div class="k">Above a flat triangle by &gt;3σ</div><div class="v">{A["above_3sigma"] + B["above_3sigma"]}</div></div>
    <div class="kv"><div class="k">Positive / negative excess</div><div class="v">{A["positive"] + B["positive"]} / {A["negative"] + B["negative"]}</div></div>
    <div class="kv"><div class="k">Breaks caused by unresolved</div><div class="v">0</div></div>
    <div class="kv"><div class="k">Other breaks in the chains</div><div class="v">{len(brk)}</div></div>
  </section>

  <section class="panel">
    <div class="ptitle">1 · The chains on a flat plane</div>
    <div class="controls"><span class="lab">Colour</span>
      <button class="cbtn" data-c="z" aria-pressed="true">vs flat triangle</button>
      <button class="cbtn" data-c="q">vs ellipsoid</button></div>
    <div class="controls"><span class="lab">Triangles</span>
      <button class="tbtn" data-t="tiles" aria-pressed="true">chain tiles</button>
      <button class="tbtn" data-t="all">all, overlapping</button></div>
    <div class="controls"><span class="lab">Chain</span>
      <button class="sbtn" data-s="both" aria-pressed="true">both</button>
      <button class="sbtn" data-s="0">39th parallel</button>
      <button class="sbtn" data-s="1">Eastern Oblique</button></div>
    <div class="controls"><span class="lab">View</span>
      <button class="vbtn" data-view="oblique" aria-pressed="true">whole</button>
      <button class="vbtn" data-view="west">west</button>
      <button class="vbtn" data-view="east">east</button>
      <button class="vbtn" data-view="top">top</button></div>
    <div class="viewer" id="viewer"><div id="vstatus">Loading the chains…</div></div>
    <div class="ex"><label for="exag">Lump height</label><input id="exag" type="range" min="0" max="100" value="62"><output id="exout" for="exag"></output></div>
    <div class="legend" id="legend"></div>
    <div class="info" id="info" aria-live="polite">Hover or tap a triangle to read its numbers.</div>
    <p class="cap">Azimuthal equidistant map of the printed station positions (centre 39° N 92° W), for display only: no number on this page is computed from the map. Each lump is the cap a sphere of that one triangle's own measured curvature would raise over its footprint, height √(area × excess) / 2π, scaled by the slider. The largest real lump is about 370 m. Pins are numbered west to east: P on the 39th parallel, E on the Eastern Oblique. Yellow pins mark gaps where no triangle joins two parts of a chain; orange pins mark joins through a single shared station with no shared side.</p>
  </section>

  <section class="panel">
    <div class="ptitle">2 · One triangle at a time, against a flat triangle</div>
    <ol class="steps">
      <li><b>Observed excess.</b> The three station-adjusted angles printed by Schott, before the network adjustment, minus 180°. A flat triangle gives 0.</li>
      <li><b>Noise.</b> The survey's closure noise per triangle: ±{A["sigma"]}″ for the 39th parallel, ±{B["sigma"]}″ for the Eastern Oblique.</li>
      <li><b>Test.</b> z = observed excess ÷ noise. On a flat plane z scatters around 0 with spread 1, with as many negative as positive.</li>
      <li><b>Unresolved.</b> If Schott's table shows an angle as "…." the angle was not observed, the triangle's sum closes by construction, and it is not tested. It is drawn red and gets no lump.</li>
      <li><b>No surface.</b> No radius or curve is fitted to the chain. The ellipsoid excess is shown only for comparison.</li>
    </ol>
    <div class="math">z = (A + B + C − 180°) / σ<sub>closure</sub>  ·  own radius = √(area / excess)</div>
    <div class="histbox">{hist}</div>
    <p class="finding">Finding: of {A["resolved"] + B["resolved"]} triangles tested on their own, {A["positive"] + B["positive"]} have angles summing to more than 180° and {A["negative"] + B["negative"]} to less; {A["above_3sigma"] + B["above_3sigma"]} exceed a flat triangle by more than 3σ, and the largest by {max(zs):.0f}σ. A flat plane predicts the red curve. The negative triangles are all small (under {max(t["a"] for t in T if t["st"]=="r" and t["eo"]<0):.0f} km²) and none falls below {min(t["z"] for t in T if t["st"]=="r" and t["eo"]<0):.1f}σ, as noise around a small positive excess would give. Small triangles have an expected excess below the noise under any model, so they pile up near zero; the test lives in the large triangles of the tail. This is an inductive result from Schott's printed angles and the stated noise.</p>
  </section>

  <section class="panel">
    <div class="ptitle">3 · Largest triangles, each on its own</div>
    <div class="tablebox"><table>
      <thead><tr><th>Triangle</th><th class="n">Area km²</th><th class="n">Observed excess</th><th class="n">σ above flat</th><th class="n">Ellipsoid excess</th><th class="n">Own radius km</th><th class="n">Lump m</th></tr></thead>
      <tbody>{big_rows}</tbody></table></div>
    <p class="cap">Own radius is what that triangle alone implies, √(area / observed excess), with the error from ±σ on its angle sum. Each is independent of every other row.</p>
  </section>

  <section class="panel">
    <div class="ptitle">4 · Chain re-run, unresolved triangles filtered</div>
    <p class="cap">Sums of observed excess over the non-overlapping chain tiles, per segment. Segments are the parts of a chain joined by shared sides; the breaks between them are in panel 5. Noise is σ·√n. No unresolved triangle is a chain tile, so filtering them leaves the report's tiles unchanged.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Chain</th><th class="n">Triangles</th><th class="n">Unresolved</th><th class="n">Tiles</th><th class="n">Σ observed</th><th class="n">Noise</th><th class="n">σ above flat</th><th class="n">Σ ellipsoid</th></tr></thead>
      <tbody>
        <tr><td>39th parallel</td><td class="n">{A["triangles"]}</td><td class="n">{A["unresolved"]}</td><td class="n">{A["tiles"]}</td><td class="n">{A["sum_obs"]:.1f}″</td><td class="n">±{A["noise"]:.1f}″</td><td class="n">{A["z_flat"]:.0f}</td><td class="n">{A["sum_pred"]:.1f}″</td></tr>
        <tr><td>Eastern Oblique</td><td class="n">{B["triangles"]}</td><td class="n">{B["unresolved"]}</td><td class="n">{B["tiles"]}</td><td class="n">{B["sum_obs"]:.1f}″</td><td class="n">±{B["noise"]:.1f}″</td><td class="n">{B["z_flat"]:.0f}</td><td class="n">{B["sum_pred"]:.1f}″</td></tr>
      </tbody></table></div>
    <div class="tablebox"><table>
      <thead><tr><th class="n">Seg.</th><th class="n">Longitude</th><th class="n">Triangles</th><th class="n">Unres.</th><th class="n">Tiles</th><th class="n">Tile area km²</th><th class="n">Σ observed</th><th class="n">Noise</th><th class="n">σ above flat</th><th class="n">Σ ellipsoid</th></tr></thead>
      <tbody><tr><td colspan="10"><b>39th parallel</b>, west to east</td></tr>{seg_rows("US 39th parallel")}
      <tr><td colspan="10"><b>Eastern Oblique</b>, west to east</td></tr>{seg_rows("US Eastern Oblique")}</tbody></table></div>
  </section>

  <section class="panel">
    <div class="ptitle">5 · Where the chains break</div>
    <p class="finding red">No break is caused by an unresolved triangle. Every red triangle sits inside a net whose resolved triangles still join each other by shared sides around it: removing all {A["unresolved"] + B["unresolved"]} leaves the same segments ({A["segments_without_unresolved"]} and {B["segments_without_unresolved"]}). The red triangles are holes in the test, not cuts in the chain.</p>
    <p class="cap">The chains do break in {len(brk)} other places in this transcription: {nvx} joins pass through a single station with no shared side, so no triangle carries a side across; {ngap} are gaps where no triangle in the data set joins the two parts. Gaps may be sections the report did not transcribe rather than gaps in Schott's network; they are listed for checking against the printed tables.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Pin</th><th>Chain</th><th class="n">Segments</th><th>Kind</th><th>Stations</th><th class="n">Gap km</th><th class="n">Position</th></tr></thead>
      <tbody>{brk_rows}</tbody></table></div>
    <p class="cap">Breaks do not change any triangle's own test. They matter for anything carried along the chain: side length from a base, and chain sums that span a break.</p>
  </section>

  <section class="panel">
    <div class="ptitle">6 · Unresolved triangles</div>
    <p class="cap">One angle printed as "…." in Schott's tables, so the angle sum closes by construction. Ellipsoid excess is shown only to give their size.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Triangle</th><th>Chain</th><th class="n">Segment</th><th class="n">Area km²</th><th class="n">Ellipsoid excess</th></tr></thead>
      <tbody>{unres_rows}</tbody></table></div>
  </section>

  <section class="panel">
    <div class="ptitle">7 · What lumps on a flat plane would have to do</div>
    <div class="prose">
      <p>The lumps are a picture of each triangle's measured excess, not a surface that could produce it. By Gauss–Bonnet, a bump that rises from flat ground and returns to it encloses zero net curvature: its positive cap is paid for by a negative skirt. A triangle drawn around one whole bump would show zero excess, and the triangles over the skirt would show negative excess.</p>
      <p>A flat plane with lumps therefore predicts excesses that cancel in the sum over neighbouring triangles. In the chain tiles they do not: every segment above sums positive, and segment 1 of the 39th parallel sums {segs[0]["sum_obs"]:.0f}″ over {segs[0]["tiles"]} tiles, {segs[0]["z_flat"]:.0f}σ above flat.</p>
    </div>
  </section>

  <section class="panel">
    <div class="ptitle">8 · Error budget and limits</div>
    <div class="tablebox"><table>
      <thead><tr><th>Source</th><th>Size</th><th>Effect here</th></tr></thead>
      <tbody>
        <tr><td>Angle-closure noise per triangle</td><td class="n">±{A["sigma"]}″ / ±{B["sigma"]}″</td><td>The σ in every z; from the report's per-survey rule</td></tr>
        <tr><td>Deflection of the vertical</td><td class="n">rms 0.07″, max 0.90″</td><td>Far below the noise (deflection-chains page)</td></tr>
        <tr><td>Area, from printed sides</td><td class="n">parts per 10⁵</td><td>Own radius only; the flat test needs no area</td></tr>
        <tr><td>Transcription (OCR of Schott's tables)</td><td>3 degree misprints corrected</td><td>Flagged in the report's qc column</td></tr>
        <tr><td>Display map</td><td>azimuthal equidistant</td><td>None: positions are drawn, not used</td></tr>
      </tbody></table></div>
  </section>

  <details class="src">
    <summary>Sources for this page (pages and quotes)</summary>
    <ul>
      <li>Schott, C. A., <i>The Transcontinental Triangulation and the American Arc of the Parallel</i>, USC&amp;GS Special Publication No. 4, 1900. Part III (d), "Adjusted triangles, Utah, Nevada, and California", pp. 588–591: columns "Observed angles", "Corrections", "Spherical excess"; unobserved angles printed "….", e.g. triangle 35 (Pilot Peak–Mount Nebo–Wheeler Peak, Wheeler Peak angle), triangles 13, 16, 20, 22 and 36. Part III §H, p. 613: triangle closing errors, 357 positive and 343 negative over 701 triangles, mean error of an angle ±0.77″.</li>
      <li>Schott, C. A., <i>The Eastern Oblique Arc of the United States and Osculating Spheroid</i>, USC&amp;GS Special Publication No. 7, 1902 (triangles of the Eastern Oblique Arc).</li>
      <li>Report: <a href="https://rooster-ninja.github.io/TheoremaEgregium_CurvatureMeasuredFromSurveyorsTriangles/">Theorema Egregium: curvature measured from surveyors' triangles</a>: <code>triangles_rule.csv</code> (observed and printed excess, area, per-survey σ, qc), <code>chain_results.json</code> (non-overlapping chain tiles), and the master KML of station positions. Copies in <code>sources/</code>.</li>
      <li>Deflection of the vertical sizes: <a href="../deflection-chains/">deflection-chains</a> (NGS DEFLEC18).</li>
      <li>Coastline: Natural Earth 1:50m admin-0 countries (public domain).</li>
    </ul>
  </details>
</div>

<script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}</script>
<script type="module">
import * as THREE from 'three';
import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
import {{CSS2DRenderer,CSS2DObject}} from 'three/addons/renderers/CSS2DRenderer.js';
const box=document.getElementById('viewer'),st=document.getElementById('vstatus'),info=document.getElementById('info');
const r=new THREE.WebGLRenderer({{antialias:true}});r.setPixelRatio(Math.min(devicePixelRatio,2));r.outputColorSpace=THREE.SRGBColorSpace;box.appendChild(r.domElement);
const lr=new CSS2DRenderer();lr.domElement.style.cssText='position:absolute;inset:0;pointer-events:none';box.appendChild(lr.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0x3a4150);
const cam=new THREE.PerspectiveCamera(30,1,5,200000);cam.up.set(0,0,1);
const ctl=new OrbitControls(cam,r.domElement);ctl.enableDamping=true;ctl.maxDistance=40000;
s.add(new THREE.HemisphereLight(0xffffff,0x334455,1.25));const dl=new THREE.DirectionalLight(0xffffff,1.6);dl.position.set(-3000,-4000,6000);s.add(dl);
const ZC=[[-1e9,-3,'#6b3d8f','below −3σ'],[-3,-1,'#a58cc0','−3 to −1σ'],[-1,1,'#e9e4d6','within ±1σ of flat'],[1,3,'#b7d7d0','1 to 3σ'],[3,10,'#5fb0b4','3 to 10σ'],[10,30,'#2b7bb0','10 to 30σ'],[30,1e9,'#173d7a','above 30σ']];
const QC=[[-1e9,.8,'#8c5a2b','q below 0.80'],[.8,.95,'#d6a96b','0.80–0.95'],[.95,1.05,'#e9e4d6','0.95–1.05'],[1.05,1.2,'#7fb3d5','1.05–1.20'],[1.2,1e9,'#2b5f9e','above 1.20']];
const LOWSNR='#8d8a82',UNRES='#c8342a';
let D,mode={{c:'z',t:'tiles',s:'both'}},lumps,unresMesh,faceTri=[],ufaceTri=[],lineObj,pins=[],exag=1;
const N=10;
function colourOf(t){{if(mode.c==='z'){{for(const b of ZC)if(t.z>=b[0]&&t.z<b[1])return b[2];}}
  else{{if(t.z<3)return LOWSNR;for(const b of QC)if(t.q>=b[0]&&t.q<b[1])return b[2];}}return '#ffffff';}}
function legend(){{const L=document.getElementById('legend');const rows=(mode.c==='z'?ZC:QC).map(b=>`<span><i style="background:${{b[2]}}"></i>${{b[3]}}</span>`);
  if(mode.c==='q')rows.push(`<span><i style="background:${{LOWSNR}}"></i>excess under 3σ (q too noisy)</span>`);
  rows.push(`<span><i style="background:${{UNRES}}"></i>unresolved: angle not observed</span><span><i style="background:#f2c14e"></i>gap</span><span><i style="background:#f08c2b"></i>single shared station</span>`);
  L.innerHTML=rows.join('');}}
function build(){{
  if(lumps){{s.remove(lumps);lumps.geometry.dispose();}} if(unresMesh){{s.remove(unresMesh);unresMesh.geometry.dispose();}}
  const pos=[],col=[],uPos=[];faceTri=[];ufaceTri=[];const c=new THREE.Color();
  D.triangles.forEach((t,ti)=>{{
    if(mode.s!=='both'&&String(t.s)!==mode.s)return;
    const [a,b,d]=t.xy;
    if(t.st==='u'){{uPos.push(a[0],a[1],0,b[0],b[1],0,d[0],d[1],0);ufaceTri.push(ti);return;}}
    if(t.st!=='r')return; if(mode.t==='tiles'&&!t.tile)return;
    const hk=t.h/1000; c.set(colourOf(t));
    const P=(i,j)=>{{const k=N-i-j,b1=i/N,b2=j/N,b3=k/N;const bub=27*b1*b2*b3;return [b1*a[0]+b2*b[0]+b3*d[0],b1*a[1]+b2*b[1]+b3*d[1],hk*bub];}};
    for(let i=0;i<N;i++)for(let j=0;j<N-i;j++){{
      const tri=[[P(i,j),P(i+1,j),P(i,j+1)]];if(i+j<N-1)tri.push([P(i+1,j),P(i+1,j+1),P(i,j+1)]);
      for(const f of tri){{for(const v of f){{pos.push(...v);col.push(c.r,c.g,c.b);}}faceTri.push(ti);}}
    }}
  }});
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.computeVertexNormals();
  lumps=new THREE.Mesh(g,new THREE.MeshStandardMaterial({{vertexColors:true,roughness:.8,metalness:0,side:THREE.DoubleSide}}));lumps.scale.z=exag;s.add(lumps);
  const ug=new THREE.BufferGeometry();ug.setAttribute('position',new THREE.Float32BufferAttribute(uPos,3));
  unresMesh=new THREE.Mesh(ug,new THREE.MeshBasicMaterial({{color:UNRES,side:THREE.DoubleSide,transparent:true,opacity:.92,depthTest:false}}));unresMesh.renderOrder=5;unresMesh.position.z=2;s.add(unresMesh);
  if(lineObj){{s.remove(lineObj);lineObj.geometry.dispose();}}
  const lp=[];D.triangles.forEach(t=>{{if(mode.s!=='both'&&String(t.s)!==mode.s)return;const[a,b,d]=t.xy;lp.push(a[0],a[1],.5,b[0],b[1],.5,b[0],b[1],.5,d[0],d[1],.5,d[0],d[1],.5,a[0],a[1],.5);}});
  const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));
  lineObj=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({{color:0x1a1813,transparent:true,opacity:.35}}));s.add(lineObj);
  pins.forEach(p=>{{const on=(mode.s==='both'||String(p.userData.s)===mode.s);p.visible=on;p.traverse(o=>{{if(o.isCSS2DObject){{o.visible=on;o.element.style.display=on?'':'none';}}}});}});
  legend();
}}
const ex=document.getElementById('exag'),exo=document.getElementById('exout');
function setEx(){{exag=Math.round(Math.pow(10,(+ex.value)/100*4));if(lumps)lumps.scale.z=exag;exo.textContent=`× ${{exag.toLocaleString()}} vertical (largest lump 370 m → ${{(0.37*exag).toLocaleString(undefined,{{maximumFractionDigits:0}})}} km)`;}}
ex.addEventListener('input',setEx);setEx();
let views={{}},cur='oblique';
function setView(n){{const[az,el,d0,tg]=views[n];ctl.target.set(...tg);const d=d0*Math.max(1,1.5/cam.aspect),a=az*Math.PI/180,e=el*Math.PI/180;
  cam.position.set(tg[0]+d*Math.cos(e)*Math.sin(a),tg[1]-d*Math.cos(e)*Math.cos(a),tg[2]+d*Math.sin(e));ctl.update();
  document.querySelectorAll('button.vbtn').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===n)));}}
function size(){{const w=box.clientWidth,h=box.clientHeight;r.setSize(w,h);lr.setSize(w,h);cam.aspect=w/h;cam.updateProjectionMatrix();if(views[cur])setView(cur);}}
new ResizeObserver(size).observe(box);
const bind=(cls,key)=>document.querySelectorAll('button.'+cls).forEach(b=>b.addEventListener('click',()=>{{mode[key]=b.dataset[key];
  document.querySelectorAll('button.'+cls).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));if(D)build();}}));
bind('cbtn','c');bind('tbtn','t');bind('sbtn','s');
document.querySelectorAll('button.vbtn').forEach(b=>b.addEventListener('click',()=>{{cur=b.dataset.view;setView(cur);}}));
const ray=new THREE.Raycaster(),mp=new THREE.Vector2();
function pick(ev){{if(!D)return;const rc=r.domElement.getBoundingClientRect();mp.set((ev.clientX-rc.left)/rc.width*2-1,-(ev.clientY-rc.top)/rc.height*2+1);ray.setFromCamera(mp,cam);
  const hits=ray.intersectObjects([unresMesh,lumps]);if(!hits.length)return;const h=hits[0];
  const t=D.triangles[h.object===unresMesh?ufaceTri[h.faceIndex]:faceTri[h.faceIndex]];const ch=t.s?'Eastern Oblique':'39th parallel';
  if(t.st==='u'){{info.innerHTML=`<b>${{t.n}}</b> · ${{ch}} · segment ${{t.seg}}<br><span style="color:var(--unres)">Unresolved: one angle not observed, so its sum closes by construction.</span> Area ${{Math.round(t.a).toLocaleString()}} km², ellipsoid excess ${{t.ep.toFixed(2)}}″.`;return;}}
  info.innerHTML=`<b>${{t.n}}</b> · ${{ch}} · segment ${{t.seg}}${{t.tile?' · chain tile':''}}<br>Observed excess ${{t.eo.toFixed(2)}}″ ± ${{t.sg}}″ = ${{t.z.toFixed(1)}}σ above a flat triangle · ellipsoid ${{t.ep.toFixed(2)}}″ (q ${{t.q.toFixed(3)}})${{t.R?` · own radius ${{t.R.toLocaleString()}} ± ${{t.sR}} km`:''}} · lump ${{Math.round(t.h)}} m · area ${{Math.round(t.a).toLocaleString()}} km²`;}}
r.domElement.addEventListener('pointermove',pick);r.domElement.addEventListener('pointerdown',pick);
fetch('data/flat_chains.json').then(x=>x.json()).then(d=>{{D=d;
  const op=[];for(const run of d.outline)for(let i=1;i<run.length;i++)op.push(run[i-1][0],run[i-1][1],0,run[i][0],run[i][1],0);
  const og=new THREE.BufferGeometry();og.setAttribute('position',new THREE.Float32BufferAttribute(op,3));
  s.add(new THREE.LineSegments(og,new THREE.LineBasicMaterial({{color:0xd9d2c0,transparent:true,opacity:.55}})));
  let xs=[],ys=[];d.triangles.forEach(t=>t.xy.forEach(p=>{{xs.push(p[0]);ys.push(p[1]);}}));
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),cx=(x0+x1)/2,cy=(y0+y1)/2;
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(30000,20000),new THREE.MeshStandardMaterial({{color:0x4b5466,roughness:1}}));ground.position.set(cx,cy+150,-1);s.add(ground);
  views={{oblique:[0,38,4700,[cx,cy-150,0]],west:[-25,30,2300,[-2350,-60,0]],east:[20,32,2600,[1250,-180,0]],top:[0,89.5,5200,[cx,cy,0]]}};
  d.breaks.forEach((b,i)=>{{const vx=b.kind.startsWith('shared');const col=vx?0xf08c2b:0xf2c14e;const p=b.xy[0],q=b.xy[1],mx=(p[0]+q[0])/2,my=(p[1]+q[1])/2;
    const g=new THREE.Group();g.userData.s=b.survey.endsWith('parallel')?0:1;
    const stick=new THREE.Mesh(new THREE.CylinderGeometry(6,6,260,8),new THREE.MeshBasicMaterial({{color:col}}));stick.rotation.x=Math.PI/2;stick.position.set(mx,my,130);g.add(stick);
    const head=new THREE.Mesh(new THREE.SphereGeometry(26,16,12),new THREE.MeshBasicMaterial({{color:col}}));head.position.set(mx,my,270);g.add(head);
    if(!vx){{const lg=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(p[0],p[1],3),new THREE.Vector3(q[0],q[1],3)]);const ln=new THREE.Line(lg,new THREE.LineDashedMaterial({{color:col,dashSize:10,gapSize:7}}));ln.computeLineDistances();g.add(ln);}}
    const el=document.createElement('div');el.className='tag'+(vx?' vx':'');el.textContent=b.id;const lab=new CSS2DObject(el);lab.position.set(mx,my,330);g.add(lab);
    s.add(g);pins.push(g);}});
  build();size();setView(cur);st.remove();window.__ready=true;
}}).catch(()=>{{st.textContent='The chain data could not be loaded here. Tables 3 to 6 list the same triangles and breaks.';}});
(function loop(){{ctl.update();r.render(s,cam);lr.render(s,cam);requestAnimationFrame(loop);}})();
</script>
</body>
</html>
'''
open(os.path.join(ROOT, "index.html"), "w").write(page)
print("wrote index.html", len(page))
