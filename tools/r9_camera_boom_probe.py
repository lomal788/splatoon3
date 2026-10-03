"""r9 camera exploratory actual factory->game sphere query->nativeWorld cast.
Physics native initialization is reused fixture plumbing; no new completion implied.
"""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
u,errors=init_native();W,D,A,ee=make_world(u,mode=1);errors+=ee
R=u.alloc(0x500);E=u.alloc(0x500);WB=u.alloc(0x400);CF=u.alloc(0x100)
u.wq(0x710599dfa8,R);u.wq(R+0xe8,E);u.wq(E,0x7105748188);u.wq(E+0xb8,WB);u.wq(E+0x10,CF);u.wq(WB+0xc0,W);u.wf(E+0x21c,.01)
VT=u.alloc(0x90)
for off in (0x18,0x20):u.wq(VT+off,0x7103c49f00)
u.wq(WB,VT)
Stage=u.alloc(0x120);Points=u.alloc(0x800);u.wq(CF+8,Stage);u.w32(Stage+0x10,16);u.wq(Stage+0x18,Points);u.w32(Stage+0x20,0x7fffffff);u.w32(Stage+0x28,0x7fffffff)
u.wq(0x710580e340,0)
trace=[]
def watch(mu,p,size,d):
 trace.append(dict(pc=hex(p),x=[hex(mu.reg_read(UC_ARM64_REG_X0+i)) for i in range(4)]))
for p in (0x7103a62e78,0x7103a72e1c,0x7103c27ae4,0x710092efbc):u.mu.hook_add(UC_HOOK_CODE,watch,begin=p,end=p)
err=u.call(0x71024d5c6c,0,count=2000000);C=u.x(0)
out=dict(scope=__doc__,world=hex(W),native_vt=hex(u.rq(W)),native_cast=hex(u.rq(u.rq(W)+0x3f8)),camera=hex(C),factory_error=err,trace=trace,errors=errors,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
# Static nativeCapsule fixture, registered in broadphase. Nativeuserdata is a
# synthesized typed CharacterMatterRigidBody only for original postprocessing.
GCap=u.alloc(0x100);u.wq(GCap,0x7105745788);S=u.alloc(0x40);u.mu.mem_write(S+0x20,struct.pack('<7f',0,-1,0,0,1,0,.6))
errors.append(['capbackend',u.call(0x7103c243dc,S,0)]);CapB=u.x(0);u.wq(GCap+0xf8,CapB);errors.append(['capowner',u.call(0x7103c27858,CapB,GCap)]);errors.append(['capnative',u.call(u.rq(u.rq(CapB)+0x10),CapB)]);Hcap=u.x(0)
B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,Hcap);u.w8(B+0x28,0);errors.append(['createBody',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
GB=u.alloc(0x400);GBB=u.alloc(0x80);LP=u.alloc(0x40);u.wq(GB,0x71057468d8);u.wq(GB+0x28,GCap);u.wq(GB+0x90,GBB);u.wq(GBB+8,H);u.wq(GB+0x88,0x40);u.wq(GB+0x180,LP);u.w32(LP+0x18,0xffffffff);u.w32(LP+0x1c,0xffffffff)
N=u.rq(W+0x38)+(H&0xffffff)*0xc0;u.wq(N+0x98,GB)
HP=u.alloc(8);u.wq(HP,H);errors.append(['addBody',u.call(0x71009c6a70,W,HP,1,0,0)])
native_traces=[]
def native_capture(mu,p,size,d):
 native_traces.append(dict(pc=hex(p),args=[hex(mu.reg_read(UC_ARM64_REG_X0+i)) for i in range(8)]))
 if p==0x7100a49378:
  native_traces[-1]['collectors']=[bytes(mu.mem_read(mu.reg_read(rr),0x80)).hex() for rr in (UC_ARM64_REG_X20,UC_ARM64_REG_X19)]
 if p==0x7100a492e8:
  native_traces[-1]['query']=bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X1),0xb0)).hex()
  native_traces[-1]['broadfn']=hex(u.rq(u.rq(u.rq(W+0x4c0))+0xd0))
for p in (0x7100a49378,0x7100a492e8,0x71009af088,0x7100947aec,0x7100948f30,0x7100aec920,0x7103c37498):u.mu.hook_add(UC_HOOK_CODE,native_capture,begin=p,end=p)
out.update(native_traces=native_traces,body_handle=hex(H),nativeBody=hex(N),userdata=hex(GB),errors=errors)
if err is None and C:
 Q=C+0x1d0;P0=u.alloc(0x10);P1=u.alloc(0x10);MX=u.alloc(0x30)
 u.mu.mem_write(P0,struct.pack('<3f',2,0,0));u.mu.mem_write(P1,struct.pack('<3f',-2,0,0));u.mu.mem_write(MX,struct.pack('<9f',1,0,0,0,1,0,0,0,1))
 out.update(query=hex(Q),query_bytes=bytes(u.mu.mem_read(Q,0x150)).hex(),shape=hex(u.rq(Q+8)))
 err=u.call(0x7103c37768,Q,0,P0,P1,MX,0,0,count=3000000);out.update(query_error=err,return_value=hex(u.x(0)),query_result=bytes(u.mu.mem_read(Q+0x40,0x20)).hex(),null_after={str(k):v for k,v in u.null_calls.items()},auto_after=u.auto_pages,faults_after=u.faults,plt_after=u.plt_stubbed)
Path('analysis/completion/r9/camera_boom_probe.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))