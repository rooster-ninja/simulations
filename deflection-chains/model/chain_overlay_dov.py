"""US triangulation chains on the curvature dome, coloured by the deflection-of-the-vertical change.

Same geometry as chain_overlay.py (the report's model): every survey triangle outlined
station to station, and the non-overlapping triangles of the report's whole-chain sums as
tiles. The tiles are coloured by how much the deflection correction changes that
triangle's angle excess compared with the raw printed angles:

    d = (excess with DEFLEC18 deflections applied) - (raw observed excess), arcseconds

from ../data/dov_triangles.csv (made by ../scripts/dov_correct.py). Seven bins, PuOr:
purple = excess reduced, orange = excess increased, grey = within +-0.03".

usage: python3 chain_overlay_dov.py           (run from this folder)
writes: dov_bodies/*.stl (one body per colour step, for SolidCraft),
        viewer_scene_dov.glb (land and ocean from viewer_scene.glb + the recoloured chains),
        overlay_dov.json (bins, colours, counts, label anchors)
"""
import os, json, csv, math, xml.etree.ElementTree as ET
import numpy as np, trimesh, matplotlib
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "data")
PRM = json.load(open(os.path.join(HERE, "mesh_params.json")))
OUT = os.path.join(HERE, "dov_bodies"); os.makedirs(OUT, exist_ok=True)
R, LIFT = PRM["R_mm"], PRM["lift_mm"]
aeqd = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0=45 +lon_0=-100 +R={R*1000} +units=km", always_xy=True)
TILE_BOT, TILE_TOP, ROD_UP, ROD_R = -0.5, 3.0, 3.6, 2.2   # mm along the sphere normal, as in chain_overlay.py

def sphere_pts(lon, lat, up=0.0):
    x, y = aeqd.transform(np.asarray(lon, float), np.asarray(lat, float))
    x, y = np.atleast_1d(x), np.atleast_1d(y)
    rho = np.hypot(x, y); c = rho / R
    k = np.where(rho > 0, R * np.sin(c) / np.where(rho > 0, rho, 1), 1.0)
    P = np.c_[x * k, y * k, R * np.cos(c) - R + LIFT]
    n = np.c_[x * k, y * k, R * np.cos(c)]; n /= np.linalg.norm(n, axis=1)[:, None]
    return P + n * up

BINS = [(-9, -0.3, -3), (-0.3, -0.1, -2), (-0.1, -0.03, -1), (-0.03, 0.03, 0), (0.03, 0.1, 1), (0.1, 0.3, 2), (0.3, 9, 3)]
LABEL = {-3: "< −0.3″", -2: "−0.3 to −0.1″", -1: "−0.1 to −0.03″", 0: "±0.03″", 1: "0.03 to 0.1″", 2: "0.1 to 0.3″", 3: "> 0.3″"}
cmap = matplotlib.colormaps["PuOr_r"]
def bcol(b):
    if b == 0: return np.array([0.86, 0.84, 0.80])
    return np.array(cmap(0.5 + b / 6.6)[:3])

# KML triangles
ns = {"k": "http://www.opengis.net/kml/2.2"}
doc = ET.parse(os.path.join(D, "arcs_parallel_master.kml")).getroot()[0]
CH = {"US 39th parallel": "US arc of the 39th parallel", "US Eastern Oblique": "Eastern Oblique Arc"}
polys = {k: {} for k in CH}
for f in doc.findall("k:Folder", ns):
    key = next((k for k, v in CH.items() if v in f.find("k:name", ns).text), None)
    if not key: continue
    for pm in f.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        if pm.find(".//k:Point", ns) is not None: continue
        cs = pm.find(".//k:coordinates", ns)
        if cs is None: continue
        polys[key][pm.find("k:name", ns).text] = [tuple(map(float, c.split(",")))[:2] for c in cs.text.split()][:3]

dmap = {(r["survey"], r["triangle"]): float(r["d_main"]) for r in csv.DictReader(open(os.path.join(D, "dov_triangles.csv")))}
chain = json.load(open(os.path.join(D, "chain_results.json")))

bodies = {}; counts = {}; labels = {}
for key in CH:
    P = polys[key]
    edges = set()
    for tri in P.values():
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            edges.add(tuple(sorted([(round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6))])))
    rods = []
    for a, b in edges:
        lo = np.linspace(a[0], b[0], 5); la = np.linspace(a[1], b[1], 5); Q = sphere_pts(lo, la, ROD_UP)
        for j in range(4): rods.append(trimesh.creation.cylinder(radius=ROD_R, segment=[Q[j], Q[j + 1]], sections=6))
    bodies[f"{key} triangles (outline)"] = (trimesh.util.concatenate(rods), np.array([0.11, 0.11, 0.10]))
    tiles = {b[2]: [] for b in BINS}
    for name in chain[key]["names"]:
        if name not in P or (key, name) not in dmap: continue
        d = dmap[(key, name)]; b = next(x[2] for x in BINS if x[0] <= d < x[1])
        lo = [p[0] for p in P[name]]; la = [p[1] for p in P[name]]
        V = np.vstack([sphere_pts(lo, la, TILE_TOP), sphere_pts(lo, la, TILE_BOT)])
        F = [[0, 1, 2], [3, 5, 4], [0, 3, 4], [0, 4, 1], [1, 4, 5], [1, 5, 2], [2, 5, 3], [2, 3, 0]]
        m = trimesh.Trimesh(V, F, process=False)
        if m.volume < 0: m.invert()
        tiles[b].append(m)
    counts[key] = {LABEL[b]: len(ms) for b, ms in tiles.items()}
    for b, ms in tiles.items():
        if ms: bodies[f"{key} DOV tiles {b:+d}"] = (trimesh.util.concatenate(ms), bcol(b))
    allp = np.array([p for t in P.values() for p in t])
    labels[key] = sphere_pts([allp[:, 0].mean()], [allp[:, 1].mean()], 40)[0].tolist()

def fname(n): return n.replace(" ", "_").replace("(", "").replace(")", "").replace("+", "p").replace("-", "m") + ".stl"
base = trimesh.load(os.path.join(HERE, "viewer_scene.glb"))
scene = trimesh.Scene()
for node in base.graph.nodes_geometry:
    if node.startswith("land"):
        T, g = base.graph[node]; scene.add_geometry(base.geometry[g], node_name=node, transform=T)
for name, (m, col) in bodies.items():
    m.export(os.path.join(OUT, fname(name)))
    mm = m.copy(); lin = col ** 2.2
    mm.visual.vertex_colors = (np.c_[np.tile(lin, (len(mm.vertices), 1)), np.ones(len(mm.vertices))] * 255).astype(np.uint8)
    scene.add_geometry(mm, node_name=name)
scene.export(os.path.join(HERE, "viewer_scene_dov.glb"))
json.dump(dict(bins={LABEL[b[2]]: "#%02x%02x%02x" % tuple(int(v * 255) for v in bcol(b[2])) for b in BINS},
               counts=counts, labels=labels, bodies={n: fname(n) for n in bodies}),
          open(os.path.join(HERE, "overlay_dov.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(counts, indent=1, ensure_ascii=False))
