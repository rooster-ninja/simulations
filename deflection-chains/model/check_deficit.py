import trimesh,numpy as np,json,sys,glob,os
R=json.load(open(sys.argv[1]))['R_mm']
D=0;AI=0;NV=0;rows=[];wt=True
for fn in sorted(glob.glob(sys.argv[2]+'/*.stl')):
  g=trimesh.load(fn); wt&=g.is_watertight and g.is_winding_consistent and g.volume>0
  F=g.faces[g.face_normals[:,2]>0.05]; V=g.vertices
  sub=trimesh.Trimesh(V,F,process=False)
  u,c=np.unique(sub.edges_sorted,axis=0,return_counts=True); bv=set(u[c==1].ravel())
  ang=np.zeros(len(V)); bary=np.zeros(len(V)); ar=trimesh.triangles.area(V[F])
  for f,a_ in zip(F,ar):
    P=V[f]
    for i in range(3):
      a=P[(i+1)%3]-P[i]; b=P[(i+2)%3]-P[i]
      ang[f[i]]+=np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1)); bary[f[i]]+=a_/3
  iv=[v for v in set(F.ravel()) if v not in bv]
  d=sum(2*np.pi-ang[v] for v in iv); A=sum(bary[v] for v in iv)
  name=os.path.basename(fn)[:-4].replace('_',' ')
  if iv: rows.append([name,len(iv),d/A*1e8])
  D+=d;AI+=A;NV+=len(iv)
rows.sort(key=lambda r:-r[1])
out=dict(R_mm=R,K_true_mm2=1/R**2,rows=rows,NV=NV,deficit_rad=D,deficit_arcsec=D*206264.806,area_mm2=AI,K_est_mm2=D/AI,ratio=(D/AI)*R**2,watertight=bool(wt))
json.dump(out,open(sys.argv[3],'w'),indent=1); print(json.dumps(out,indent=1))
