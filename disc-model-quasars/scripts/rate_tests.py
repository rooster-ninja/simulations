"""Simple checks behind the WIP page: rotation rates, pole-star heights, hidden-zone speeds."""
import numpy as np
from model import R, D, proj, OBSERVERS

DAY = 23.9345                                  # sidereal day, hours
print('Observed rate: %.3f deg/h' % (360 / DAY))
for dec in (0, 30, 45, 60, 80, 89.35):
    print('  dec %5.2f: %.2f deg/h' % (dec, 360 / DAY * np.cos(dec * D)))

print('\nPole-star height needed for altitude = |latitude| (disc layout)')
for name, la, lo in OBSERVERS:
    pole = np.array([0, -R]) if la >= 0 else np.array([0, R])
    d = np.linalg.norm(proj(la, lo) - pole)
    print(f'  {name:12s} lat {la:6.1f}  d {d:7.0f} km  h {d*np.tan(abs(la)*D):7.0f} km')

print('\nVisible arc / hidden time -> required speeds')
for arc, hid in ((180, 0), (180, 6), (180, DAY/2), (270, 0), (270, 6), (360, 0)):
    vis_t = DAY - hid
    hr = 'instant' if hid == 0 and arc < 360 else ('none' if arc == 360 else '%.2f' % ((360-arc)/hid))
    print(f'  arc {arc:3d} deg, hidden {hid:5.2f} h: visible {arc/vis_t:5.2f} deg/h, hidden {hr}')
