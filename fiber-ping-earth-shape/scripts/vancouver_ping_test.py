#!/usr/bin/env python3
"""
Vancouver -> coastal backhaul cities: ping + traceroute mini test.

Runs on any machine with Python 3 and internet (no installs needed).
Uses Globalping (https://globalping.io) so every measurement starts from a
real probe in Vancouver, BC, not from wherever this script runs.

Targets are Vultr per-datacentre test hosts: one physical site each
(not anycast/CDN), so the city label matches where the reply comes from.
The traceroute's last hops are logged so that can be checked, not assumed.

Outputs (next to this script):
  results.csv      one row per city: distance, min/avg/max ping, loss,
                   fiber and vacuum light-speed floors, ratio, hop count
  traceroutes.txt  full traceroute text per city
  Console summary sorted by distance, with a flag on anything below the floor.

Optional: export GLOBALPING_TOKEN=... for higher rate limits
(anonymous limit is plenty for this: ~40 measurements).
"""
import csv, json, math, os, sys, time, urllib.request, urllib.error

API = "https://api.globalping.io/v1/measurements"
SOURCE = {"city": "Vancouver", "country": "CA"}
PACKETS = 16                      # pings per target (min of these is what matters)
C_KM_S = 299_792.458
FIBER_N = 1.468                   # group index of standard single-mode fiber

# (label, host, lat, lon, note) — Vultr datacentre city coordinates
TARGETS = [
    ("Seattle",        "wa-us-ping.vultr.com",    47.61, -122.33, "Pacific NW hub"),
    ("Silicon Valley", "sjo-ca-us-ping.vultr.com",37.35, -121.95, "Trans-Pacific landings (CA)"),
    ("Los Angeles",    "lax-ca-us-ping.vultr.com",34.05, -118.24, "Trans-Pacific landings"),
    ("Honolulu",       "hon-hi-us-ping.vultr.com",21.31, -157.86, "Mid-Pacific cable hub"),
    ("Miami",          "fl-us-ping.vultr.com",    25.76,  -80.19, "Latin America gateway"),
    ("New Jersey",     "nj-us-ping.vultr.com",    40.55,  -74.46, "Trans-Atlantic landings"),
    ("London",         "lon-gb-ping.vultr.com",   51.51,   -0.13, "Trans-Atlantic landings"),
    ("Amsterdam",      "ams-nl-ping.vultr.com",   52.37,    4.90, "North Sea / AMS-IX"),
    ("Stockholm",      "sto-se-ping.vultr.com",   59.33,   18.07, "Baltic"),
    ("Tokyo",          "hnd-jp-ping.vultr.com",   35.68,  139.69, "Trans-Pacific landings"),
    ("Osaka",          "osk-jp-ping.vultr.com",   34.69,  135.50, "Trans-Pacific landings"),
    ("Seoul",          "sel-kor-ping.vultr.com",  37.57,  126.98, "Busan landings"),
    ("Singapore",      "sgp-ping.vultr.com",       1.35,  103.82, "SE Asia hub"),
    ("Sydney",         "syd-au-ping.vultr.com",  -33.87,  151.21, "Southern Cross / Hawaiki"),
    ("Melbourne",      "mel-au-ping.vultr.com",  -37.81,  144.96, "Bass Strait"),
    ("Mumbai",         "bom-in-ping.vultr.com",   19.08,   72.88, "Indian Ocean landings"),
    ("Sao Paulo",      "sao-br-ping.vultr.com",  -23.55,  -46.63, "Santos/Fortaleza landings"),
    ("Santiago",       "scl-cl-ping.vultr.com",  -33.45,  -70.67, "Valparaiso landings (inland ~100 km)"),
    ("Johannesburg",   "jnb-za-ping.vultr.com",  -26.20,   28.05, "Inland; via Cape Town / Durban"),
]

def api(method, url, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": "ping-distance-test/1.0"}
    tok = os.environ.get("GLOBALPING_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
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

def haversine_km(a, b):
    R = 6371.0088
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rows, probe_ref, probe = [], None, None
    tr_out = open(os.path.join(here, "traceroutes.txt"), "w")

    for label, host, lat, lon, note in TARGETS:
        print(f"-> {label:15s} {host}", flush=True)
        try:
            # first measurement picks the probe; the rest reuse that exact probe
            loc = probe_ref or [SOURCE]
            mid, pr = run("ping", host, loc, {"packets": PACKETS})
            if probe_ref is None:
                probe_ref, probe = mid, pr["probe"]
                print(f"   probe: {probe['city']}, {probe['country']}  "
                      f"AS{probe['asn']} {probe['network']}  "
                      f"({probe['latitude']}, {probe['longitude']})")
            _, tr = run("traceroute", host, probe_ref, {"protocol": "ICMP"})
        except (urllib.error.URLError, KeyError, TimeoutError, IndexError) as e:
            print(f"   FAILED: {e}")
            rows.append({"city": label, "target": host, "note": note, "flag": f"error: {e}"})
            continue

        r = pr["result"]
        s = r.get("stats") or {}
        d = haversine_km((probe["latitude"], probe["longitude"]), (lat, lon))
        fiber = 2 * d * FIBER_N / C_KM_S * 1000
        vac = 2 * d / C_KM_S * 1000
        mn = s.get("min")
        hops = tr["result"].get("hops") or []
        last = next((h for h in reversed(hops) if h.get("resolvedAddress")), {})
        flag = ""
        if mn is None:
            flag = "no reply"
        elif mn < vac:
            flag = "BELOW VACUUM LIGHT SPEED - check where reply came from"
        elif mn < fiber:
            flag = "below fiber floor - radio/laser path or mislabelled site"

        rows.append({
            "city": label, "target": host, "resolved_ip": r.get("resolvedAddress"),
            "distance_km": round(d, 1),
            "ping_min_ms": mn, "ping_avg_ms": s.get("avg"), "ping_max_ms": s.get("max"),
            "loss_pct": s.get("loss"),
            "fiber_floor_ms": round(fiber, 2), "vacuum_floor_ms": round(vac, 2),
            "min_over_fiber": round(mn / fiber, 2) if mn and fiber else None,
            "hops": len(hops), "last_hop_host": last.get("resolvedHostname"),
            "last_hop_ip": last.get("resolvedAddress"), "note": note, "flag": flag,
        })
        tr_out.write(f"===== {label} ({host}) — {round(d)} km =====\n")
        tr_out.write((tr["result"].get("rawOutput") or "") + "\n\n")
        tr_out.flush()

    tr_out.close()
    fields = ["city", "target", "resolved_ip", "distance_km", "ping_min_ms", "ping_avg_ms",
              "ping_max_ms", "loss_pct", "fiber_floor_ms", "vacuum_floor_ms",
              "min_over_fiber", "hops", "last_hop_host", "last_hop_ip", "note", "flag"]
    with open(os.path.join(here, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print("\n{:15s} {:>8s} {:>8s} {:>8s} {:>6s} {:>5s}  {}".format(
        "city", "km", "min ms", "floor", "ratio", "hops", "flag"))
    for r in sorted((r for r in rows if "distance_km" in r), key=lambda r: r["distance_km"]):
        print("{:15s} {:8.0f} {:>8} {:8.1f} {:>6} {:5d}  {}".format(
            r["city"], r["distance_km"], r["ping_min_ms"], r["fiber_floor_ms"],
            r["min_over_fiber"], r["hops"], r["flag"]))
    print("\nSaved results.csv and traceroutes.txt")

if __name__ == "__main__":
    sys.exit(main())
