"""r9 exploratory engine 4 TOI handlers -> original native query. Explicit capsule/world/object fixture. World locks are original RET, optional filter pointers null; not actual-game layer binding. No geometry/query arithmetic callback replaced. No closure claimed."""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
u,errors=init_native();W,D,A,e=make_world(u,mode=1);errors+=e
R=u.alloc(0x500);E=u.alloc(0x500);WB=u.alloc(0x400);CF=u.alloc(0x100);u.wq(0x710599dfa8,R);u.wq(R+0xe8,E);u.wq(E,0x7105748188);u.wq(E+0xb8,WB);u.wq(E+0x10,CF);u.wq(WB+0xc0,W)
VT=u.alloc(0x90)
for off in (0x18,0x20):u.wq(VT+off,0x7103c49f00)
u.wq(WB,VT)
GCap=u.alloc(0x100);u.wq(GCap,0x7105745788);S=u.alloc(0x40);u.mu.mem_write(S+0x20,struct.pack('<7f',0,0,0,0,.7,0,.6));errors.append(['original capbackend',u.call(0x7103c243dc,S,0)]);CapB=u.x(0);u.wq(GCap+0xf8,CapB);errors.append(['original capowner',u.call(0x7103c27858,CapB,GCap)]);errors.append(['original capnative getter',u.call(u.rq(u.rq(CapB)+0x10),CapB)]);Hcap=u.x(0)
B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,Hcap);u.w8(B+0x28,0);errors.append(['createBody',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
GB=u.alloc(0x400);GBB=u.alloc(0x80);u.wq(GB,0x7105749048);u.wq(GB+0x28,GCap);u.wq(GB+0x90,GBB);u.wq(GBB+8,H);u.wq(GB+0x88,0x40)
mx=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.];u.mu.mem_write(GB+0xd8,struct.pack('<12f',*mx));u.mu.mem_write(GB+0x108,struct.pack('<12f',*mx))
Bullet=u.alloc(0x200);u.wq(Bullet,0x7105749990);P0=u.alloc(0x10);P1=u.alloc(0x10);Rot=u.alloc(0x30);Ang=u.alloc(0x10);u.mu.mem_write(Rot,struct.pack('<9f',1,0,0,0,1,0,0,0,1));u.mu.mem_write(P0,struct.pack('<3f',2,0,0));u.mu.mem_write(P1,struct.pack('<3f',-2,0,0));Args=u.alloc(0x40)
for i,p in enumerate((Bullet,0,GCap,GB,P0,P1,Rot,Ang)):u.wq(Args+8*i,p)
records=[]
hits={hex(p):0 for p in (0x71009af088,0x7100947aec,0x7100949570,0x710094ae10,0x7100948f30,0x7100aec920,0x7100aefd00,0x7103c5606c,0x7103c563dc)};q=[]
def pc(mu,p,size,d):
 hits[hex(p)]+=1
 if p==0x71009af088:
  qp=mu.reg_read(UC_ARM64_REG_X1);records.append(dict(pc=hex(p),query=bytes(mu.mem_read(qp,0xb0)).hex()))
 if p==0x7103c563dc:
  qp=mu.reg_read(UC_ARM64_REG_X1);records.append(dict(pc=hex(p),point=bytes(mu.mem_read(qp,0x80)).hex()))
 if p==0x7100aec920:
  ss=mu.reg_read(UC_ARM64_REG_X4);q.append(dict(p=hex(p),settings=bytes(mu.mem_read(ss,0x70)).hex(),countA=mu.reg_read(UC_ARM64_REG_X1),countB=mu.reg_read(UC_ARM64_REG_X3)))
for p in hits:u.mu.hook_add(UC_HOOK_CODE,pc,begin=int(p,16),end=int(p,16))
results=[]
for fn in (0x7103c52d30,0x7103c5368c,0x7103c54140,0x7103c54de4):
 before=dict(hits);e=u.call(fn,0,Args,count=5000000);results.append(dict(fn=hex(fn),error=e,hits={k:v-before[k] for k,v in hits.items()},pc=hex(u.mu.reg_read(UC_ARM64_REG_PC))));print(results[-1])
r=dict(scope=__doc__,results=results,init_errors=errors,queries=q,records=records,shape_native=hex(Hcap),shape_bytes=bytes(u.mu.mem_read(Hcap,0x80)).hex(),bodyhandle=hex(H),null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_engine_toi_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
