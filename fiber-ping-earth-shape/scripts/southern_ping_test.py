#!/usr/bin/env python3
"""
Southern-hemisphere ping test: globe vs flat-map (north-pole azimuthal
equidistant) distance, checked against the speed of light in fiber.

Each pair uses a real Globalping probe in the source city pinging a
single-site Vultr test server (not anycast). Ping + traceroute use the
same probe. Distances use the probe's own reported coordinates.

Verdict logic, per pair (min of 16 pings):
  min < flat fiber floor  -> that map's distance is too long for fiber
  min < flat vacuum floor -> too long even at light speed in vacuum
  min < globe fiber floor -> anomaly: check where the reply came from

Outputs next to this script: southern_results.csv, southern_traceroutes.txt
Python 3 stdlib only. Optional: export GLOBALPING_TOKEN=...
"""
import csv, json, math, os, sys, time, urllib.request, urllib.error

API = "https://api.globalping.io/v1/measurements"
PACKETS = 16
C = 299_792.458
N_FIBER = 1.468
R_EARTH = 6371.0088
KM_PER_DEG = math.pi * R_EARTH / 180      # flat map: equal spacing of latitude rings

# (source city, country, magic fallback, target label, host, target lat, lon, role)
PAIRS = [
    ("Auckland",     "NZ", "Auckland",     "Sydney",       "syd-au-ping.vultr.com",  -33.87, 151.21, "test"),
    ("Perth",        "AU", "Perth",        "Sydney",       "syd-au-ping.vultr.com",  -33.87, 151.21, "test"),
    ("Cape Town",    "ZA", "Cape Town",    "Sao Paulo",    "sao-br-ping.vultr.com",  -23.55, -46.63, "test"),
    ("Sao Paulo",    "BR", "Sao Paulo",    "Johannesburg", "jnb-za-ping.vultr.com",  -26.20,  28.05, "test"),
    ("Johannesburg", "ZA", "Johannesburg", "Sao Paulo",    "sao-br-ping.vultr.com",  -23.55, -46.63, "test"),
    ("Sydney",       "AU", "Sydney",       "Santiago",     "scl-cl-ping.vultr.com",  -33.45, -70.67, "control"),
]

def api(method, url, body=None):
    h = {"Content-Type": "application/json", "User-Agent": "ping-distance-test/1.0"}
    if os.environ.get("GLOBALPING_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GLOBALPING_TOKEN"]
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def run(mtype, target, locations, options):
    body = {"type": mtype, "target": target, "locations": locations,
            "measurementOptions": options}
    if not isinstance(locations, str):
        body["limit"] = 1
    mid = api("POST", API, body)["id"]
    for _ in range(60):
        time.sleep(1.5)
        m = api("GET", f"{API}/{mid}")
        if m["status"] != "in-progress":
            return mid, m["results"][0]
    raise TimeoutError(f"{mtype} to {target} did not finish")

def globe_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * R_EARTH * math.asin(math.sqrt(h))

def flat_km(a, b):
    r1, r2 = (90 - a[0]) * KM_PER_DEG, (90 - b[0]) * KM_PER_DEG
    d = math.radians(b[1] - a[1])
    return math.sqrt(r1*r1 + r2*r2 - 2*r1*r2*math.cos(d))

fiber = lambda d: 2 * d * N_FIBER / C * 1000
vacuum = lambda d: 2 * d / C * 1000

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rows = []
    tr_out = open(os.path.join(here, "southern_traceroutes.txt"), "w")

    for src, cc, magic, tgt, host, tlat, tlon, role in PAIRS:
        print(f"-> {src} -> {tgt} ({host})", flush=True)
        try:
            try:
                mid, pr = run("ping", host, [{"city": src, "country": cc}], {"packets": PACKETS})
            except urllib.error.HTTPError:
                mid, pr = run("ping", host, [{"magic": magic}], {"packets": PACKETS})
            _, tr = run("traceroute", host, mid, {"protocol": "ICMP"})
        except (urllib.error.URLError, KeyError, TimeoutError, IndexError) as e:
            print(f"   FAILED: {e}")
            rows.append({"source": src, "target": tgt, "role": role, "verdict": f"error: {e}"})
            continue

        p = pr["probe"]
        a, b = (p["latitude"], p["longitude"]), (tlat, tlon)
        g, f = globe_km(a, b), flat_km(a, b)
        s = pr["result"].get("stats") or {}
        mn = s.get("min")
        hops = tr["result"].get("hops") or []
        last = next((h for h in reversed(hops) if h.get("resolvedAddress")), {})

        if mn is None:
            verdict = "no reply"
        elif mn < fiber(g):
            verdict = "ANOMALY: below globe fiber floor - check reply origin"
        elif mn < vacuum(f):
            verdict = "flat map ruled out (even at vacuum light speed)"
        elif mn < fiber(f):
            verdict = "flat map ruled out (fiber)"
        else:
            verdict = "no discrimination (both models allowed)"

        print(f"   probe {p['city']}, {p['country']} AS{p['asn']} {p['network']}: "
              f"min {mn} ms | globe floor {fiber(g):.0f} | flat floor {fiber(f):.0f} -> {verdict}")
        rows.append({
            "source": src, "probe_city": p["city"], "probe_asn": p["asn"],
            "probe_network": p["network"], "probe_lat": p["latitude"], "probe_lon": p["longitude"],
            "target": tgt, "host": host, "role": role,
            "globe_km": round(g, 1), "flat_km": round(f, 1),
            "ping_min_ms": mn, "ping_avg_ms": s.get("avg"), "ping_max_ms": s.get("max"),
            "loss_pct": s.get("loss"),
            "globe_fiber_floor_ms": round(fiber(g), 1), "flat_fiber_floor_ms": round(fiber(f), 1),
            "flat_vacuum_floor_ms": round(vacuum(f), 1),
            "min_over_globe_floor": round(mn / fiber(g), 2) if mn else None,
            "min_over_flat_floor": round(mn / fiber(f), 2) if mn else None,
            "hops": len(hops), "last_hop_host": last.get("resolvedHostname"),
            "verdict": verdict,
        })
        tr_out.write(f"===== {src} -> {tgt} ({host}) | globe {g:.0f} km, flat {f:.0f} km =====\n")
        tr_out.write((tr["result"].get("rawOutput") or "") + "\n\n")
        tr_out.flush()

    tr_out.close()
    fields = ["source", "probe_city", "probe_asn", "probe_network", "probe_lat", "probe_lon",
              "target", "host", "role", "globe_km", "flat_km", "ping_min_ms", "ping_avg_ms",
              "ping_max_ms", "loss_pct", "globe_fiber_floor_ms", "flat_fiber_floor_ms",
              "flat_vacuum_floor_ms", "min_over_globe_floor", "min_over_flat_floor",
              "hops", "last_hop_host", "verdict"]
    with open(os.path.join(here, "southern_results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'pair':28s} {'min':>7s} {'globe':>6s} {'flat':>6s}  verdict")
    for r in rows:
        if "globe_km" in r:
            print(f"{r['source'] + ' -> ' + r['target']:28s} {r['ping_min_ms']:7.1f} "
                  f"{r['globe_fiber_floor_ms']:6.0f} {r['flat_fiber_floor_ms']:6.0f}  {r['verdict']}")
    print("\nSaved southern_results.csv and southern_traceroutes.txt")

if __name__ == "__main__":
    sys.exit(main())
