"""Population-density colouring of the North America dome + latitude band lines -> GLB, plus stats JSON."""
import json, numpy as np, trimesh
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from pyproj import Transformer
import matplotlib.cm as cm

import sys
# usage: pop_scene.py <mesh.3mf> <mesh_params.json> [out.glb]; params come from na_dome_mesh.py
MESH = sys.argv[1] if len(sys.argv) > 1 else "north_america_dome.3mf"
PRM = json.load(open(sys.argv[2] if len(sys.argv) > 2 else MESH.rsplit(".", 1)[0] + "_params.json"))
OUT = sys.argv[3] if len(sys.argv) > 3 else "pop_scene.glb"
R = PRM["R_mm"]      # sphere radius, mm (= km at 1:1 000 000), R = 1/sqrt(K)
LIFT = PRM["lift_mm"]
aeqd = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0=45 +lon_0=-100 +R={R*1000} +units=km", always_xy=True)
inv = Transformer.from_crs(f"+proj=aeqd +lat_0=45 +lon_0=-100 +R={R*1000} +units=km", "EPSG:4326", always_xy=True)

# North America polygon (lon/lat) for selecting cities
d = json.load(open("ne/countries50.geojson"))
na_ll = unary_union([shape(f["geometry"]) for f in d["features"]
                     if f["properties"].get("CONTINENT") == "North America"]).buffer(0.3)
na_p = prep(na_ll)
P = json.load(open("ne/places10.geojson"))["features"]
lat = np.array([f["properties"]["latitude"] for f in P]); lon = np.array([f["properties"]["longitude"] for f in P])
pop = np.array([max(f["properties"].get("pop_max") or 0, 0) for f in P], float)
glob = dict(lat=lat, pop=pop)
inna = np.array([na_p.contains(Point(x, y)) for x, y in zip(lon, lat)])
nlat, nlon, npop = lat[inna], lon[inna], pop[inna]

def quant(l, w, qs):
    o = np.argsort(l); c = np.cumsum(w[o]) / w.sum()
    return [float(l[o][np.searchsorted(c, q)]) for q in qs]
stats = {
    "na_cities": int(inna.sum()), "na_city_pop_M": float(npop.sum() / 1e6),
    "na_q10_q50_q90": quant(nlat, npop, (0.1, 0.5, 0.9)),
    "na_share_25_50": float(npop[(nlat >= 25) & (nlat < 50)].sum() / npop.sum()),
    "global_cities": int(len(pop)), "global_city_pop_M": float(pop.sum() / 1e6),
    "global_q25_q50_q75": quant(lat, pop, (0.25, 0.5, 0.75)),
    "global_share_20_40N": float(pop[(lat >= 20) & (lat < 40)].sum() / pop.sum()),
    "global_share_N": float(pop[lat > 0].sum() / pop.sum()),
}
q10, q50, q90 = stats["na_q10_q50_q90"]
print(json.dumps(stats, indent=1))

def to_ll(V):
    x, y = V[:, 0], V[:, 1]
    ro = np.hypot(x, y); c = np.arcsin(np.clip(ro / R, 0, 1))
    k = np.where(ro > 0, R * c / np.where(ro > 0, ro, 1), 1)
    lo, la = inv.transform(x * k, y * k)
    return np.array(lo), np.array(la)

def unit(lo, la):
    lo, la = np.radians(lo), np.radians(la)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
cu = unit(nlon, nlat)
sig = 150.0 / R  # 150 km kernel

scene = trimesh.Scene()
src = trimesh.load(MESH)
dens_all = []
parts = []
for name, g in src.geometry.items():
    V = g.vertices.copy()
    lo, la = to_ll(V)
    vu = unit(lo, la)
    ang = np.arccos(np.clip(vu @ cu.T, -1, 1))
    dens = (np.exp(-0.5 * (ang / sig) ** 2) * npop).sum(1)
    dens_all.append(dens); parts.append((name, g, dens))
ref = np.percentile(np.concatenate(dens_all), 99.5)
import matplotlib; cmap = matplotlib.colormaps["inferno"]
for name, g, dens in parts:
    F = g.faces; V = g.vertices
    fd = dens[F].mean(1)
    t = np.clip(np.log10(1 + 99 * fd / ref) / 2, 0, 1)
    base = np.array([0.78, 0.80, 0.83])
    rgb = cmap(0.2 + 0.8 * t)[:, :3]
    a = np.clip(t * 1.5, 0, 1)[:, None]
    col = base * (1 - a) + rgb * a
    up = g.face_normals[:, 2] > 0.05
    col[~up] = np.array([0.55, 0.57, 0.60])
    lin = col ** 2.2
    m = trimesh.Trimesh(V[F].reshape(-1, 3), np.arange(len(F) * 3).reshape(-1, 3), process=False)
    m.visual.vertex_colors = (np.c_[np.repeat(lin, 3, axis=0), np.ones(len(F) * 3)] * 255).astype(np.uint8)
    scene.add_geometry(m, node_name=name)

# ocean + star slabs
oc = trimesh.creation.box(extents=[6900, 8600, 50]); oc.apply_translation([-3500 + 3450, -3900 + 4300, -25])
oc.visual.face_colors = [4, 30, 87, 255]; scene.add_geometry(oc, node_name="Ocean")


# latitude lines on the dome, only over land; sphere point lifted with LIFT
land_aeqd = None
def sphere_pt(lo, la, up=6):
    x, y = aeqd.transform(lo, la)
    x, y = np.asarray(x), np.asarray(y)
    rho = np.hypot(x, y); c = rho / R
    k = np.where(rho > 0, R * np.sin(c) / np.where(rho > 0, rho, 1), 1)
    z = R * np.cos(c) - R + LIFT
    n = np.c_[x * k, y * k, z + R - LIFT]; n = n / np.linalg.norm(n, axis=1)[:, None]
    return np.c_[x * k, y * k, z] + n * up

landmesh = trimesh.util.concatenate([g for _, g, _ in parts])
def over_land(P3):
    # land if a vertical ray from just below the sphere hits the land top near this height
    o = P3.copy(); o[:, 2] = -1
    loc, ri, _ = landmesh.ray.intersects_location(o, np.tile([0, 0, 1], (len(o), 1)), multiple_hits=False)
    hit = np.zeros(len(P3), bool); hit[ri] = True
    return hit

def lat_line(la, color, radius):
    lo = np.linspace(-175, -50, 2500)
    P3 = sphere_pt(lo, np.full_like(lo, la))
    ok = over_land(P3)
    segs = []
    for i in range(len(P3) - 1):
        if ok[i] and ok[i + 1]:
            segs.append((P3[i], P3[i + 1]))
    # merge consecutive into polylines and sweep as cylinders
    meshes = []
    for a, b in segs:
        cyl = trimesh.creation.cylinder(radius=radius, segment=[a, b], sections=8)
        cyl.visual.face_colors = color; meshes.append(cyl)
    if meshes:
        m = trimesh.util.concatenate(meshes); scene.add_geometry(m, node_name=f"lat_{la:.1f}")

lat_line(q10, [10, 120, 230, 255], 20)
lat_line(q90, [10, 120, 230, 255], 20)
lat_line(q50, [255, 255, 255, 255], 16)
scene.export(OUT)
json.dump(stats, open("pop_stats.json", "w"), indent=1)
print("ok")
