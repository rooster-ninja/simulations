"""Independent 3-D check of the direction-reduction formula used in dov_correct.py.

Builds each corner's two lines of sight as ECEF vectors, projects them onto the plane
perpendicular to (a) the ellipsoid normal and (b) the plumb line tilted by xi (north) and
eta (east), and differences the two horizontal angles. Compares with the formula value.
"""
import math, numpy as np, sys
sys.argv = ["x"]
import importlib.util
spec = importlib.util.spec_from_file_location("dc", "dov_correct.py"); dc = importlib.util.module_from_spec(spec)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(dc)
from pyproj import Transformer
ecef = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True)
RAD = math.pi / 180 / 3600
def frame(lo, la):
    l, p = math.radians(lo), math.radians(la)
    up = np.array([math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p)])
    east = np.array([-math.sin(l), math.cos(l), 0.0]); north = np.cross(up, east)
    return up, east, north
def hangle(Pv, up, Bv, Cv):
    def proj(v): v = v - up * (v @ up); return v / np.linalg.norm(v)
    b, c = proj(Bv - Pv), proj(Cv - Pv)
    return math.atan2(np.cross(b, c) @ up, b @ c)
worst = 0; n = 0
for t in sorted(dc.out, key=lambda t: -abs(t["d_main"]))[:40]:
    V = t["coords"]; tot = 0
    for i in range(3):
        P, B, C = V[i], V[(i + 1) % 3], V[(i + 2) % 3]
        X = {}
        for q in (P, B, C):
            s = dc.sval(q); X[q] = np.array(ecef.transform(q[0], q[1], s["h_best"] + s["N"]))
        s = dc.sval(P); up, east, north = frame(*P)
        # refraction: lift each target by the light-path bend so the sight line matches the formula's e
        Bv, Cv = X[B].copy(), X[C].copy()
        for q, Qv in ((B, Bv), (C, Cv)):
            d = np.linalg.norm(X[q] - X[P]); Qv += up * (dc.K_REFR * d * d / (2 * 6371000.0))
        plumb = up + (s["xi18"] * north + s["eta18"] * east) * RAD; plumb /= np.linalg.norm(plumb)
        a_ell = hangle(X[P], up, Bv, Cv); a_pl = hangle(X[P], plumb, Bv, Cv)
        # interior angle magnitude change: observed (plumb) minus reduced (ellipsoid)... formula gives reduced - observed
        diff = (abs(a_ell) - abs(a_pl)) / RAD
        tot += diff
    worst = max(worst, abs(tot - t["d_main"])); n += 1
    if n <= 6: print(f'{t["triangle"][:45]:45s} formula {t["d_main"]:+.4f}"  3-D {tot:+.4f}"')
print(f"largest |formula - 3-D| over the {n} biggest corrections: {worst:.4f}\"")
