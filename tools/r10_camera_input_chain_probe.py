"""Native0874..1cd0 stick chain probe with original predicate/math.

Synthetic normal Player component state and no special/periscope/damage input.
This block starts after movement-blend production and stops before the final
gyro absolute-angle/normalized-p update. No whole input/scene claim.
"""
import json,struct
from pathlib import Path
from unicorn.arm64_const import *
from r6_player_uc import PUC,BASE,STACK,STACK_SZ
from r5_player_libm_emu import Sdk
sdk=Sdk();calls={}
names={BASE+0x3e9bb60:'powf',BASE+0x3e9c2a0:'logf',BASE+0x3e9be20:'expf',BASE+0x3e9be30:'cosf',BASE+0x3e9be40:'sinf'}
class Native(PUC):
 def _plt(self,mu,pc,n,o):
  if pc in names:
   name=names[pc];args=[struct.unpack('<f',struct.pack('<I',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff))[0]]
   if name=='powf':args.append(struct.unpack('<f',struct.pack('<I',mu.reg_read(UC_ARM64_REG_S1)&0xffffffff))[0])
   calls[name]=calls.get(name,0)+1;mu.reg_write(UC_ARM64_REG_S0,sdk.call(name,*args));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
  else:super()._plt(mu,pc,n,o)
u=Native();m=u.mu;C=u.alloc(0x2000);B=u.alloc(0xb000);H=u.alloc(0x200)
control,mission,sm,a860,coop,dokan,pipeline,camflags=[u.alloc(n) for n in [0xc00,0x100,0x100,0x100,0x100,0x100,0x100,0x200]]
manager=u.alloc(0x200);device=u.alloc(0x200)
u.wq(BASE+0x59a57d0,manager);u.wq(manager+0x20,device);u.wq(manager+0xd0,device)
u.wq(H+0x108,B);u.wq(C+0x1968,H);u.wq(C+0x1950,camflags)
for off,p in [(0xa650,control),(0xa6c8,mission),(0xa8c8,sm),(0xa860,a860),(0xa830,coop),(0xa880,dokan),(0xa6d0,pipeline)]:u.wq(B+off,p)
u.w8(control+0x34,1);u.w32(sm+0xc8,0x82)
sp=STACK+STACK_SZ-0x2000
def sf(k,v):m.reg_write(globals()['UC_ARM64_REG_S'+str(k)],struct.unpack('<I',struct.pack('<f',v))[0])
rows=[]
for gyro in [0,1]:
 for raw in [(0,0),(0,.8),(.8,0),(.4,.8)]:
  for bodyGyroFlag in [0,1]:
   for off in [0x180,0x184,0x188,0x14f8,0x1504,0x150c,0x1680,0x1c8,0x1cc]:u.wf(C+off,0)
   u.wf(C+0x168,.2);u.wf(C+0x7c,55);u.wf(C+0x179c,55);u.wf(C+0x156c,7)
   u.wf(C+0x18c,0);u.wf(C+0x190,0);u.wf(C+0x194,1);u.w32(C+0x16a8,0xffffffff)
   u.w8(C+0x15d8,gyro);u.w8(B+0x4cc,bodyGyroFlag);u.wf(B+0xa9c,raw[0]);u.wf(B+0xaa0,raw[1])
   u.wf(B+0xaa4,raw[0]);u.wf(B+0xaa8,raw[1]);u.w8(B+0x9210,1);u.w8(B+0x9212,0)
   for k,v in [(19,C),(23,B),(25,C+0x1968),(28,C+0x1521),(22,B+0xa650),(21,B+0xa830)]:m.reg_write(globals()['UC_ARM64_REG_X'+str(k)],v)
   m.reg_write(UC_ARM64_REG_SP,sp)
   sf(4,0);sf(13,1);sf(8,0);sf(15,0);sf(14,1)
   m.emu_start(BASE+0x24e0874,BASE+0x24e1cd0,count=20000)
   rows.append(dict(gyro=gyro,raw=raw,bodyIsEnableGyro4cc=bodyGyroFlag,consistentGyroFlags=gyro==bodyGyroFlag,pc=hex(m.reg_read(UC_ARM64_REG_PC)),yawVelocity=u.rf(C+0x14f8),pitchVelocity=u.rf(C+0x1504),pitchAccumulator=u.rf(C+0x150c)))
out=dict(scope=__doc__,cases=rows,sdkCalls=calls,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,fault=u.faults,plt=u.plt_stubbed)
p=Path('analysis/camera_100_r10/input/chain_probe.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
raise SystemExit(bool(u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or any(r['pc']!=hex(BASE+0x24e1cd0) for r in rows)))
