// ---- Peak chord curvature engine. Units: km. u = signed curvature of the reference sphere (1/R; 0 = flat). ----
const R0=6371.0087714;
const BASE=[ // the triangle: one observer, two peaks
  {n:"Nanton",lat:50.349,lon:-113.772,h:1021,kind:"obs",approx:true},
  {n:"Mount Burke",lat:50.29,lon:-114.5244444,h:2535,kind:"peak"},
  {n:"Plateau Mountain",lat:50.207957,lon:-114.517108,h:2515,kind:"peak"}];
const PAIRS3=[[0,1],[0,2],[1,2]], PAIRS=[[0,1],[0,2],[1,2],[0,3],[1,3],[2,3]];
function mk(s){return function(){s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function gauss(r){let a=0,b=0;while(!a)a=r();while(!b)b=r();return Math.sqrt(-2*Math.log(a))*Math.cos(2*Math.PI*b);}
function xyz(s){const a=s.lat*Math.PI/180,o=s.lon*Math.PI/180,r=R0+s.h/1000;return[r*Math.cos(a)*Math.cos(o),r*Math.cos(a)*Math.sin(o),r*Math.sin(a)];}
const dist3=(p,q)=>Math.hypot(p[0]-q[0],p[1]-q[1],p[2]-q[2]);
// constant-curvature trig, stable through K = 0
function S(x,K){const z=K*x*x;if(Math.abs(z)<1e-10)return x*(1-z/6);return K>0?Math.sin(Math.sqrt(K)*x)/Math.sqrt(K):Math.sinh(Math.sqrt(-K)*x)/Math.sqrt(-K);}
function Si(y,K){const z=K*y*y;if(Math.abs(z)<1e-10)return y*(1+z/6);return K>0?Math.asin(Math.min(1,Math.sqrt(K)*y))/Math.sqrt(K):Math.asinh(Math.sqrt(-K)*y)/Math.sqrt(-K);}
const Vk=(x,K)=>2*S(x/2,K)**2;
// a chord between stations at heights h1, h2 above a sphere of signed curvature u -> distance along that surface
function arcFromChord(c,h1,h2,u){const W=(c*c-(h1-h2)**2)/(2*(1+u*h1)*(1+u*h2));return 2*Si(Math.sqrt(Math.max(0,W)/2),u*u);}
function solve4(M,b){const A=M.map((r,i)=>r.concat([b[i]]));for(let c=0;c<4;c++){let p=c;for(let r=c+1;r<4;r++)if(Math.abs(A[r][c])>Math.abs(A[p][c]))p=r;[A[c],A[p]]=[A[p],A[c]];
  for(let r=0;r<4;r++){if(r===c)continue;const f=A[r][c]/A[c][c];for(let k=c;k<5;k++)A[r][k]-=f*A[c][k];}}return A.map((r,i)=>r[4]/r[i]);}
// four points on a surface of curvature K satisfy  1ᵀ V⁻¹ 1 = K,  V_ij = V_K(s_ij).  F(u) = 1ᵀV⁻¹1 − u²; F = 0 at the right u.
function F(c,h,u){const K=u*u,M=[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];
  PAIRS.forEach(([i,j],k)=>{M[i][j]=M[j][i]=Vk(arcFromChord(c[k],h[i],h[j],u),K);});const x=solve4(M,[1,1,1,1]);return x[0]+x[1]+x[2]+x[3]-K;}
function solveU(c,h){let u0=0,u1=1/R0,f0=F(c,h,u0),f1=F(c,h,u1);
  for(let i=0;i<25&&Math.abs(u1-u0)>1e-14;i++){if(f1===f0)break;const u2=u1-f1*(u1-u0)/(f1-f0);u0=u1;f0=f1;u1=Math.max(-20/R0,Math.min(20/R0,u2));f1=F(c,h,u1);}
  return Math.abs(f1)<1e-12?u1:NaN;}
function stations(D){return BASE.concat([D]);}
function trueChords(st){const P=st.map(xyz);return PAIRS.map(([i,j])=>dist3(P[i],P[j]));}
function campaign(st,r,o){const b=gauss(r)*o.bias/1000;
  const c=trueChords(st).map(L=>L+L**3*(0.25/R0)**2/24+L*gauss(r)*o.ppm*1e-6+gauss(r)*o.sig/1000+b);
  const h=st.map(s=>s.h/1000+gauss(r)*o.hs/1000);return{c,h,u:solveU(c,h)};}
function stats(a){const f=a.filter(Number.isFinite),m=f.reduce((s,x)=>s+x,0)/f.length;return{m,s:Math.sqrt(f.reduce((s,x)=>s+(x-m)**2,0)/Math.max(1,f.length-1)),n:f.length};}
function monte(st,o,N,seed){const r=mk(seed),U=[];for(let i=0;i<N;i++)U.push(campaign(st,r,o).u);return stats(U);}
// quick linear error estimate of u for planning the fourth station
function planZ(st,o){const c=trueChords(st),h=st.map(s=>s.h/1000),f0=F(c,h,0),e=1e-7;let v=0;
  c.forEach((L,k)=>{const c2=c.slice();c2[k]+=e;const g=(F(c2,h,0)-f0)/e;v+=(g*Math.hypot(o.sig*1e-3,L*o.ppm*1e-6))**2;});
  h.forEach((x,k)=>{const h2=h.slice();h2[k]+=e;const g=(F(c,h2,0)-f0)/e;v+=(g*o.hs*1e-3)**2;});
  const cb=c.map(x=>x+e);v+=(((F(cb,h,0)-f0)/e)*o.bias*1e-3)**2;
  return{z:Math.abs(f0)/Math.sqrt(v),maxL:Math.max(...c)};}

if(typeof module!=='undefined')module.exports={BASE,PAIRS,monte,planZ,stations,campaign,solveU,trueChords,R0,mk};
