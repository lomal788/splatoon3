"""Original Phive stage velocity bridge -> native setter; independent f32 comparison, fixture native motion cap100."""
import json,struct,random,math
from pathlib import Path
import numpy as np
from r8_physics_native_uc import init_native,make_world
u,errors=init_native();W,D,A,e=make_world(u,mode=0);errors+=e
V=u.alloc(0x20);P=u.alloc(8);u.wf(V+0x14,.7)
errors.append(['capsule',u.call(0x7100930b40,V,V+0x10,0,0,0,0,0,0,P,fargs=(.6,))]);Shape=u.rq(P)
C=u.alloc(0xc0);errors.append(['cinfo',u.call(0x71009e64f8,C)]);u.wq(C,Shape);u.w8(C+0x28,2);u.wf(C+0x70,100)
errors.append(['body',u.call(0x71009c78f0,W,C,0xffffffffffffffff)]);H=u.x(0)
HP=u.alloc(8);u.wq(HP,H);errors.append(['addBody',u.call(0x71009c6a70,W,HP,1,0,0)])
N=u.rq(W+0x38)+(H&0xffffff)*0xc0;M=u.rq(W+0x150)+u.r32(N+0x80)*0x80
G=u.alloc(0x200);F=u.alloc(0x200);Ch=u.alloc(0x400);Body=u.alloc(0x400);O=u.alloc(0x20);Lin=u.alloc(16);Ang=u.alloc(16)
u.wq(0x710599dfa8,G);u.wq(G+0xe8,F);u.wq(F+0xb8,Ch);u.wq(Ch+0xc0,W);u.wq(O+8,H);u.wq(Body+0x90,O);u.wq(Body+0x88,4)
f=np.float32
EPS=f(2**-23);fac=f(1-f(2*EPS));rng=random.Random(0x8c50);mismatch=[];traces=[]
inputs=[]
for i in range(1000):
 old=[f(rng.uniform(-60,60)) for _ in range(3)];v=[f(rng.uniform(-250,250)) for _ in range(3)];inputs.append((old,v))
for x in [0.,1.,1e-6,1e-10]:
 for d in [0.,float(EPS)/2,float(EPS),float(EPS)*1.01,-float(EPS)]:inputs.append(([f(x)]*3,[f(x+d)]*3))
inputs += [([f(1)]*3,[f(x),f(0),f(0)]) for x in [float('nan'),float('inf'),-float('inf'),100.,100.00001,0.] for flag in range(4)]
for i,(old,v) in enumerate(inputs):
 cap=f(100);u.mu.mem_write(M+0x60,struct.pack('<4f',*old,cap));u.mu.mem_write(Lin,struct.pack('<4f',*v,0));u.mu.mem_write(M+0x70,struct.pack('<4f',0,0,0,100))
 flag=i%4;linflag=flag&1;angflag=(flag>>1)&1
 # Same scalar reference only identity orientation/zero angular input; both and lone linear must use same linear semantics.
 out=old[:]
 if linflag and not all(abs(f(v[j]-old[j]))<=EPS for j in range(3)):
  with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
   norm=f(f(f(v[0]*v[0])+f(v[1]*v[1]))+f(v[2]*v[2]))
   if norm<=f(cap*cap):out=v[:]
   elif (struct.unpack('<I',struct.pack('<f',norm))[0]^0xffffffff)&0x7fc00000:
    inv=f(f(1)/f(np.sqrt(norm)))
    if (struct.unpack('<I',struct.pack('<f',inv))[0]^0xffffffff)&0x7fc00000:
     k=f(f(cap*inv)*fac);out=[f(a*k) for a in v]
     out=[struct.unpack('<f',struct.pack('<I',0x7fc00000))[0] if math.isnan(a) else a for a in out]
 err=u.call(0x7103c50c7c,O,Lin,linflag,Ang,angflag,Body,0,1)
 got=bytes(u.mu.mem_read(M+0x60,12));expected=struct.pack('<3f',*out)
 if err or got!=expected:mismatch.append(dict(i=i,error=err,flag=flag,old=[float(x) for x in old],v=[float(x) for x in v],got=got.hex(),expected=expected.hex()))
 if i<4 or i>=1000:traces.append(dict(i=i,flags=[linflag,angflag],result=struct.unpack('<3f',got)))
r=dict(cases=len(inputs),fields=len(inputs)*3,mismatch=mismatch,trace=traces,cap=100,eps=float(EPS),factor=float(fac),errors=errors,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/physics_native_velocity_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
