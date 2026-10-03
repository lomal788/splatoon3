"""r9 original actual MotionProperty13 full native bridge -> original MT contact/integration. Geometry/world wrappers are explicit fixtures. Wrapper lock/unlock use a no-op original RET callback; no shape getter/native create/arithmetic/register/contact callback is substituted. Custom optional body modifier desc+a0 is disabled for this probe, not asserted as actual-game default."""
import json,struct
from pathlib import Path
from r9_physics_motion_property_emu import u,W,D,A,E,WB,MC,rows,errors
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import HEAP,STACK,STACK_SZ

Mat=u.alloc(0x50);errors.append(['materialCtor',u.call(0x7100a507cc,Mat)])
for off in (0x1a,0x1c,0x1e):u.mu.mem_write(Mat+off,b'\0\0')
errors.append(['materialLibrary',u.call(0x7100a4f76c,u.rq(W+0x8a8),Mat)]);MatID=u.x(0)&0xffff
hits={hex(p):0 for p in (0x7100a181fc,0x7100a29f20,0x7100a4b8c8,0x71009d5b68)}
def hit(mu,addr,size,data):
 hits[hex(addr)]+=1
for p in hits:u.mu.hook_add(UC_HOOK_CODE,hit,begin=int(p,16),end=int(p,16))
def cap(a,b,r):
 V=u.alloc(0x20);P=u.alloc(8)
 for j,v in enumerate(a):u.wf(V+j*4,v)
 for j,v in enumerate(b):u.wf(V+0x10+j*4,v)
 errors.append(['capsule',u.call(0x7100930b40,V,V+0x10,0,0,0,0,0,0,P,fargs=(r,))]);return u.rq(P)
def body(shape,pos,vel=(0,0,0),kind=2):
 B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,shape);u.w8(B+0x28,kind);u.wf(B+0x70,100);u.mu.mem_write(B+0xc,struct.pack('<H',MatID))
 for j,v in enumerate(pos):u.wf(B+0x30+j*4,v)
 for j,v in enumerate(vel):u.wf(B+0x50+j*4,v)
 errors.append(['createBody',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
 if kind==2:
  MD=u.alloc(0x30);errors.append(['massDistribution',u.call(0x7100abf6e0,MD,shape,0x7104a81450)])
  for j in range(3):u.wf(MD+0x20+j*4,0)
  errors.append(['setDistribution',u.call(0x71009db37c,W,H,MD,0)])
  errors.append(['setMass',u.call(0x71009d7338,W,H,0,fargs=(100.,))])
 P=u.alloc(8);u.wq(P,H);errors.append(['addBody',u.call(0x71009c6a70,W,P,1,0,0)]);return H
F=body(cap((-10,-.1,0),(10,-.1,0),.1),(0,0,0),kind=0)
# Build actual game Capsule wrapper/backend, then original Character native-body
# bridge 3c4e8c4. It must select special13 regardless of declared SplPlayer index3.
VT=u.alloc(0x100);u.wq(VT+0x28,0x7103c49f00);u.wq(VT+0x30,0x7103c49f00);u.wq(WB,VT)
bridge_trace=[]
def capture_cinfo(mu,pc,size,data):
 if mu.reg_read(UC_ARM64_REG_X0)==W:
  c=mu.reg_read(UC_ARM64_REG_X1)
  bridge_trace.append(dict(pc=hex(pc),cinfo=bytes(mu.mem_read(c,0xc0)).hex(),native_property=struct.unpack('<H',mu.mem_read(c+0x88,2))[0]))
u.mu.hook_add(UC_HOOK_CODE,capture_cinfo,begin=0x71009c78f0,end=0x71009c78f0)
def game_character(pos,vel):
 GCap=u.alloc(0x100);u.wq(GCap,0x7105745788)
 S=u.alloc(0x40);u.mu.mem_write(S+0x20,struct.pack('<7f',0,0,0,0,.7,0,.6))
 errors.append(['original capbackend',u.call(0x7103c243dc,S,0)]);u.wq(GCap+0xf8,u.x(0))
 errors.append(['original capowner',u.call(0x7103c27858,u.rq(GCap+0xf8),GCap)])
 C=u.alloc(0xd0);Nname=u.alloc(16);u.mu.mem_write(Nname,b'charfixture\0');u.wq(C+8,Nname);u.wq(C+0x10,GCap)
 mx=[1.,0.,0.,pos[0],0.,1.,0.,pos[1],0.,0.,1.,pos[2]];u.mu.mem_write(C+0x18,struct.pack('<12f',*mx))
 u.w32(C+0x78,0xffffffff);u.w32(C+0x80,2);u.w32(C+0x84,3);u.wf(C+0x90,100.)
 SI=u.alloc(0x20);errors.append(['whole nativeCharacter bridge',u.call(0x7103c4e8c4,1,C,SI,0)])
 backend=u.x(0);handle=u.rq(backend+8) if backend else 0xffffffff
 V=u.alloc(16);u.mu.mem_write(V,struct.pack('<4f',*vel,0.))
 errors.append(['setLinearVelocity',u.call(u.rq(u.rq(W)+0x198),W,handle,V,0)])
 P=u.alloc(8);u.wq(P,handle);errors.append(['add originalCharacter',u.call(0x71009c6a70,W,P,1,0,0)])
 return handle,backend
H,HB=game_character((0,.45,0),(0,-3,0))
Fast,FB=game_character((100.,3.,0),(300.,0,0))
TG=u.alloc(0x500);errors.append(['taskgraph',u.call(0x7100902bb0,TG)]);TI=u.alloc(0x20);u.wf(TI,1/60);u.wf(TI+4,0);u.w32(TI+8,1)
N=u.rq(W+0x38)+int(H&0xffffff)*0xc0;M=u.rq(W+0x150)+u.r32(N+0x80)*0x80
CTX=u.alloc(0xc0);u.w32(CTX+0x98,1);graphs=[];done=set()
for off in (0x4c8,0x4d0,0x4d8):u.wq(TG+off,0xffffffffffffffff)
def run_graph():
 count=u.r32(TG+0x20);ptr=u.rq(TG+0x18);ep=u.rq(TG+0x328);ec=u.r32(TG+0x330)
 edges=[struct.unpack('<HH',u.mu.mem_read(ep+4*i,4)) for i in range(ec)];log=[]
 for guard in range(count+1):
  ready=[i for i in range(count) if i not in done and all(a in done for a,b in edges if b==i and a<count)]
  if not ready:break
  for i in ready:
   node=ptr+i*0x18;task=u.rq(node);times=struct.unpack('<H',u.mu.mem_read(node+8,2))[0]
   if task:
    try:fn=u.rq(u.rq(task)+0x18)
    except Exception as ex:
     log.append(dict(index=i,task=hex(task),times=times,error=str(ex)));graphs.append(dict(count=count,edges=edges,log=log));return 'invalid task header'
    for k in range(times):
     error=u.call(fn,task,CTX,count=30000000);log.append(dict(index=i,task=hex(task),fn=hex(fn),times=times,iteration=k,error=error))
     if error:graphs.append(dict(count=count,edges=edges,log=log));return error
   done.add(i)
 graphs.append(dict(count=count,edges=edges,log=log,done=len(done)))
 return None if len(done)==count else 'task graph cycle/unhandled dependency'
FN=u.rq(W+0x38)+int(Fast&0xffffff)*0xc0;FM=u.rq(W+0x150)+u.r32(FN+0x80)*0x80
initial_fast_com=struct.unpack('<ddd',u.mu.mem_read(FM+0x10,24));ref_fast=list(initial_fast_com);fast_bad=[]
trace=[]
for i in range(10):
 c=u.call(0x71009ce484,W,TI,TG,count=50000000)
 if c is None:c=run_graph()
 if c is None:errors.append(['collideGraphReset',u.call(0x71009d275c,TG)]);done.clear()
 s=u.call(0x71009cee34,W,TG,count=50000000) if c is None else 'collide failed'
 if s is None:s=run_graph()
 import numpy as np
 step=float(np.float32(np.float32(300.)*np.float32(1/60)))
 ref_fast[0]+=step
 got_fast=bytes(u.mu.mem_read(FM+0x10,24));expected_fast=struct.pack('<ddd',*ref_fast)
 if got_fast!=expected_fast or bytes(u.mu.mem_read(FM+0x60,12))!=struct.pack('<3f',300.,0.,0.):fast_bad.append(dict(frame=i,com=got_fast.hex(),expected=expected_fast.hex(),velocity=bytes(u.mu.mem_read(FM+0x60,12)).hex()))
 trace.append(dict(fast_com=struct.unpack('<ddd',got_fast),fast_position=struct.unpack('<3f',u.mu.mem_read(FN+0x30,12)),fast_velocity=struct.unpack('<3f',u.mu.mem_read(FM+0x60,12)),frame=i,errors=[c,s],position=[u.rf(N+0x30+j*4) for j in range(3)],com=struct.unpack('<ddd',u.mu.mem_read(M+0x10,24)),vel=[u.rf(M+0x60+j*4) for j in range(3)],hits=dict(hits)))
 if c or s:break
 errors.append(["graphReset",u.call(0x71009d275c,TG)]);done.clear()
r=dict(bridge_trace=bridge_trace,fast_mismatch=fast_bad,fast_fields=len(trace)*6,fast_native_motion=bytes(u.mu.mem_read(FM,0x80)).hex(),graphs=graphs,native_motion=bytes(u.mu.mem_read(M,0x80)).hex(),material=bytes(u.mu.mem_read(Mat,0x50)).hex(),scope=__doc__,errors=errors,trace=trace,hits=hits,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,os=u.os_calls)
Path('analysis/completion/r9/physics_actual13_dynamic_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(bridge_property=[v['native_property'] for v in bridge_trace],fast_mismatch=len(fast_bad),frames=len(trace),hits=hits,null=r['null'],auto=r['auto'],faults=r['faults']),ensure_ascii=False))
