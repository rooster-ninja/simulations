#!/usr/bin/env python3
"""
landmark_campaign.py - ping each target server from many landmark cities.

This collects the data for multilaterate.py. Each target is pinged from up to
two Globalping probes in each of ~20 landmark cities spread over both
hemispheres. The probes' own reported coordinates are saved. No server
position is assumed: the analysis works out where each server can be under
each model, from these pings alone.

    python3 landmark_campaign.py                     # default targets
    python3 landmark_campaign.py Sydney Johannesburg # just these targets

Output, next to this script:
    landmark_pings.csv   one row per (target, landmark probe)

Rate limits: about 11 targets x 22 cities x 2 probes = ~480 probe-tests.
With GLOBALPING_TOKEN (500/h) that fits in about an hour. Without a token
(250/h) the script waits out the limit when it is hit. Rows are appended as
they arrive, so an interrupted run can be resumed: targets already complete
are skipped. Python 3 stdlib only.
"""
import csv, json, os, sys, time, urllib.error, urllib.request

API = "https://api.globalping.io/v1/measurements"
PACKETS = 8
PER_CITY = 2
OUT = "landmark_pings.csv"

TARGETS = {
    "Sydney":       "syd-au-ping.vultr.com",
    "Melbourne":    "mel-au-ping.vultr.com",
    "Johannesburg": "jnb-za-ping.vultr.com",
    "Sao Paulo":    "sao-br-ping.vultr.com",
    "Santiago":     "scl-cl-ping.vultr.com",
    "Singapore":    "sgp-ping.vultr.com",
    "Mumbai":       "bom-in-ping.vultr.com",
    "Honolulu":     "hon-hi-us-ping.vultr.com",
    "Tokyo":        "hnd-jp-ping.vultr.com",
    "London":       "lon-gb-ping.vultr.com",
    "Los Angeles":  "lax-ca-us-ping.vultr.com",
    # also available: Seattle, Silicon Valley, Miami, New Jersey, Amsterdam,
    # Stockholm, Osaka, Seoul (add here to include them)
    "Seattle":        "wa-us-ping.vultr.com",
    "Silicon Valley": "sjo-ca-us-ping.vultr.com",
    "Miami":          "fl-us-ping.vultr.com",
    "New Jersey":     "nj-us-ping.vultr.com",
    "Amsterdam":      "ams-nl-ping.vultr.com",
    "Stockholm":      "sto-se-ping.vultr.com",
    "Osaka":          "osk-jp-ping.vultr.com",
    "Seoul":          "sel-kor-ping.vultr.com",
}
DEFAULT = ["Sydney", "Melbourne", "Johannesburg", "Sao Paulo", "Santiago", "Singapore",
           "Mumbai", "Honolulu", "Tokyo", "London", "Los Angeles"]

# Landmark cities, spread over both hemispheres and all longitudes.
LANDMARKS = [
    ("Auckland", "NZ"), ("Wellington", "NZ"), ("Sydney", "AU"), ("Melbourne", "AU"),
    ("Brisbane", "AU"), ("Perth", "AU"), ("Johannesburg", "ZA"), ("Cape Town", "ZA"),
    ("Nairobi", "KE"), ("Lagos", "NG"), ("Sao Paulo", "BR"), ("Buenos Aires", "AR"),
    ("Santiago", "CL"), ("Lima", "PE"), ("Bogota", "CO"), ("Miami", "US"),
    ("Los Angeles", "US"), ("Vancouver", "CA"), ("Honolulu", "US"), ("London", "GB"),
    ("Frankfurt", "DE"), ("Tokyo", "JP"), ("Singapore", "SG"), ("Mumbai", "IN"),
]
FIELDS = ["target", "host", "landmark_city", "landmark_country", "probe_city", "probe_asn",
          "probe_network", "probe_lat", "probe_lon", "ping_min_ms", "ping_avg_ms", "loss_pct", "measured_utc"]


def api(method, url, body=None):
    h = {"Content-Type": "application/json", "User-Agent": "landmark-campaign/1.0"}
    if os.environ.get("GLOBALPING_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GLOBALPING_TOKEN"]
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=h, method=method)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                wait = int(e.headers.get("Retry-After", "120"))
                print(f"   rate limited, waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise


def ping(host, city, cc):
    body = {"type": "ping", "target": host, "limit": PER_CITY,
            "locations": [{"city": city, "country": cc}], "measurementOptions": {"packets": PACKETS}}
    mid = api("POST", API, body)["id"]
    for _ in range(60):
        time.sleep(1.5)
        m = api("GET", f"{API}/{mid}")
        if m["status"] != "in-progress":
            return m["results"]
    raise TimeoutError(f"ping {host} from {city} did not finish")


def main():
    names = sys.argv[1:] or DEFAULT
    bad = [n for n in names if n not in TARGETS]
    if bad:
        sys.exit(f"unknown target(s): {bad}. Choose from: {', '.join(TARGETS)}")
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, OUT)
    done = set()
    if os.path.exists(path):
        with open(path) as fh:
            for r in csv.DictReader(fh):
                done.add((r["target"], r["landmark_city"]))
    new = not os.path.exists(path)
    fh = open(path, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()

    for t in names:
        host = TARGETS[t]
        print(f"-> {t} ({host})", flush=True)
        for city, cc in LANDMARKS:
            if (t, city) in done:
                continue
            try:
                results = ping(host, city, cc)
            except urllib.error.HTTPError as e:
                print(f"   {city:13s} no probe ({e.code})")
                w.writerow({"target": t, "host": host, "landmark_city": city, "landmark_country": cc,
                            "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                fh.flush()
                continue
            except (urllib.error.URLError, TimeoutError, KeyError) as e:
                print(f"   {city:13s} failed: {e}")
                continue
            for res in results:
                p, s = res["probe"], res["result"].get("stats") or {}
                w.writerow({"target": t, "host": host, "landmark_city": city, "landmark_country": cc,
                            "probe_city": p.get("city"), "probe_asn": p.get("asn"), "probe_network": p.get("network"),
                            "probe_lat": p.get("latitude"), "probe_lon": p.get("longitude"),
                            "ping_min_ms": s.get("min"), "ping_avg_ms": s.get("avg"), "loss_pct": s.get("loss"),
                            "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            fh.flush()
            mins = [ (r["result"].get("stats") or {}).get("min") for r in results]
            print(f"   {city:13s} " + ", ".join(f"{m:.1f}" if m is not None else "-" for m in mins), flush=True)
    fh.close()
    print(f"\nSaved {OUT}. Next: python3 multilaterate.py")


if __name__ == "__main__":
    main()
