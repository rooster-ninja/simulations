# Build the embedded terrain for index.html from SRTM 1" Skadi tiles (Terrain Tiles on AWS).
# Usage: python3 build_dem.py N50W115.hgt.gz N50W114.hgt.gz  -> dem_grid.b64, contours.json
import gzip, sys, math, json, base64, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
def load(p):
    b = gzip.open(p).read(); n = int((len(b) / 2) ** 0.5)
    return np.frombuffer(b, dtype=">i2").reshape(n, n).astype(float)
W, E = load(sys.argv[1]), load(sys.argv[2])
M = np.hstack([W[:, :-1], E])                      # lon -115..-113, lat 51 (row 0)..50
LO0, LO1, LA0, LA1, ST = -114.98, -113.55, 50.02, 50.68, 0.004
nx = int(round((LO1 - LO0) / ST)) + 1; ny = int(round((LA1 - LA0) / ST)) + 1
G = np.zeros((ny, nx), dtype=np.int16)
for j in range(ny):
    la = LA1 - j * ST
    for i in range(nx):
        lo = LO0 + i * ST; r = int(round((51 - la) * 3600)); c = int(round((lo + 115) * 3600))
        G[j, i] = int(round(M[max(0, r - 7):r + 8, max(0, c - 7):c + 8].mean()))   # ~15x15 cell mean
open("dem_grid.b64", "w").write(base64.b64encode(G.astype("<i2").tobytes()).decode())
# contours in page coordinates (viewBox 680 x 500, same projection as index.html)
Wd, Hd, PAD = 680, 500, 24; kx = math.cos(50.35 * math.pi / 180)
sc = min((Wd - 2 * PAD) / ((LO1 - LO0) * kx), (Hd - 2 * PAD) / (LA1 - LA0))
X = PAD + (LO0 + np.arange(nx) * ST - LO0) * kx * sc; Y = Hd - PAD - (LA1 - np.arange(ny) * ST - LA0) * sc
Gs = gaussian_filter(G.astype(float), 1.2); out = {}
for name, levels in [("minor", [l for l in range(1000, 3100, 100) if l % 500]), ("major", list(range(1000, 3100, 500)))]:
    cs = plt.contour(X, Y, Gs, levels=levels); paths = []
    for segs in cs.allsegs:
        for s in segs:
            if len(s) < 4: continue
            s = s[::2] if len(s) > 40 else s
            paths.append("M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in s))
    out[name] = " ".join(paths); plt.clf()
json.dump(out, open("contours.json", "w"))
