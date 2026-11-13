#!/usr/bin/env python3
"""
multilaterate.py - can each model place each server anywhere at all?

This test assumes no server position and no map. For every target server, each
landmark probe's minimum ping gives a maximum distance: light in glass cannot
cover more than  d_max = (t_min / 2) * c / n  in the time. Under a given model of
the Earth the server must lie within d_max of every landmark at once.

    globe: d = great-circle arc on a 6,371 km sphere
    flat:  d = straight line on the north-pole azimuthal equidistant plane

If the circles drawn under a model have no common point, that model cannot
place the server anywhere: the model fails for that server, with no assumption
about where the server really is. If they do overlap, the model survives, and
we report where it puts the server and how far that is from the labelled city.

Method: for each model, maximise the slack s(x) = min_i (d_max_i - d_i(x)) over
every possible position x (a 2-degree global grid, then local refinement).
max s >= 0: a position exists. max s < 0: no position exists, short by |s| km.

Errors: each landmark position is known to city level, taken as 25 km (1 sigma).
Monte Carlo (default 200 trials) jitters every landmark by that much and
re-solves, giving the spread of max s. Timing 0.05 ms adds ~5 km per circle.
Glass: n = 1.462 (fastest commercial fibre), so the circles are as large as
glass allows; a vacuum run (n = 1) is reported too.

    python3 multilaterate.py                          # reads landmark_pings.csv
    python3 multilaterate.py landmark_pings.csv vancouver_campaign.csv santiago_campaign.csv

Any CSV with columns target, probe_lat, probe_lon, ping_min_ms can be added
as landmarks. Outputs next to this script:
    multilateration_results.csv   one row per target and model
    multilateration_summary.json  same, plus every circle, for the page
Python 3 stdlib only.
"""
import csv, json, math, os, random, sys

C = 299_792.458
N_GLASS = 1.462
R = 6371.0088
KPD = math.pi * R / 180
SIG_POS = 25.0          # km, 1 sigma per landmark position
SIG_T = 0.05            # ms, timing
MC = int(os.environ.get("MC_TRIALS", "200"))
LABELLED = {  # labelled city of each Vultr site, used only for reporting
    "Seattle": (47.61, -122.33), "Silicon Valley": (37.35, -121.95), "Los Angeles": (34.05, -118.24),
    "Honolulu": (21.31, -157.86), "Miami": (25.76, -80.19), "New Jersey": (40.55, -74.46),
    "London": (51.51, -0.13), "Amsterdam": (52.37, 4.90), "Stockholm": (59.33, 18.07),
    "Tokyo": (35.68, 139.69), "Osaka": (34.69, 135.50), "Seoul": (37.57, 126.98),
    "Singapore": (1.35, 103.82), "Sydney": (-33.87, 151.21), "Melbourne": (-37.81, 144.96),
    "Mumbai": (19.08, 72.88), "Sao Paulo": (-23.55, -46.63), "Santiago": (-33.45, -70.67),
    "Johannesburg": (-26.20, 28.05),
}


# ---------- geometry ----------
def xyz(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))

def plane(lat, lon):
    r = (90 - lat) * KPD
    lo = math.radians(lon)
    return (r * math.cos(lo), r * math.sin(lo))

def d_globe(p, q):   # p, q: unit vectors
    dot = max(-1.0, min(1.0, p[0] * q[0] + p[1] * q[1] + p[2] * q[2]))
    return R * math.acos(dot)

def d_flat(p, q):    # p, q: plane coords
    return math.hypot(p[0] - q[0], p[1] - q[1])

MODELS = {"globe": (xyz, d_globe), "flat": (plane, d_flat)}


def slack(model, lms, lat, lon):
    to, dist = MODELS[model]
    x = to(lat, lon)
    return min(dmax - dist(p, x) for p, dmax in lms)


def solve(model, lms, starts=None):
    """Maximise slack over all positions. lms: list of (point-in-model, d_max)."""
    best = []
    if starts is None:
        for la in range(-90, 91, 2):
            for lo in range(-180, 180, 2):
                best.append((slack(model, lms, la, lo), la, lo))
        best.sort(reverse=True)
        starts = [(b[1], b[2]) for b in best[:6]]
    top = (-1e18, 0, 0)
    for la, lo in starts:
        s = slack(model, lms, la, lo)
        step = 2.0
        while step > 1e-4:
            moved = False
            for dla, dlo in ((step, 0), (-step, 0), (0, step), (0, -step),
                             (step, step), (step, -step), (-step, step), (-step, -step)):
                nla = max(-90.0, min(90.0, la + dla))
                nlo = (lo + dlo + 180) % 360 - 180
                ns = slack(model, lms, nla, nlo)
                if ns > s:
                    s, la, lo, moved = ns, nla, nlo, True
                    break
            if not moved:
                step /= 2
        if s > top[0]:
            top = (s, la, lo)
    return top


def load(paths):
    rows = {}
    for path in paths:
        with open(path) as fh:
            for r in csv.DictReader(fh):
                try:
                    t = r["target"]; lat = float(r["probe_lat"]); lon = float(r["probe_lon"])
                    mn = float(r["ping_min_ms"])
                except (KeyError, ValueError, TypeError):
                    continue
                key = (round(lat, 3), round(lon, 3))
                rows.setdefault(t, {})
                if key not in rows[t] or mn < rows[t][key]["ms"]:
                    rows[t][key] = {"lat": lat, "lon": lon, "ms": mn,
                                    "city": r.get("probe_city") or r.get("landmark_city") or r.get("source") or ""}
    return {t: list(v.values()) for t, v in rows.items()}


def jitter(lat, lon):
    dlat = random.gauss(0, SIG_POS) / 111.195
    dlon = random.gauss(0, SIG_POS) / (111.195 * max(0.05, math.cos(math.radians(lat))))
    return max(-90.0, min(90.0, lat + dlat)), (lon + dlon + 180) % 360 - 180


def analyse(target, lm, n):
    out = {}
    for model, (to, dist) in MODELS.items():
        def build(jit):
            res = []
            for L in lm:
                la, lo = jitter(L["lat"], L["lon"]) if jit else (L["lat"], L["lon"])
                ms = L["ms"] - (abs(random.gauss(0, SIG_T)) if jit else 0)
                res.append((to(la, lo), ms / 2 / 1000 * C / n))
            return res
        lms = build(False)
        s, la, lo = solve(model, lms)
        mc = []
        for _ in range(MC):
            mc.append(solve(model, build(True), starts=[(la, lo)])[0])
        mc.sort()
        sd = (sum((v - sum(mc) / len(mc)) ** 2 for v in mc) / max(1, len(mc) - 1)) ** 0.5 if mc else 0
        x = to(la, lo)
        binding = sorted(((dmax - dist(p, x), L) for (p, dmax), L in zip(lms, lm)), key=lambda z: z[0])[:3]
        lab = LABELLED.get(target)
        off = dist(to(*lab), x) if lab else None
        out[model] = {
            "max_slack_km": round(s, 1), "sigma_km": round(sd, 1),
            "z": round(s / sd, 1) if sd > 0 else None,
            "mc_p05_km": round(mc[int(0.05 * len(mc))], 1) if mc else None,
            "mc_p95_km": round(mc[int(0.95 * len(mc)) - 1], 1) if mc else None,
            "feasible": s >= 0, "best_lat": round(la, 3), "best_lon": round(lo, 3),
            "km_from_labelled_city": round(off, 0) if off is not None else None,
            "binding": [f"{L['city']} {L['ms']:.1f} ms" for _, L in binding],
        }
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    paths = sys.argv[1:] or [os.path.join(here, "landmark_pings.csv")]
    data = load(paths)
    if not data:
        sys.exit("no usable rows (need target, probe_lat, probe_lon, ping_min_ms)")
    random.seed(1)
    rows, summary = [], {"n_glass": N_GLASS, "sigma_pos_km": SIG_POS, "mc_trials": MC, "targets": {}}
    print(f"{'target':15s} {'n':>3s}  {'globe slack km':>15s}  {'flat slack km':>15s}  {'flat (vacuum)':>13s}")
    for t in sorted(data):
        lm = data[t]
        if len(lm) < 3:
            continue
        a = analyse(t, lm, N_GLASS)
        v = analyse(t, lm, 1.0)
        summary["targets"][t] = {"landmarks": lm, "glass": a, "vacuum": v}
        for medium, res in (("glass", a), ("vacuum", v)):
            for model, r in res.items():
                rows.append({"target": t, "medium": medium, "model": model, "landmarks": len(lm), **{
                    k: (";".join(r[k]) if k == "binding" else r[k]) for k in r}})
        g, f, fv = a["globe"], a["flat"], v["flat"]
        fmt = lambda r: f"{r['max_slack_km']:+8.0f} ({r['z']:+.1f}σ)" if r["z"] is not None else f"{r['max_slack_km']:+8.0f}"
        print(f"{t:15s} {len(lm):3d}  {fmt(g):>15s}  {fmt(f):>15s}  {fmt(fv):>13s}"
              + ("   FLAT CANNOT PLACE" if not f["feasible"] else "")
              + ("   GLOBE CANNOT PLACE" if not g["feasible"] else ""))
    with open(os.path.join(here, "multilateration_results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(here, "multilateration_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print("\nslack > 0: the model can place the server somewhere; slack < 0: it cannot, short by that many km.")
    print("Saved multilateration_results.csv and multilateration_summary.json")


if __name__ == "__main__":
    main()
