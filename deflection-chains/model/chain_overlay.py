"""Overlay the two US triangulation chains from the report on the curvature dome.

For each chain:
  * every survey triangle as an outline (rods along the printed station-to-station lines),
  * the non-overlapping triangles used in the report's whole-chain sums as coloured tiles,
    coloured like the report's chain figure: z = (observed - expected excess) / noise,
    expected = area x K_ellipsoid, noise = the survey's sigma, RdBu_r scale from -3 to +3.
Vertices are placed exactly like the coastline: azimuthal equidistant from 45N 100W on the sphere
of radius R = 1/sqrt(K) (K from mesh_params.json), then lifted by the same 'lift' as the land.

usage: chain_overlay.py <repo> <mesh_params.json> <outdir>
writes: per-body STLs for SolidCraft, chain_overlay.glb (vertex colours) for rendering, labels.json
"""
import sys, os, json, csv, math, struct, xml.etree.ElementTree as ET
import numpy as np, trimesh, matplotlib
from pyproj import Transformer

REPO, PRM, OUT = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
os.makedirs(OUT, exist_ok=True)
R, LIFT = PRM["R_mm"], PRM["lift_mm"]
aeqd = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0=45 +lon_0=-100 +R={R*1000} +units=km", always_xy=True)
RAD = math.pi / 180 / 3600
TILE_BOT, TILE_TOP, ROD_UP, ROD_R = -0.5, 3.0, 3.6, 2.2   # mm, along the sphere normal

def sphere_pts(lon, lat, up=0.0):
    x, y = aeqd.transform(np.asarray(lon, float), np.asarray(lat, float))
    x, y = np.atleast_1d(x), np.atleast_1d(y)
    rho = np.hypot(x, y); c = rho / R
    k = np.where(rho > 0, R * np.sin(c) / np.where(rho > 0, rho, 1), 1.0)
    P = np.c_[x * k, y * k, R * np.cos(c) - R + LIFT]
    n = np.c_[x * k, y * k, R * np.cos(c)]; n /= np.linalg.norm(n, axis=1)[:, None]
    return P + n * up

# --- KML polygons for the two chains
ns = {"k": "http://www.opengis.net/kml/2.2"}
doc = ET.parse(os.path.join(REPO, "data/arcs_parallel_master.kml")).getroot()[0]
CH = {"US 39th parallel": "US arc of the 39th parallel",
      "US Eastern Oblique": "Eastern Oblique Arc"}
polys = {k: {} for k in CH}
for f in doc.findall("k:Folder", ns):
    fname = f.find("k:name", ns).text
    key = next((k for k, v in CH.items() if v in fname), None)
    if not key: continue
    for pm in f.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        poly = pm.find(".//k:Polygon", ns) or pm.find(".//k:LineString", ns) or pm.find(".//k:LinearRing", ns)
        if poly is None: continue
        cs = pm.find(".//k:coordinates", ns).text.split()
        pts = [tuple(map(float, c.split(",")))[:2] for c in cs]
        polys[key][pm.find("k:name", ns).text] = pts[:3]

rows = {r["triangle"]: r for r in csv.DictReader(open(os.path.join(REPO, "data/triangles_rule.csv")))
        if r["survey"] in CH}
chain = json.load(open(os.path.join(REPO, "data/chain_results.json")))
cmap = matplotlib.colormaps["RdBu_r"]
def zcol(z): return np.array(cmap((np.clip(z, -3, 3) + 3) / 6)[:3])
BINS = [(-9, -2.5, -3), (-2.5, -1.5, -2), (-1.5, -0.5, -1), (-0.5, 0.5, 0), (0.5, 1.5, 1), (1.5, 2.5, 2), (2.5, 9, 3)]

scene = trimesh.Scene(); bodies = {}; labels = {}; stats = {}
for key in CH:
    P = polys[key]; chosen = set(chain[key]["names"])
    # outlines: unique station-to-station edges
    edges = {}
    for name, tri in P.items():
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            kk = tuple(sorted([(round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6))]))
            edges[kk] = 1
    rods = []
    for (a, b) in edges:
        n_seg = 4
        lo = np.linspace(a[0], b[0], n_seg + 1); la = np.linspace(a[1], b[1], n_seg + 1)
        Q = sphere_pts(lo, la, ROD_UP)
        for j in range(n_seg):
            rods.append(trimesh.creation.cylinder(radius=ROD_R, segment=[Q[j], Q[j + 1]], sections=6))
    rodm = trimesh.util.concatenate(rods)
    ink = np.array([0.11, 0.11, 0.10])
    bodies[f"{key} triangles (outline)"] = (rodm, ink)
    # coloured tiles of the non-overlapping chain triangles, binned by z
    tiles = {b[2]: [] for b in BINS}; zs = []
    for name in chosen:
        if name not in P or name not in rows: continue
        r = rows[name]
        A = float(r["area_sides_km2"]) * 1e6; E = float(r["observed_excess_arcsec"])
        Ee = A * float(r["K_ellipsoid_per_m2"]) / RAD; z = (E - Ee) / float(r["survey_sigma_arcsec"])
        zs.append(z)
        lo = [p[0] for p in P[name]]; la = [p[1] for p in P[name]]
        T = sphere_pts(lo, la, TILE_TOP); B = sphere_pts(lo, la, TILE_BOT)
        V = np.vstack([T, B])
        F = [[0, 1, 2], [3, 5, 4], [0, 3, 4], [0, 4, 1], [1, 4, 5], [1, 5, 2], [2, 5, 3], [2, 3, 0]]
        m = trimesh.Trimesh(V, F, process=False)
        if m.volume < 0: m.invert()
        bin_c = next(b[2] for b in BINS if b[0] <= z < b[1])
        tiles[bin_c].append(m)
    for c, ms in tiles.items():
        if ms:
            bodies[f"{key} chain tiles z={c:+d}"] = (trimesh.util.concatenate(ms), zcol(c))
    # label anchor: centroid of stations, lifted
    allp = np.array([p for t in P.values() for p in t])
    labels[key] = sphere_pts([allp[:, 0].mean()], [allp[:, 1].mean()], 40)[0].tolist()
    labels[key + " west"] = sphere_pts([allp[:, 0].min()], [allp[allp[:, 0].argmin(), 1]], 40)[0].tolist()
    labels[key + " south"] = sphere_pts([allp[allp[:, 1].argmin(), 0]], [allp[:, 1].min()], 40)[0].tolist()
    stats[key] = dict(triangles=len(P), edges=len(edges), chosen=len(zs),
                      z_mean=float(np.mean(zs)), z_sd=float(np.std(zs)),
                      q=chain[key]["q"], sq=chain[key]["sq"], R_km=chain[key]["R"], n=chain[key]["n"], A=chain[key]["A"])

# per-body STLs (for SolidCraft) and a colour GLB (for renders)
for name, (m, col) in bodies.items():
    fn = os.path.join(OUT, name.replace(" ", "_").replace("=", "").replace("+", "p").replace("-", "m") + ".stl")
    m.export(fn)
    mm = m.copy(); lin = col ** 2.2
    mm.visual.vertex_colors = (np.c_[np.tile(lin, (len(mm.vertices), 1)), np.ones(len(mm.vertices))] * 255).astype(np.uint8)
    scene.add_geometry(mm, node_name=name)
scene.export(os.path.join(OUT, "chain_overlay.glb"))
json.dump(dict(labels=labels, stats=stats, bodies={n: [os.path.basename(n.replace(" ", "_").replace("=", "").replace("+", "p").replace("-", "m") + ".stl"), "#%02x%02x%02x" % tuple(int(v * 255) for v in c)] for n, (m, c) in bodies.items()}),
          open(os.path.join(OUT, "overlay.json"), "w"), indent=1)
print(json.dumps(stats, indent=1))
