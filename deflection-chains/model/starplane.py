# Stereographic star chart from the north celestial pole: the whole sky on an infinite plane,
# south pole at infinity. Drawn out to dec -60 (edge), fading out from dec -20 to the edge.
import json, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
N=4096; H=N/2; DEC_EDGE=-45
REDGE=2*math.tan(math.radians((90-DEC_EDGE)/2))
def rr(dec): return 2*math.tan(math.radians((90-dec)/2))/REDGE*H
def xy(ra,dec):
    r=rr(dec); a=math.radians(ra); return H+r*math.cos(a), H-r*math.sin(a)
img=Image.new('RGBA',(N,N),(8,12,30,255)); d=ImageDraw.Draw(img)
rng=np.random.default_rng(7)
for _ in range(14000):
    x,y=rng.uniform(0,N,2); v=int(rng.uniform(40,110)); d.point((x,y),fill=(v,v,v+15,180))
grid=Image.new('RGBA',(N,N),(0,0,0,0)); g=ImageDraw.Draw(grid)
for dec in (60,30,0):
    r=rr(dec); g.ellipse([H-r,H-r,H+r,H+r],outline=(90,120,170,70 if dec else 120),width=4 if dec else 6)
for h in range(12):
    a=math.radians(h*30); g.line([H,H,H+H*1.5*math.cos(a),H-H*1.5*math.sin(a)],fill=(90,120,170,45),width=3)
L=json.load(open('lines.json'))
for f in L['features']:
    for line in f['geometry']['coordinates']:
        if min(p[1] for p in line)<DEC_EDGE: continue
        g.line([xy(ra,dec) for ra,dec in line],fill=(120,160,220,70),width=2)
img=Image.alpha_composite(img,grid)
glow=Image.new('RGBA',(N,N),(0,0,0,0)); gl=ImageDraw.Draw(glow)
core=Image.new('RGBA',(N,N),(0,0,0,0)); co=ImageDraw.Draw(core)
def col(bv):
    try: bv=float(bv)
    except: bv=0.6
    t=max(0,min(1,(bv+0.3)/2.0)); return (int(170+85*t),int(200+30*(1-abs(t-0.4))),int(255-120*t))
for s in json.load(open('stars.6.json'))['features']:
    ra,dec=s['geometry']['coordinates']; m=s['properties']['mag']
    if dec<DEC_EDGE: continue
    x,y=xy(ra,dec); r=max(1.2,6.5-1.05*m); c=col(s['properties'].get('bv'))
    co.ellipse([x-r,y-r,x+r,y+r],fill=c+(255,))
    if m<3.5: R=r*2.6; gl.ellipse([x-R,y-R,x+R,y+R],fill=c+(110,))
img=Image.alpha_composite(img,glow.filter(ImageFilter.GaussianBlur(9))); img=Image.alpha_composite(img,core)
# alpha: circular, fading from dec -20 to the edge (toward infinity)
yy,xx=np.mgrid[0:N,0:N]; r=np.hypot(xx-H,yy-H)
r0=rr(-15); a=np.clip(1-(r-r0)/(H-r0),0,1)**1.6
arr=np.array(img); arr[...,3]=(arr[...,3]*a).astype(np.uint8)
Image.fromarray(arr).save('starplane.png',optimize=True)
Image.fromarray(arr).convert('RGBA').resize((1024,1024)).save('starplane_small.png')
print('equator radius fraction', rr(0)/H)
