# Fibre ping and the figure of the Earth

Two measurement series, both on 12 Nov 2026: Vancouver and Santiago, each to the same 19 coastal Vultr hosts, best of three probes per pair.

## What it shows

A round trip through fibre can't be faster than light in glass covering the distance twice. Routing, queues and routers only add time, so the minimum ping between two cities sets an upper bound on how far apart they are. The page checks each measured minimum against the fibre floor of two models, each using its own shortest path:

- **Globe:** the great-circle arc along the surface of a sphere.
- **Flat map:** the straight line on the north-pole azimuthal equidistant plane.

Results:

- **Vancouver, 19 cities:** every pair clears both floors. From a northern source the flat map stretches distances only 0–14 %, less than normal route slack, so this series is the calibration.
- **Santiago → São Paulo:** 47.8 ms, which is 6.9 ms (8.7σ) under the flat-map fibre floor and 22.5 ms (63σ) above the globe fibre floor. It is still above the flat-map vacuum floor, so the flat map survives only if part of that route runs outside glass.
- **Other Santiago pairs:** Sydney, Melbourne and Johannesburg route north through the US or Europe, so they can't tell the two maps apart.

## Why the test is built this way

| Choice | Reason |
|---|---|
| Minimum of 16 pings | Every delay adds time, so the fastest echo is closest to the physical floor. |
| Single-site Vultr test hosts | Anycast addresses can answer from a closer machine and fake a short time. |
| Best of 3 probes per source city | Different ISPs take different routes, and only the shortest route tests the floor. |
| Traceroute from the same probes | Shows which cable path was used and that the last hop is the labelled datacentre. |
| Home check (ping from the target's own city) | Fixes server position within a few hundred km without assuming an Earth shape. Long-range ping geolocation would be circular. |
| Shortest path per model (arc vs straight line) | No cable can beat its model's shortest path, so each floor is the most favourable that model can claim. |
| Same fibre floor for both models; vacuum shown as an absolute limit | The routes are glass (submarine and terrestrial fibre). n = 1.468 gives the lower floor; verdicts hold at 1.462. |
| Clocks only at the sender | One clock times the round trip. Only clock error can make a ping read too fast (0.05 ms). |

## Errors used

- Endpoint position: 25 km (1σ) per end, city-level. This is propagated to the floors by Monte Carlo (4,000 trials) and comes to 0.34–0.80 ms.
- Ping timestamp, fast side: 0.05 ms.
- Fibre group index: 1.462–1.468. 1.468 gives the lower floor, and the verdicts are the same at 1.462.

## Run it yourself

All scripts are Python 3 standard library only.

### `scripts/coastal_campaign.py`: one source city to every coastal host

Runs from any computer. Measurements come from Globalping probes in the source city, not from your machine.

```
cd scripts
export GLOBALPING_TOKEN=...          # optional; free token at dash.globalping.io (500 tests/h)
python3 coastal_campaign.py Vancouver CA
python3 coastal_campaign.py Santiago CL
```

- `PROBES=3` (environment variable) sets how many source probes are tried per target. The default is 3.
- Writes `<city>_campaign.csv` (one row per target) and `<city>_traceroutes.txt` (every probe's traceroute).
- One campaign uses about 144 probe-tests. Without a token the limit is about 250 per hour, so wait an hour between campaigns.
- CSV columns include the best probe (ASN, network, coordinates), all probe minimums, globe and flat distances, fibre and vacuum floors for both, the home-check minimum, the site verdict and the overall verdict.

### `scripts/verified_ping.py`: a pinger you can trust, for your own stations

Linux, run as root (raw ICMP socket), IPv4.

```
sudo python3 verified_ping.py ping  HOST -c 20 --flows 4
sudo python3 verified_ping.py trace HOST -q 3 --flows 4
sudo python3 verified_ping.py ping  HOST --from 49.28,-123.12 --to -33.87,151.21 --csv out.csv
```

- The send time is never put in the packet. RTT is taken from kernel transmit and receive timestamps (`SO_TIMESTAMPING`) on the sender's clock.
- Each packet carries a random nonce and an HMAC-SHA256 tag under a per-run secret key. A reply counts only if it comes back byte-identical with a valid tag. Router quotes in traceroute are checked as far as they go.
- The ICMP id, starting sequence number and inter-probe gap are randomised, so replies can't be pre-sent.
- `--flows N` explores N load-balanced paths, Paris-traceroute style, and reports the shortest.
- `--from/--to` adds the great-circle distance, the fibre floor and the path inflation.
- A verified reply proves your packet was echoed, not which machine echoed it. The light-speed floor is what catches a machine answering from too close.

## Simplifications

- Rejects one specific flat map (north-pole azimuthal equidistant), not every flat layout.
- City-level coordinates. Santiago → São Paulo should be repeated from other networks.
- Spherical Earth for globe distances (no flattening; under 0.5 %).

## Files

- `index.html`: the paper. Data is embedded from `data/summary.json`.
- `data/`: `summary.json` (both series), plus `<city>_campaign.csv` and `<city>_traceroutes.txt` for Vancouver and Santiago.
- `scripts/`: the measurement scripts, plus `page.template.html` (the page with a `__DATA__` placeholder).

## Sources

- NIST, speed of light in vacuum: https://physics.nist.gov/cuu/Constants/Value/c.html
- Corning SMF-28e+ (group index 1.4682 at 1550 nm) and SMF-28 ULL (1.4620)
- RFC 792 (ICMP); RFC 1122 §3.2.2.6
- Globalping: https://globalping.io
- Gill et al., "Dude, where's that IP?", USENIX Security 2010
- Linux kernel timestamping: https://docs.kernel.org/networking/timestamping.html
