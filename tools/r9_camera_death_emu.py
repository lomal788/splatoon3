"""r9 new original SplPlayer death-pose message receiver and six-axis camera blend blocks.
Reset/rig setup boundaries stubbed, receiver RTTI and copies original. No game renderer/solo death event runs.
"""
from pathlib import Path
import random,json,struct
import numpy as np
from network_uc import UC,BASE,END
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
F=np.float32
E=UC();mu=E.mu;C=E.alloc(0x1978);Body=E.alloc(0xac00);comp=E.alloc(0x200);Actor=E.alloc(0x400);Msg=E.alloc(0x70);Packet=E.alloc(0x30);Pos=E.alloc(0x10)
def w(a,fmt,*v):mu.mem_write(a,struct.pack('<'+fmt,*v))
def r(a,fmt):return list(struct.unpack('<'+fmt,mu.mem_read(a,struct.calcsize('<'+fmt))))
def bit(x):return struct.pack('<f',float(x))
def add(x,y):return F(F(x)+F(y))
def sub(x,y):return F(F(x)-F(y))
def mul(x,y):return F(F(x)*F(y))
w(C+0x1968,'Q',comp);w(comp+0x108,'Q',Body);w(Body+0xa878,'Q',C);w(C+0x28,'Q',Actor);w(C+0x60,'Q',Pos);w(Msg,'Q',BASE+0x56250f8);w(Packet+4,'I',0x6c2b6a0e);w(Packet+0x10,'Q',Msg);mu.mem_write(BASE+0x58b2aa8,b'\1');boundaries={};fault=[]
def hook(mu,pc,n,u):
 if pc in (BASE+0x24d6598,BASE+0x24d6e84):
  boundaries[hex(pc)]=boundaries.get(hex(pc),0)+1;mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def inv(mu,access,a,size,value,u):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),address=hex(a),access=access));return False
mu.hook_add(UC_HOOK_CODE,hook);mu.hook_add(UC_HOOK_MEM_INVALID,inv);rng=random.Random(2340518);fields=0
for n in range(1024):
 vals=[F(rng.uniform(-30,30)) for _ in range(13)];p,a,d=vals[:3],vals[3:6],vals[6:9];pitch=vals[9];t=[F(rng.uniform(-20,20)) for _ in range(3)];up=[F(rng.uniform(-1,1)) for _ in range(3)]
 w(Msg+0x40,'10f',*p,*a,*d,pitch)
 for off,v in zip((0x28c,0x290,0x294),t):w(Actor+off,'f',v)
 for off,v in zip((0x29c,0x2a8,0x2b4),up):w(Actor+off,'f',v)
 gotret=E.call(BASE+0x234f518,comp,Packet);assert mu.reg_read(UC_ARM64_REG_PC)==END and gotret==1
 got=[*r(C+0x18c,'3f'),*r(C+0x150c,'f'),*r(C+0x16b0,'6f'),*r(C+0x16c8,'6f'),*r(C+0x16e0,'3I'),*r(C+0x150,'3f')]
 want=[*d,pitch,*p,*a,*p,*a,0,0,0,*[add(t[i],mul(up[i],F(.6))) for i in range(3)]]
 assert [bit(v) for v in got]==[bit(v) for v in want],('receiver',n,got,want)
 assert r(C+0x16ed,'B')==[1];fields+=22
# original cancellation whole dispatcher: clears ec/ed/ef; preserves ee and blend fields.
for flags in (0,1,255):
 w(C+0x16ec,'4B',flags,flags,77,flags);w(Packet+4,'I',0x6c2b6a0f);assert E.call(BASE+0x234f518,comp,Packet)==1;assert r(C+0x16ec,'4B')==[0,0,77,0]
blendfields=0;examples=[]
for n in range(2048):
 old=[F(rng.uniform(-100,100)) for _ in range(6)];target=[F(rng.uniform(-100,100)) for _ in range(6)];current=[F(rng.uniform(-100,100)) for _ in range(6)];rate=F(rng.uniform(0,1));progress=F(rng.uniform(0,1));ef=n&1;frame=rng.randrange(0,500)
 w(C+0x16b0,'6f',*old);w(C+0x16c8,'6f',*target);w(C+0x16e0,'2fI',progress,rate,frame);w(C+0x16ef,'B',ef);w(Pos,'3f',*current[:3]);w(C+0x70,'3f',*current[3:]);mu.reg_write(UC_ARM64_REG_X19,C);mu.reg_write(UC_ARM64_REG_X26,C+0x1520);mu.reg_write(UC_ARM64_REG_S15,0x3f800000)
 mu.emu_start(BASE+0x24dd3a4,BASE+0x24df40c,count=500);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0x24df40c
 dst=target if ef else current;new=[add(old[i],mul(rate,sub(dst[i],old[i]))) for i in range(6)];pr=add(progress,mul(rate,sub(1,progress)));nr=add(rate,mul(sub(1,rate),F(.01)))
 got=[*r(C+0x16b0,'6f'),*r(Pos,'3f'),*r(C+0x70,'3f'),*r(C+0x16e0,'2f')];want=[*new,*new,pr,nr];assert [bit(v) for v in got]==[bit(v) for v in want],('blend',n,got,want);assert r(C+0x16e8,'I')==[frame+1];blendfields+=14
 if n<4:examples.append(dict(ef=ef,old=[float(v) for v in old],target=[float(v) for v in dst],rate=float(rate),output=[float(v) for v in new],next_rate=float(nr)))
out=dict(receiver_cases=1024,receiver_fields=fields,clear_cases=3,blend_cases=2048,blend_fields=blendfields,mismatches=0,faults=fault,null_calls=0,auto_pages=0,examples=examples,stub_counts=boundaries,boundaries=['24d6598 reset and 24d6e84 rig setup skip; receiver and RTTI original','blend starts at24dd3a4 with x26=C1520 and s15=1 matching original main registers','does not run native renderer, queue dispatch timing, complete camera frame or death event in solo range'])
Path('analysis/completion/r9/camera_death_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='examples'}))