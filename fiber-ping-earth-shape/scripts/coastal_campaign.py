#!/usr/bin/env python3
"""
coastal_campaign.py - one source city -> every coastal Vultr test host.

    python3 coastal_campaign.py Vancouver CA
    python3 coastal_campaign.py Santiago CL

What it does for each target
  1. Shortest route: pings from up to --probes different Globalping probes in
     the source city (different ISPs/ASNs, so different routes) and keeps the
     lowest minimum RTT. That probe's route is the shortest one seen.
  2. Traceroute (ICMP) from the same probes, saved to text.
  3. Where is the server really? A "home check" pings the target from probes
     in the target's own city. A min RTT of a few ms puts the server within a
     few hundred km of that city, whatever shape the Earth is: at that scale
     globe and flat distances agree to well under 1 %. A large home RTT
     flags a mislabelled site.
  4. Globe and flat (north-pole azimuthal equidistant) distances, fibre and
     vacuum floors, and a verdict.

Outputs next to the script:
  <source>_campaign.csv, <source>_traceroutes.txt

Rate limits: anonymous Globalping allows about 250 probe-tests/hour per IP.
One campaign at the defaults uses about 18 x (3+3+2) = 144. Set
GLOBALPING_TOKEN (free account, 500/h) to run both campaigns back to back.
Python 3 stdlib only.
"""
import csv, json, math, os, sys, time, urllib.error, urllib.request

API = "https://api.globalping.io/v1/measurements"
PACKETS = 16
C = 299_792.458
N_FIBER = 1.468
R_EARTH = 6371.0088
KM_PER_DEG = math.pi * R_EARTH / 180
HOME_OK_MS = 6.0          # home-check min RTT under this -> site confirmed (~600 km fibre radius)

# (label, host, lat, lon, country code for home check, landing note)
TARGETS = [
    ("Seattle",        "wa-us-ping.vultr.com",      47.61, -122.33, "US", "Pacific NW hub"),
    ("Silicon Valley", "sjo-ca-us-ping.vultr.com",  37.35, -121.95, "US", "Trans-Pacific landings (CA)"),
    ("Los Angeles",    "lax-ca-us-ping.vultr.com",  34.05, -118.24, "US", "Trans-Pacific landings"),
    ("Honolulu",       "hon-hi-us-ping.vultr.com",  21.31, -157.86, "US", "Mid-Pacific cable hub"),
    ("Miami",          "fl-us-ping.vultr.com",      25.76,  -80.19, "US", "Latin America gateway"),
    ("New Jersey",     "nj-us-ping.vultr.com",      40.55,  -74.46, "US", "Trans-Atlantic landings"),
    ("London",         "lon-gb-ping.vultr.com",     51.51,   -0.13, "GB", "Trans-Atlantic landings"),
    ("Amsterdam",      "ams-nl-ping.vultr.com",     52.37,    4.90, "NL", "North Sea / AMS-IX"),
    ("Stockholm",      "sto-se-ping.vultr.com",     59.33,   18.07, "SE", "Baltic"),
    ("Tokyo",          "hnd-jp-ping.vultr.com",     35.68,  139.69, "JP", "Trans-Pacific landings"),
    ("Osaka",          "osk-jp-ping.vultr.com",     34.69,  135.50, "JP", "Trans-Pacific landings"),
    ("Seoul",          "sel-kor-ping.vultr.com",    37.57,  126.98, "KR", "Busan landings"),
    ("Singapore",      "sgp-ping.vultr.com",         1.35,  103.82, "SG", "SE Asia hub"),
    ("Sydney",         "syd-au-ping.vultr.com",    -33.87,  151.21, "AU", "Southern Cross / Hawaiki"),
    ("Melbourne",      "mel-au-ping.vultr.com",    -37.81,  144.96, "AU", "Bass Strait"),
    ("Mumbai",         "bom-in-ping.vultr.com",     19.08,   72.88, "IN", "Indian Ocean landings"),
    ("Sao Paulo",      "sao-br-ping.vultr.com",    -23.55,  -46.63, "BR", "Santos/Fortaleza landings"),
    ("Santiago",       "scl-cl-ping.vultr.com",    -33.45,  -70.67, "CL", "Valparaiso landings (~100 km inland)"),
    ("Johannesburg",   "jnb-za-ping.vultr.com",    -26.20,   28.05, "ZA", "Inland; via Cape Town / Durban"),
]
HOME_CITY = {"Silicon Valley": "San Jose", "New Jersey": "Newark", "Sao Paulo": "São Paulo"}


# ---------- Globalping ----------
def api(method, url, body=None):
    h = {"Content-Type": "application/json", "User-Agent": "coastal-campaign/1.0"}
    if os.environ.get("GLOBALPING_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GLOBALPING_TOKEN"]
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers=h, method=method)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                wait = int(e.headers.get("Retry-After", "60"))
                print(f"   rate limited, waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise

def run(mtype, target, locations, options, limit=None):
    body = {"type": mtype, "target": target, "locations": locations, "measurementOptions": options}
    if limit and not isinstance(locations, str):
        body["limit"] = limit
    mid = api("POST", API, body)["id"]
    for _ in range(80):
        time.sleep(1.5)
        m = api("GET", f"{API}/{mid}")
        if m["status"] != "in-progress":
            return mid, m["results"]
    raise TimeoutError(f"{mtype} to {target} did not finish")


# ---------- geometry ----------
def globe_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))

def flat_km(a, b):
    r1, r2 = (90 - a[0]) * KM_PER_DEG, (90 - b[0]) * KM_PER_DEG
    d = math.radians(b[1] - a[1])
    return math.sqrt(max(0.0, r1 * r1 + r2 * r2 - 2 * r1 * r2 * math.cos(d)))

fiber = lambda d: 2 * d * N_FIBER / C * 1000
vacuum = lambda d: 2 * d / C * 1000


def verdict(mn, g, f):
    if mn is None:
        return "no reply"
    if mn < vacuum(g):
        return "ANOMALY: below globe VACUUM floor - wrong coords or reply not from target"
    if mn < fiber(g):
        return "ANOMALY: below globe fibre floor - check reply origin / coords"
    if mn < vacuum(f):
        return "flat map ruled out (even at vacuum c)"
    if mn < fiber(f):
        return "flat map ruled out (fibre)"
    return "no discrimination"


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src_city, src_cc = sys.argv[1], sys.argv[2].upper()
    n_probes = int(os.environ.get("PROBES", "3"))
    tag = src_city.lower().replace(" ", "_")
    here = os.path.dirname(os.path.abspath(__file__))
    tr_out = open(os.path.join(here, f"{tag}_traceroutes.txt"), "w")
    rows = []

    for label, host, tlat, tlon, tcc, note in TARGETS:
        if label.lower() == src_city.lower():
            continue
        print(f"-> {src_city} -> {label} ({host})", flush=True)
        try:
            mid, results = run("ping", host, [{"city": src_city, "country": src_cc}],
                               {"packets": PACKETS}, limit=n_probes)
            _, trs = run("traceroute", host, mid, {"protocol": "ICMP"})
            home_city = HOME_CITY.get(label, label)
            try:
                _, home = run("ping", host, [{"city": home_city, "country": tcc}],
                              {"packets": 8}, limit=2)
            except urllib.error.HTTPError:
                home = []
        except (urllib.error.URLError, KeyError, TimeoutError, IndexError) as e:
            print(f"   FAILED: {e}")
            rows.append({"target": label, "verdict": f"error: {e}"})
            continue

        # --- shortest route across source probes ---
        cands = []
        for res in results:
            p, s = res["probe"], res["result"].get("stats") or {}
            if s.get("min") is not None:
                cands.append((s["min"], p, s))
        if not cands:
            rows.append({"target": label, "verdict": "no reply"})
            continue
        cands.sort(key=lambda x: x[0])
        mn, p, s = cands[0]
        a, b = (p["latitude"], p["longitude"]), (tlat, tlon)
        g, f = globe_km(a, b), flat_km(a, b)

        # --- home check (target's own city) ---
        home_mins = [(h["result"].get("stats") or {}).get("min") for h in home]
        home_mins = [x for x in home_mins if x is not None]
        home_min = min(home_mins) if home_mins else None
        site = ("confirmed" if home_min is not None and home_min < HOME_OK_MS else
                "SUSPECT" if home_min is not None else "unchecked (no local probe)")

        v = verdict(mn, g, f)
        spread = ", ".join(f"AS{c[1]['asn']} {c[0]:.1f}" for c in cands)
        print(f"   best AS{p['asn']} {p['network']}: min {mn:.1f} ms  [{spread}]")
        print(f"   globe {g:,.0f} km (floor {fiber(g):.1f}) | flat {f:,.0f} km (floor {fiber(f):.1f}) "
              f"| home {home_min} ms -> site {site} | {v}")

        best_tr = next((t for t in trs if t["probe"].get("asn") == p["asn"]
                        and t["probe"].get("city") == p["city"]), trs[0] if trs else None)
        hops = (best_tr or {}).get("result", {}).get("hops") or []
        last = next((h for h in reversed(hops) if h.get("resolvedAddress")), {})
        rows.append({
            "source": src_city, "target": label, "host": host, "note": note,
            "probes_tried": len(cands), "best_probe_asn": p["asn"], "best_probe_network": p["network"],
            "probe_city": p["city"], "probe_lat": p["latitude"], "probe_lon": p["longitude"],
            "all_probe_mins": spread,
            "globe_km": round(g, 1), "flat_km": round(f, 1),
            "ping_min_ms": mn, "ping_avg_ms": s.get("avg"), "loss_pct": s.get("loss"),
            "globe_fiber_floor_ms": round(fiber(g), 1), "globe_vacuum_floor_ms": round(vacuum(g), 1),
            "flat_fiber_floor_ms": round(fiber(f), 1), "flat_vacuum_floor_ms": round(vacuum(f), 1),
            "inflation_globe": round(mn / fiber(g), 2), "inflation_flat": round(mn / fiber(f), 2),
            "home_min_ms": home_min, "site_check": site,
            "hops": len(hops), "last_hop_host": last.get("resolvedHostname"), "verdict": v,
        })
        for t in trs:
            tp = t["probe"]
            tr_out.write(f"===== {src_city} -> {label} | probe AS{tp.get('asn')} {tp.get('network')}"
                         f"{'  <- shortest' if t is best_tr else ''} | globe {g:.0f} km, flat {f:.0f} km =====\n")
            tr_out.write((t["result"].get("rawOutput") or "") + "\n\n")
        tr_out.flush()

    tr_out.close()
    fields = ["source", "target", "host", "note", "probes_tried", "best_probe_asn", "best_probe_network",
              "probe_city", "probe_lat", "probe_lon", "all_probe_mins", "globe_km", "flat_km",
              "ping_min_ms", "ping_avg_ms", "loss_pct", "globe_fiber_floor_ms", "globe_vacuum_floor_ms",
              "flat_fiber_floor_ms", "flat_vacuum_floor_ms", "inflation_globe", "inflation_flat",
              "home_min_ms", "site_check", "hops", "last_hop_host", "verdict"]
    with open(os.path.join(here, f"{tag}_campaign.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'target':15s} {'globe km':>9s} {'flat km':>9s} {'min ms':>7s} {'g-floor':>7s} "
          f"{'f-floor':>7s} {'site':>9s}  verdict")
    for r in sorted((r for r in rows if "globe_km" in r), key=lambda r: r["globe_km"]):
        print(f"{r['target']:15s} {r['globe_km']:9,.0f} {r['flat_km']:9,.0f} {r['ping_min_ms']:7.1f} "
              f"{r['globe_fiber_floor_ms']:7.1f} {r['flat_fiber_floor_ms']:7.1f} "
              f"{r['site_check'][:9]:>9s}  {r['verdict']}")
    print(f"\nSaved {tag}_campaign.csv and {tag}_traceroutes.txt")

if __name__ == "__main__":
    sys.exit(main())
