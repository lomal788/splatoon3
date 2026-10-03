"""r9 new original camera collision-displacement consumer24da320..5a4.
Supplied rig-relative input vector S11/S10/S8; prior producer is read separately.
Finite synthetic spring inputs, no original world frame.
"""
import json,struct,random
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,STACK
from unicorn.arm64_const import *
F=np.float32
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
def norm(v):return F(np.sqrt(add(add(mul(v[0],v[0]),mul(v[1],v[1])),mul(v[2],v[2]))))
def bits(v):return struct.pack('<f',v).hex()
u=PUC();m=u.mu;C=u.alloc(0x2000);B=u.alloc(0xb000);BH=u.alloc(0x200);u.wq(C+0x1968,BH);u.wq(BH+0x108,B)
def vec(p,v):m.mem_write(p,struct.pack('<3f',*v))
def getv(p):return list(struct.unpack('<3f',m.mem_read(p,12)))
rng=random.Random(0x9a320);bad=[];count=2048;samples=[]
for i in range(count):
 spring=[F(rng.uniform(-2,2)) for _ in range(3)];prior=[F(rng.uniform(-10,10)) for _ in range(3)];inp=[F(rng.uniform(-.5,.5)) for _ in range(3)];body=[F(rng.uniform(-.5,.5)) for _ in range(3)];vel=[F(rng.uniform(-.5,.5)) for _ in range(3)];aim=[F(rng.uniform(-1,1)) for _ in range(3)];ratio=F(rng.choice([0,.4,1,1.2,rng.uniform(0,1)]));hold=(i%4)-1
 if i%17==0:spring=[F(0)]*3
 if i%31==0:inp=body=[F(0)]*3
 vec(C+0x144,spring);vec(C+0x120,prior);vec(C+0x18c,aim);vec(B+0x210,body);vec(B+0xe4,vel);u.wf(C+0x14c4,ratio)
 oldlen=norm(spring)
 k=F(.25) if oldlen<=1 else F(0) if oldlen>=F(2.5) else add(add(mul(div(add(oldlen,-1),F(-1.5)),F(.25)),F(.95)),F(-.7))
 damp=add(mul(k,ratio),F(.7));expected=[mul(x,damp) for x in spring];outpos=list(prior)
 if hold<1:
  weight=F(0) if ratio<=F(.4) else F(1) if ratio>=1 else add(div(add(ratio,F(-.4)),F(.6)),F(0))
  v=[add(inp[j],mul(weight,body[j])) for j in range(3)];length=norm(v);unit=[mul(x,div(1,length)) for x in v] if length>0 else v
  dot=add(mul(unit[2],vel[2]),add(mul(unit[0],vel[0]),mul(unit[1],vel[1])));amount=sub(length,min(F(-dot),length) if dot<=0 else F(0));expected=[add(expected[j],mul(unit[j],amount)) for j in range(3)]
  d=add(mul(expected[2],aim[2]),add(mul(aim[0],expected[0]),mul(aim[1],expected[1])))
  if d>0:
   response=mul(mul(sub(1,ratio),d),F(-.7));expected=[add(expected[j],mul(aim[j],response)) for j in range(3)]
  outpos=[sub(prior[j],expected[j]) for j in range(3)]
 for rr,val in [(UC_ARM64_REG_S11,inp[0]),(UC_ARM64_REG_S10,inp[1]),(UC_ARM64_REG_S8,inp[2])]:m.reg_write(rr,struct.unpack('<I',struct.pack('<f',val))[0])
 for rr,val in [(UC_ARM64_REG_X19,C),(UC_ARM64_REG_X27,C+0x1968),(UC_ARM64_REG_W22,hold&0xffffffff),(UC_ARM64_REG_SP,STACK+0x3d0000)]:m.reg_write(rr,val)
 m.emu_start(0x71024da320,0x71024da5a4,count=2000);got=getv(C+0x144)+getv(C+0x120);exp=expected+outpos
 if [bits(x) for x in got]!=[bits(x) for x in exp]:bad.append(dict(i=i,hold=hold,ratio=float(ratio),got=got,expected=exp))
 if i<3:samples.append(dict(hold=hold,ratio=float(ratio),got=got))
out=dict(scope=__doc__,cases=count,fields=count*6,mismatches=bad,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/camera_collision_spring_emu.json').write_text(json.dumps(out,default=float,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['scope','samples']},default=float))