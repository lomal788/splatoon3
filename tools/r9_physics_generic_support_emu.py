"""r9 whole original convex support af107c vs independent float32 four-lane picker, including exact tie priority. Finite vertices/count1..64; no NaN or invalid count claim."""
import json,struct,random
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
f=np.float32;u=PhysicsUC();A=u.alloc(0x20);V=u.alloc(0x400);D=u.alloc(0x10);O=u.alloc(0x10);u.wq(A,V);rng=random.Random(0xAF107C);bad=[];fields=0;ties=0;samples=[]
pack=lambda vv:struct.pack('<'+'f'*len(vv),*map(float,vv))
def dot(v,d):return f(f(f(v[0]*d[0])+f(v[1]*d[1]))+f(v[2]*d[2]))
def choose(pts,d):
 n=len(pts);dots=[dot(v,d) for v in pts]
 if n==3:return (0,0,1,1,2,2,2,2)[sum(1<<k for k in range(3) if dots[k]>=max(dots))]
 if n%4==1:values=[dots[0]]*4;ids=[0]*4;start=1
 elif n%4==2:values=[dots[0],dots[1],f(-np.inf),f(-np.inf)];ids=[0,1,2,3];start=2
 else:values=dots[:4];ids=[0,1,2,3];start=3 if n%4==3 else 4
 for j in range(start,n,4):
  for lane in range(4):
   if dots[j+lane]>values[lane]:values[lane]=dots[j+lane];ids[lane]=j+lane
 p=0 if values[0]>=values[1] else 1;q=2 if values[2]>=values[3] else 3
 return ids[p if values[p]>=values[q] else q]
for i in range(8193):
 n=1+i%64;d=[f(rng.randint(-32,32)/16) for _ in range(3)]+[f(0)];pts=[[f(rng.randint(-128,128)/16) for _ in range(3)] for j in range(n)]
 if i%8==0:d=[f(0)]*4
 if i==1:n=8;d=[f(1),f(0),f(0),f(0)];pts=[[f(0)]*3 for j in range(n)];pts[1][0]=pts[4][0]=f(1)
 ds=[dot(v,d) for v in pts];ties+=sum(v==max(ds) for v in ds)>1
 idx=choose(pts,d);expect=pack(pts[idx])+struct.pack('<I',0x3f000000|idx)
 u.w32(A+8,n);u.mu.mem_write(V,pack(sum(pts,[])));u.mu.mem_write(D,pack(d));u.mu.mem_write(O,bytes(16));e=u.call(0x7100af107c,A,D,O,count=100000);got=bytes(u.mu.mem_read(O,16));fields+=4
 if e or got!=expect:bad.append(dict(i=i,n=n,index=idx,error=e,actual=got.hex(),reference=expect.hex(),direction=list(map(float,d))))
 if i<3:samples.append(dict(i=i,n=n,index=idx,actual=got.hex(),reference=expect.hex()))
r=dict(scope=__doc__,cases=8193,fields=fields,tie_cases=int(ties),bad_count=len(bad),bad=bad[:20],samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_support_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k not in ('scope','bad','samples')},ensure_ascii=False))
