"""r8 original native body creation probe, synthetic capsule fixture."""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
u,errors=init_native();W,D,A,e=make_world(u,mode=0);errors+=e
P=u.alloc(0x10);V=u.alloc(0x20);u.wf(V+0x14,.7)
errors.append(['capsule',u.call(0x7100930b40,V,V+0x10,0,0,0,0,0,0,P,fargs=(.6,))]);Shape=u.rq(P)
B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,Shape);u.w8(B+0x28,2);u.wf(B+0x70,100)
u.wf(B+0x30,2);u.wf(B+0x34,3);u.wf(B+0x38,4);u.wf(B+0x50,6);u.wf(B+0x54,7);u.wf(B+0x58,8)
errors.append(['body',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
print('worldvt',hex(u.rq(W)),[(hex(o),hex(u.rq(u.rq(W)+o))) for o in range(0xa0,0x121,8)])
HP=u.alloc(0x10);u.wq(HP,H);errors.append(['addBodies',u.call(0x71009c6a70,W,HP,1,0,0)])
TG=u.alloc(0x500);TI=u.alloc(0x20);u.wf(TI,1/60);u.wf(TI+4,1/60);u.w32(TI+8,1)
errors.append(['taskgraph',u.call(0x7100902bb0,TG)])
errors.append(['collide',u.call(0x71009ce484,W,TI,TG,count=30000000)])
errors.append(['solve',u.call(0x71009cee34,W,TG,count=30000000)])
bodyarr=u.rq(W+0x38);motionarr=u.rq(W+0x150)
rows=[]
for i in range(4):
 N=bodyarr+i*0xc0;mid=u.r32(N+0x80);M=motionarr+mid*0x80 if mid<100 else 0
 rows.append(dict(index=i,bodyid=hex(u.r32(N+0x50)),motionid=mid,handle=hex(u.rq(N+0xb0)),flags=hex(u.r32(N+0x54)),body=bytes(u.mu.mem_read(N,0xc0)).hex(),motion=bytes(u.mu.mem_read(M,0x80)).hex() if M else None))
r=dict(taskgraph=bytes(u.mu.mem_read(TG,0x500)).hex(),errors=errors,world=hex(W),shape=hex(Shape),handle=hex(H),rows=rows,faults=u.faults,auto=u.auto_pages,nullcalls={str(k):v for k,v in u.null_calls.items()},plt=u.plt_stubbed,os=u.os_calls)
Path('analysis/completion/r8/physics_body_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in r.items() if k not in ('rows','plt','os','taskgraph')},ensure_ascii=False));print('rows',[(v['index'],v['bodyid'],v['motionid'],v['handle'],v['flags']) for v in rows])
