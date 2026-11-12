#!/usr/bin/env python3
"""
verified_ping.py - ICMP ping + traceroute that can't be fooled into a short RTT.

Design
  * Sender-side clocks only. The send time is never put in the packet, so the
    far end can't edit it. RTT is (kernel RX stamp - kernel TX stamp) from
    SO_TIMESTAMPING on one host clock, with a user-space monotonic RTT shown
    alongside it.
  * Payloads you can verify. Each probe carries a 16-byte random nonce and an
    HMAC-SHA256 tag (per-run secret key) over magic|id|seq|ttl|nonce, plus
    random padding. An echo reply counts only if its payload is byte-identical
    to the one sent AND the HMAC checks. Time-exceeded quotes are checked as
    far as the router quoted them.
  * Replies can't be predicted. The ICMP id is random, seq starts at a random
    value, and the gap between probes is jittered, so nobody can pre-send
    replies.
  * Shortest route:
      - ECMP exploration. --flows N sends on N different flow ids, Paris-style:
        each probe's checksum is held at a per-flow constant, so load
        balancers keep each flow on one path. The lowest-RTT flow is the
        shortest path seen.
      - Physics check. With --from/--to coords you get the great-circle
        distance, the fibre RTT floor, and path inflation (min RTT / floor).
        With no coords, min RTT still gives a hard upper bound on distance.

Usage (Linux, needs root or CAP_NET_RAW, IPv4)
  sudo ./verified_ping.py ping  HOST [-c 20] [-i 1.0] [-s 56] [--flows 4]
  sudo ./verified_ping.py trace HOST [-q 3] [-m 30] [--flows 4]
  add --from LAT,LON --to LAT,LON for the great-circle comparison
  add --csv out.csv to save every probe
"""
import argparse, csv, hashlib, hmac, math, os, random, select, socket, statistics, struct, sys, time

# Linux SO_TIMESTAMPING constants (asm-generic, x86_64/arm64)
SO_TIMESTAMPING = 37
SCM_TIMESTAMPING = 37
F_TX_SW, F_RX_SW, F_SW, F_TSONLY = 1 << 1, 1 << 3, 1 << 4, 1 << 11
MSG_ERRQUEUE = getattr(socket, "MSG_ERRQUEUE", 0x2000)

C_KM_S = 299_792.458
N_FIBER = 1.468                       # group index, SMF-28 @1550 nm
R_EARTH = 6371.0088
MAGIC = b"VPNG"
KEY = os.urandom(32)                  # per-run secret; never leaves this host
BODY_LEN = len(MAGIC) + 5 + 16        # magic + id,seq,ttl + nonce
TAG_LEN = 16
MIN_PAYLOAD = BODY_LEN + TAG_LEN + 2  # + 2 checksum-fix bytes


# ---------- packet building / checking ----------
def ones_sum(b):
    if len(b) % 2:
        b += b"\0"
    s = sum(struct.unpack(f"!{len(b)//2}H", b))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return s

def checksum(b):
    return ~ones_sum(b) & 0xFFFF

def tag(ident, seq, ttl, nonce):
    body = MAGIC + struct.pack("!HHB", ident, seq, ttl) + nonce
    return body, hmac.new(KEY, body, hashlib.sha256).digest()[:TAG_LEN]

def build_probe(ident, seq, ttl, size, flow_cksum):
    """Echo request whose ICMP checksum == flow_cksum (Paris-traceroute trick)."""
    size = max(size, MIN_PAYLOAD)
    for _ in range(8):
        nonce = os.urandom(16)
        body, mac = tag(ident, seq, ttl, nonce)
        pad = os.urandom(size - BODY_LEN - TAG_LEN - 2)
        base = body + mac + pad
        if len(base) % 2:                     # keep the fix word 16-bit aligned
            base = base[:-1]
        hdr = struct.pack("!BBHHH", 8, 0, 0, ident, seq)
        s = ones_sum(hdr + base)
        # want ~(s + fix) == flow_cksum  ->  fix = ~flow_cksum - s (one's complement)
        fix = ones_sum(struct.pack("!HH", ~flow_cksum & 0xFFFF, ~s & 0xFFFF))
        payload = base + struct.pack("!H", fix)
        pkt = struct.pack("!BBHHH", 8, 0, flow_cksum, ident, seq) + payload
        if checksum(pkt) == 0:                # valid, and checksum field == flow_cksum
            return pkt, payload
    raise RuntimeError("could not hit flow checksum")

def check_tag(payload, ident, seq, ttl):
    if len(payload) < BODY_LEN + TAG_LEN or payload[:4] != MAGIC:
        return False
    i, s, t = struct.unpack("!HHB", payload[4:9])
    if (i, s, t) != (ident, seq, ttl):
        return False
    _, mac = tag(ident, seq, ttl, payload[9:BODY_LEN])
    return hmac.compare_digest(mac, payload[BODY_LEN:BODY_LEN + TAG_LEN])


# ---------- timestamps ----------
def ts_from_cmsg(ancdata):
    for level, ctype, data in ancdata:
        if level == socket.SOL_SOCKET and ctype == SCM_TIMESTAMPING and len(data) >= 16:
            sec, nsec = struct.unpack("qq", data[:16])   # [0] = software stamp
            if sec or nsec:
                return sec * 1_000_000_000 + nsec
    return None

def read_tx_stamp(sock, wait_s=0.02):
    end = time.perf_counter() + wait_s
    while time.perf_counter() < end:
        try:
            _, anc, _, _ = sock.recvmsg(64, 1024, MSG_ERRQUEUE | socket.MSG_DONTWAIT)
            ts = ts_from_cmsg(anc)
            if ts:
                return ts
        except BlockingIOError:
            time.sleep(0.0002)
    return None


# ---------- one probe ----------
def probe(sock, dst, ident, seq, ttl, size, flow_cksum, timeout, kts):
    pkt, payload = build_probe(ident, seq, ttl, size, flow_cksum)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
    t_user0 = time.perf_counter_ns()
    sock.sendto(pkt, (dst, 0))
    t_tx = read_tx_stamp(sock) if kts else None
    deadline = time.perf_counter() + timeout
    while True:
        left = deadline - time.perf_counter()
        if left <= 0:
            return {"seq": seq, "ttl": ttl, "status": "timeout"}
        r, _, _ = select.select([sock], [], [], left)
        if not r:
            continue
        data, anc, _, addr = sock.recvmsg(4096, 1024)
        t_user1 = time.perf_counter_ns()
        t_rx = ts_from_cmsg(anc) if kts else None
        if len(data) < 28:
            continue
        ihl = (data[0] & 0x0F) * 4
        reply_ttl = data[8]
        src = socket.inet_ntoa(data[12:16])
        icmp = data[ihl:]
        typ, code = icmp[0], icmp[1]
        res = None
        if typ == 0:                                    # echo reply
            rid, rseq = struct.unpack("!HH", icmp[4:8])
            if (rid, rseq) != (ident, seq) or src != dst:
                continue
            body = icmp[8:]
            ok = checksum(icmp) == 0 and body == payload and check_tag(body, ident, seq, ttl)
            res = {"kind": "echo", "verify": "FULL" if ok else "MISMATCH"}
        elif typ in (11, 3):                            # time exceeded / unreachable
            q = icmp[8:]
            if len(q) < 20 or q[9] != 1 or socket.inet_ntoa(q[16:20]) != dst:
                continue
            qihl = (q[0] & 0x0F) * 4
            qi = q[qihl:]
            if len(qi) < 8 or qi[0] != 8:
                continue
            qid, qseq = struct.unpack("!HH", qi[4:8])
            if (qid, qseq) != (ident, seq):
                continue
            qbody = qi[8:]
            if len(qbody) >= BODY_LEN + TAG_LEN and check_tag(qbody, ident, seq, ttl) \
                    and payload.startswith(qbody[:len(payload)]):
                v = "FULL"
            elif qbody and payload.startswith(qbody):
                v = f"PARTIAL({len(qbody)}B)"
            elif qbody:
                v = "MISMATCH"
            else:
                v = "ID/SEQ"                            # RFC 792 minimum quote: 8 bytes
            res = {"kind": "ttl-exceeded" if typ == 11 else f"unreach/{code}", "verify": v}
        else:
            continue
        rtt_user = (t_user1 - t_user0) / 1e6
        rtt_kern = (t_rx - t_tx) / 1e6 if (t_rx and t_tx) else None
        res.update(seq=seq, ttl=ttl, src=src, reply_ttl=reply_ttl, status="ok",
                   rtt_kernel_ms=rtt_kern, rtt_user_ms=rtt_user,
                   rtt_ms=rtt_kern if rtt_kern is not None else rtt_user)
        return res


# ---------- geometry ----------
def great_circle(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))

fiber_rtt_ms = lambda km: 2 * km * N_FIBER / C_KM_S * 1000
max_km = lambda rtt: rtt / 2 / 1000 * C_KM_S / N_FIBER
guess_hops = lambda t: next(i - t for i in (32, 64, 128, 255) if t <= i)

def coords(s):
    lat, lon = (float(x) for x in s.split(","))
    return lat, lon


# ---------- main ----------
def open_sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    try:
        s.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPING, F_TX_SW | F_RX_SW | F_SW | F_TSONLY)
        return s, True
    except OSError:
        return s, False

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["ping", "trace"])
    ap.add_argument("host")
    ap.add_argument("-c", "--count", type=int, default=20, help="ping: probes per flow")
    ap.add_argument("-i", "--interval", type=float, default=1.0, help="mean gap (s), jittered +/-50%%")
    ap.add_argument("-s", "--size", type=int, default=56, help="payload bytes (min %d)" % MIN_PAYLOAD)
    ap.add_argument("-q", "--queries", type=int, default=3, help="trace: probes per hop per flow")
    ap.add_argument("-m", "--max-ttl", type=int, default=30)
    ap.add_argument("-W", "--timeout", type=float, default=2.0)
    ap.add_argument("--flows", type=int, default=1, help="distinct ECMP flows to explore")
    ap.add_argument("--from", dest="src", type=coords, help="LAT,LON of this host")
    ap.add_argument("--to", dest="dst", type=coords, help="LAT,LON of target")
    ap.add_argument("--csv")
    a = ap.parse_args()

    dst = socket.gethostbyname(a.host)
    sock, kts = open_sock()
    ident = random.randrange(1, 0xFFFF)
    seq = random.randrange(0, 0xFFFF)
    flows = random.sample(range(1, 0xFFFF), a.flows)
    print(f"{a.mode} {a.host} ({dst})  id={ident}  flows={a.flows}  "
          f"timestamps={'kernel SO_TIMESTAMPING' if kts else 'user-space only'}")
    rows = []

    def nxt():
        nonlocal seq
        seq = (seq + 1) & 0xFFFF
        return seq

    def gap():
        time.sleep(random.uniform(0.5, 1.5) * a.interval)

    per_flow = {}
    if a.mode == "ping":
        for fi, fc in enumerate(flows):
            for _ in range(a.count):
                r = probe(sock, dst, ident, nxt(), 64, a.size, fc, a.timeout, kts)
                r["flow"] = fi
                rows.append(r)
                if r["status"] == "ok":
                    per_flow.setdefault(fi, []).append(r["rtt_ms"])
                    ku = f"{r['rtt_kernel_ms']:.3f}" if r["rtt_kernel_ms"] is not None else "-"
                    print(f"flow {fi} seq={r['seq']:5d} {r['src']} ttl={r['reply_ttl']} "
                          f"(~{guess_hops(r['reply_ttl'])} hops back) rtt={ku} ms kernel / "
                          f"{r['rtt_user_ms']:.3f} ms user  [{r['verify']}]")
                else:
                    print(f"flow {fi} seq={r['seq']:5d} timeout")
                gap()
    else:
        for fi, fc in enumerate(flows):
            print(f"\n-- flow {fi} (checksum 0x{fc:04x}) --")
            for ttl in range(1, a.max_ttl + 1):
                hop, done = [], False
                for _ in range(a.queries):
                    r = probe(sock, dst, ident, nxt(), ttl, a.size, fc, a.timeout, kts)
                    r["flow"] = fi
                    rows.append(r)
                    hop.append(r)
                    done |= r.get("kind") == "echo"
                    time.sleep(random.uniform(0.02, 0.08))
                ok = [h for h in hop if h["status"] == "ok"]
                if ok:
                    srcs = sorted({h["src"] for h in ok})
                    try:
                        name = socket.gethostbyaddr(srcs[0])[0]
                    except OSError:
                        name = ""
                    rt = " ".join(f"{h['rtt_ms']:.3f}" for h in ok)
                    ver = ",".join(sorted({h["verify"] for h in ok}))
                    print(f"{ttl:2d}  {' / '.join(srcs)} {name}  {rt} ms  [{ver}]")
                else:
                    print(f"{ttl:2d}  *")
                if done:
                    per_flow[fi] = [h["rtt_ms"] for h in ok if h.get("kind") == "echo"]
                    break

    # ---- summary / shortest route ----
    print("\n== summary ==")
    good = [r for r in rows if r["status"] == "ok"]
    full = sum(1 for r in good if r["verify"] == "FULL")
    bad = sum(1 for r in good if r["verify"] == "MISMATCH")
    print(f"probes {len(rows)}  replies {len(good)}  verified FULL {full}  MISMATCH {bad}"
          + ("   <-- payload tampering or a box answering for the target!" if bad else ""))
    if not per_flow:
        return
    best_flow, best = min(((f, min(v)) for f, v in per_flow.items() if v), key=lambda x: x[1])
    for f, v in sorted(per_flow.items()):
        if v:
            print(f"flow {f}: n={len(v)} min {min(v):.3f}  median {statistics.median(v):.3f}  "
                  f"stdev {statistics.pstdev(v):.3f} ms" + ("   <- shortest" if f == best_flow else ""))
    print(f"shortest observed RTT {best:.3f} ms -> target is at most {max_km(best):,.0f} km away "
          f"(fibre, n={N_FIBER}), {best/2/1000*C_KM_S:,.0f} km at vacuum c")
    if a.src and a.dst:
        gc = great_circle(a.src, a.dst)
        fl = fiber_rtt_ms(gc)
        print(f"great-circle {gc:,.1f} km -> fibre RTT floor {fl:.3f} ms; "
              f"path inflation {best/fl:.2f}x" + ("   ANOMALY: faster than fibre on the "
              "great circle - check who replied / coordinates" if best < fl else ""))

    if a.csv:
        keys = ["flow", "seq", "ttl", "status", "kind", "src", "reply_ttl",
                "rtt_kernel_ms", "rtt_user_ms", "rtt_ms", "verify"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"saved {a.csv}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("needs root (raw ICMP socket): sudo " + " ".join(sys.argv))
    main()
