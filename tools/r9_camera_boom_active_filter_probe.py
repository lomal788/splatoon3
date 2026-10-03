"""r9 camera factory -> original reset filter writer -> game sphere query -> nativeWorld cast.
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
# Exact object headers from original 3c4579c; provider unused on this kind6 path.
errors.append(['actualFilterProvider',u.call(0x7103b1ab5c,0)]);Provider=u.x(0)
FB=u.alloc(0x28);u.wq(FB,0x7105756560);u.wq(FB+8,0xffffffff);u.wq(FB+0x10,1);u.w8(FB+0x18,4);u.wq(FB+0x20,Provider);u.wq(WB+0x110,FB)
Codec=u.alloc(0x20);u.wq(Codec,0x7105755ee8);u.wq(Codec+8,0xffffffff);u.wq(Codec+0x10,1);u.wq(WB+0xd0,Codec)

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
GCap=u.alloc(0x100);u.wq(GCap,0x7105745788);
for off in (0xb8,0xbc,0xc0,0xc4):u.w32(GCap+off,0xffffffff)
S=u.alloc(0x40);u.mu.mem_write(S+0x20,struct.pack('<7f',0,-1,0,0,1,0,.6))
errors.append(['capbackend',u.call(0x7103c243dc,S,0)]);CapB=u.x(0);u.wq(GCap+0xf8,CapB);errors.append(['capowner',u.call(0x7103c27858,CapB,GCap)]);errors.append(['capnative',u.call(u.rq(u.rq(CapB)+0x10),CapB)]);Hcap=u.x(0)
B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,Hcap);u.w8(B+0x28,0);errors.append(['createBody',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
GB=u.alloc(0x400);GBB=u.alloc(0x80);LP=u.alloc(0x40);u.wq(GB,0x71057468d8);u.wq(GB+0x28,GCap);u.wq(GB+0x90,GBB);u.wq(GBB+8,H);u.wq(GB+0x88,0x40);u.wq(GB+0x180,LP);u.w32(LP+8,3);u.wq(GB+0x80,u.alloc(0xd8));u.w32(LP+0x0c,0xffffffff);u.w32(LP+0x10,0xffffffff);u.w32(LP+0x18,0xffffffff);u.w32(LP+0x1c,0xffffffff)
N=u.rq(W+0x38)+(H&0xffffff)*0xc0;u.wq(N+0x98,GB)
HP=u.alloc(8);u.wq(HP,H);errors.append(['addBody',u.call(0x71009c6a70,W,HP,1,0,0)])
native_traces=[];branch_pcs=[]
u.mu.hook_add(UC_HOOK_CODE,lambda mu,p,n,d:branch_pcs.append(hex(p)),begin=0x7103b19dd4,end=0x7103b1a2f0)
def native_capture(mu,p,size,d):
 native_traces.append(dict(pc=hex(p),args=[hex(mu.reg_read(UC_ARM64_REG_X0+i)) for i in range(8)]))
 if p==0x7100a49378:
  native_traces[-1]['collectors']=[bytes(mu.mem_read(mu.reg_read(rr),0x80)).hex() for rr in (UC_ARM64_REG_X20,UC_ARM64_REG_X19)]
 if p==0x7100a492e8:
  native_traces[-1]['query']=bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X1),0xb0)).hex()
  native_traces[-1]['broadfn']=hex(u.rq(u.rq(u.rq(W+0x4c0))+0xd0))
for p in (0x7100a49378,0x7100a492e8,0x71009af088,0x7100947aec,0x7100948f30,0x7100aec920,0x7103c37498,0x7103c570c4,0x7103c57b00,0x7103c57d04,0x7103c49f00,0x7103c56f80,0x7103c56d08,0x7103b1a4e8,0x7103b19308,0x7103c56c6c,0x7103a5f36c,0x7103c37768,0x7103b1a114):u.mu.hook_add(UC_HOOK_CODE,native_capture,begin=p,end=p)
out.update(filter_vt28=hex(u.rq(0x7105756560+0x28)),provider=hex(Provider),native_traces=native_traces,body_handle=hex(H),nativeBody=hex(N),userdata=hex(GB),errors=errors)
if err is None and C:
 Q=C+0x1d0;P0=u.alloc(0x10);P1=u.alloc(0x10);MX=u.alloc(0x30)
 u.mu.mem_write(P0,struct.pack('<3f',2,0,0));u.mu.mem_write(P1,struct.pack('<3f',-2,0,0));u.mu.mem_write(MX,struct.pack('<9f',1,0,0,0,1,0,0,0,1))
 out['branch_bytes']=bytes(u.mu.mem_read(0x7103b19f5c,4)).hex();out['fn_bytes']=bytes(u.mu.mem_read(0x7103b1a114,12)).hex()
 out['bodyfilterGet_error']=u.call(u.rq(0x71057468d8+0x90),GB);out['bodyfilterGetter']=hex(u.rq(0x71057468d8+0x90));out['bodyfilterGot']=hex(u.x(0));out['bodyfilterBytes']=bytes(u.mu.mem_read(u.x(0),0x40)).hex()
 out['beforeResetFilter']=bytes(u.mu.mem_read(C+0x2d8,0x38)).hex()
 u.mu.reg_write(UC_ARM64_REG_X19,C);u.mu.reg_write(UC_ARM64_REG_X8,0x3f80000000000000);u.mu.reg_write(UC_ARM64_REG_W25,0x3f800000)
 u.mu.emu_start(0x71024d6d94,0x71024d6dc8,count=40)
 out['resetFilterPC']=hex(u.mu.reg_read(UC_ARM64_REG_PC));out['afterResetFilter']=bytes(u.mu.mem_read(C+0x2d8,0x38)).hex()
 assert u.r32(C+0x2e0)&63==7 and u.r32(C+0x2e4)==8
 out.update(query=hex(Q),query_bytes=bytes(u.mu.mem_read(Q,0x150)).hex(),shape=hex(u.rq(Q+8)))
 u.mu.mem_write(Q+0x10,bytes(u.mu.mem_read(P0,12)));u.mu.mem_write(Q+0x1c,bytes(u.mu.mem_read(P1,12)));u.w32(Q+0xf8,u.r32(Q+0xf8)|0xc)
 err=u.call(0x7103a5f36c,Q,count=3000000);out.update(branch_pcs=branch_pcs,query_error=err,return_value=hex(u.x(0)),query_result=bytes(u.mu.mem_read(Q+0x40,0x20)).hex(),null_after={str(k):v for k,v in u.null_calls.items()},auto_after=u.auto_pages,faults_after=u.faults,plt_after=u.plt_stubbed)
if out.get('return_value')=='0x1':
 L=u.rq(C+0x318);It=u.alloc(0x48);u.mu.reg_write(UC_ARM64_REG_X8,It);out['iterator_error']=u.call(0x71012d8dcc,L)
 out['listener']=hex(L);out['listener_bytes']=bytes(u.mu.mem_read(L,0xa8)).hex();out['iterator_bytes']=bytes(u.mu.mem_read(It,0x48)).hex()
 First=u.rq(It+8);P=u.rq(First);out['first_point']=hex(P);out['first_point_bytes']=bytes(u.mu.mem_read(P,0x80)).hex();out['point_normal']=list(struct.unpack('<3f',u.mu.mem_read(P+0xc,12)));out['point_entry_flags']=hex(u.rq(First+8))
Path('analysis/completion/r9/camera_boom_active_filter_probe.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:out[k] for k in ("query_error","return_value","query_result","faults_after","null_after","auto_after")}))