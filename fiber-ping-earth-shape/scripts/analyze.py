#!/usr/bin/env python3
"""
Combine both ping runs, compute globe and flat-map (north-pole azimuthal
equidistant) distances, light-speed floors, and the margin of each
measured minimum below/above the flat vacuum floor, with a Monte Carlo
uncertainty on the floor from endpoint-position errors.

Usage: python3 -I scripts/analyze.py   (run from the simulation folder)
Writes data/summary.json.
"""
import csv, json, math, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 299_792.458            # km/s, exact (NIST)
N_FIBER = 1.468            # SMF-28 family group index at 1550 nm (1.4682)
R = 6371.0088
KM_PER_DEG = math.pi * R / 180
SIGMA_POS_KM = 25.0        # 1σ position error per endpoint (city-level coordinates)
SIGMA_PING_MS = 0.05       # 1σ timestamp error that could make a ping read fast
TRIALS = 4000

# Vultr datacentre coordinates (city level), as used in the scripts
TARGETS = {
    "Seattle": (47.61, -122.33), "Silicon Valley": (37.35, -121.95), "Los Angeles": (34.05, -118.24),
    "Honolulu": (21.31, -157.86), "Miami": (25.76, -80.19), "New Jersey": (40.55, -74.46),
    "London": (51.51, -0.13), "Amsterdam": (52.37, 4.90), "Stockholm": (59.33, 18.07),
    "Tokyo": (35.68, 139.69), "Osaka": (34.69, 135.50), "Seoul": (37.57, 126.98),
    "Singapore": (1.35, 103.82), "Sydney": (-33.87, 151.21), "Melbourne": (-37.81, 144.96),
    "Mumbai": (19.08, 72.88), "Sao Paulo": (-23.55, -46.63), "Santiago": (-33.45, -70.67),
    "Johannesburg": (-26.20, 28.05),
}
VANCOUVER = (49.28, -123.12)   # run 1 probe coordinates were not logged; city centre used

def globe(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def flat(a, b):
    r1, r2 = (90 - a[0]) * KM_PER_DEG, (90 - b[0]) * KM_PER_DEG
    d = math.radians(b[1] - a[1])
    return math.sqrt(max(r1*r1 + r2*r2 - 2*r1*r2*math.cos(d), 0))

def jitter(p, rng):
    """Move a point by a 2-D Gaussian of SIGMA_POS_KM on the globe."""
    dn, de = rng.gauss(0, SIGMA_POS_KM), rng.gauss(0, SIGMA_POS_KM)
    lat = p[0] + dn / KM_PER_DEG
    lon = p[1] + de / (KM_PER_DEG * max(math.cos(math.radians(p[0])), 1e-6))
    return (lat, lon)

fiber = lambda d: 2 * d * N_FIBER / C * 1000
vac = lambda d: 2 * d / C * 1000

def row(run, src, a, tgt, b, mn, avg):
    rng = random.Random(f"{src}-{tgt}")
    fs = [vac(flat(jitter(a, rng), jitter(b, rng))) for _ in range(TRIALS)]
    gs = [vac(globe(jitter(a, rng), jitter(b, rng))) for _ in range(TRIALS)]
    sd = lambda xs: (sum((x - sum(xs)/len(xs))**2 for x in xs) / (len(xs)-1)) ** 0.5
    g, f = globe(a, b), flat(a, b)
    s_flat = math.hypot(sd(fs), SIGMA_PING_MS)
    s_glob = math.hypot(sd(gs) * N_FIBER, SIGMA_PING_MS)
    return {
        "run": run, "source": src, "target": tgt,
        "globe_km": round(g, 1), "flat_km": round(f, 1),
        "min_ms": mn, "avg_ms": avg,
        "globe_fiber_ms": round(fiber(g), 2), "globe_vac_ms": round(vac(g), 2),
        "flat_fiber_ms": round(fiber(f), 2), "flat_vac_ms": round(vac(f), 2),
        "sigma_flat_vac_ms": round(s_flat, 2),
        # positive = ping is FASTER than the flat vacuum floor allows (flat ruled out)
        "flat_margin_ms": round(vac(f) - mn, 2),
        "flat_margin_sigma": round((vac(f) - mn) / s_flat, 1),
        # positive = ping is slower than the globe fiber floor (globe allowed)
        "globe_margin_ms": round(mn - fiber(g), 2),
        "globe_margin_sigma": round((mn - fiber(g)) / s_glob, 1),
    }

def main():
    out = []
    for r in csv.DictReader(open(os.path.join(HERE, "data", "vancouver_results.csv"))):
        out.append(row("Vancouver", "Vancouver", VANCOUVER, r["city"], TARGETS[r["city"]],
                       float(r["ping_min_ms"]), float(r["ping_avg_ms"])))
    for r in csv.DictReader(open(os.path.join(HERE, "data", "southern_results.csv"))):
        out.append(row("Southern", r["source"], (float(r["probe_lat"]), float(r["probe_lon"])),
                       r["target"], TARGETS[r["target"]],
                       float(r["ping_min_ms"]), float(r["ping_avg_ms"])))
    json.dump(out, open(os.path.join(HERE, "data", "summary.json"), "w"), indent=1)
    print(f"{'pair':30s} {'min':>7s} {'flatVac':>8s} {'σ':>5s} {'margin σ':>9s} {'globe σ':>8s}")
    for r in out:
        print(f"{r['source']+'→'+r['target']:30s} {r['min_ms']:7.1f} {r['flat_vac_ms']:8.1f} "
              f"{r['sigma_flat_vac_ms']:5.2f} {r['flat_margin_sigma']:9.1f} {r['globe_margin_sigma']:8.1f}")

if __name__ == "__main__":
    main()
