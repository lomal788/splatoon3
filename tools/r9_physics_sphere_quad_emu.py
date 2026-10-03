"""Original full sphere→quad specialized sweep exploratory fixture. Collector capture is output boundary; no shape/query arithmetic stub."""
import struct,json
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import init_native
u,errors=init_native();mu=u.mu
Center=u.alloc(0x10);Out=u.alloc(8);mu.reg_write(UC_ARM64_REG_X8,Out);errors.append(['originalSphere',u.call(0x710092efbc,Center,0,fargs=(.5,))]);SA=u.rq(Out)
SB=u.alloc(0xc0);u.w8(SB+0x18,4);mu.mem_write(SB+0x1a,struct.pack('<H',1));u.w32(SB+0x40,0x40);V=SB+0x80
verts=[(-1,0,-1),(-1,0,1),(1,0,1),(1,0,-1)];mu.mem_write(V,struct.pack('<12f',*sum((list(v) for v in verts),[])))
IA=u.alloc(0x60);IB=u.alloc(0x60);M=u.alloc(0x40);mu.mem_write(M,struct.pack('<16f',1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1));W=u.alloc(0x40);mu.mem_write(W,struct.pack('<16f',1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1));u.wq(IA+0x20,W);u.wq(IB+0x20,W)
for I in (IA,IB):mu.mem_write(I+0x40,struct.pack('<4f',1,1,1,1))
Q=u.alloc(0xb0);Ctx=u.alloc(0x40);Tag=u.alloc(0x10);u.wq(Q+0x38,SA);u.wf(Q+0x78,.001);Meta=u.alloc(0x30);VT=u.alloc(0x40);CB=u.alloc(0x10);mu.mem_write(CB,bytes.fromhex('c0035fd6'));u.wq(VT+0x28,CB);u.wq(Meta,VT);mu.mem_write(Meta+0x10,struct.pack('<2f',1,1));records=[]
def capture(mu,p,size,data):
 addr=mu.reg_read(UC_ARM64_REG_X1);raw=bytes(mu.mem_read(addr,0x80));records.append(raw.hex())
mu.hook_add(UC_HOOK_CODE,capture,begin=CB,end=CB)

import numpy as np,random
f=np.float32;rng=random.Random(0x94ae10);F=lambda x:f(x);pk=lambda x:struct.pack('<'+'f'*len(x),*map(float,x))
def add(a,b):return f(f(a)+f(b))
def sub(a,b):return f(f(a)-f(b))
def mul(a,b):return f(f(a)*f(b))
def div(a,b):return f(f(a)/f(b))
def dot(a,b):return add(add(mul(a[0],b[0]),mul(a[1],b[1])),mul(a[2],b[2]))
def cross(a,b):return [sub(mul(a[1],b[2]),mul(a[2],b[1])),sub(mul(a[2],b[0]),mul(a[0],b[2])),sub(mul(a[0],b[1]),mul(a[1],b[0]))]
def norm(v):
 d=f(np.sqrt(dot(v,v)));return [div(x,d) for x in v]+[f(0)]
def ref(o,d,r,cap):
 candidates=[]
 # Face candidate: original sign xor uses comparison sep<0, not copy-sign for -0.
 ny=f(-1) if o[1]<0 else f(1);closing=mul(d[1],ny);gap=sub(r,abs(o[1]))
 if abs(o[1])>add(r,f(.001)) and (not(closing<0 and gap<=0) or div(gap,closing)>=cap):return []
 if closing<0 and gap<=0:
  t=div(gap,closing)
  if abs(o[0])<=1 and abs(o[2])<=1:candidates.append((t,'face',-1))
 # Four original vertex and infinite-edge quadratic roots; edge coordinate gate in squared-length units.
 for k in range(4):
  a=list(map(f,verts[k]));b=list(map(f,verts[(k+1)&3]));e=[sub(y,x) for x,y in zip(a,b)];m=[sub(x,y) for x,y in zip(o,a)];ee=dot(e,e);invEE=div(1,ee)
  mm=mul(dot(m,e),invEE);ve=mul(dot(d,e),invEE);mp=[sub(x,mul(y,mm)) for x,y in zip(m,e)];vp=[sub(x,mul(y,ve)) for x,y in zip(d,e)]
  for kind,M,V in [('vertex',m,d),('edge',mp,vp)]:
   vv=dot(V,V);iv=div(1,vv) if vv else f(0);bq=mul(dot(V,M),iv);res=[sub(x,mul(y,bq)) for x,y in zip(M,V)];dd=dot(res,res)
   if not dd<mul(r,r):continue
   rt=f(np.sqrt(mul(iv,sub(mul(r,r),dd))))
   if rt>-bq:continue
   t=sub(f(-bq),rt)
   if kind=='edge':
    along=add(dot(m,e),mul(dot(d,e),t))
    if not 0<=along<=ee:continue
   candidates.append((t,kind,k))
 candidates=[c for c in candidates if c[0]<cap]
 if not candidates:return []
 # Original priority vertex then edge then face; original bitmap table selects lowest matching lane.
 t=min(c[0] for c in candidates);choice=min((c for c in candidates if c[0]==t),key=lambda c:({'vertex':0,'edge':1,'face':2}[c[1]],c[2]));_,kind,k=choice
 at=[add(x,mul(y,t)) for x,y in zip(o,d)]
 if kind=='face':N=[mul(f(0),ny),ny,mul(f(0),ny),mul(f(0),ny)]
 elif kind=='vertex':N=norm([sub(x,f(y)) for x,y in zip(at,verts[k])])
 else:
  a=list(map(f,verts[k]));e=[sub(f(y),x) for x,y in zip(a,verts[(k+1)&3])];p=[sub(x,y) for x,y in zip(at,a)];N=norm(cross(cross(e,p),e))
 point=[sub(x,mul(r,n)) for x,n in zip(at,N)]+[f(1)]
 # Identity transform sums x+y then z; terms0 can change signed zero.
 normal=[add(add(mul(f(j==0),N[0]),mul(f(j==1),N[1])),mul(f(j==2),N[2])) for j in range(4)]
 return [dict(fraction=float(t),point=pk(point).hex(),normal=pk(normal).hex(),mode=2,feature=kind)]
rows=[];bad=[];fields=0;counts={}
for i in range(2048):
 typ=i%8;r=f(.125+(i%7)*.0625);speed=f(2+(i%9)*.25);cap=f(.5+(i%3)*.25)
 if typ==0:x,z=f(rng.randint(-14,14)/16),f(rng.randint(-14,14)/16)
 elif typ==1:x,z=add(1,mul(r,.5)),f(rng.randint(-12,12)/16)
 elif typ==2:x,z=add(1,mul(r,.375)),add(1,mul(r,.5))
 elif typ==3:x,z=f(2),f(0)
 elif typ==4:x,z=f(0),f(0)
 elif typ==5:x,z=f(-.5),f(.375)
 elif typ==6:x,z=f(-1)-mul(r,.5),f(-.625)
 else:x,z=f(1),f(-1)
 y=f(1+(i%13)*.125);sgn=-1 if typ==5 else 1;o=[x,mul(y,sgn),z];d=[f(0),mul(speed,sgn if typ==4 else -sgn),f(0)]
 u.wf(SA+0x20,r);mu.mem_write(Q+0x50,pk(d+[f(0)]));mu.mem_write(M+0x30,pk(o+[f(0)]));u.wf(Meta+0x10,cap);u.wf(Meta+0x14,cap);u.wf(Ctx+0x18,0);records.clear()
 e=u.call(0x710094ae10,Ctx,Q,IA,SB,Tag,IB,M,0,stack_args=(Meta,0),count=2000000);got=[bytes.fromhex(rr) for rr in records];ex=ref(o,d,r,cap);fields+=1+len(ex)*10
 errs=[]
 if e or len(got)!=len(ex):errs.append('record_count/error')
 for g,refrow in zip(got,ex):
  if g[:16].hex()!=refrow['point']:errs.append('point')
  if g[16:32].hex()!=refrow['normal']:errs.append('normal')
  if g[32:36]!=pk([refrow['fraction']]):errs.append('fraction')
  if struct.unpack_from('<I',g,0x78)[0]!=2:errs.append('mode')
 if errs:bad.append(dict(i=i,origin=list(map(float,o)),delta=list(map(float,d)),radius=float(r),cap=float(cap),error=e,fields=errs,actual=[dict(point=g[:16].hex(),normal=g[16:32].hex(),fraction=struct.unpack_from('<f',g,32)[0],mode=struct.unpack_from('<I',g,0x78)[0]) for g in got],reference=ex))
 for rr in ex:counts[rr['feature']]=counts.get(rr['feature'],0)+1
 if i<16:rows.append(dict(i=i,expected=ex,actual=[g[:36].hex() for g in got]))
out=dict(scope='Whole original094ae10 vs independent f32 axis-aligned quad/vertical finite sweep reference; no initial collector/general oblique proof',cases=2048,fields=fields,features=counts,bad_count=len(bad),bad=bad[:40],samples=rows,init=errors,runtime=dict(null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed));Path('analysis/completion/r9/physics_sphere_quad_emu.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ('bad','samples')},indent=2))
if bad:raise SystemExit(1)
