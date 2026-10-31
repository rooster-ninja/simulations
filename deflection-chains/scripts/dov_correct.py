"""Deflection-of-the-vertical correction for the two US triangulation chains.

The theodolite's horizontal circle is levelled to the local plumb line, not to the
ellipsoid normal. The two differ by the deflection of the vertical (xi north-south,
eta east-west). A direction observed to a station seen at elevation angle e is reduced
to the ellipsoid normal by

    delta = -(xi * sin(alpha) - eta * cos(alpha)) * tan(e)

(the zenith-distance term of the Laplace azimuth equation; the -eta*tan(phi) term is
common to every direction at a station and cancels in an angle). An angle is the
difference of two directions, so its correction is delta(right) - delta(left), and a
triangle's excess changes by the sum over its three corners.

Inputs (all in ../data):
  arcs_parallel_master.kml           station and triangle coordinates (the report's KML)
  triangles_rule.csv                 observed excess, areas, tiers, sigma (the report's)
  chain_results.json                 non-overlapping chain-sum triangles (the report's)
  eigen6c4_geoid_10arcmin.nc         EIGEN-6C4 geoid, degree 720, 10' grid (Fatiando data)
  etopo1_topography_10arcmin.nc      ETOPO1 heights, degree 720, 10' grid (Fatiando data)

Deflections come from the geoid slope: xi = -dN/(M dphi), eta = -dN/(N cos(phi) dlambda).
Station heights come from the 10' topography two ways, to bracket the elevation angles:
  'grid' = bilinear value at the station; 'peak' = highest grid value within 20 km.

usage: python3 dov_correct.py      (run from this folder)
writes: ../data/dov_stations.csv, ../data/dov_triangles.csv, ../data/dov_results.json
"""
import csv, json, math, os, xml.etree.ElementTree as ET
import numpy as np, xarray as xr
from pyproj import Geod
from scipy.interpolate import RegularGridInterpolator

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "data")
RAD = math.pi / 180 / 3600
A_WGS, F_WGS = 6378137.0, 1 / 298.257223563; E2 = F_WGS * (2 - F_WGS)
K_REFR = 0.13                       # refraction coefficient, enters only the elevation angle
geod = Geod(ellps="WGS84")
CH = {"US 39th parallel": "US arc of the 39th parallel", "US Eastern Oblique": "Eastern Oblique Arc"}
TIERW = {"A": 1.0, "B": 0.5, "C": 0.25}

# ---------- grids
G = xr.open_dataset(os.path.join(D, "eigen6c4_geoid_10arcmin.nc"))["geoid"]
T = xr.open_dataset(os.path.join(D, "etopo1_topography_10arcmin.nc"))["topography"]
lat = G.latitude.values; lon = G.longitude.values; N = G.values
dphi = np.deg2rad(lat[1] - lat[0]); dlam = np.deg2rad(lon[1] - lon[0])
phi = np.deg2rad(lat)[:, None]
w = np.sqrt(1 - E2 * np.sin(phi) ** 2)
Mr = A_WGS * (1 - E2) / w ** 3; Nr = A_WGS / w
dN_dphi = np.gradient(N, axis=0) / dphi
dN_dlam = np.gradient(N, axis=1) / dlam
XI = -dN_dphi / Mr / RAD                                   # arcsec, + when astronomic zenith is north
ETA = -dN_dlam / (Nr * np.cos(np.clip(phi, -1.5, 1.5))) / RAD   # arcsec, + when east
fxi = RegularGridInterpolator((lat, lon), XI); feta = RegularGridInterpolator((lat, lon), ETA)
fN = RegularGridInterpolator((lat, lon), N); fh = RegularGridInterpolator((lat, lon), T.values)
Tv = T.values

def peak_height(la, lo, radius_km=20.0):
    i0 = np.searchsorted(lat, la); j0 = np.searchsorted(lon, lo)
    best = -1e9
    for i in range(i0 - 4, i0 + 5):
        for j in range(j0 - 6, j0 + 7):
            dy = (lat[i] - la) * 111.2; dx = (lon[j] - lo) * 111.2 * math.cos(math.radians(la))
            if math.hypot(dx, dy) <= radius_km: best = max(best, Tv[i, j])
    return float(best)

# ---------- KML: stations and triangles of the two chains
ns = {"k": "http://www.opengis.net/kml/2.2"}
doc = ET.parse(os.path.join(D, "arcs_parallel_master.kml")).getroot()[0]
stations = {}; tris = {}
for f in doc.findall("k:Folder", ns):
    fname = f.find("k:name", ns).text
    key = next((k for k, v in CH.items() if v in fname), None)
    if not key: continue
    for pm in f.findall("k:Placemark", ns):
        name = pm.find("k:name", ns).text
        pt = pm.find(".//k:Point/k:coordinates", ns)
        if pt is not None:
            lo, la = map(float, pt.text.split(",")[:2]); stations[(round(lo, 6), round(la, 6))] = (key, name)
            continue
        cs = pm.find(".//k:coordinates", ns)
        if cs is None: continue
        pts = [tuple(map(float, c.split(",")))[:2] for c in cs.text.split()][:3]
        tris[(key, name)] = [(round(a, 6), round(b, 6)) for a, b in pts]

# station values
st = {}
for (lo, la), (key, name) in stations.items():
    st[(lo, la)] = dict(chain=key, station=name, lon=lo, lat=la,
                        xi=float(fxi((la, lo))), eta=float(feta((la, lo))), N=float(fN((la, lo))),
                        h_grid=max(0.0, float(fh((la, lo)))), h_peak=max(0.0, peak_height(la, lo)))
def sval(p):
    if p not in st:  # triangle vertex without a station point: compute it directly
        lo, la = p
        st[p] = dict(chain="", station="", lon=lo, lat=la, xi=float(fxi((la, lo))), eta=float(feta((la, lo))),
                     N=float(fN((la, lo))), h_grid=max(0.0, float(fh((la, lo)))), h_peak=max(0.0, peak_height(la, lo)))
    return st[p]

def direction(P, Q, hkey):
    """azimuth (deg) and DOV reduction (arcsec) of the direction observed at P to Q"""
    a, P, Q = None, sval(P), sval(Q)
    az, _, d = geod.inv(P["lon"], P["lat"], Q["lon"], Q["lat"])
    hP = P[hkey] + P["N"]; hQ = Q[hkey] + Q["N"]
    e = math.atan((hQ - hP) / d - (1 - K_REFR) * d / (2 * 6371000.0))
    al = math.radians(az)
    delta = -(P["xi"] * math.sin(al) - P["eta"] * math.cos(al)) * math.tan(e)
    return az, delta, math.degrees(e), d

def tri_correction(V, hkey):
    tot = 0.0; corners = []
    for i in range(3):
        P, B, C = V[i], V[(i + 1) % 3], V[(i + 2) % 3]
        azB, dB, eB, _ = direction(P, B, hkey); azC, dC, eC, _ = direction(P, C, hkey)
        turn = (azC - azB + 540) % 360 - 180          # C clockwise from B -> positive
        c = (dC - dB) if turn > 0 else (dB - dC)       # correction to the interior angle
        tot += c; corners.append(c)
    return tot, corners

# ---------- per-triangle corrections
rows = {(r["survey"], r["triangle"]): r for r in csv.DictReader(open(os.path.join(D, "triangles_rule.csv"))) if r["survey"] in CH}
out = []
for (key, name), V in tris.items():
    r = rows.get((key, name))
    if r is None or len(set(V)) < 3 or not r["observed_excess_arcsec"]: continue
    area = float(r["area_sides_km2"]) if (r["area_sides_km2"] and r["tier"] != "C") else float(r["area_coords_km2"])
    dg, cg = tri_correction(V, "h_grid"); dp, cp = tri_correction(V, "h_peak")
    out.append(dict(survey=key, triangle=name, tier=r["tier"], in_result=r["in_result"] == "True",
                    area_km2=area, sigma=float(r["survey_sigma_arcsec"]),
                    K_ell=float(r["K_ellipsoid_per_m2"]), excess_raw=float(r["observed_excess_arcsec"]),
                    d_excess_grid=dg, d_excess_peak=dp,
                    max_corner_grid=max(abs(c) for c in cg), max_corner_peak=max(abs(c) for c in cp),
                    xi_mean=float(np.mean([sval(p)["xi"] for p in V])), eta_mean=float(np.mean([sval(p)["eta"] for p in V])),
                    coords=V))

# ---------- refits: report's declared rule for the US triangles (selection and sigma held fixed)
def fit(S, col):
    A = np.array([t["area_km2"] for t in S]) * 1e6
    E = np.array([t["excess_raw"] + (t[col] if col else 0.0) for t in S]) * RAD
    s = np.array([t["sigma"] for t in S]) * RAD
    w = np.array([TIERW[t["tier"]] for t in S]) / s ** 2
    Kell = np.array([t["K_ell"] for t in S])
    K = (w * A) @ E / ((w * A) @ A)
    var = np.sum((w * A) ** 2 * s ** 2) / ((w * A) @ A) ** 2
    chi = np.sum(((E - K * A) / s) ** 2); inf = max(1, math.sqrt(chi / (len(E) - 1)))
    Kref = (w * A) @ (Kell * A) / ((w * A) @ A)
    return dict(n=len(S), K=K, sK=math.sqrt(var) * inf, q=K / Kref, sq=math.sqrt(var) * inf / Kref, chi_dof=chi / (len(E) - 1))

chain = json.load(open(os.path.join(D, "chain_results.json")))
res = {}
for key in list(CH) + ["both"]:
    S = [t for t in out if t["in_result"] and (key == "both" or t["survey"] == key)]
    res[key] = {c: fit(S, c) for c in ("", "d_excess_grid", "d_excess_peak")}
    if key in chain:
        names = set(chain[key]["names"]); C = [t for t in out if t["survey"] == key and t["triangle"] in names]
        Esum = sum(t["excess_raw"] for t in C); Epred = sum(t["area_km2"] * 1e6 * t["K_ell"] / RAD for t in C)
        res[key]["chain"] = dict(n=len(C), raw=Esum, grid=Esum + sum(t["d_excess_grid"] for t in C),
                                 peak=Esum + sum(t["d_excess_peak"] for t in C), pred=Epred,
                                 noise=float(np.sqrt(len(C)) * C[0]["sigma"]))
sts = list(st.values())
summary = dict(
    stations=len(sts), triangles=len(out),
    xi_rms=float(np.sqrt(np.mean([s["xi"] ** 2 for s in sts]))), eta_rms=float(np.sqrt(np.mean([s["eta"] ** 2 for s in sts]))),
    defl_max=float(max(math.hypot(s["xi"], s["eta"]) for s in sts)),
    d_grid_rms=float(np.sqrt(np.mean([t["d_excess_grid"] ** 2 for t in out]))),
    d_peak_rms=float(np.sqrt(np.mean([t["d_excess_peak"] ** 2 for t in out]))),
    d_grid_max=float(max(abs(t["d_excess_grid"]) for t in out)), d_peak_max=float(max(abs(t["d_excess_peak"]) for t in out)),
    d_grid_mean=float(np.mean([t["d_excess_grid"] for t in out])), d_peak_mean=float(np.mean([t["d_excess_peak"] for t in out])),
    fits=res)
json.dump(summary, open(os.path.join(D, "dov_results.json"), "w"), indent=1, default=float)
with open(os.path.join(D, "dov_stations.csv"), "w", newline="") as fh_:
    wr = csv.writer(fh_); wr.writerow(["chain", "station", "lon", "lat", "xi_arcsec", "eta_arcsec", "geoid_N_m", "h_grid_m", "h_peak_m"])
    for s in sorted(sts, key=lambda s: (s["chain"], s["lon"])):
        wr.writerow([s["chain"], s["station"], f'{s["lon"]:.6f}', f'{s["lat"]:.6f}', f'{s["xi"]:.2f}', f'{s["eta"]:.2f}', f'{s["N"]:.2f}', f'{s["h_grid"]:.0f}', f'{s["h_peak"]:.0f}'])
with open(os.path.join(D, "dov_triangles.csv"), "w", newline="") as fh_:
    cols = ["survey", "triangle", "tier", "in_result", "area_km2", "sigma", "excess_raw", "d_excess_grid", "d_excess_peak", "max_corner_grid", "max_corner_peak", "xi_mean", "eta_mean"]
    wr = csv.writer(fh_); wr.writerow(cols + ["z_peak"])
    for t in out:
        wr.writerow([t[c] if not isinstance(t[c], float) else f"{t[c]:.4f}" for c in cols] + [f'{t["d_excess_peak"] / t["sigma"]:.3f}'])
print(json.dumps({k: v for k, v in summary.items() if k != "fits"}, indent=1))
for k, v in res.items():
    for c in ("", "d_excess_grid", "d_excess_peak"):
        f = v[c]; print(f"{k:20s} {c or 'raw':15s} n={f['n']} q={f['q']:.4f}±{f['sq']:.4f}")
    if "chain" in v: print("   chain", {a: round(b, 1) for a, b in v["chain"].items()})
