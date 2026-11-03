"""Survey triangles across America: Gauss vs Tarski.

Every US triangle (Schott 1900, 1902) is put through two readings:

  Gauss  - curvature from the angular excess: sum of observed angles - 180 deg.
  Tarski - lengths only: the three printed sides decide, in plane geometry,
           whether the triangle exists flat and what its flat angles are.

Then the closed fans (a station surrounded by triangles) are checked by lengths
only: the flat angles at the centre, taken from printed sides, should total 360 deg
on a flat surface.

Inputs (sources/): KML extracts of Schott's printed angles, excess and sides;
triangles_rule.csv (observed excess after the report's QC); us_triangle_vertices.csv.
Output (data/): triangles.csv, fans.csv, gauss_tarski.json.
"""
import json, re, math, itertools, csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'sources')
OUT = os.path.join(HERE, '..', 'data')
ARC = math.pi / 180 / 3600
SIGMA = {'US 39th parallel': 1.261, 'US Eastern Oblique': 1.397}   # report rule, per triangle
SOURCES = {'US 39th parallel': 'kml_us39_triangles.json',
           'US Eastern Oblique': 'kml_eastern_oblique_triangles.json'}


def dms(s):
    if '.' * 4 in s:
        return None                     # angle never observed, printed "...."
    d, m, sec = s.split()
    return int(d) + int(m) / 60 + float(sec) / 3600


def field(desc, key):
    m = re.search(key + r': (.*?)(?:<br>|$)', desc)
    return json.loads(m.group(1)) if m else None


def proj(lon, lat, lon0=-92.0, lat0=39.0, R=6371.0):
    """Azimuthal equidistant on a sphere (km); display only, no number is computed from it."""
    p, p0, dl = math.radians(lat), math.radians(lat0), math.radians(lon - lon0)
    c = math.acos(max(-1, min(1, math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(dl))))
    k = R * c / math.sin(c) if c > 1e-12 else R
    return (k * math.cos(p) * math.sin(dl), k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(dl)))


def base_name(s):
    """'Kent Island North Base' -> 'Kent Island'; None if the station is not a base terminal."""
    m = re.match(r'(.*?)\s+(North|South|East|West|Northeast|Northwest|Southeast|Southwest|Middle|Upper|Lower|Check)?\s*Base$', s)
    return m.group(1) if m else None


def flat_angles(a, b, c):
    """Angles (deg) opposite sides a, b, c of the plane triangle with these sides."""
    A = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
    B = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
    return A, B, 180.0 - A - B, A + B + math.degrees(math.acos((a * a + b * b - c * c) / (2 * a * b)))


rule = {}
with open(os.path.join(SRC, 'triangles_rule.csv')) as f:
    for r in csv.DictReader(f):
        if r['survey'] in SIGMA:
            rule[(r['survey'], r['triangle'])] = r
verts = {}
with open(os.path.join(SRC, 'us_triangle_vertices.csv')) as f:
    for r in csv.DictReader(f):
        verts[(r['survey'], r['triangle'])] = [(float(r['lon%d' % i]), float(r['lat%d' % i])) for i in (1, 2, 3)]

rows = []
for survey, fn in SOURCES.items():
    for o in json.load(open(os.path.join(SRC, fn))):
        name = o['name']; st = name.split(' - ')
        ang = [dms(x) for x in field(o['desc'], 'angles printed')]
        exc = field(o['desc'], 'spherical excess printed')
        eps_printed = float(exc) if isinstance(exc, str) else sum(float(x) for x in exc)  # SP7 prints e/3 per angle
        sides = field(o['desc'], 'sides printed')
        page = re.search(r'page: (\S+)', o['desc']).group(1)
        L = {}
        for k, v in sides.items():
            # station names may contain '-': match against the triangle's own names
            pair = next(fs for fs in itertools.combinations(st, 2) if k in (fs[0] + '-' + fs[1], fs[1] + '-' + fs[0]))
            lg = float(re.search(r'(\d\.\d+)', v).group(1))
            L[frozenset(pair)] = 10 ** lg          # printed logs are log metres
        a, b, c = (L[frozenset([st[1], st[2]])], L[frozenset([st[0], st[2]])], L[frozenset([st[0], st[1]])])
        A, B, C, _ = flat_angles(a, b, c)
        flat = [A, B, C]
        ineq = min(b + c - a, a + c - b, a + b - c)        # Tarski: exists flat iff > 0
        R = rule[(survey, name)]
        eps_obs = float(R['observed_excess_arcsec']) if R['observed_excess_arcsec'] else None
        qc = R['qc']
        # printed angles carry 3 known degree misprints (report qc); use printed sides to fix the degree
        if qc != 'ok':
            ang = [None if x is None else x + round(f - x) for x, f in zip(ang, flat)]
        # Legendre: plane angle = spherical angle - e/3. Sides were computed that way.
        leg = [(x - eps_printed / 3 / 3600 - f) * 3600 for x, f in zip(ang, flat) if x is not None]
        T = 0.5 * b * c * math.sin(math.radians(A))
        # a side is a measured base line when both ends are terminals of the same base
        opp = [(st[1], st[2]), (st[0], st[2]), (st[0], st[1])]
        measured = [bool(base_name(p) and base_name(p) == base_name(q)) for p, q in opp]
        sig = SIGMA[survey]
        rows.append(dict(
            survey=survey, triangle=name, page=page, qc=qc,
            side_a_m=a, side_b_m=b, side_c_m=c, area_km2=T / 1e6,
            flat_exists=ineq > 0, triangle_ineq_margin_m=ineq,
            flat_angle_sum_minus_180_arcsec=(sum(flat) - 180) * 3600,
            printed_angle_sum_minus_180_arcsec=(sum(ang) - 180) * 3600 if None not in ang else None,
            observed_excess_arcsec=eps_obs, printed_excess_arcsec=eps_printed,
            sigma_arcsec=sig, z=(eps_obs / sig) if eps_obs is not None else None,
            K_from_excess_per_m2=(eps_obs * ARC / T) if eps_obs is not None else None,
            legendre_residual_rms_arcsec=math.sqrt(sum(x * x for x in leg) / len(leg)),
            stations=st, flat_angles=flat, printed_angles=ang, measured_side=measured,
            n_measured_sides=sum(measured),
            verts=verts[(survey, name)]))

# ---------- closed fans: a station ringed by triangles, checked by lengths only ----------
def azim(c, p):
    lat0 = math.radians(c[1])
    return math.atan2((p[0] - c[0]) * math.cos(lat0), p[1] - c[1]) % (2 * math.pi)

fans = []
for survey in SOURCES:
    tri = [r for r in rows if r['survey'] == survey]
    pos = {}
    at = defaultdict(list)
    for r in tri:
        for s, v in zip(r['stations'], r['verts']): pos[s] = v
        for i, s in enumerate(r['stations']): at[s].append((r, i))
    for v, lst in at.items():
        nb = sorted({s for r, i in lst for s in r['stations'] if s != v}, key=lambda s: azim(pos[v], pos[s]))
        k = len(nb)
        if k < 3: continue
        az = [azim(pos[v], pos[s]) for s in nb]
        edge = {}
        for r, i in lst:
            o = [s for s in r['stations'] if s != v]
            edge[frozenset(o)] = (r, i)
        best = None
        for s0 in range(k):                     # shortest-sweep cycle of non-overlapping wedges
            # dp over positions going counter-clockwise from s0
            reach = {0: [0]}
            order = [(s0 + j) % k for j in range(k)] + [s0]
            for j in range(1, k + 1):
                for pj in range(j):
                    if pj not in reach: continue
                    i0, i1 = order[pj], order[j]
                    if i0 == i1: continue
                    e = edge.get(frozenset([nb[i0], nb[i1]]))
                    gap = (az[i1] - az[i0]) % (2 * math.pi)
                    if e and 0 < gap < math.pi and (j not in reach or len(reach[pj]) + 1 > len(reach[j])):
                        reach[j] = reach[pj] + [j]
            if k in reach:
                path = [order[j] for j in reach[k]]
                if best is None or len(path) > len(best): best = path
        if not best: continue
        wedges = [edge[frozenset([nb[best[j]], nb[best[j + 1]]])] for j in range(len(best) - 1)]
        sweep = sum((az[best[j + 1]] - az[best[j]]) % (2 * math.pi) for j in range(len(best) - 1))
        if abs(sweep - 2 * math.pi) > 1e-6: continue
        # each wedge's angle at the centre must match its map gap (rejects overlapping/reflex picks)
        gaps = [math.degrees((az[best[j + 1]] - az[best[j]]) % (2 * math.pi)) for j in range(len(best) - 1)]
        if any(abs(r['flat_angles'][i] - g) > 2.0 for (r, i), g in zip(wedges, gaps)): continue
        flat_sum = sum(r['flat_angles'][i] for r, i in wedges)
        oa = [r['printed_angles'][i] for r, i in wedges]
        obs_sum = sum(oa) if None not in oa else None
        fans.append(dict(survey=survey, centre=v, n_triangles=len(wedges),
                         ring=' - '.join(nb[j] for j in best[:-1]),
                         lon=pos[v][0], lat=pos[v][1], xy=proj(*pos[v]),
                         flat_angles_from_sides_minus_360_arcsec=(flat_sum - 360) * 3600,
                         printed_angles_minus_360_arcsec=(obs_sum - 360) * 3600 if obs_sum is not None else None,
                         third_of_printed_excess_arcsec=sum(r['printed_excess_arcsec'] for r, i in wedges) / 3,
                         third_of_observed_excess_arcsec=(sum(r['observed_excess_arcsec'] for r, i in wedges) / 3
                                                          if all(r['observed_excess_arcsec'] is not None for r, i in wedges) else None),
                         triangles=[r['triangle'] for r, i in wedges]))

os.makedirs(OUT, exist_ok=True)
cols = ['survey', 'triangle', 'page', 'qc', 'side_a_m', 'side_b_m', 'side_c_m', 'area_km2', 'flat_exists',
        'triangle_ineq_margin_m', 'flat_angle_sum_minus_180_arcsec', 'printed_angle_sum_minus_180_arcsec',
        'observed_excess_arcsec', 'printed_excess_arcsec', 'sigma_arcsec', 'z', 'K_from_excess_per_m2',
        'legendre_residual_rms_arcsec', 'n_measured_sides']
with open(os.path.join(OUT, 'triangles.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(cols)
    for r in rows:
        w.writerow([('%.6g' % r[c]) if isinstance(r[c], float) else r[c] for c in cols])
fcols = ['survey', 'centre', 'n_triangles', 'ring', 'flat_angles_from_sides_minus_360_arcsec',
         'printed_angles_minus_360_arcsec', 'third_of_printed_excess_arcsec', 'third_of_observed_excess_arcsec']
with open(os.path.join(OUT, 'fans.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(fcols)
    for r in fans:
        w.writerow([('%.4f' % r[c]) if isinstance(r[c], float) else ('' if r[c] is None else r[c]) for c in fcols])

summ = {}
for s in SOURCES:
    t = [r for r in rows if r['survey'] == s]
    tested = [r for r in t if r['z'] is not None]
    fs = [x for x in fans if x['survey'] == s]
    resid = [x['flat_angles_from_sides_minus_360_arcsec'] + x['third_of_printed_excess_arcsec'] for x in fs]
    summ[s] = dict(
        triangles=len(t), tested=len(tested), untested=len(t) - len(tested),
        flat_exists=sum(r['flat_exists'] for r in t),
        max_flat_sum_err_arcsec=max(abs(r['flat_angle_sum_minus_180_arcsec']) for r in t),
        positive=sum(r['z'] > 0 for r in tested), above3=sum(r['z'] > 3 for r in tested),
        legendre_rms_arcsec=math.sqrt(sum(r['legendre_residual_rms_arcsec'] ** 2 for r in t) / len(t)),
        fans=len(fs), measured_side_triangles=sum(r['n_measured_sides'] > 0 for r in t),
        fan_resid_mean=(sum(resid) / len(resid)) if resid else None,
        fan_resid_sd=(math.sqrt(sum((x - sum(resid) / len(resid)) ** 2 for x in resid) / (len(resid) - 1)) if len(resid) > 1 else None),
        fan_deficit_mean=(-sum(x['flat_angles_from_sides_minus_360_arcsec'] for x in fs) / len(fs)) if fs else None)
json.dump(dict(summary=summ,
               triangles=[{k: r[k] for k in ('survey', 'triangle', 'page', 'area_km2', 'observed_excess_arcsec',
                                             'printed_excess_arcsec', 'sigma_arcsec', 'z', 'flat_exists',
                                             'triangle_ineq_margin_m', 'flat_angle_sum_minus_180_arcsec',
                                             'legendre_residual_rms_arcsec', 'stations', 'flat_angles',
                                             'printed_angles', 'verts', 'side_a_m', 'side_b_m', 'side_c_m', 'qc',
                                             'measured_side')} | {'xy': [proj(*v) for v in r['verts']]}
                          for r in rows],
               fans=fans),
          open(os.path.join(OUT, 'gauss_tarski.json'), 'w'), separators=(',', ':'))
print(json.dumps(summ, indent=1))
