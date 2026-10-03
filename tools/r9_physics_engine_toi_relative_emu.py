"""r9 whole game four TOI handlers: native capsule-axis conservative advance plus game staging/list. Dynamic-like game matrices previous/current and original local COM getter with zero COM. Native body itself is static fixture; optional filters null. No rotation, generic-simplex closure."""
import json,struct,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
F=make_engine_toi_fixture();u=F['u'];GB=F['GB'];GBB=F['GBB'];Args=F['Args'];P0=F['P0'];P1=F['P1'];Stage=F['Stage'];CL=F['CL'];Points=F['Points'];Entries=F['Entries'];f=np.float32;rng=random.Random(0x5756468)
u.wq(GBB,0x7105756338);u.wq(GB+0x88,4)
query=[]
def capture(mu,p,size,data):
 q=mu.reg_read(UC_ARM64_REG_X1);query[:]=[bytes(mu.mem_read(q,0xb0))]
u.mu.hook_add(UC_HOOK_CODE,capture,begin=0x71009af088,end=0x71009af088)
bad=[];errors=[];samples=[];cases=0;fields=0;hit=miss=0;query_bad=[]
for i in range(256):
 axis=(i%2)*2;sgn=f(1 if i%4<2 else -1);tc=f(rng.randrange(-16,17)/4);tp=f(tc+f(rng.randrange(-4,5)/4));D=f(rng.randrange(7,81)/4);end=f(-rng.randrange(0,17)/4);p0=[f(0)]*3;p1=[f(0)]*3;p0[axis]=f(tc+f(sgn*D));p1[axis]=f(tc+f(sgn*end));shift=f(tp-tc)
 def matrix(t):
  r=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.];r[axis*4+3]=t;return r
 u.mu.mem_write(GB+0xd8,struct.pack('<12f',*matrix(tc)));u.mu.mem_write(GB+0x108,struct.pack('<12f',*matrix(tp)));u.mu.mem_write(P0,struct.pack('<3f',*p0));u.mu.mem_write(P1,struct.pack('<3f',*p1))
 for k,fn in enumerate((0x7103c52d30,0x7103c5368c,0x7103c54140,0x7103c54de4)):
  u.w32(Stage+0x24,0);u.w32(CL+8,0);u.mu.mem_write(Points,bytes(0x400));u.mu.mem_write(Entries,bytes(0x80));query.clear();e=u.call(fn,0,Args,count=5000000);cases+=1
  if e:errors.append(dict(i=i,k=k,error=e));continue
  if k==0:o=f(p0[axis]-tc);dv=f(f(p1[axis]-tc)-o)
  elif k==2:o=f(tp-p0[axis]);dv=f(f(tc+f(p0[axis]-p1[axis]))-tp)
  else:o=f(p0[axis]-tp);dv=f(f(f(p1[axis]+shift)-tp)-o)
  q=query[0];actualO=struct.unpack_from('<f',q,0x40+4*axis)[0];actualD=struct.unpack_from('<f',q,0x50+4*axis)[0]
  if struct.pack('<2f',o,dv)!=struct.pack('<2f',actualO,actualD):query_bad.append(dict(i=i,k=k,expected=[float(o),float(dv)],actual=[actualO,actualD]))
  len2=f(o*o);inv=f(f(1)/f(np.sqrt(len2)));normal=f(o*inv);closing=f(normal*dv);gap=f(f(len2*inv)-f(f(.6)+f(.6)));t=f(0) if gap<=f(.001) else f(f(0)-f(gap/closing));expectedHit=bool(closing<-f(np.finfo(np.float32).eps) and t<=f(1))
  raw=bytes(u.mu.mem_read(Points,0x80));count=u.r32(CL+8);hit+=bool(count);miss+=not bool(count)
  expectedpos=[f(p0[a]+f(t*f(p1[a]-p0[a]))) for a in range(3)];expected=struct.pack('<f',t)+struct.pack('<3f',*expectedpos)
  actual=raw[0x60:0x64]+raw[0x24:0x30];fields+=4 if expectedHit else 0
  expectedCount=2 if expectedHit and gap<=f(0) else int(expectedHit)
  if count!=expectedCount or (expectedHit and (actual!=expected or u.rq(Entries)!=Points)):bad.append(dict(i=i,k=k,axis=axis,tc=float(tc),tp=float(tp),p0=list(map(float,p0)),p1=list(map(float,p1)),expected=expected.hex(),actual=actual.hex(),count=count,raw=raw.hex()))
  samples.append(dict(i=i,k=k,expectedHit=expectedHit,origin=float(o),delta=float(dv),query=q.hex(),staged=raw.hex(),count=count))
r=dict(scope=__doc__,cases=cases,hit=hit,miss=miss,fields=fields,bit_mismatch=bad,query_mismatch=query_bad,errors=errors,samples=samples,init_errors=F['errors'],null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_engine_toi_relative_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(cases=cases,fields=fields,hit=hit,miss=miss,bitbad=len(bad),querybad=len(query_bad),examples=bad[:2],errors=errors,null=r['null'],auto=r['auto'],faults=r['faults'])))
