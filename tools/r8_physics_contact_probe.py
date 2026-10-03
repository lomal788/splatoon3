"""r8 original native capsule-to-capsule contact probe; diagnostic single-thread world."""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
from unicorn import UC_HOOK_CODE
u,errors=init_native();W,D,A,e=make_world(u,mode=0);errors+=e
Mat=u.alloc(0x50);errors.append(['materialCtor',u.call(0x7100a507cc,Mat)])
for off in (0x1a,0x1c,0x1e):u.mu.mem_write(Mat+off,b'\0\0')
errors.append(['materialLibrary',u.call(0x7100a4f76c,u.rq(W+0x8a8),Mat)]);MatID=u.x(0)&0xffff
hits={hex(p):0 for p in (0x7100a181fc,0x7100a29f20,0x7100a4b8c8,0x71009d5b68)}
def hit(mu,addr,size,data):hits[hex(addr)]+=1
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
H=body(cap((0,0,0),(0,.7,0),.6),(0,.45,0),(0,-3,0))
TG=u.alloc(0x500);errors.append(['taskgraph',u.call(0x7100902bb0,TG)]);TI=u.alloc(0x20);u.wf(TI,1/60);u.wf(TI+4,1/60);u.w32(TI+8,1)
N=u.rq(W+0x38)+int(H&0xffffff)*0xc0;M=u.rq(W+0x150)+u.r32(N+0x80)*0x80
trace=[]
for i in range(10):
 c=u.call(0x71009ce484,W,TI,TG,count=50000000);s=u.call(0x71009cee34,W,TG,count=50000000);trace.append(dict(frame=i,errors=[c,s],position=[u.rf(N+0x30+j*4) for j in range(3)],com=struct.unpack('<ddd',u.mu.mem_read(M+0x10,24)),vel=[u.rf(M+0x60+j*4) for j in range(3)],hits=dict(hits)))
 if c or s:break
r=dict(native_motion=bytes(u.mu.mem_read(M,0x80)).hex(),material=bytes(u.mu.mem_read(Mat,0x50)).hex(),scope=__doc__,errors=errors,trace=trace,hits=hits,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,os=u.os_calls)
Path('analysis/completion/r8/physics_contact_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(r,ensure_ascii=False))
