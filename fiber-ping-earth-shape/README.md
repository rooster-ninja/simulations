# Fibre ping and the figure of the Earth

Three series, 12–13 Nov 2026: Vancouver and Santiago each to the same 19 coastal Vultr hosts (best of three probes per pair); a full mesh between 28 rented servers of our own in 19 cities, every reply hash-verified; and a circle test that places 11 servers from landmark pings alone, presuming no position.

## What it shows

Nothing outruns light in a vacuum, whatever carries the signal. Routing, queues and routers only add time, so the minimum ping between two places sets an upper bound on how far apart they are. The page checks each measured minimum against the **speed-of-light (vacuum) floor** of two models, each using its own shortest path:

- **Globe:** the great-circle arc along the surface of a sphere.
- **Flat map:** the straight line on the north-pole azimuthal equidistant plane.

No medium is presumed. The fibre floor (light in glass, n = 1.462–1.468) is shown for reference only.

Results:

- **Vancouver, 19 cities, and Santiago, 18 cities:** every pair clears both speed-of-light floors, so no single pair decides. From a northern source the two maps differ by only 0–14 %.
- **Santiago → São Paulo:** 47.8 ms, 10.5 ms (19σ) above the flat-map vacuum floor. It would fall 6.9 ms under the flat-map *fibre* floor if glass were assumed, so it is reported as undecided.
- **Other Santiago pairs:** Sydney, Melbourne and Johannesburg route north through the US or Europe, so they can't tell the two maps apart.
- **Mesh of our own servers:** 28 servers (18 Vultr, 10 AWS) in 19 cities, 22,680 pings over 756 links; all 22,611 replies passed the hash check and carried a kernel timestamp. Of the 171 city pairs, none beats the globe's floor (closest: Amsterdam–London, +3.5 ms, 15σ). **Melbourne–Sydney** returned 10.52 ms against a flat-map vacuum floor of 10.59 ± 0.62 ms: 0.07 ms under it, only 0.1σ, so it sits on the line without deciding. Where both providers had a server in one city they reached each other in 0.68–3.72 ms, confirming each site without using either map.
- **No position presumed (circle test):** 11 servers placed from 30–47 landmarks each (24 probe cities plus the mesh servers). At the speed of light the globe places all 11 within 19 km of their labelled cities, its least slack 37 km; the flat map cannot place **Sydney** (short by 1,494 km, 34σ) or **Melbourne** (1,116 km, 30σ) anywhere. Adding the mesh landmarks changed neither verdict — the deciding circles are still Auckland, Wellington and Perth, where the mesh had no server. Had glass been assumed, the flat map would fail for 7 of the 11.

## Why the test is built this way

| Choice | Reason |
|---|---|
| Minimum of 16 pings | Every delay adds time, so the fastest echo is closest to the physical floor. |
| Single-site Vultr test hosts | Anycast addresses can answer from a closer machine and fake a short time. |
| Best of 3 probes per source city | Different ISPs take different routes, and only the shortest route tests the floor. |
| Traceroute from the same probes | Shows which cable path was used and that the last hop is the labelled datacentre. |
| Home check (ping from the target's own city) | Fixes server position within a few hundred km without assuming an Earth shape. Long-range ping geolocation would be circular. |
| Shortest path per model (arc vs straight line) | No path can beat its model's shortest path, so each floor is the most favourable that model can claim. |
| Speed-of-light floor for both models; fibre shown for reference | No carrier of any kind, known or unknown, beats c, so the verdicts do not depend on the signals travelling in glass. |
| Mesh on two providers, every city to every other | Each company routes its own traffic, so a pair with a server at both ends is measured twice over independent networks. A mesh also reaches the short southern pairs that one-source campaigns miss. |
| Same-city check between providers | Where both have a datacentre in one city, their servers ping each other. Half that round trip at c bounds their separation with no figure of the Earth assumed. |
| Hash-sealed payloads on the mesh | Every echo carries a fresh random payload under a per-run key, so no router, cache or impostor can answer early for the far server. |
| Circle test from 24 landmarks plus the mesh | Places each server from pings alone, so no server position is presumed. It can only reject a model (the flat map never shortens a distance), so it is reported as one-sided. |
| Clocks only at the sender | One clock times the round trip. Only clock error can make a ping read too fast (0.05 ms). |

## Errors used

- Endpoint position: 25 km (1σ) per end, city-level. This is propagated to the vacuum floors by Monte Carlo (4,000 trials) and comes to 0.23–0.62 ms, the largest for the far-southern pairs, where the flat map spreads a small position error over the most ground.
- Ping timestamp, fast side: 0.05 ms.
- Fibre group index (1.462–1.468) affects only the reference floors, not the verdicts.

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

### `scripts/landmark_campaign.py` and `scripts/multilaterate.py`: placing servers with no presumed position

```
python3 landmark_campaign.py                       # writes landmark_pings.csv (resumable)
python3 multilaterate.py landmark_pings.csv ../data/mesh_as_landmarks.csv
```

- The campaign pings each target from up to 2 Globalping probes in each of 24 landmark cities, about 480 probe-tests for the default 11 targets (an hour with a token). Name targets on the command line to run a subset.
- For each target and each model, the analysis maximises the slack: the largest margin by which one position can lie inside every landmark's reach circle (radius = half the fastest echo at light speed, in a vacuum and, for reference, in glass with n = 1.462). Negative slack means no position exists. A 2° global grid is refined by pattern search; 200 Monte Carlo trials jitter each landmark 25 km (set `MC_TRIALS` to change).
- Writes `multilateration_results.csv` (one row per target, model and medium) and `multilateration_summary.json` (with every landmark).
- Any CSV with `target`, `probe_lat`, `probe_lon` and `ping_min_ms` columns can be added as extra landmarks. `data/mesh_as_landmarks.csv` is the mesh in that form, and is what the published run used.
- One-sided: it can reject the flat map, but on data generated from a flat world it still lets the globe place every server.

### `scripts/ping_mesh.py`: rent a mesh, run it, tear it down

Rents servers by the hour from Vultr and AWS, runs `verified_ping.py` between every pair, collects the results and deletes everything. **It spends money** — about US$0.01/hour per server, roughly $0.30/hour for the full 28 — and the `down` command is what stops the meter.

```
export VULTR_API_KEY=...                 # Vultr: Account > API; allow your IP in the access control list
pip install boto3                        # AWS: credentials via `aws configure` or environment
python3 ping_mesh.py up                   # create every server (--vultr-only / --aws-only / --cities A,B)
python3 ping_mesh.py status               # addresses and readiness
python3 ping_mesh.py run                  # upload the pinger, 30 pings each way on every link
python3 ping_mesh.py collect              # re-fetch results if a session dropped mid-run
python3 ping_mesh.py compare              # write mesh_pings.csv and mesh_compare.csv
python3 ping_mesh.py down                 # delete every server, then check `status` and both dashboards
```

- Writes `mesh_servers.json` (the manifest), `mesh_raw/` (per-server CSVs), `mesh_pings.csv` (one row per ordered server pair) and `mesh_compare.csv` (per city pair, both providers side by side, with both floors).
- Only replies verified `FULL` are counted, so an echo with a damaged or unsigned payload is dropped rather than timed.
- SSH runs with a dedicated `mesh_known_hosts` and keepalives. `run` is long; use tmux. If a session drops, `collect` finishes the job without re-pinging.
- `up` keeps going when one region fails: Vultr Santiago never came up for us, so that city is served by an AWS local zone instead.

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
- City-level coordinates: every server sits at the centre of the city its datacentre is named for. That matters most for Melbourne–Sydney, where datacentre street addresses would decide whether the pair crosses the flat map's floor.
- The mesh has no server in Auckland, Wellington or Perth, so it cannot reproduce the circle test's verdict on its own.
- Spherical Earth for globe distances (no flattening; under 0.5 %).

## Files

- `index.html`: the paper. Data is embedded from `data/summary.json`.
- `data/`: `summary.json` (everything the page shows), `<city>_campaign.csv` and `<city>_traceroutes.txt` for Vancouver and Santiago, `landmark_pings.csv`, `mesh_pings.csv`, `mesh_compare.csv`, `mesh_as_landmarks.csv`, `multilateration_results.csv` and `multilateration_summary.json`.
- `scripts/`: the measurement scripts, plus `page.template.html` (the page with a `__DATA__` placeholder).

## Sources

- NIST, speed of light in vacuum: https://physics.nist.gov/cuu/Constants/Value/c.html
- Corning SMF-28e+ (group index 1.4682 at 1550 nm) and SMF-28 ULL (1.4620)
- RFC 792 (ICMP); RFC 1122 §3.2.2.6
- Globalping: https://globalping.io
- Gill et al., "Dude, where's that IP?", USENIX Security 2010
- Linux kernel timestamping: https://docs.kernel.org/networking/timestamping.html
- Vultr API v2: https://www.vultr.com/api/ · AWS EC2 (boto3): https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html
