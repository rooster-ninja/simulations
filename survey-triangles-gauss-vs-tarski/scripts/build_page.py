"""Write index.html from data/gauss_tarski.json (run build.py first)."""
import json, math, os, html, statistics as stt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(ROOT, 'data', 'gauss_tarski.json')))
S = J['summary']; A, B = S['US 39th parallel'], S['US Eastern Oblique']
T = J['triangles']; F = J['fans']
esc = html.escape
CH = ['US 39th parallel', 'US Eastern Oblique']
SHORT = {'US 39th parallel': '39th parallel', 'US Eastern Oblique': 'Eastern Oblique'}
f0 = lambda v: f"{v:,.0f}".replace(',', ' ')

# ---------- numbers ----------
n_tri = len(T)
tested = [t for t in T if t['z'] is not None]
above3 = [t for t in tested if t['z'] > 3]
pos = sum(t['z'] > 0 for t in tested)
flat_ok = sum(t['flat_exists'] for t in T)
max_sum_err = max(abs(t['flat_angle_sum_minus_180_arcsec']) for t in T)
leg = sorted(t['legendre_residual_rms_arcsec'] for t in T)
leg_med = stt.median(leg); leg_95 = leg[int(0.95 * len(leg))]
measured_tri = [t for t in T if any(t['measured_side'])]
min_margin = min(T, key=lambda t: t['triangle_ineq_margin_m'] / max(t['side_a_m'], t['side_b_m'], t['side_c_m']))
deg_ang = max(min_margin['flat_angles'])

def fan_stats(fs, key):
    r = [-f['flat_angles_from_sides_minus_360_arcsec'] - f[key] for f in fs if f[key] is not None]
    m = sum(r) / len(r); sd = math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1))
    return len(r), m, sd
fan_p = {c: fan_stats([f for f in F if f['survey'] == c], 'third_of_printed_excess_arcsec') for c in CH}
fan_o = {c: fan_stats([f for f in F if f['survey'] == c], 'third_of_observed_excess_arcsec') for c in CH}
fan_all_p = fan_stats(F, 'third_of_printed_excess_arcsec')
fan_all_o = fan_stats(F, 'third_of_observed_excess_arcsec')
defs = [-f['flat_angles_from_sides_minus_360_arcsec'] for f in F]

# ---------- per-chain tables ----------
def chain_row(c):
    t = [x for x in T if x['survey'] == c]; te = [x for x in t if x['z'] is not None]
    return (f'<tr><td>{SHORT[c]}</td><td class="n">{len(t)}</td><td class="n">{len(te)}</td>'
            f'<td class="n">{sum(x["z"] > 0 for x in te)} / {sum(x["z"] < 0 for x in te)}</td>'
            f'<td class="n">{sum(x["z"] > 3 for x in te)}</td><td class="n">±{te[0]["sigma_arcsec"]:.3f}″</td>'
            f'<td class="n">{len(te)} of {len(te)}</td></tr>')
gauss_rows = ''.join(chain_row(c) for c in CH)

def tarski_row(c):
    t = [x for x in T if x['survey'] == c]
    lg = sorted(x['legendre_residual_rms_arcsec'] for x in t)
    return (f'<tr><td>{SHORT[c]}</td><td class="n">{len(t)}</td><td class="n">{sum(x["flat_exists"] for x in t)}</td>'
            f'<td class="n">{max(abs(x["flat_angle_sum_minus_180_arcsec"]) for x in t):.0e}″</td>'
            f'<td class="n">{sum(any(x["measured_side"]) for x in t)}</td>'
            f'<td class="n">{stt.median(lg):.2f}″</td><td class="n">{lg[int(.95 * len(lg))]:.2f}″</td></tr>')
tarski_rows = ''.join(tarski_row(c) for c in CH)

def fan_row(c):
    n, m, sd = fan_p[c]; no, mo, sdo = fan_o[c]
    d = [-f['flat_angles_from_sides_minus_360_arcsec'] for f in F if f['survey'] == c]
    return (f'<tr><td>{SHORT[c]}</td><td class="n">{n}</td><td class="n">{min(d):.2f}″ to {max(d):.2f}″</td>'
            f'<td class="n">{m:+.2f}″ ± {sd:.2f}″</td><td class="n">{mo:+.2f}″ ± {sdo:.2f}″ <span class="mut">({no})</span></td></tr>')
fan_rows = ''.join(fan_row(c) for c in CH)

top_fans = sorted(F, key=lambda f: f['flat_angles_from_sides_minus_360_arcsec'])[:10]
fan_top_rows = ''.join(
    f'<tr><td>{esc(f["centre"])}</td><td>{SHORT[f["survey"]]}</td><td class="n">{f["n_triangles"]}</td>'
    f'<td class="n">{-f["flat_angles_from_sides_minus_360_arcsec"]:.2f}″</td><td class="n">{f["third_of_printed_excess_arcsec"]:.2f}″</td>'
    f'<td class="n">{"—" if f["third_of_observed_excess_arcsec"] is None else "%.2f″" % f["third_of_observed_excess_arcsec"]}</td></tr>'
    for f in top_fans)

meas_rows = ''.join(
    f'<tr><td>{esc(t["triangle"])}</td><td class="n">{t["page"]}</td>'
    f'<td>{esc(", ".join(" – ".join(s for j, s in enumerate(t["stations"]) if j != i) for i, mm in enumerate(t["measured_side"]) if mm))}</td>'
    f'<td class="n">{"—" if t["z"] is None else "%.1f" % t["z"]}</td></tr>' for t in measured_tri)

BASES = [('Kent Island and St. Albans', '+11', '395 000'), ('St. Albans and Holton', '−24', '181 000'),
         ('Holton and Olney', '−71', '61 200'), ('Olney and American Bottom', '−6', '724 000'),
         ('American Bottom and Versailles', '+86', '50 500'), ('Versailles and Salina', '+169', '25 700'),
         ('Salina and El Paso', '−92.3', '47 000'), ('El Paso and Salt Lake', '+85.4', '50 840'),
         ('Salt Lake and Yolo', '+82.6', '52 600')]
base_rows = ''.join(f'<tr><td>{a}</td><td class="n">{b}</td><td class="n">{c}</td></tr>' for a, b, c in BASES)

# ---------- fan scatter (SVG) ----------
W, H, ml, mb, mt, mr = 720, 300, 48, 44, 14, 14
pw, ph = W - ml - mr, H - mb - mt
xmax = max(max(f['third_of_printed_excess_arcsec'] for f in F),
           max((f['third_of_observed_excess_arcsec'] or 0) for f in F)) * 1.05
ymax = max(defs) * 1.05
vmax = max(xmax, ymax)
X = lambda v: ml + v / vmax * pw
Y = lambda v: mt + ph - v / vmax * ph
pts_o = ''.join(f'<circle cx="{X(f["third_of_observed_excess_arcsec"]):.1f}" cy="{Y(-f["flat_angles_from_sides_minus_360_arcsec"]):.1f}" r="4" fill="none" stroke="var(--obs)" stroke-width="1.4"/>'
                for f in F if f['third_of_observed_excess_arcsec'] is not None)
pts_p = ''.join(f'<circle cx="{X(f["third_of_printed_excess_arcsec"]):.1f}" cy="{Y(-f["flat_angles_from_sides_minus_360_arcsec"]):.1f}" r="3.2" fill="var(--bar-fill)"/>' for f in F)
ticks = ''
for v in range(0, int(vmax) + 1, 10):
    ticks += (f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{mt + ph}" y2="{mt + ph + 5}" stroke="var(--muted)"/>'
              f'<text x="{X(v):.1f}" y="{mt + ph + 19}" text-anchor="middle">{v}</text>'
              f'<line x1="{ml}" x2="{ml + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--rule)"/>'
              f'<text x="{ml - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
scatter = f'''<svg viewBox="0 0 {W} {H}" role="img" aria-label="Closed fans: angle deficit from printed sides against one third of the excess of the fan's triangles">
{ticks}<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(vmax):.1f}" y2="{Y(vmax):.1f}" stroke="var(--flatline)" stroke-dasharray="5 4" stroke-width="1.5"/>
{pts_o}{pts_p}
<text x="{ml + pw / 2:.1f}" y="{H - 6}" text-anchor="middle">one third of the excess of the fan's triangles (″)</text>
<text transform="translate(13 {mt + ph / 2:.1f}) rotate(-90)" text-anchor="middle">deficit from printed sides only (″)</text>
<text x="{X(vmax * 0.06):.1f}" y="{Y(vmax * 0.88):.1f}" fill="var(--flatline)">dashed: deficit = ⅓ Σ excess</text></svg>'''

# ---------- map data ----------
na = json.load(open(os.path.join(ROOT, 'sources', 'na_outline_lonlat.json')))
def proj(lon, lat, lon0=-92.0, lat0=39.0, R=6371.0):
    p, p0, dl = math.radians(lat), math.radians(lat0), math.radians(lon - lon0)
    c = math.acos(max(-1, min(1, math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(dl))))
    k = R * c / math.sin(c) if c > 1e-12 else R
    return (k * math.cos(p) * math.sin(dl), k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(dl)))
outline = [[[round(v, 1) for v in proj(*pt)] for pt in poly['pts']] for poly in na]
r3 = lambda v: None if v is None else round(v, 3)
import csv
TILE = {(r['survey'], r['triangle']): int(r['chain_tile'] == '1')
        for r in csv.DictReader(open(os.path.join(ROOT, 'sources', 'flat_plane_chains_triangles.csv')))}
MAPT = [[CH.index(t['survey']), t['triangle'], t['page'], [[round(v, 2) for v in xy] for xy in t['xy']],
         r3(t['observed_excess_arcsec']), r3(t['printed_excess_arcsec']), r3(t['z']), round(t['area_km2'], 1),
         [round(t['side_a_m'], 2), round(t['side_b_m'], 2), round(t['side_c_m'], 2)],
         [round(a, 6) for a in t['flat_angles']], [None if a is None else round(a, 6) for a in t['printed_angles']],
         [int(m) for m in t['measured_side']], round(t['legendre_residual_rms_arcsec'], 2), t['stations'],
         round(t['triangle_ineq_margin_m'], 4), int(t['flat_exists']), TILE.get((t['survey'], t['triangle']), 0)] for t in T]
MAPF = [[CH.index(f['survey']), f['centre'], [round(v, 2) for v in f['xy']], f['n_triangles'],
         round(-f['flat_angles_from_sides_minus_360_arcsec'], 3), round(f['third_of_printed_excess_arcsec'], 3),
         r3(f['third_of_observed_excess_arcsec']), f['ring'], f['triangles']] for f in F]
DATA = json.dumps(dict(t=MAPT, f=MAPF, o=outline), separators=(',', ':'), ensure_ascii=False)

big = sorted(tested, key=lambda t: -t['z'])[0]

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Gauss vs Tarski</title>
<meta property="og:title" content="Survey triangles across America: Gauss vs Tarski">
<meta property="og:description" content="Every triangle of Schott's 39th-parallel and Eastern Oblique chains read two ways. By angles (Gauss): {len(above3)} triangles are curved beyond 3σ, but every one gets there through angular excess, which exits TE (the Theorema Egregium). By lengths only (Tarski): all {n_tri} close as flat triangles, and the closed fans carry only the curvature Legendre's theorem put into the computed sides.">
<meta name="theme-color" content="#f3efe4">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,700;8..60,800&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
/* Surface Lab / triangulation-chain theme; layout: header, readout, viewer, numbered panels, sources */
:root{{
  --bg:#f3efe4; --card:#f8f5ec; --plate:#ffffff; --ink:#1a1813; --muted:#6b6658; --rule:#ddd5c2;
  --accent:#4a8fb0; --bar:#16140f; --bar-ink:#f3efe4; --unres:#c8342a; --bar-fill:#2b7bb0; --flatline:#c8342a; --obs:#b0782a;
  --map:#e9e3d3; --land:#f6f2e8; --coast:#b9b09a; --tri-flat:#8fa88a; --tri-edge:#3d4a3a; --neg:#d07a2a; --pos:#2b6fa8;
  --f-display:"Source Serif 4",Georgia,"Times New Roman",serif; --f-body:"Archivo",system-ui,sans-serif; --f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; --unres:#ef6a5e; --bar-fill:#5fa6d6; --flatline:#ef6a5e; --obs:#d9a55a;
  --map:#1b1a16; --land:#26241d; --coast:#4a4536; --tri-flat:#7f9a79; --tri-edge:#c9d6c3; --neg:#e39350; --pos:#6aa8db; color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#17150f; --card:#1f1c15; --plate:#25221a; --ink:#efe9da; --muted:#a59e8b; --rule:#3a352a;
  --accent:#6fb3d3; --bar:#0d0c09; --bar-ink:#efe9da; --unres:#ef6a5e; --bar-fill:#5fa6d6; --flatline:#ef6a5e; --obs:#d9a55a;
  --map:#1b1a16; --land:#26241d; --coast:#4a4536; --tri-flat:#7f9a79; --tri-edge:#c9d6c3; --neg:#e39350; --pos:#6aa8db; color-scheme:dark}}
*,*::before,*::after{{box-sizing:border-box}}
html,body{{margin:0}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.55;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 40px}}
.wrap{{max-width:1100px;margin:0 auto;display:flex;flex-direction:column;gap:22px;padding-top:28px}}
.back{{margin:0 0 14px;font-family:var(--f-mono);font-size:13px}}.back a{{color:var(--muted);text-decoration:none}}.back a:hover{{color:var(--accent)}}
.eyebrow{{font-family:var(--f-mono);font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin:0}}
h1{{font-family:var(--f-display);font-weight:800;font-size:clamp(32px,5.2vw,54px);line-height:1.04;letter-spacing:-.01em;margin:10px 0 0;text-wrap:balance;max-width:24ch}}
.sub{{color:var(--ink);font-size:18px;max-width:68ch;margin:14px 0 0}}
.panel{{background:var(--card);border:1.5px solid var(--rule);border-radius:16px;padding:18px 18px 16px;display:flex;flex-direction:column;gap:12px;min-width:0}}
.ptitle{{font-family:var(--f-mono);font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);font-weight:500}}
.math{{font-family:var(--f-display);font-style:italic;font-size:19px;text-align:center;line-height:1.7;overflow-x:auto;padding:2px 4px}}
.controls{{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center}}
.controls .lab{{font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);min-width:7.5em}}
button{{font:500 14px var(--f-mono);letter-spacing:.04em;color:var(--ink);background:var(--card);border:1.5px solid var(--rule);border-radius:10px;padding:8px 12px;cursor:pointer}}
button:hover{{border-color:var(--muted)}}button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
button[aria-pressed="true"]{{border-color:var(--accent);color:var(--accent)}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 16px;font-family:var(--f-mono);font-size:12px;color:var(--muted)}}
.legend i{{display:inline-block;width:16px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;border:1px solid var(--muted)}}
.cap{{font-size:16px;margin:0;max-width:74ch}}
.mut{{color:var(--muted)}}
.viewer{{position:relative;height:min(64vh,560px);min-height:340px;border-radius:12px;overflow:hidden;background:var(--map);border:1.5px solid var(--rule)}}
.viewer canvas{{display:block;width:100%;height:100%;touch-action:none;cursor:crosshair}}
#vstatus{{position:absolute;left:12px;top:10px;right:12px;font:600 13px var(--f-mono);color:var(--ink);pointer-events:none;text-shadow:0 0 4px var(--map)}}
.viewer3{{position:relative;height:min(66vh,580px);min-height:340px;border-radius:12px;overflow:hidden;background:#3a4150;border:1.5px solid var(--rule)}}
.viewer3 canvas{{display:block;width:100%;height:100%;touch-action:none}}
#v3status{{position:absolute;inset:auto 12px 12px 12px;color:#e8e3d8;font:13px var(--f-mono)}}
.info{{font-family:var(--f-mono);font-size:13px;color:var(--ink);min-height:3.2em;background:var(--plate);border:1px solid var(--rule);border-radius:10px;padding:8px 12px}}
.ex{{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;align-items:center;font-family:var(--f-mono);font-size:13px;color:var(--muted)}}
.ex input{{width:100%;accent-color:var(--accent)}}
.ex output{{grid-column:1/-1}}
.audit{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
@media (max-width:720px){{.audit{{grid-template-columns:1fr}}}}
.audit>div{{font-family:var(--f-mono);font-size:13px;background:var(--plate);border:1px solid var(--rule);border-radius:10px;padding:10px 12px;min-height:7em;overflow-x:auto}}
.audit h4{{margin:0 0 6px;font:600 12px var(--f-mono);letter-spacing:.14em;text-transform:uppercase}}
.audit .g h4{{color:var(--unres)}}.audit .t h4{{color:var(--accent)}}
.audit .row{{display:flex;justify-content:space-between;gap:12px;border-bottom:1px dotted var(--rule);padding:2px 0}}
.audit .row span:last-child{{text-align:right;font-variant-numeric:tabular-nums}}
.audit .exit{{color:var(--unres)}}
.readout{{background:var(--card);border:1.5px solid var(--rule);border-radius:16px;padding:16px 18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px 20px}}
.kv .k{{font-family:var(--f-mono);text-transform:uppercase;letter-spacing:.14em;font-size:11.5px;color:var(--muted)}}
.kv .v{{font-family:var(--f-display);font-weight:700;font-size:23px;line-height:1.2;font-variant-numeric:tabular-nums}}
.kv .v.red{{color:var(--unres)}}.kv .v.blue{{color:var(--accent)}}
.prose p{{margin:0 0 10px;max-width:74ch}}.prose p:last-child{{margin:0}}
ol.steps{{margin:0;padding-left:22px;max-width:76ch}}ol.steps li{{margin:0 0 8px}}
.finding{{border-left:3px solid var(--accent);padding-left:14px;margin:0;max-width:76ch}}
.finding.red{{border-color:var(--unres)}}
blockquote{{margin:0;padding:8px 14px;border-left:3px solid var(--rule);font-family:var(--f-display);font-size:18px;max-width:72ch}}
blockquote cite{{display:block;font:13px var(--f-mono);color:var(--muted);font-style:normal;margin-top:4px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media (max-width:760px){{.two{{grid-template-columns:1fr}}}}
.col h3{{font-family:var(--f-display);font-size:22px;margin:0 0 6px}}
.col.g h3{{color:var(--unres)}}.col.t h3{{color:var(--accent)}}
table{{border-collapse:collapse;width:100%;font-size:15px}}
th{{font-family:var(--f-display);font-variant:small-caps;font-weight:700;letter-spacing:.03em;text-align:left;border-bottom:1.5px solid var(--rule);padding:8px 10px;font-size:16px;white-space:nowrap}}
td{{border-bottom:1px solid var(--rule);padding:7px 10px;vertical-align:top}}
td.n,th.n{{text-align:right;font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
td.x{{color:var(--unres);font-family:var(--f-mono);white-space:nowrap}}td.ok{{color:var(--accent);font-family:var(--f-mono);white-space:nowrap}}
.tablebox{{overflow-x:auto}}
.histbox{{overflow-x:auto}}.histbox svg{{display:block;width:100%;min-width:520px;height:auto}}
.histbox text{{font:12px var(--f-mono);fill:var(--muted)}}
details.src{{background:var(--bar);color:var(--bar-ink);border-radius:12px;padding:14px 18px;font-family:var(--f-mono);font-size:14px}}
details.src summary{{cursor:pointer;font-weight:600}}
details.src ul{{margin:12px 0 0;padding-left:18px;font-family:var(--f-body);font-size:14px;line-height:1.6}}
details.src li{{margin-bottom:6px}}
details.src a{{color:var(--bar-ink)}}
code{{font-family:var(--f-mono);font-size:.92em}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="back"><a href="../">← All simulations</a></p>
    <p class="eyebrow">Theorema Egregium · Gauss vs Tarski</p>
    <h1>Survey triangles across America: Gauss vs Tarski</h1>
    <p class="sub">Every triangle of Schott's 39th-parallel and Eastern Oblique chains, read two ways. Read by its angles, a triangle can show curvature, but only through angular excess, and that step exits TE (the Theorema Egregium). Read by its lengths only, as Tarski's plane geometry decides, every triangle closes flat. The curved triangles all live on the angle side.</p>
  </header>

  <section class="readout" aria-label="Key numbers">
    <div class="kv"><div class="k">Triangles</div><div class="v">{n_tri}</div></div>
    <div class="kv"><div class="k">Curved by angles, &gt;3σ</div><div class="v red">{len(above3)}</div></div>
    <div class="kv"><div class="k">Of those, curvature via angular excess</div><div class="v red">{len(above3)} of {len(above3)}</div></div>
    <div class="kv"><div class="k">Close flat from their own sides</div><div class="v blue">{flat_ok} of {n_tri}</div></div>
    <div class="kv"><div class="k">Triangles with a measured side</div><div class="v">{len(measured_tri)}</div></div>
    <div class="kv"><div class="k">Closed fans: deficit − ⅓Σ printed ε</div><div class="v">{fan_all_p[1]:+.2f}″ ± {fan_all_p[2]:.2f}″</div></div>
  </section>

  <section class="panel">
    <div class="ptitle">1 · The same triangles, two readings</div>
    <div class="controls"><span class="lab">Reading</span>
      <button class="mbtn" data-m="gauss" aria-pressed="true">Gauss: angles</button>
      <button class="mbtn" data-m="tarski">Tarski: lengths</button>
      <button class="mbtn" data-m="fans">Closed fans: lengths</button></div>
    <div class="controls"><span class="lab">Chain</span>
      <button class="sbtn" data-s="both" aria-pressed="true">both</button>
      <button class="sbtn" data-s="0">39th parallel</button>
      <button class="sbtn" data-s="1">Eastern Oblique</button></div>
    <div class="controls"><span class="lab">View</span>
      <button class="vbtn" data-v="all" aria-pressed="true">whole</button>
      <button class="vbtn" data-v="west">west</button>
      <button class="vbtn" data-v="east">east</button>
      <button class="vbtn" data-v="dauph">Dauphin Island base</button>
      <button class="vbtn" data-v="mass">Massachusetts base</button></div>
    <div class="viewer" id="viewer"><canvas id="map" aria-label="Map of the survey triangles"></canvas><div id="vstatus">Loading…</div></div>
    <div class="legend" id="legend"></div>
    <div class="audit" id="audit" aria-live="polite">
      <div class="g"><h4>Gauss · angles</h4><span class="mut">Tap a triangle, or a fan centre in the fan view.</span></div>
      <div class="t"><h4>Tarski · lengths</h4><span class="mut">Its three printed sides, decided as a plane triangle.</span></div>
    </div>
    <p class="cap">Drag to pan, wheel or pinch to zoom. The map is an azimuthal equidistant projection of the printed station positions (centre 39° N 92° W), for display only: no number on this page comes from it. In the Gauss reading each triangle is coloured by z = (sum of observed angles − 180°) ÷ closure noise; under 3σ is faded; red outline means one angle was never observed. In the Tarski reading each triangle is drawn from what its three printed sides decide; heavy ink marks a side that is a measured base line. In the fan reading each dot is a station ringed by triangles, sized by the angle deficit computed from printed sides alone.</p>
  </section>

  <section class="panel">
    <div class="ptitle">2 · Gauss curves in 3D: each triangle's own excess</div>
    <div class="controls"><span class="lab">Reading</span>
      <button class="rbtn" data-r="gauss" aria-pressed="true">Gauss: curved by angles</button>
      <button class="rbtn" data-r="tarski">Tarski: lengths only</button></div>
    <div class="controls"><span class="lab">Triangles</span>
      <button class="tbtn" data-t="tiles" aria-pressed="true">chain tiles</button>
      <button class="tbtn" data-t="all">all, overlapping</button></div>
    <div class="controls"><span class="lab">Chain</span>
      <button class="s3btn" data-s="both" aria-pressed="true">both</button>
      <button class="s3btn" data-s="0">39th parallel</button>
      <button class="s3btn" data-s="1">Eastern Oblique</button></div>
    <div class="controls"><span class="lab">View</span>
      <button class="v3btn" data-v="oblique" aria-pressed="true">whole</button>
      <button class="v3btn" data-v="west">west</button>
      <button class="v3btn" data-v="nebo">Nebo–Tushar–Wheeler</button>
      <button class="v3btn" data-v="east">east</button>
      <button class="v3btn" data-v="top">top</button></div>
    <div class="viewer3" id="viewer3"><div id="v3status">Loading 3D…</div></div>
    <div class="ex"><label for="exag">Curve height</label><input id="exag" type="range" min="0" max="100" value="50"><output id="exout" for="exag"></output></div>
    <div class="legend" id="legend3"></div>
    <div class="info" id="info3" aria-live="polite">Hover or tap a curved triangle to read its numbers.</div>
    <p class="cap">Each tested triangle is drawn as the piece of a sphere of its own radius, √(area / observed excess), through its three corners: height (r² − d²) / 2R above the flat plane, r its circumradius and d the distance from the circumcentre. Negative excess dips below. Nothing joins one triangle's curve to the next: each curve is that triangle's own excess and exists only inside it. The excess gives only the triangle's total curvature, so the even spread drawn inside it is a display choice. Under 3σ is faded; red is an angle never observed. Switch to the Tarski reading and every curve settles flat: from its three printed sides each triangle is a plane triangle. Map: azimuthal equidistant, display only.</p>
  </section>

  <section class="panel">
    <div class="ptitle">3 · What the theorem allows</div>
    <div class="two">
      <div class="col g prose">
        <h3>Gauss, 1827</h3>
        <blockquote>"If a curved surface is developed upon any other surface whatever, the measure of curvature in each point remains unchanged."<cite>Disquisitiones generales, Art. 12 (Theorema Egregium)</cite></blockquote>
        <p>The proof (Art. 11) gives the measure of curvature by a formula "which involves only the quantities E, F, G and their differential quotients": lengths measured on the surface. That is the whole theorem. It names no triangle, no angle sum and no excess.</p>
        <p>The angle-sum theorem is a different one, Art. 20, and Gauss states it through the normals: the excess "is measured by the area of the part of the sphere which corresponds, through the directions of the normals, to that triangle". Getting from excess to curvature exits TE: it leaves Art. 12 for Art. 20.</p>
      </div>
      <div class="col t prose">
        <h3>Tarski, 1948 / 1951</h3>
        <blockquote>"A decision method by which the truth of sentences of the elementary algebra and geometry of real numbers is determined."<cite>A Decision Method for Elementary Algebra and Geometry, RAND R-109, summary</cite></blockquote>
        <p>Plane geometry written in first-order terms (points, betweenness, equal distances) is complete: every sentence in it is mechanically proved or refuted. For survey lengths two sentences matter, and both are decided here for every case:</p>
        <ol class="steps"><li><b>Triangle.</b> Three lengths form a plane triangle if and only if each is shorter than the sum of the other two. Its plane angles then sum to exactly 180°.</li>
        <li><b>Closed fan.</b> Triangles ringed round one station lie flat if and only if their plane angles at that station sum to exactly 360°.</li></ol>
      </div>
    </div>
    <p class="finding">Inside the Theorema Egregium, curvature must come from lengths. Tarski's method says what lengths alone decide in the plane. Angles, plumb lines and the excess are outside both.</p>
  </section>

  <section class="panel">
    <div class="ptitle">4 · Gauss reading: every curved triangle exits TE</div>
    <div class="tablebox"><table>
      <thead><tr><th>Chain</th><th class="n">Triangles</th><th class="n">Tested by angles</th><th class="n">Excess + / −</th><th class="n">&gt;3σ curved</th><th class="n">Closure noise</th><th class="n">Via angular excess</th></tr></thead>
      <tbody>{gauss_rows}</tbody></table></div>
    <div class="math">ε = A + B + C − 180°  ·  z = ε / σ  ·  K ≈ ε / area</div>
    <p class="cap">Each step that turns a curved triangle's numbers into curvature, and where it exits TE. Every one of the {len(tested)} tested triangles takes all of rows 1–4; none takes a length-only route.</p>
    <div class="tablebox"><table>
      <thead><tr><th class="n">#</th><th>Step</th><th>What it rests on</th><th>Exits TE?</th><th>Source</th></tr></thead>
      <tbody>
        <tr><td class="n">1</td><td>The data are angles, not lengths</td><td>Theodolite readings between signals</td><td class="x">exits TE: Art. 12 uses E, F, G</td><td>Schott SP4 §H p. 612</td></tr>
        <tr><td class="n">2</td><td>Each angle lies in the station's horizontal plane</td><td>Instrument "necessarily adjusted to the plumb-line": gravity sets the plane</td><td class="x">exits TE: extrinsic, the plumb line is not a surface length</td><td>SP4 p. 206; SP7 p. 26</td></tr>
        <tr><td class="n">3</td><td>Sight lines stand in for shortest lines on the surface</td><td>Light through air, with "persistent lateral refraction"</td><td class="x">exits TE: assumed, not measured</td><td>SP4 p. 206; SP7 p. 26</td></tr>
        <tr><td class="n">4</td><td>Excess over 180° = integral curvature</td><td>Gauss Art. 20, stated "through the directions of the normals"</td><td class="x">exits TE: Art. 20, a different theorem</td><td>Gauss Art. 20</td></tr>
        <tr><td class="n">5</td><td>K = excess ÷ area</td><td>Curvature taken as even over the triangle</td><td class="x">exits TE: an average, not a point value</td><td>—</td></tr>
        <tr><td class="n">6</td><td>The printed excess column</td><td>Computed from ab sin C over the ellipsoid's radii ρ<sub>m</sub>ρ<sub>n</sub></td><td class="x">exits TE: model output, not observed</td><td>SP4 p. 51; SP7 p. 26</td></tr>
      </tbody></table></div>
    <p class="finding red">Finding: {len(above3)} triangles are curved beyond 3σ by their angles, the largest {esc(big["triangle"])} at {big["z"]:.0f}σ. All {len(above3)}, and all {len(tested)} tested, reach curvature through steps 1–4. Every one exits TE; none is a Theorema Egregium result. They are results of Art. 20 applied to plumb-levelled angles. This is a statement about the route, not the size: the excess is measured and real at the stated noise.</p>
  </section>

  <section class="panel">
    <div class="ptitle">5 · Tarski reading: every triangle closes flat</div>
    <div class="tablebox"><table>
      <thead><tr><th>Chain</th><th class="n">Triangles</th><th class="n">Exist flat</th><th class="n">|Σ − 180°| max</th><th class="n">With a measured side</th><th class="n">Legendre residual, median</th><th class="n">95%</th></tr></thead>
      <tbody>{tarski_rows}</tbody></table></div>
    <div class="math">cos A* = (b² + c² − a²) / 2bc  ·  A* + B* + C* = 180° exactly  ·  A* ≈ A − ε/3</div>
    <ol class="steps">
      <li><b>Every triangle exists flat.</b> All {n_tri} sets of three printed sides pass the triangle inequality. The thinnest is {esc(min_margin["triangle"])}, nearly a straight line ({deg_ang:.2f}° at one corner), still a valid plane triangle.</li>
      <li><b>Its flat angles sum to 180°.</b> To {max_sum_err:.0e}″, the rounding of the arithmetic. Three lengths cannot show curvature: the excess is invisible to them.</li>
      <li><b>The sides came from the angles.</b> Each flat angle from the printed sides equals the observed angle less one third of the printed excess, to a median {leg_med:.2f}″ (95% under {leg_95:.2f}″, the size of the network adjustment). That is Legendre's theorem, used by Schott to compute the sides. The lengths are not independent of the angles: they are the angles, reduced to a plane.</li>
      <li><b>Measured lengths are base lines.</b> {len(measured_tri)} chain triangles have a measured base as a side; every other side in both chains was computed through angles from a base.</li>
    </ol>
    <div class="tablebox"><table>
      <thead><tr><th>Triangle with a measured side</th><th class="n">SP7 page</th><th>Measured side</th><th class="n">z by angles</th></tr></thead>
      <tbody>{meas_rows}</tbody></table></div>
  </section>

  <section class="panel">
    <div class="ptitle">6 · Closed fans: the one lengths-only test, and what it finds</div>
    <p class="cap">A strip of triangles always lays flat. Curvature can show in lengths only where triangles close around a station: then their plane angles at the centre, computed from sides alone, must total 360° on a flat surface. Schott built both chains of "quadrilaterals or central figures" (SP4 p. 25), so such fans exist: {len(F)} found.</p>
    <div class="math">deficit = 360° − Σ A*<sub>i</sub>  (A* from printed sides only)</div>
    <div class="histbox">{scatter}</div>
    <div class="legend"><span><i style="background:var(--bar-fill);border-color:var(--bar-fill);border-radius:50%"></i>against the printed (ellipsoid) excess</span><span><i style="background:transparent;border-color:var(--obs);border-radius:50%"></i>against the observed excess</span><span><i style="background:var(--flatline);height:2px;border:0"></i>deficit = ⅓ Σ excess</span></div>
    <div class="tablebox"><table>
      <thead><tr><th>Chain</th><th class="n">Fans</th><th class="n">Deficit from sides</th><th class="n">Deficit − ⅓Σ printed ε</th><th class="n">Deficit − ⅓Σ observed ε</th></tr></thead>
      <tbody>{fan_rows}</tbody></table></div>
    <p class="finding red">Finding: from lengths alone, every fan fails to lie flat: deficits of {min(defs):.1f}″ to {max(defs):.1f}″, so as a lengths-only sentence, "flat" is refuted. But the deficit equals one third of the fan's printed excess to {fan_all_p[1]:+.2f}″ ± {fan_all_p[2]:.2f}″, closer than it matches the observed excess ({fan_all_o[1]:+.2f}″ ± {fan_all_o[2]:.2f}″). The curvature in the lengths is the ellipsoid excess Schott subtracted from each angle to compute the sides. It entered through steps 1–6 of panel 4; it was not measured as a length.</p>
    <div class="tablebox"><table>
      <thead><tr><th>Centre (10 largest)</th><th>Chain</th><th class="n">Triangles</th><th class="n">Deficit from sides</th><th class="n">⅓Σ printed ε</th><th class="n">⅓Σ observed ε</th></tr></thead>
      <tbody>{fan_top_rows}</tbody></table></div>
  </section>

  <section class="panel">
    <div class="ptitle">7 · The measured lengths, and how they were compared</div>
    <p class="cap">The 39th-parallel chain "is supported by 10 base lines suitably distributed" (SP4 p. 25), measured with bars on the ground. Adjacent bases were compared through the triangulation between them, and Schott says how: the length equation "has been derived from the angles", with "Spherical angles … the logarithms of the terminal lines having been corrected for difference in arc and sine" (SP4 p. 613).</p>
    <div class="tablebox"><table>
      <thead><tr><th>Base lines (SP4 p. 614)</th><th class="n">Discrepancy, 7th place of log</th><th class="n">One part in</th></tr></thead>
      <tbody>{base_rows}</tbody></table></div>
    <p class="cap">Raw values as printed; a plus sign means the eastern base gives the greater length. These are length against length, but the bridge between them is angles reduced with spherical excess, so they exit TE the same way as panel 4. No pair of measured lengths in either chain closes a figure by lengths alone.</p>
  </section>

  <section class="panel">
    <div class="ptitle">8 · Verdict</div>
    <div class="prose">
      <p><b>Gauss reading.</b> All {len(above3)} curved triangles (&gt;3σ), and all {len(tested)} tested, owe their curvature to angular excess: plumb-levelled angles, sight lines taken as shortest lines, and Art. 20 rather than Art. 12. Each one exits TE. They are inductive findings from the printed angles at the stated noise, but not findings of that theorem.</p>
      <p><b>Tarski reading.</b> By lengths, all {n_tri} triangles are flat triangles. The {len(F)} closed fans do refute flatness by lengths, yet only by the excess that Legendre's theorem put into the sides. In this data no length was measured independently of the angles, apart from {len(measured_tri)} base sides, and those close nothing by themselves.</p>
      <p><b>What would stay inside the theorem.</b> A closed fan, or a quadrilateral with both diagonals, whose every side is a measured length. Then the deficit is computed from lengths alone, and only turning it into a value of K needs a further theorem.</p>
    </div>
  </section>

  <section class="panel">
    <div class="ptitle">9 · Methods</div>
    <ol class="steps">
      <li><b>Data.</b> Schott's printed angles, spherical excess and sides for every triangle of the 39th-parallel arc (SP4, 465 triangles) and the Eastern Oblique arc (SP7, 281), as transcribed in the Theorema Egregium report's master KML. Sides are printed as log metres. Observed excess and qc (3 degree misprints corrected from the printed sides) come from the report's <code>triangles_rule.csv</code>.</li>
      <li><b>Gauss reading.</b> ε = sum of the three station-adjusted angles − 180°; z = ε / σ with the report's per-survey closure noise. Triangles with an angle printed "…." are not tested.</li>
      <li><b>Tarski reading.</b> From the three printed sides only: triangle inequality; plane angles by the law of cosines; their sum. Legendre residual = observed angle − printed ε/3 − plane angle, rms over the three corners.</li>
      <li><b>Closed fans.</b> For each station, its neighbours are ordered by map bearing and the finest ring of triangles that wraps 360° without overlap is chosen; each triangle's plane angle at the centre must match its bearing gap within 2°. Deficit = 360° − sum of plane angles at the centre from printed sides.</li>
      <li><b>Measured sides.</b> A side is a measured base when both ends are terminals of the same base line (for example "Dauphin Island East Base" and "Dauphin Island West Base").</li>
    </ol>
  </section>

  <section class="panel">
    <div class="ptitle">10 · Error budget and limits</div>
    <div class="tablebox"><table>
      <thead><tr><th>Source</th><th>Size</th><th>Effect here</th></tr></thead>
      <tbody>
        <tr><td>Angle-closure noise per triangle</td><td class="n">±1.261″ / ±1.397″</td><td>The σ in every z</td></tr>
        <tr><td>Printed sides, 7-place logs</td><td class="n">±1.2 × 10⁻⁷ relative</td><td>Plane angles to about ±0.03″ for well-shaped triangles; flat closure is exact regardless</td></tr>
        <tr><td>Network adjustment</td><td class="n">median {leg_med:.2f}″ per angle</td><td>Spread of the Legendre residual; sides follow adjusted, not observed, angles</td></tr>
        <tr><td>Fan deficit vs ⅓Σε</td><td class="n">±{fan_all_p[2]:.2f}″</td><td>Adjustment and log rounding summed round 3–8 triangles</td></tr>
        <tr><td>Near-degenerate triangle</td><td class="n">{deg_ang:.2f}° corner</td><td>{esc(min_margin["triangle"])}: triangle-inequality margin {min_margin["triangle_ineq_margin_m"]*100:.1f} cm, against about ±0.5 cm from 7-place logs on its {max(min_margin["side_a_m"],min_margin["side_b_m"],min_margin["side_c_m"])/1000:.0f} km side; plane angles ill-conditioned</td></tr>
        <tr><td>Transcription</td><td>3 degree misprints</td><td>Corrected from printed sides (report qc)</td></tr>
        <tr><td>Fan finder</td><td>map bearings</td><td>Chooses which triangles ring a station; values use sides only</td></tr>
        <tr><td>Display map</td><td>azimuthal equidistant</td><td>None: drawn, not used</td></tr>
      </tbody></table></div>
  </section>

  <section class="panel">
    <div class="ptitle">Appendix · Earlier pages on these chains</div>
    <ul class="steps" style="margin:0;padding-left:22px">
      <li><a href="../flat-plane-chains/">Flat plane, lumpy triangles</a>: the same chains on a flat map, each triangle's excess drawn as a lump, unresolved triangles and chain breaks.</li>
      <li><a href="../triangulation-chain/">Triangulation chain</a> and <a href="../deflection-chains/">deflection-chains</a> (deflection of the vertical, NGS DEFLEC18).</li>
      <li>Report: <a href="https://rooster-ninja.github.io/TheoremaEgregium_CurvatureMeasuredFromSurveyorsTriangles/">Theorema Egregium: curvature measured from surveyors' triangles</a>.</li>
    </ul>
  </section>

  <details class="src">
    <summary>Sources for this page (pages and quotes)</summary>
    <ul>
      <li>Gauss, C. F., <i>Disquisitiones generales circa superficies curvas</i> (1827), tr. Morehead &amp; Hiltebeitel, <i>General Investigations of Curved Surfaces</i> (Princeton, 1902); <a href="https://www.gutenberg.org/ebooks/36856">Project Gutenberg 36856</a>. Art. 11, p. 19: "which involves only the quantities E, F, G and their differential quotients". Art. 12, p. 20: "If a curved surface is developed upon any other surface whatever, the measure of curvature in each point remains unchanged." Art. 20, p. 29: "The excess over 180° of the sum of the angles of a triangle formed by shortest lines on a concavo-concave curved surface … is measured by the area of the part of the sphere which corresponds, through the directions of the normals, to that triangle". Art. 27 (p. 42 of the 1902 printing): "the well-known theorem first established by the illustrious Legendre"; Art. 28 (p. 43): the Hohehagen–Brocken–Inselsberg triangle, "where the excess of the sum of the angles was 14″.85348".</li>
      <li>Tarski, A., <i>A Decision Method for Elementary Algebra and Geometry</i>, RAND R-109 (1948; 2nd ed. University of California Press, 1951); <a href="https://www.rand.org/pubs/reports/R109.html">RAND report page</a>, summary: "A decision method by which the truth of sentences of the elementary algebra and geometry of real numbers is determined." The RAND scan is image-only; no further page is quoted.</li>
      <li>Schott, C. A., <i>The Transcontinental Triangulation and the American Arc of the Parallel</i>, USC&amp;GS Special Publication No. 4, 1900. p. 25: "Either quadrilaterals or central figures such as polygons formed by combination of triangles compose the scheme, while its length is supported by 10 base lines suitably distributed." p. 51: "the comparative shortness of the sides of the triangles admits of the application of Legendre's theorem in its simple form"; sides of "a plane triangle, whose angles are those of the corresponding small spherical triangle after each has been diminished by ⅓ E". p. 206: "the vertical axis of the theodolite being necessarily adjusted to the plumb-line … Persistent lateral refraction also has a share". p. 612: closure of the triangles "(π plus spherical excess minus the sum of the angles)". p. 613: "the length equation has been derived from the angles"; "Spherical angles have been used, the logarithms of the terminal lines having been corrected for difference in arc and sine." p. 614: discord between adjacent base lines (table in panel 7). Page extracts: <code>sources/Schott_SP4_1900_pp25_51_206_612-614.pdf</code>.</li>
      <li>Schott, C. A., <i>The Eastern Oblique Arc of the United States and Osculating Spheroid</i>, USC&amp;GS Special Publication No. 7, 1902. p. 26: "effects of large local deflections of the vertical at a station, persistent lateral refraction along a line"; "For the computation of the sides of the triangles Legendre's theorem was used"; excess "computed by the simple formula ab sin C / 2ρ<sub>m</sub>ρ<sub>n</sub> sin 1″". Page extract: <code>sources/Schott_SP7_1902_p26.pdf</code>.</li>
      <li>Triangle angles, sides, excess and station positions: the Theorema Egregium report's master KML and <code>triangles_rule.csv</code> (copies in <code>sources/</code>).</li>
      <li>Coastline: Natural Earth 1:50m admin-0 countries (public domain).</li>
    </ul>
  </details>
</div>

<script>
const D = {DATA};
window.__GT = D;
const CH = ["39th parallel","Eastern Oblique"];
const cv = document.getElementById('map'), ctx = cv.getContext('2d'), st = document.getElementById('vstatus');
let mode = 'gauss', chain = 'both', sel = null, selFan = null;
let view = {{cx:0, cy:0, s:1}};
const VIEWS = {{all:[-2700,2650,-50,1200], west:[-2700,-1000,-250,700], east:[-50,2650,-650,1150], dauph:[330,410,-995,-915], mass:[1660,1740,495,570]}};
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function fit(k){{ const [x0,x1,y0,y1] = VIEWS[k]; const r = cv.getBoundingClientRect();
  view.cx = (x0+x1)/2; view.cy = (y0+y1)/2; view.s = Math.min(r.width/(x1-x0), r.height/(y1-y0))*0.94; draw(); }}
function sx(x){{ return (x-view.cx)*view.s + cv.clientWidth/2; }}
function sy(y){{ return -(y-view.cy)*view.s + cv.clientHeight/2; }}
function vis(c){{ return chain==='both' || +chain===c; }}
function zcol(z){{ // diverging: blue positive, orange negative, alpha by |z|
  const a = Math.min(1, 0.18 + Math.abs(z)/12); const faded = Math.abs(z) < 3;
  const c = z>=0 ? css('--pos') : css('--neg'); return [c, faded ? 0.16 : a]; }}
function path(xy){{ ctx.beginPath(); ctx.moveTo(sx(xy[0][0]),sy(xy[0][1])); ctx.lineTo(sx(xy[1][0]),sy(xy[1][1])); ctx.lineTo(sx(xy[2][0]),sy(xy[2][1])); ctx.closePath(); }}
function draw(){{
  const dpr = window.devicePixelRatio||1, w = cv.clientWidth, h = cv.clientHeight;
  if (cv.width !== Math.round(w*dpr) || cv.height !== Math.round(h*dpr)) {{ cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr); }}
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,w,h);
  ctx.fillStyle = css('--map'); ctx.fillRect(0,0,w,h);
  ctx.fillStyle = css('--land'); ctx.strokeStyle = css('--coast'); ctx.lineWidth = 1;
  for (const p of D.o) {{ ctx.beginPath(); p.forEach((q,i)=> i?ctx.lineTo(sx(q[0]),sy(q[1])):ctx.moveTo(sx(q[0]),sy(q[1]))); ctx.closePath(); ctx.fill(); ctx.stroke(); }}
  const lw = Math.max(0.4, Math.min(1.2, view.s*2));
  let shown = 0, curved = 0, flat = 0;
  for (const t of D.t) {{
    if (!vis(t[0])) continue; shown++;
    path(t[3]);
    if (mode==='gauss') {{
      if (t[6]===null) {{ ctx.globalAlpha = 0.15; ctx.fillStyle = css('--unres'); ctx.fill(); ctx.globalAlpha = 1; ctx.strokeStyle = css('--unres'); ctx.lineWidth = lw*1.6; ctx.stroke(); }}
      else {{ const [c,a] = zcol(t[6]); if (t[6]>3) curved++; ctx.globalAlpha = a; ctx.fillStyle = c; ctx.fill(); ctx.globalAlpha = 0.55; ctx.strokeStyle = css('--ink'); ctx.lineWidth = lw*0.6; ctx.stroke(); ctx.globalAlpha = 1; }}
    }} else if (mode==='tarski') {{
      if (t[15]) flat++;
      ctx.globalAlpha = 0.22; ctx.fillStyle = css('--tri-flat'); ctx.fill(); ctx.globalAlpha = 0.8; ctx.strokeStyle = css('--tri-edge'); ctx.lineWidth = lw*0.6; ctx.stroke(); ctx.globalAlpha = 1;
      t[11].forEach((m,i)=>{{ if (!m) return; const a = t[3][(i+1)%3], b = t[3][(i+2)%3];
        ctx.beginPath(); ctx.moveTo(sx(a[0]),sy(a[1])); ctx.lineTo(sx(b[0]),sy(b[1])); ctx.strokeStyle = css('--ink'); ctx.lineWidth = 4; ctx.stroke(); }});
    }} else {{
      ctx.globalAlpha = 0.08; ctx.fillStyle = css('--tri-flat'); ctx.fill(); ctx.globalAlpha = 0.35; ctx.strokeStyle = css('--tri-edge'); ctx.lineWidth = lw*0.5; ctx.stroke(); ctx.globalAlpha = 1;
    }}
  }}
  if (mode==='fans') {{
    for (const f of D.f) {{ if (!vis(f[0])) continue;
      const r = 2.5 + Math.sqrt(f[4])*1.3;
      if (selFan===f) for (const name of f[8]) {{ const t = D.t.find(q=>q[1]===name && q[0]===f[0]); if (t) {{ path(t[3]); ctx.globalAlpha=0.35; ctx.fillStyle=css('--accent'); ctx.fill(); ctx.globalAlpha=1; ctx.strokeStyle=css('--accent'); ctx.lineWidth=1.5; ctx.stroke(); }} }}
      ctx.beginPath(); ctx.arc(sx(f[2][0]),sy(f[2][1]),r,0,2*Math.PI); ctx.fillStyle = css('--accent'); ctx.globalAlpha = 0.8; ctx.fill(); ctx.globalAlpha = 1; ctx.strokeStyle = css('--ink'); ctx.lineWidth = selFan===f?2.5:1; ctx.stroke();
    }}
  }}
  if (sel && vis(sel[0]) && mode!=='fans') {{ path(sel[3]); ctx.strokeStyle = css('--accent'); ctx.lineWidth = 3; ctx.stroke(); }}
  const nf = D.f.filter(f=>vis(f[0])).length;
  st.textContent = mode==='gauss' ? `Gauss · angles: ${{curved}} of ${{shown}} triangles curved beyond 3σ, all via angular excess, all exit TE`
    : mode==='tarski' ? `Tarski · lengths: ${{flat}} of ${{shown}} triangles close as flat triangles`
    : `Closed fans · lengths: ${{nf}} fans; deficit = ⅓ of the printed excess`;
}}
function legend(){{
  const L = document.getElementById('legend');
  L.innerHTML = mode==='gauss'
    ? `<span><i style="background:${{css('--pos')}}"></i>excess &gt;3σ (curved by angles)</span><span><i style="background:${{css('--pos')}};opacity:.25"></i>under 3σ</span><span><i style="background:${{css('--neg')}}"></i>negative excess</span><span><i style="background:transparent;border:2px solid ${{css('--unres')}}"></i>angle never observed</span>`
    : mode==='tarski'
    ? `<span><i style="background:${{css('--tri-flat')}};opacity:.5"></i>closes flat from its three sides</span><span><i style="background:${{css('--ink')}};height:4px;border:0"></i>measured base line</span><span>every other side: computed from angles</span>`
    : `<span><i style="background:${{css('--accent')}};border-radius:50%"></i>closed fan; size = deficit from sides</span><span>tap a dot to see its ring</span>`;
}}
const fmtA = a => {{ if (a===null) return '….'; const d = Math.floor(a), m = Math.floor((a-d)*60), s = ((a-d)*60-m)*60; return `${{d}}° ${{String(m).padStart(2,'0')}}′ ${{s.toFixed(2).padStart(5,'0')}}″`; }};
const row = (k,v,c='') => `<div class="row ${{c}}"><span>${{k}}</span><span>${{v}}</span></div>`;
function audit(t){{
  const A = document.getElementById('audit');
  const g = `<div class="g"><h4>Gauss · angles</h4><b>${{t[1]}}</b> <span class="mut">(${{CH[t[0]]}}, p. ${{t[2]}})</span>`
    + t[13].map((s,i)=>row(s, fmtA(t[10][i]))).join('')
    + row('observed excess ε', t[4]===null ? 'not tested' : t[4].toFixed(2)+'″')
    + row('z = ε / σ', t[6]===null ? '—' : t[6].toFixed(1)+'σ')
    + row('printed (ellipsoid) excess', t[5].toFixed(2)+'″')
    + row('route to curvature', 'exits TE: angles → plumb → Art. 20', 'exit') + '</div>';
  const sides = t[8].map((L,i)=> row(`${{t[13][(i+1)%3]}} – ${{t[13][(i+2)%3]}}`, L.toFixed(2)+' m' + (t[11][i]?' · measured base':' · computed'))).join('');
  const fs = t[9].reduce((a,b)=>a+b,0);
  const tt = `<div class="t"><h4>Tarski · lengths</h4>` + sides
    + row('triangle inequality', t[15] ? 'holds (margin '+(t[14]>=1000 ? (t[14]/1000).toFixed(2)+' km' : t[14].toFixed(3)+' m')+')' : 'fails')
    + t[13].map((s,i)=>row('plane angle at '+s, fmtA(t[9][i]))).join('')
    + row('sum of plane angles', fmtA(fs))
    + row('Legendre residual (rms)', t[12].toFixed(2)+'″') + '</div>';
  A.innerHTML = g + tt;
}}
function auditFan(f){{
  const A = document.getElementById('audit');
  A.innerHTML = `<div class="g"><h4>Gauss · angles</h4><b>${{f[1]}}</b> <span class="mut">(${{CH[f[0]]}}, ${{f[3]}} triangles)</span>`
    + row('ring', f[7]) + row('⅓ Σ observed excess', f[6]===null?'— (an angle unobserved)':f[6].toFixed(2)+'″')
    + row('⅓ Σ printed (ellipsoid) excess', f[5].toFixed(2)+'″') + '</div>'
    + `<div class="t"><h4>Tarski · lengths</h4>` + row('Σ plane angles at centre, from sides', '360° − '+f[4].toFixed(2)+'″')
    + row('flat (= 360°)?', f[4]>0.05?'no: refuted by lengths':'yes')
    + row('deficit − ⅓ Σ printed ε', (f[4]-f[5]>=0?'+':'')+(f[4]-f[5]).toFixed(2)+'″')
    + row('where the deficit came from', 'ε/3 taken off each angle to compute the sides', 'exit') + '</div>';
}}
function pickTri(px,py){{
  const x = (px - cv.clientWidth/2)/view.s + view.cx, y = -(py - cv.clientHeight/2)/view.s + view.cy;
  let best = null, ba = Infinity;
  for (const t of D.t) {{ if (!vis(t[0])) continue; const [a,b,c] = t[3];
    const d = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1]);
    const l1 = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1]))/d, l2 = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1]))/d, l3 = 1-l1-l2;
    if (l1>=0 && l2>=0 && l3>=0) {{ const ar = Math.abs(d); if (ar < ba) {{ ba = ar; best = t; }} }} }}
  return best;
}}
function pickFan(px,py){{
  let best = null, bd = 400;
  for (const f of D.f) {{ if (!vis(f[0])) continue; const dx = sx(f[2][0])-px, dy = sy(f[2][1])-py, d = dx*dx+dy*dy; const r = 6 + Math.sqrt(f[4])*1.3; if (d < Math.max(bd, r*r) && d < r*r + 60) {{ bd = d; best = f; }} }}
  return best;
}}
// interaction: pan, zoom, tap
let drag = null, moved = false; const ptrs = new Map(); let pinch0 = null;
cv.addEventListener('pointerdown', e => {{ cv.setPointerCapture(e.pointerId); ptrs.set(e.pointerId,[e.offsetX,e.offsetY]); drag = [e.offsetX,e.offsetY,view.cx,view.cy]; moved = false;
  if (ptrs.size===2) {{ const [p,q] = [...ptrs.values()]; pinch0 = [Math.hypot(p[0]-q[0],p[1]-q[1]), view.s]; }} }});
cv.addEventListener('pointermove', e => {{ if (!ptrs.has(e.pointerId)) return; ptrs.set(e.pointerId,[e.offsetX,e.offsetY]);
  if (ptrs.size===2 && pinch0) {{ const [p,q] = [...ptrs.values()]; view.s = pinch0[1]*Math.hypot(p[0]-q[0],p[1]-q[1])/pinch0[0]; moved = true; draw(); return; }}
  if (!drag) return; const dx = e.offsetX-drag[0], dy = e.offsetY-drag[1]; if (Math.abs(dx)+Math.abs(dy) > 4) moved = true;
  view.cx = drag[2] - dx/view.s; view.cy = drag[3] + dy/view.s; draw(); }});
const up = e => {{ ptrs.delete(e.pointerId); if (ptrs.size<2) pinch0 = null;
  if (drag && !moved && e.type==='pointerup') {{
    if (mode==='fans') {{ const f = pickFan(e.offsetX,e.offsetY); if (f) {{ selFan = f; auditFan(f); draw(); }} }}
    else {{ const t = pickTri(e.offsetX,e.offsetY); if (t) {{ sel = t; audit(t); draw(); }} }}
  }} if (!ptrs.size) drag = null; }};
cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
cv.addEventListener('wheel', e => {{ e.preventDefault(); const k = Math.exp(-e.deltaY*0.0015);
  const x = (e.offsetX - cv.clientWidth/2)/view.s + view.cx, y = -(e.offsetY - cv.clientHeight/2)/view.s + view.cy;
  view.s *= k; view.cx = x - (e.offsetX - cv.clientWidth/2)/view.s; view.cy = y + (e.offsetY - cv.clientHeight/2)/view.s; draw(); }}, {{passive:false}});
function group(cls, fn){{ document.querySelectorAll(cls).forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll(cls).forEach(x => x.setAttribute('aria-pressed', x===b ? 'true':'false')); fn(b); }})); }}
group('.mbtn', b => {{ mode = b.dataset.m; legend(); draw(); }});
group('.sbtn', b => {{ chain = b.dataset.s; draw(); }});
group('.vbtn', b => fit(b.dataset.v));
new ResizeObserver(() => draw()).observe(cv);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {{ legend(); draw(); }});
legend(); fit('all');
// open with the most curved triangle selected
sel = D.t.reduce((a,t)=> (t[6]!==null && (a===null || t[6]>a[6])) ? t : a, null); audit(sel); draw();
</script>
<script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}</script>
<script type="module">
import * as THREE from 'three';
import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
const box=document.getElementById('viewer3'),st3=document.getElementById('v3status'),info=document.getElementById('info3');
const T=window.__GT.t, O=window.__GT.o;
const r=new THREE.WebGLRenderer({{antialias:true}});r.setPixelRatio(Math.min(devicePixelRatio,2));r.outputColorSpace=THREE.SRGBColorSpace;box.appendChild(r.domElement);
const s=new THREE.Scene();s.background=new THREE.Color(0x3a4150);
const cam=new THREE.PerspectiveCamera(30,1,5,200000);cam.up.set(0,0,1);
const ctl=new OrbitControls(cam,r.domElement);ctl.enableDamping=true;ctl.maxDistance=40000;
s.add(new THREE.HemisphereLight(0xffffff,0x334455,1.25));const dl=new THREE.DirectionalLight(0xffffff,1.6);dl.position.set(-3000,-4000,6000);s.add(dl);
const ZC=[[-1e9,-3,'#6b3d8f','below −3σ'],[-3,-1,'#a58cc0','−3 to −1σ'],[-1,1,'#e9e4d6','within ±1σ of flat'],[1,3,'#b7d7d0','1 to 3σ'],[3,10,'#5fb0b4','3 to 10σ'],[10,30,'#2b7bb0','10 to 30σ'],[30,1e9,'#173d7a','above 30σ']];
const UNRES='#c8342a',FLAT='#9fb59a',GROUND=new THREE.Color(0x4b5466);
const N=10, ARC=4.84813681e-6;
let mode={{t:'tiles',s:'both'}}, reading='gauss', k=1, kTarget=1, exag=1, maxH=0, mesh=null, umesh=null, lines=null, faceTri=[], ufaceTri=[];
function zcol(z){{for(const b of ZC)if(z>=b[0]&&z<b[1])return b[2];return '#ffffff';}}
function legend(){{document.getElementById('legend3').innerHTML = reading==='gauss'
  ? ZC.map(b=>`<span><i style="background:${{b[2]}}"></i>${{b[3]}}</span>`).join('')+`<span><i style="background:${{UNRES}}"></i>angle never observed</span>`
  : `<span><i style="background:${{FLAT}}"></i>closes flat from its three printed sides</span><span><i style="background:${{UNRES}}"></i>angle never observed (still flat by sides)</span>`;}}
function build(){{
  for(const o of [mesh,umesh,lines])if(o){{s.remove(o);o.geometry.dispose();}}
  const pos=[],col=[],up=[];faceTri=[];ufaceTri=[];const c=new THREE.Color();maxH=0;
  T.forEach((t,ti)=>{{
    if(mode.s!=='both'&&String(t[0])!==mode.s)return;
    if(mode.t==='tiles'&&!t[16])return;
    const [a,b,d]=t[3];
    if(t[6]===null){{up.push(a[0],a[1],0,b[0],b[1],0,d[0],d[1],0);ufaceTri.push(ti);return;}}
    if(reading==='gauss'){{c.set(zcol(t[6]));c.lerp(GROUND,(1-Math.min(Math.abs(t[6]),3)/3)*.6);}} else c.set(FLAT);
    const D2=2*(a[0]*(b[1]-d[1])+b[0]*(d[1]-a[1])+d[0]*(a[1]-b[1]));
    const ux=((a[0]**2+a[1]**2)*(b[1]-d[1])+(b[0]**2+b[1]**2)*(d[1]-a[1])+(d[0]**2+d[1]**2)*(a[1]-b[1]))/D2;
    const uy=((a[0]**2+a[1]**2)*(d[0]-b[0])+(b[0]**2+b[1]**2)*(a[0]-d[0])+(d[0]**2+d[1]**2)*(b[0]-a[0]))/D2;
    const rc2=(a[0]-ux)**2+(a[1]-uy)**2, ek=t[4]*ARC/t[7], invR=Math.sign(ek)*Math.sqrt(Math.abs(ek));
    const P=(i,j)=>{{const kk=N-i-j,b1=i/N,b2=j/N,b3=kk/N;const x=b1*a[0]+b2*b[0]+b3*d[0],y=b1*a[1]+b2*b[1]+b3*d[1];
      const h=(rc2-(x-ux)**2-(y-uy)**2)/2*invR;if(Math.abs(h)>maxH)maxH=Math.abs(h);return [x,y,h];}};
    for(let i=0;i<N;i++)for(let j=0;j<N-i;j++){{
      const tri=[[P(i,j),P(i+1,j),P(i,j+1)]];if(i+j<N-1)tri.push([P(i+1,j),P(i+1,j+1),P(i,j+1)]);
      for(const f of tri){{for(const v of f){{pos.push(...v);col.push(c.r,c.g,c.b);}}faceTri.push(ti);}}
    }}
  }});
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.computeVertexNormals();
  mesh=new THREE.Mesh(g,new THREE.MeshStandardMaterial({{vertexColors:true,roughness:.8,metalness:0,side:THREE.DoubleSide}}));s.add(mesh);
  const ug=new THREE.BufferGeometry();ug.setAttribute('position',new THREE.Float32BufferAttribute(up,3));
  umesh=new THREE.Mesh(ug,new THREE.MeshBasicMaterial({{color:UNRES,side:THREE.DoubleSide,transparent:true,opacity:.85,polygonOffset:true,polygonOffsetFactor:-2}}));umesh.position.z=2;s.add(umesh);
  const lp=[];T.forEach(t=>{{if(mode.s!=='both'&&String(t[0])!==mode.s)return;if(mode.t==='tiles'&&!t[16]&&t[6]!==null)return;const[a,b,d]=t[3];lp.push(a[0],a[1],.5,b[0],b[1],.5,b[0],b[1],.5,d[0],d[1],.5,d[0],d[1],.5,a[0],a[1],.5);}});
  const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));
  lines=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({{color:0x1a1813,transparent:true,opacity:.35}}));s.add(lines);
  legend();setEx();
}}
const ex=document.getElementById('exag'),exo=document.getElementById('exout');
function setEx(){{exag=Math.round(Math.pow(10,(+ex.value)/100*4));if(mesh)mesh.scale.z=exag*k;
  exo.textContent = reading==='gauss'
    ? `× ${{exag.toLocaleString()}} vertical · highest curve ${{Math.round(maxH*1000).toLocaleString()}} m above its own flat triangle → drawn ${{(maxH*exag).toLocaleString(undefined,{{maximumFractionDigits:0}})}} km`
    : `Tarski reading: every triangle flat (height 0 at any exaggeration)`;}}
ex.addEventListener('input',setEx);
let views={{}},cur='oblique';
function setView(n){{const[az,el,d0,tg]=views[n];ctl.target.set(...tg);const d=d0*Math.max(1,1.5/cam.aspect),a=az*Math.PI/180,e=el*Math.PI/180;
  cam.position.set(tg[0]+d*Math.cos(e)*Math.sin(a),tg[1]-d*Math.cos(e)*Math.cos(a),tg[2]+d*Math.sin(e));ctl.update();
  document.querySelectorAll('button.v3btn').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===n)));}}
function size(){{const w=box.clientWidth,h=box.clientHeight;r.setSize(w,h);cam.aspect=w/h;cam.updateProjectionMatrix();if(views[cur])setView(cur);}}
new ResizeObserver(size).observe(box);
const bind=(cls,fn)=>document.querySelectorAll('button.'+cls).forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('button.'+cls).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));fn(b);}}));
bind('tbtn',b=>{{mode.t=b.dataset.t;build();}});
bind('s3btn',b=>{{mode.s=b.dataset.s;build();}});
bind('v3btn',b=>{{cur=b.dataset.v;setView(cur);}});
bind('rbtn',b=>{{reading=b.dataset.r;kTarget=reading==='gauss'?1:0;build();}});
const ray=new THREE.Raycaster(),mp=new THREE.Vector2();
function pick(ev){{const rc=r.domElement.getBoundingClientRect();mp.set((ev.clientX-rc.left)/rc.width*2-1,-(ev.clientY-rc.top)/rc.height*2+1);ray.setFromCamera(mp,cam);
  const hits=ray.intersectObjects([umesh,mesh]);if(!hits.length)return;const h=hits[0];
  const t=T[h.object===umesh?ufaceTri[h.faceIndex]:faceTri[h.faceIndex]];const ch=t[0]?'Eastern Oblique':'39th parallel';
  if(t[6]===null){{info.innerHTML=`<b>${{t[1]}}</b> · ${{ch}}<br><span style="color:var(--unres)">One angle never observed: no excess, no curve.</span> By its printed sides it is a flat triangle.`;return;}}
  const R=t[4]>0?Math.sqrt(t[7]/(t[4]*ARC)):null;
  const D2=t[3];
  info.innerHTML = reading==='gauss'
    ? `<b>${{t[1]}}</b> · ${{ch}} · area ${{Math.round(t[7]).toLocaleString()}} km²<br>Observed excess ${{t[4].toFixed(2)}}″ = ${{t[6].toFixed(1)}}σ above flat${{R?` · own radius ${{Math.round(R).toLocaleString()}} km`:''}} · <span style="color:var(--unres)">exits TE: curvature from angles (Art. 20), not from lengths</span>`
    : `<b>${{t[1]}}</b> · ${{ch}}<br>Printed sides ${{t[8].map(x=>(x/1000).toFixed(3)).join(', ')}} km → a plane triangle, angles sum to 180° exactly · <span style="color:var(--accent)">no curvature in three lengths</span>`;}}
r.domElement.addEventListener('pointermove',pick);r.domElement.addEventListener('pointerdown',pick);
const op=[];for(const run of O)for(let i=1;i<run.length;i++)op.push(run[i-1][0],run[i-1][1],0,run[i][0],run[i][1],0);
const og=new THREE.BufferGeometry();og.setAttribute('position',new THREE.Float32BufferAttribute(op,3));
s.add(new THREE.LineSegments(og,new THREE.LineBasicMaterial({{color:0xd9d2c0,transparent:true,opacity:.55}})));
let xs=[],ys=[];T.forEach(t=>t[3].forEach(p=>{{xs.push(p[0]);ys.push(p[1]);}}));
const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),cx=(x0+x1)/2,cy=(y0+y1)/2;
const ground=new THREE.Mesh(new THREE.PlaneGeometry(30000,20000),new THREE.MeshStandardMaterial({{color:0x4b5466,roughness:1}}));ground.position.set(cx,cy+150,-1);s.add(ground);
const neb=T.find(t=>t[1]==='Mount Nebo - Tushar - Wheeler Peak')||T[0];const nx=(neb[3][0][0]+neb[3][1][0]+neb[3][2][0])/3,ny=(neb[3][0][1]+neb[3][1][1]+neb[3][2][1])/3;
views={{oblique:[0,38,4700,[cx,cy-150,0]],west:[-25,30,2300,[-2350,-60,0]],nebo:[-20,28,900,[nx,ny,0]],east:[20,32,2600,[1250,-180,0]],top:[0,89.5,5200,[cx,cy,0]]}};
build();size();setView(cur);st3.remove();window.__ready3=true;
(function loop(){{if(Math.abs(k-kTarget)>1e-3){{k+= (kTarget-k)*0.12;if(Math.abs(k-kTarget)<1e-3)k=kTarget;if(mesh)mesh.scale.z=exag*k;}}ctl.update();r.render(s,cam);requestAnimationFrame(loop);}})();
</script>
</body>
</html>
'''
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('wrote index.html', len(page), 'bytes;', len(above3), 'curved;', len(F), 'fans; measured', len(measured_tri))
