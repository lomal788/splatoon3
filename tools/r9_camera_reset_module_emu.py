"""r9 camera reset-from-module24e4bc8 whole original function.
Only24d6598(reset/settings/rig) is intercepted. Tested C15e8/C1c8 are supplied
post-reset values because the original reset's own existing proof is reused.
Quaternion/math/input-device selection/slot stores remain original.
"""
import random,json,struct
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
F=np.float32
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def bits(a):return struct.pack('<f',a).hex()
u=PUC();m=u.mu;C=u.alloc(0x2000);B=u.alloc(0xb000);BH=u.alloc(0x200);Mgr=u.alloc(0x100);Mod=u.alloc(0x180);I=u.alloc(0x200);D0=u.alloc(0x200);D1=u.alloc(0x200)
u.wq(C+0x1968,BH);u.wq(BH+0x108,B);u.wq(u.rq(BASE+0x5790ef8),Mgr);u.wq(Mgr+0xe8,Mod);u.wq(u.rq(BASE+0x5790f50),I);u.wq(I+0x20,D0);u.wq(I+0xd0,D1)
resets=[]
def hook(mu,pc,n,_):
 if pc==BASE+0x24d6598:
  p=mu.reg_read(UC_ARM64_REG_X3);resets.append(dict(x0=mu.reg_read(UC_ARM64_REG_X0),w1=mu.reg_read(UC_ARM64_REG_W1),w2=mu.reg_read(UC_ARM64_REG_W2),dir=list(struct.unpack('<3f',mu.mem_read(p,12)))));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
m.hook_add(UC_HOOK_CODE,hook,begin=BASE+0x24d6598,end=BASE+0x24d6598)
rng=random.Random(0x94bc8);bad=[];samples=[];fields=0;count=2048;upper=lower=0
for i in range(count):
 q=np.asarray([rng.uniform(-1,1) for _ in range(4)],dtype='float32');q=q/F(np.sqrt(np.sum(q*q,dtype='float32')));x,y,z,w=q
 m.mem_write(Mod+0x150,struct.pack('<4f',*q));m.mem_write(Mod+0x140,b'\1');m.mem_write(Mod+0x144,struct.pack('<3f',1,2,3))
 idx=[0,1,2,0xffffffff][i%4];slot=idx if idx<2 else 0;mode=(i//4)%3;flip=(i//12)&1
 u.w32(I+0x164,4 if flip else 0);m.mem_write(D0+0x17d,bytes([mode if not flip else 2]));m.mem_write(D1+0x17d,bytes([mode if flip else 2]));u.w32(C+0x15f0,idx)
 gain=F(rng.uniform(-3,3));bias=F(rng.uniform(-150,150));p=F(rng.uniform(-1,1));u.wf(C+0x1c8,gain);u.wf(C+0x15e8,bias);u.wf(B+0x544,p)
 for off in (0x168,0x16c,0x14f8,0x1504,0x150c,0x15f4,0x15f8,0x15fc,0x1600,0x1604,0x1608):u.wf(C+off,F(123))
 rx=add(mul(z,add(x,x)),mul(y,add(w,w)));rz=sub(sub(1,mul(x,add(x,x))),mul(y,add(y,y)));ln=F(np.sqrt(add(add(mul(rx,rx),0),mul(rz,rz))))
 expected_dir=[mul(rx,F(F(1)/ln)),F(0),mul(rz,F(F(1)/ln))] if ln>0 else [rx,F(0),rz]
 off=sub(F(-65 if mode==1 else -75),bias);lo=F(-120 if mode==1 else -45);v=lo if off<lo else min(off,F(45));upper+=int(off>45);lower+=int(off<lo)
 u.call(BASE+0x24e4bc8,C,count=1500)
 reset=resets[-1];exp=[p,F(.2),F(0),F(0),F(0),F(0) if slot==0 else F(123),F(0) if slot==1 else F(123),v if slot==0 else F(123),v if slot==1 else F(123),v if slot==0 else F(123),v if slot==1 else F(123)]
 got=[u.rf(C+o) for o in (0x16c,0x168,0x14f8,0x1504,0x150c,0x15f4,0x15f8,0x15fc,0x1600,0x1604,0x1608)]
 if [bits(v) for v in got]!=[bits(v) for v in exp] or [bits(v) for v in reset['dir']]!=[bits(v) for v in expected_dir] or (reset['w1'],reset['w2'])!=(0,0):bad.append(dict(i=i,got=got,expected=exp,reset=reset,expected_dir=expected_dir))
 fields+=14
 if i<5:samples.append(dict(i=i,idx=idx,mode=mode,flip=flip,bias=bias,dir=reset['dir'],pitch=v))
# Module-invalid path preserves complete camera state and never calls reset.
invalid=64
for i in range(invalid):
 m.mem_write(Mod+0x140,b'\0');m.mem_write(C,b'\xa5'*0x1968);before=bytes(m.mem_read(C,0x1968));n=len(resets);u.call(BASE+0x24e4bc8,C,count=100)
 if bytes(m.mem_read(C,0x1968))!=before or len(resets)!=n:bad.append(dict(invalid=i))
out=dict(scope=__doc__,active_cases=count,inactive_cases=invalid,fields=fields,reset_calls=len(resets),upper45_cases=upper,lower_cases=lower,mismatches=bad,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/camera_reset_module_emu.json').write_text(json.dumps(out,default=float,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['scope','samples']},default=float))