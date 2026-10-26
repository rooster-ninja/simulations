"""Minimum-error position for each quasar on the fixed disc layout (WIP).

For every quasar and every 2 sidereal hours, the quasar may sit anywhere
(any x, y, any height 1 m to 100 000 000 km). We solve for the single point that
minimises the angular error to the real sight lines of all observers who can see it
above 5°. Output: data/disc_best_fit.csv
"""
import csv, os
import numpy as np
from scipy.optimize import least_squares
from model import QUASARS, OBSERVERS, local_frame, sight_lines, angular_residuals

here = os.path.dirname(os.path.abspath(__file__))
frames = {n: local_frame(la, lo) for n, la, lo in OBSERVERS}
rows = []
for q in QUASARS:
    for g in range(0, 360, 30):
        rays = sight_lines(q, g, frames)
        if len(rays) < 3:
            continue
        M = np.zeros((3, 3)); v = np.zeros(3)
        for _, o, d in rays:
            P = np.eye(3) - np.outer(d, d); M += P; v += P @ o
        x0 = np.linalg.lstsq(M, v, rcond=None)[0]
        best = None
        for z in (abs(x0[2]) + 100, 1000, 5000, 30000):
            r = least_squares(lambda x: angular_residuals(x, rays), np.array([x0[0], x0[1], z]),
                              bounds=([-1e7, -1e7, 0.001], [1e7, 1e7, 1e8]), x_scale='jac')
            if best is None or r.cost < best.cost:
                best = r
        e = np.degrees(np.arcsin(np.clip(angular_residuals(best.x, rays), 0, 1)))
        rows.append([q[0], g, *np.round(best.x).astype(int), round(float(np.sqrt(np.mean(e**2))), 2),
                     round(float(e.max()), 2), len(rays)])
with open(os.path.join(here, '..', 'data', 'disc_best_fit.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['quasar', 'gmst_deg', 'x_km', 'y_km', 'height_km', 'rms_err_deg', 'max_err_deg', 'n_observers'])
    w.writerows(rows)
e = np.array([r[5] for r in rows])
print(f'{len(rows)} fits; rms error median {np.median(e):.1f} deg, min {e.min():.1f} deg')
