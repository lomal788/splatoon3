"""r9 explicit capsule engine/native TOI fixture. No query arithmetic is replaced; lock slots use original RET. Optional filter/codec null. Native body is created but not Added (caller chooses broadphase)."""
import struct
from r8_physics_native_uc import init_native,make_world

def make_engine_toi_fixture(with_staging=True):
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
 if with_staging:
  Stage=u.alloc(0x100);Points=u.alloc(0x400);CL=u.alloc(0x200);Entries=u.alloc(0x80)
  u.wq(CF+8,Stage);u.w32(Stage+0x10,8);u.wq(Stage+0x18,Points);u.w32(Stage+0x20,0x7fffffff);u.w32(Stage+0x28,0x7fffffff)
  u.w32(CL+0x28,8);u.wq(CL+0x30,Entries);u.wq(Args+8,CL)
 return locals()
