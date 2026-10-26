"""Shared geometry for the stationary-disc quasar test (WIP).

Disc layout (from the original sketch): radius R = 10 002 km (pole-to-equator),
S pole point at the top of the rim (+y), N pole point at the bottom (-y),
equator = horizontal diameter, 0°E on the left edge, 0°W on the right edge,
180° down the centre. Meridians are circular arcs through both pole points;
parallels are circular arcs evenly spaced in latitude.
"""
import numpy as np

R = 10002.0          # disc radius, km
RE = 6371.0          # globe radius used only for comparison distances, km
D = np.pi / 180

# Quasars: name, RA (deg, J2000), Dec (deg, J2000). Approximate values typed from
# memory, good to about an arcminute. Check against ICRF3 / Milliquas before use.
QUASARS = [
    ("3C 273", 187.278, 2.053), ("3C 279", 194.047, -5.789), ("3C 48", 24.422, 33.160),
    ("3C 147", 85.651, 49.852), ("3C 196", 123.400, 48.217), ("3C 286", 202.785, 30.509),
    ("3C 345", 250.745, 39.810), ("3C 454.3", 343.491, 16.148), ("3C 9", 5.105, 15.682),
    ("Twin QSO", 150.337, 55.899), ("Einstein Cross", 340.126, 3.359),
    ("APM 08279", 127.924, 52.755), ("TON 618", 187.104, 31.477), ("Mrk 231", 194.059, 56.874),
    ("H1821+643", 275.489, 64.343), ("PG 1634+706", 248.620, 70.526),
    ("S5 0836+710", 130.352, 70.895), ("ULAS J1342", 205.533, 9.477),
    ("ULAS J1120", 170.006, 6.690), ("PKS 1510-089", 228.211, -9.100),
    ("PKS 1127-145", 172.530, -14.824), ("PKS 1830-211", 278.416, -21.061),
    ("PKS 1921-293", 291.213, -29.242), ("HE 0450-2958", 73.125, -29.893),
    ("PKS 0405-385", 61.746, -38.441), ("PKS 1424-418", 216.985, -42.105),
    ("J0529-4351", 82.316, -43.858), ("PKS 0537-441", 84.710, -44.086),
    ("PKS 0208-512", 32.693, -51.017), ("PKS 0637-752", 98.944, -75.271),
]

# Observers: name, latitude, longitude (deg, east positive)
OBSERVERS = [
    ("Nanton", 50.35, -113.77), ("Edmonton", 53.55, -113.49), ("Denver", 39.74, -104.99),
    ("Mexico City", 19.43, -99.13), ("Quito", -0.18, -78.47), ("Lima", -12.05, -77.04),
    ("Santiago", -33.45, -70.67), ("Buenos Aires", -34.6, -58.38), ("Ushuaia", -54.8, -68.3),
    ("New York", 40.71, -74.0), ("London", 51.51, -0.13), ("Tromso", 69.65, 18.96),
    ("Cairo", 30.04, 31.24), ("Nairobi", -1.29, 36.82), ("Cape Town", -33.92, 18.42),
    ("Mumbai", 19.08, 72.88), ("Singapore", 1.35, 103.82), ("Tokyo", 35.68, 139.69),
    ("Perth", -31.95, 115.86), ("Sydney", -33.87, 151.21), ("Auckland", -36.85, 174.76),
    ("Honolulu", 21.31, -157.86), ("Anchorage", 61.22, -149.9), ("Reykjavik", 64.15, -21.94),
]

MIN_ALT = 5 * D      # sightings below 5° altitude are not used


def _circ3(p1, p2, p3):
    (ax, ay), (bx, by), (cx, cy) = p1, p2, p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / d
    uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / d
    return np.array([ux, uy]), np.hypot(ax - ux, ay - uy)


def proj(lat, lon):
    """Latitude/longitude to disc x, y (km)."""
    lp = (lon - 180) if lon > 0 else (lon + 180)
    lp = -abs(lp) if lon >= 0 else abs(lp)
    y = -R * lat / 90.0
    if abs(lat) > 89.9999:
        return np.array([0.0, y])
    xe, ye, xm = R * np.cos(lat * D), -R * np.sin(lat * D), R * lp / 180.0
    if abs(lat) < 1e-9:
        return np.array([xm, 0.0])
    if abs(lp) < 1e-9:
        return np.array([0.0, y])
    c1, r1 = _circ3((-xe, ye), (0, y), (xe, ye))          # parallel
    c2, r2 = _circ3((0, R), (xm, 0), (0, -R))             # meridian
    d = np.linalg.norm(c2 - c1)
    a = (r1*r1 - r2*r2 + d*d) / (2 * d)
    h = np.sqrt(max(r1*r1 - a*a, 0))
    p = c1 + a * (c2 - c1) / d
    perp = np.array([-(c2 - c1)[1], (c2 - c1)[0]]) / d
    return min((p + h * perp, p - h * perp), key=np.linalg.norm)


def great_circle(a, b):
    la1, lo1, la2, lo2 = (a[0]*D, a[1]*D, b[0]*D, b[1]*D)
    return 2 * RE * np.arcsin(np.sqrt(np.sin((la2-la1)/2)**2 +
                                      np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2))


def altaz(ra, dec, lat, lon, gmst):
    """Real observed altitude/azimuth (rad), azimuth from north through east.
    gmst = Greenwich sidereal angle in degrees."""
    H, la, de = (gmst + lon - ra) * D, lat * D, dec * D
    alt = np.arcsin(np.sin(la)*np.sin(de) + np.cos(la)*np.cos(de)*np.cos(H))
    az = np.arctan2(-np.cos(de)*np.sin(H),
                    np.cos(la)*np.sin(de) - np.sin(la)*np.cos(de)*np.cos(H))
    return alt, az


def local_frame(lat, lon):
    """Disc position, local north (towards N pole point along the meridian) and east."""
    e = 1e-3
    p = proj(lat, lon)
    n = proj(lat + e, lon) - proj(lat - e, lon); n /= np.linalg.norm(n)
    E = proj(lat, lon + e) - proj(lat, lon - e); E /= np.linalg.norm(E)
    return np.array([p[0], p[1], 0.0]), n, E


def sight_lines(q, gmst, frames):
    """Rays (origin, unit direction) from every observer who sees quasar q above MIN_ALT."""
    out = []
    for name, lat, lon in OBSERVERS:
        alt, az = altaz(q[1], q[2], lat, lon, gmst)
        if alt < MIN_ALT:
            continue
        o, n, E = frames[name]
        h = np.cos(alt) * (np.cos(az) * n + np.sin(az) * E)
        out.append((name, o, np.array([h[0], h[1], np.sin(alt)])))
    return out


def angular_residuals(x, rays):
    """Sine of the angle between each observed ray and the direction to point x."""
    O = np.array([o for _, o, _ in rays]); Dd = np.array([d for _, _, d in rays])
    V = x - O; V /= np.linalg.norm(V, axis=1)[:, None]
    return np.linalg.norm(np.cross(V, Dd), axis=1)
