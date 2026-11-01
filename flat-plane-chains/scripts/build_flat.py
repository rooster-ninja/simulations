"""Flat plane, lumpy triangles: the two US chains with no curve fitted under them.

Every triangle is tested on its own, against a flat triangle (angle sum exactly 180 deg):
  observed excess  = (sum of the three observed angles) - 180 deg      (Schott's tables)
  z_flat           = observed excess / sigma_closure                    (per-survey closure noise)
  R_own            = sqrt(area / observed excess)   (the radius that one triangle alone implies)
  lump             = the piece of a sphere of the triangle's own radius that passes through its
                     three corners: height (r_c^2 - d^2) / 2R above the plane, r_c the circumradius,
                     d the distance from the circumcentre. Same radius -> same curvature at any size.
Triangles whose printed table has a blank observed angle ("....") have no observed excess:
they are marked unresolved and get no lump.

Nothing here fits a surface. The flat layout is an azimuthal equidistant map of the printed
station positions, for display only; no number on the page is computed from it.

Inputs (sources/):
  triangles_rule.csv        the report's per-triangle table (observed and printed excess, area, sigma, qc)
  chain_results.json        the report's non-overlapping chain tiles
  us_triangle_vertices.csv  station positions per triangle, from the report's master KML
  na_outline_lonlat.json    Natural Earth 1:50m outline, US/Canada/Mexico, for the backdrop
Outputs (data/): flat_chains.json, flat_triangles.csv, chain_segments.csv, chain_breaks.csv
"""
import csv, json, math, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = lambda *p: os.path.join(ROOT, "sources", *p)
O = lambda *p: os.path.join(ROOT, "data", *p)
RAD = math.pi / 180 / 3600
CH = ["US 39th parallel", "US Eastern Oblique"]

# --- display projection: azimuthal equidistant on a sphere, centre 39 N 92 W (km) ---
LAT0, LON0, RS = math.radians(39.0), math.radians(-92.0), 6371.0
def proj(lon, lat):
    la, lo = math.radians(lat), math.radians(lon)
    c = math.acos(max(-1, min(1, math.sin(LAT0) * math.sin(la) + math.cos(LAT0) * math.cos(la) * math.cos(lo - LON0))))
    k = 1.0 if c < 1e-12 else c / math.sin(c)
    x = RS * k * math.cos(la) * math.sin(lo - LON0)
    y = RS * k * (math.cos(LAT0) * math.sin(la) - math.sin(LAT0) * math.cos(la) * math.cos(lo - LON0))
    return x, y

st = lambda n: [s.strip() for s in n.split(" - ")]
rows = {(r["survey"], r["triangle"]): r for r in csv.DictReader(open(S("triangles_rule.csv"))) if r["survey"] in CH}
verts = {(r["survey"], r["triangle"]): [(float(r[f"lon{i}"]), float(r[f"lat{i}"])) for i in (1, 2, 3)]
         for r in csv.DictReader(open(S("us_triangle_vertices.csv")))}
chain = json.load(open(S("chain_results.json")))

def fnum(s):
    try: return float(s)
    except (TypeError, ValueError): return None

tris = []
for (sv, name), r in rows.items():
    eo, ep = fnum(r["observed_excess_arcsec"]), fnum(r["printed_excess_arcsec"])
    area = fnum(r["area_sides_km2"]) or fnum(r["area_coords_km2"])
    sig = fnum(r["survey_sigma_arcsec"])
    if eo is None: status = "unresolved"
    elif r["qc"].startswith("dropped"): status = "dropped"
    else: status = "resolved"
    t = dict(survey=sv, name=name, stations=st(name), status=status, qc=r["qc"], area_km2=area,
             eps_obs=eo, eps_pred=ep, sigma=sig, tile=name in set(chain[sv]["names"]),
             lonlat=verts[(sv, name)], xy=[proj(*p) for p in verts[(sv, name)]])
    if status != "unresolved":
        t["z_flat"] = eo / sig
        t["q"] = eo / ep if ep else None
        e = eo * RAD
        if e > 0:
            R = math.sqrt(area * 1e6 / e) / 1e3
            t["R_own_km"] = R; t["R_own_sig_km"] = R * 0.5 * sig / eo
        # lump: sphere of the triangle's own radius through its three corners (display plane, km)
        (ax, ay), (bx, by), (cx_, cy_) = t["xy"]
        dd = 2 * (ax * (by - cy_) + bx * (cy_ - ay) + cx_ * (ay - by))
        ux = ((ax**2 + ay**2) * (by - cy_) + (bx**2 + by**2) * (cy_ - ay) + (cx_**2 + cy_**2) * (ay - by)) / dd
        uy = ((ax**2 + ay**2) * (cx_ - bx) + (bx**2 + by**2) * (ax - cx_) + (cx_**2 + cy_**2) * (bx - ax)) / dd
        rc2 = (ax - ux)**2 + (ay - uy)**2
        invR = math.copysign(math.sqrt(abs(e) / (area * 1e6)), e) * 1e3        # 1/km
        best = 0.0
        M = 40
        for i in range(M + 1):
            for j in range(M + 1 - i):
                b1, b2 = i / M, j / M; b3 = 1 - b1 - b2
                px = b1 * ax + b2 * bx + b3 * cx_; py = b1 * ay + b2 * by + b3 * cy_
                h = (rc2 - (px - ux)**2 - (py - uy)**2) / 2 * invR
                if abs(h) > abs(best): best = h
        t["cap_m"] = best * 1e3
    tris.append(t)

# --- connectivity: triangles joined by a shared printed side ---
def components(names, sv):
    E = collections.defaultdict(set)
    for t in tris:
        if t["survey"] != sv: continue
        a, b, c = t["stations"]
        for p in ((a, b), (b, c), (a, c)): E[frozenset(p)].add(t["name"])
    nb = lambda n: set().union(*[E[frozenset(p)] for p in ((st(n)[0], st(n)[1]), (st(n)[1], st(n)[2]), (st(n)[0], st(n)[2]))]) - {n}
    comp, k = {}, 0
    for n in sorted(names):
        if n in comp: continue
        k += 1; stack = [n]; comp[n] = k
        while stack:
            x = stack.pop()
            for y in nb(x):
                if y in names and y not in comp: comp[y] = k; stack.append(y)
    return comp, nb

def gc_km(p, q):
    a1, b1, a2, b2 = map(math.radians, (p[1], p[0], q[1], q[0]))
    return RS * math.acos(max(-1, min(1, math.sin(a1) * math.sin(a2) + math.cos(a1) * math.cos(a2) * math.cos(b2 - b1))))

summary, segments, breaks = {}, [], []
for sv in CH:
    T = [t for t in tris if t["survey"] == sv]
    alln = {t["name"] for t in T}
    resn = {t["name"] for t in T if t["status"] == "resolved"}
    comp_all, nb = components(alln, sv)
    comp_res, _ = components(resn, sv)
    # does removing the unresolved triangles split anything that was joined by a side?
    split_by_unres = []
    for t in T:
        if t["status"] != "unresolved": continue
        touching = sorted({comp_res[y] for y in nb(t["name"]) if y in comp_res})
        groups_before = {comp_all[y] for y in nb(t["name"]) if y in comp_all}
        t["touches_segments"] = touching
        if len(touching) > 1: split_by_unres.append(t["name"])
    n_seg_all = len(set(comp_all.values())); n_seg_res = len(set(comp_res.values()))
    # renumber segments west to east by mean longitude
    order = sorted(set(comp_all.values()), key=lambda c: sum(p[0] for t in T if comp_all[t["name"]] == c for p in t["lonlat"]) / sum(3 for t in T if comp_all[t["name"]] == c))
    ren = {c: i + 1 for i, c in enumerate(order)}
    for t in T: t["segment"] = ren[comp_all[t["name"]]]
    # station positions per segment
    pos = collections.defaultdict(dict)
    for t in T:
        for s, p in zip(t["stations"], t["lonlat"]): pos[t["segment"]][s] = p
    # links between neighbouring segments: minimum spanning tree on closest station pairs
    segs = sorted(pos)
    link = {}
    for i in segs:
        for j in segs:
            if j <= i: continue
            best = None
            for si, p in pos[i].items():
                for sj, q in pos[j].items():
                    d = gc_km(p, q)
                    if best is None or d < best[0]: best = (d, si, sj, p, q)
            link[(i, j)] = best
    parent = {s: s for s in segs}
    def find(a):
        while parent[a] != a: a = parent[a]
        return a
    for (i, j), b in sorted(link.items(), key=lambda kv: kv[1][0]):
        if find(i) != find(j):
            parent[find(i)] = find(j)
            d, si, sj, p, q = b
            kind = "shared station only (no shared side)" if (si == sj and d < 1.0) else "gap (no triangle joins them)"
            d = 0.0 if d < 1.0 else d
            breaks.append(dict(survey=sv, between=f"{i}-{j}", kind=kind, station_a=si, station_b=sj, gap_km=round(d, 1),
                               lon=round((p[0] + q[0]) / 2, 4), lat=round((p[1] + q[1]) / 2, 4),
                               xy=[proj(*p), proj(*q)]))
    for s in segs:
        tiles = [t for t in T if t["segment"] == s and t["tile"] and t["status"] == "resolved"]
        sig = T[0]["sigma"]
        n = len(tiles); E = sum(t["eps_obs"] for t in tiles); P = sum(t["eps_pred"] for t in tiles)
        A = sum(t["area_km2"] for t in tiles)
        noise = sig * math.sqrt(n) if n else None
        W = [t for t in T if t["segment"] == s]
        segments.append(dict(survey=sv, segment=s, triangles=len(W), resolved=sum(t["status"] == "resolved" for t in W),
                             unresolved=sum(t["status"] == "unresolved" for t in W), tiles=n, area_km2=round(A, 1),
                             sum_obs=round(E, 3), sum_pred=round(P, 3), noise=round(noise, 2) if noise else None,
                             z_flat=round(E / noise, 2) if n else None, q=round(E / P, 4) if P else None,
                             lon_min=round(min(p[0] for t in W for p in t["lonlat"]), 2), lon_max=round(max(p[0] for t in W for p in t["lonlat"]), 2)))
    tiles = [t for t in T if t["tile"] and t["status"] == "resolved"]
    n = len(tiles); E = sum(t["eps_obs"] for t in tiles); P = sum(t["eps_pred"] for t in tiles); sig = T[0]["sigma"]
    res = [t for t in T if t["status"] == "resolved"]
    summary[sv] = dict(triangles=len(T), resolved=len(res), unresolved=sum(t["status"] == "unresolved" for t in T),
                       dropped=sum(t["status"] == "dropped" for t in T), segments=n_seg_all,
                       segments_without_unresolved=n_seg_res, split_by_unresolved=split_by_unres,
                       tiles=n, sum_obs=E, sum_pred=P, noise=sig * math.sqrt(n), z_flat=E / (sig * math.sqrt(n)), q=E / P,
                       positive=sum(t["eps_obs"] > 0 for t in res), negative=sum(t["eps_obs"] < 0 for t in res),
                       above_3sigma=sum(t["z_flat"] > 3 for t in res), sigma=sig)

# number breaks west to east within each chain: P1.. on the 39th parallel, E1.. on the Eastern Oblique
breaks.sort(key=lambda b: (CH.index(b["survey"]), b["lon"]))
cnt = collections.Counter()
for b in breaks:
    cnt[b["survey"]] += 1
    b["id"] = ("P" if b["survey"] == CH[0] else "E") + str(cnt[b["survey"]])

# --- outputs ---
os.makedirs(O(), exist_ok=True)
outline = json.load(open(S("na_outline_lonlat.json")))
json.dump(dict(
    projection=dict(kind="azimuthal equidistant, sphere R=6371 km", centre=[-92.0, 39.0], units="km"),
    summary=summary, segments=segments,
    breaks=[{k: v for k, v in b.items()} for b in breaks],
    triangles=[dict(s=0 if t["survey"] == CH[0] else 1, n=t["name"], st=t["status"][0], tile=int(t["tile"]),
                    seg=t["segment"], xy=[[round(x, 2), round(y, 2)] for x, y in t["xy"]],
                    a=round(t["area_km2"], 1) if t["area_km2"] else None,
                    eo=t["eps_obs"], ep=t["eps_pred"], sg=t["sigma"],
                    z=round(t["z_flat"], 2) if "z_flat" in t else None,
                    q=round(t["q"], 4) if t.get("q") is not None else None,
                    R=round(t["R_own_km"]) if "R_own_km" in t else None,
                    sR=round(t["R_own_sig_km"]) if "R_own_sig_km" in t else None,
                    h=round(t["cap_m"], 1) if "cap_m" in t else None) for t in tris],
    outline=[[[round(v, 1) for v in proj(*p)] for p in o["pts"]] for o in outline],
), open(O("flat_chains.json"), "w"), separators=(",", ":"))

with open(O("flat_triangles.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["survey", "triangle", "status", "segment", "chain_tile", "area_km2", "observed_excess_arcsec", "sigma_arcsec",
                "z_vs_flat", "ellipsoid_excess_arcsec", "q_obs_over_ellipsoid", "R_own_km", "R_own_sigma_km", "cap_height_m", "qc"])
    for t in sorted(tris, key=lambda t: (t["survey"], t["segment"], t["name"])):
        w.writerow([t["survey"], t["name"], t["status"], t["segment"], int(t["tile"]), t["area_km2"], t["eps_obs"], t["sigma"],
                    round(t["z_flat"], 3) if "z_flat" in t else "", t["eps_pred"], round(t["q"], 4) if t.get("q") else "",
                    round(t["R_own_km"]) if "R_own_km" in t else "", round(t["R_own_sig_km"]) if "R_own_sig_km" in t else "",
                    round(t["cap_m"], 1) if "cap_m" in t else "", t["qc"]])
with open(O("chain_segments.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(segments[0])); w.writeheader(); w.writerows(segments)
with open(O("chain_breaks.csv"), "w", newline="") as f:
    keys = ["id", "survey", "between", "kind", "station_a", "station_b", "gap_km", "lon", "lat"]
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows([{k: b[k] for k in keys} for b in breaks])

for sv, s in summary.items():
    print(sv, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()})
for s in segments: print(s)
for b in breaks: print({k: b[k] for k in ("survey", "between", "kind", "station_a", "station_b", "gap_km", "lon", "lat")})
