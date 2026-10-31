#!/usr/bin/env python3
"""
North America on a true-scale Earth sphere, faceted triangle top, flat base.

Scale: 1 mm = 1 km. Sphere radius R from the measured curvature K (default K = 2.450e-14 m^-2,
the value measured from surveyors' triangles in the report), R = 1/sqrt(K). Projection centre 45N 100W.
Coastline: Natural Earth 1:50m, lightly averaged (small inlets/peninsulas rounded).
Each landmass -> one closed (watertight) mesh body:
  top    = triangles whose vertices lie exactly on the sphere,
  walls  = vertical, following the coastline,
  base   = flat at z = 0.

Usage: python3 na_dome_mesh.py --tri 100 --base 50 --out north_america_dome.3mf
  --tri   triangle edge length along the surface, mm (= km)
  --base  thickness at the lowest coastline point, mm
"""
import argparse, json, math, zipfile
import numpy as np
from shapely.geometry import shape, Polygon, Point
from shapely.ops import unary_union, transform
from shapely.prepared import prep
from pyproj import Transformer
import triangle as tr

ap = argparse.ArgumentParser()
ap.add_argument("--tri", type=float, default=100.0)
ap.add_argument("--base", type=float, default=50.0)
ap.add_argument("--countries", default="ne/countries50.geojson")
ap.add_argument("--K", type=float, default=2.450e-14, help="Gaussian curvature, m^-2")
ap.add_argument("--out", default="north_america_dome.3mf")
ap.add_argument("--stl_dir", default=None, help="also write one STL per landmass here")
a = ap.parse_args()
R = 1.0 / math.sqrt(a.K) / 1000.0  # km (= mm in the model)
print(f"K = {a.K:.4e} m^-2  ->  R = {R:.2f} km")
S = a.tri

# --- outlines in azimuthal-equidistant coords (distance along the surface from centre) ---
d = json.load(open(a.countries))
u = unary_union([shape(f["geometry"]) for f in d["features"]
                 if f["properties"].get("CONTINENT") == "North America"]).buffer(0)
aeqd = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0=45 +lon_0=-100 +R={R*1000} +units=km",
                            always_xy=True)
def f(x, y, z=None):
    x = np.asarray(x); return aeqd.transform(np.where(x > 0, x - 360, x), y)
p = transform(f, u)
polys = sorted(p.geoms, key=lambda g: -g.area)
names = ["Mainland", "Greenland", "Baffin Island", "Victoria Island", "Ellesmere Island",
         "Newfoundland", "Cuba", "Hispaniola", "Banks Island", "Devon Island"]
keep = [g for g in polys if g.area > 50000][:10]

def smooth(g, name):
    r = {"Mainland": 25, "Greenland": 20}.get(name, 8)
    s = Polygon(g.exterior).buffer(r, join_style=1).buffer(-r, join_style=1)
    s = s.buffer(-r / 2, join_style=1).buffer(r / 2, join_style=1)
    if s.geom_type != "Polygon": s = max(s.geoms, key=lambda x: x.area)
    return Polygon(s.exterior)

def to_sphere(xy):
    # aeqd plane (km) -> 3D on sphere with centre (0,0,-R) so the pole of projection is at (0,0,0)
    x, y = xy[:, 0], xy[:, 1]
    rho = np.hypot(x, y); c = rho / R
    k = np.where(rho > 0, R * np.sin(c) / np.where(rho > 0, rho, 1), 1.0)
    return np.c_[x * k, y * k, R * np.cos(c) - R]

out = []
for name, g in zip(names, keep):
    poly = smooth(g, name)
    ring = poly.exterior
    if ring.is_ccw is False: ring = Polygon(list(ring.coords)[::-1]).exterior
    L = ring.length
    nb = max(12, int(round(L / S)))
    bpts = np.array([ring.interpolate(i * L / nb).coords[0] for i in range(nb)])
    # triangular lattice inside, kept away from the coast by ~0.5 S
    minx, miny, maxx, maxy = poly.bounds
    h = S * math.sqrt(3) / 2
    inner = prep(poly.buffer(-0.5 * S))
    lat = []
    j = 0; yy = miny
    while yy <= maxy:
        off = (S / 2) if j % 2 else 0.0
        xx = minx + off
        while xx <= maxx:
            if inner.contains(Point(xx, yy)): lat.append((xx, yy))
            xx += S
        yy += h; j += 1
    pts = np.vstack([bpts, np.array(lat).reshape(-1, 2)])
    seg = np.c_[np.arange(nb), (np.arange(nb) + 1) % nb]
    T = tr.triangulate({"vertices": pts, "segments": seg}, "p")
    V2, F = T["vertices"], T["triangles"]
    nb2 = len(bpts)  # triangle keeps input vertices first
    top = to_sphere(V2)
    out.append((name, V2, F, top, bpts))

# lift so the lowest coastline point sits at z = base
zmin_coast = min(o[3][:len(o[4])][:, 2].min() for o in out)
lift = a.base - zmin_coast

objs = []
for name, V2, F, top, bpts in out:
    nb = len(bpts)
    top = top.copy(); top[:, 2] += lift
    nt = len(top)
    bot = np.c_[top[:nb, 0], top[:nb, 1], np.zeros(nb)]
    verts = np.vstack([top, bot])
    tris = []
    # top faces: make normals point up
    for t in F:
        A, B, C = top[t]
        n = np.cross(B - A, C - A)
        tris.append(tuple(t) if n[2] > 0 else (t[0], t[2], t[1]))
    # walls (boundary is CCW seen from above -> outward normals with this winding)
    for i in range(nb):
        i2 = (i + 1) % nb
        tris.append((i, nt + i, nt + i2))
        tris.append((i, nt + i2, i2))
    # flat base: triangulate the coastline polygon, normals down
    B = tr.triangulate({"vertices": bpts, "segments": np.c_[np.arange(nb), (np.arange(nb) + 1) % nb]}, "p")
    assert len(B["vertices"]) == nb, "base triangulation added points"
    for t in B["triangles"]:
        A_, B_, C_ = bot[t]
        n = np.cross(B_ - A_, C_ - A_)
        tt = nt + t
        tris.append(tuple(tt) if n[2] < 0 else (tt[0], tt[2], tt[1]))
    objs.append((name, verts, np.array(tris)))
    print(f"{name:17s} top triangles {len(F):6d}  vertices {len(verts):6d}  "
          f"peak z {top[:,2].max():8.1f}  coast z {top[:nb,2].min():6.1f}-{top[:nb,2].max():6.1f}")

# --- write 3MF (units mm), one object per landmass ---
model = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
         '<resources>']
for k, (name, V, T) in enumerate(objs, 1):
    model.append(f'<object id="{k}" name="{name}" type="model"><mesh><vertices>')
    model += [f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V]
    model.append('</vertices><triangles>')
    model += [f'<triangle v1="{i}" v2="{j}" v3="{l}"/>' for i, j, l in T]
    model.append('</triangles></mesh></object>')
model.append('</resources><build>')
model += [f'<item objectid="{k}"/>' for k in range(1, len(objs) + 1)]
model.append('</build></model>')
with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml",
               '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
               '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr("_rels/.rels",
               '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr("3D/3dmodel.model", "\n".join(model))
print("wrote", a.out, "lift", round(lift, 3))
json.dump({"K_m2": a.K, "R_mm": R, "lift_mm": lift, "tri_km": S, "base_mm": a.base}, open(a.out.rsplit(".", 1)[0] + "_params.json", "w"), indent=1)
if a.stl_dir:
    import os, struct
    os.makedirs(a.stl_dir, exist_ok=True)
    for name, V, T in objs:
        fn = os.path.join(a.stl_dir, name.replace(" ", "_") + ".stl")
        with open(fn, "wb") as fh:
            fh.write(name.encode()[:80].ljust(80, b" ")); fh.write(struct.pack("<I", len(T)))
            for t in T:
                p0, p1, p2 = V[t[0]], V[t[1]], V[t[2]]
                n = np.cross(p1 - p0, p2 - p0); n = n / (np.linalg.norm(n) or 1)
                fh.write(struct.pack("<12fH", *n, *p0, *p1, *p2, 0))
    print("STLs in", a.stl_dir)
