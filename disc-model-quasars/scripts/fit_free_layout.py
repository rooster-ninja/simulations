"""Most general flat-plane test (WIP): free city layout AND free quasar positions.

Unknowns: every observer's x, y on the plane and its local-north direction, plus every
quasar's 3D position at each 2-sidereal-hour step. 24 observers, 30 quasars,
12 time steps. Fitted to the real alt/az sightings (above 5°) by sparse least
squares, from two different starting layouts. Gauge: Nanton fixed at the origin
with north along +x. The scale is free; it is set afterwards to best match
real distances. Output: data/free_layout_fit.json and a summary on stdout.
"""
import json, os, time
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from model import QUASARS, OBSERVERS, D, MIN_ALT, altaz, local_frame, great_circle

here = os.path.dirname(os.path.abspath(__file__))
names = [o[0] for o in OBSERVERS]; NC = len(OBSERVERS)
objs, obs = [], []
for q in QUASARS:
    for g in range(0, 360, 30):
        rows = [(ci, *altaz(q[1], q[2], la, lo, g)) for ci, (_, la, lo) in enumerate(OBSERVERS)]
        rows = [r for r in rows if r[1] >= MIN_ALT]
        if len(rows) >= 3:
            k = len(objs); objs.append((q[0], g))
            obs += [(k, ci, a, z) for ci, a, z in rows]
NO, NOBS = len(objs), len(obs)
oi, ci = np.array([o[0] for o in obs]), np.array([o[1] for o in obs])
ALT, AZ = np.array([o[2] for o in obs]), np.array([o[3] for o in obs])


def unpack(p):
    return p[:2*NC].reshape(NC, 2), p[2*NC:3*NC], p[3*NC:].reshape(NO, 3)


def obsvec(T):
    th = T[ci]
    n = np.stack([np.cos(th), np.sin(th)], 1); e = np.stack([-np.sin(th), np.cos(th)], 1)
    h = np.cos(ALT)[:, None] * (np.cos(AZ)[:, None] * n + np.sin(AZ)[:, None] * e)
    return np.column_stack([h, np.sin(ALT)])


def res(p):
    C, T, X = unpack(p)
    d = obsvec(T); O = np.column_stack([C[ci], np.zeros(NOBS)])
    v = X[oi] - O; v /= np.linalg.norm(v, axis=1)[:, None]
    r = np.linalg.norm(np.cross(v, d), axis=1)
    r = np.where(np.sum(v * d, 1) < 0, 2 - r, r)          # penalise pointing backwards
    return np.concatenate([r, [1e3*C[0, 0]/1e4, 1e3*C[0, 1]/1e4, 1e3*T[0]]])


def sparsity():
    S = lil_matrix((NOBS + 3, 3*NC + 3*NO), dtype=int)
    for i in range(NOBS):
        S[i, 2*ci[i]] = S[i, 2*ci[i]+1] = S[i, 2*NC+ci[i]] = 1
        for k in range(3):
            S[i, 3*NC + 3*oi[i] + k] = 1
    S[NOBS, 0] = S[NOBS+1, 1] = S[NOBS+2, 2*NC] = 1
    return S


def gauge(C, T):
    C = C - C[0]; rot = -T[0]
    R2 = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]])
    return C @ R2.T, T + rot


def run(C0, T0, label):
    d0 = obsvec(T0); X0 = []
    for k in range(NO):
        m = oi == k; M = np.zeros((3, 3)); v = np.zeros(3)
        for o2, dd in zip(C0[ci[m]], d0[m]):
            P = np.eye(3) - np.outer(dd, dd); M += P; v += P @ np.array([*o2, 0])
        x = np.linalg.lstsq(M, v, rcond=None)[0]; x[2] = max(abs(x[2]), 500); X0.append(x)
    p0 = np.concatenate([C0.ravel(), T0, np.array(X0).ravel()])
    t = time.time()
    r = least_squares(res, p0, jac_sparsity=sparsity(), x_scale='jac', max_nfev=4000)
    rr = res(r.x)[:NOBS]
    print(f'{label}: rms {np.degrees(np.sqrt(np.mean(rr**2))):.2f} deg, '
          f'median {np.degrees(np.median(rr)):.2f} deg ({time.time()-t:.0f} s)')
    return r.x, rr


frames = {n: local_frame(la, lo) for n, la, lo in OBSERVERS}
CA = np.array([frames[n][0][:2] for n in names]); TA = np.array([np.arctan2(frames[n][1][1], frames[n][1][0]) for n in names])
pA = run(*gauge(CA, TA), 'start = disc layout')
aeq = lambda la, lo: np.array([(90-la)*111.19*np.sin(lo*D), -(90-la)*111.19*np.cos(lo*D)])
CB = np.array([aeq(la, lo) for _, la, lo in OBSERVERS]); TB = np.array([np.arctan2(-c[1], -c[0]) for c in CB])
pB = run(*gauge(CB, TB), 'start = north-centred azimuthal equidistant')
p, rr = min((pA, pB), key=lambda x: np.mean(x[1]**2))
C, T, X = unpack(p)
I, J = np.triu_indices(NC, 1)
dm = np.linalg.norm(C[I] - C[J], axis=1)
dg = np.array([great_circle(OBSERVERS[i][1:], OBSERVERS[j][1:]) for i, j in zip(I, J)])
s = np.sum(dm*dg) / np.sum(dm*dm); ratio = dm*s/dg
pc = np.degrees(rr)
print(f'flat/globe distance ratio: median {np.median(ratio):.2f}, range {ratio.min():.2f}-{ratio.max():.2f}')
json.dump(dict(
    rms_deg=float(np.sqrt(np.mean(pc**2))), median_deg=float(np.median(pc)), p90_deg=float(np.percentile(pc, 90)),
    cities=[dict(name=names[i], x_km=float(C[i, 0]*s), y_km=float(C[i, 1]*s), north_rad=float(T[i]),
                 rms_deg=float(np.sqrt(np.mean(pc[ci == i]**2)))) for i in range(NC)],
    pairs=[dict(a=names[i], b=names[j], globe_km=float(g), flat_km=float(d*s)) for i, j, g, d in zip(I, J, dg, dm)],
    quasars=[dict(name=objs[k][0], gmst_deg=objs[k][1], x_km=float(X[k, 0]*s), y_km=float(X[k, 1]*s),
                  height_km=float(X[k, 2]*s)) for k in range(NO)]),
    open(os.path.join(here, '..', 'data', 'free_layout_fit.json'), 'w'), indent=1)
