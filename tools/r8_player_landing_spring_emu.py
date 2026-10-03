"""r8 landing B740 consumer: original 248e14c..e638 and spring integration d7a0..7f4.
Synthetic B/state/spring inputs; not original contact detection or full slot19.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import PUC,STACK,STACK_SZ,RET_MAGIC
u=PUC();m=u.mu;B=u.alloc(0xb000);S=u.alloc(0x100);sp=STACK+STACK_SZ-0x20000
F=lambda x:float(np.float32(x))
def bits(x):return struct.unpack('<I',struct.pack('<f',F(x)))[0]
def rfreg(i,x):m.reg_write(getattr(sys.modules[__name__],'UC_ARM64_REG_S'+str(i)),bits(x))
def stop(mu,a,n,d):
 if a==0x710248e638:mu.reg_write(UC_ARM64_REG_PC,RET_MAGIC)
hook=m.hook_add(UC_HOOK_CODE,stop)
g={hex(a):u.rf(a) for a in (0x71058bbc60,0x71058bbfd0,0x71058bbfdc,0x71058bbfe0,0x71058bbfe4,0x71058bbfe8)}
cap=u.rs32(0x71058bbfec)
J=g['0x71058bbc60'];T=g['0x71058bbfdc'];a0=g['0x71058bbfe0'];a1=g['0x71058bbfe4'];amin=g['0x71058bbfe8'];stmax=g['0x71058bbfd0']
def ramp(x,a,b):
 if a<=b:
  if x<=a:return F(0)
  if x>=b:return F(1)
  return F(F(x-a)/F(b-a)) if b!=a else F(0)
 return F(1-ramp(x,b,a))
rng=random.Random(740);out={'scope':__doc__,'globals':g,'air_frames_cap':cap,'landing_cases':0,'landing_fields':0,'integration_cases':0,'integration_fields':0,'mismatch':[]}
for i in range(6000):
 vy=F(rng.choice((0,.115,-.115,-T,-.001,rng.uniform(-.7,.2))))
 active=i%4!=0;mode=4 if i%11==0 else 0;dokan=i%3==0;age=rng.choice((0,1,3,4,12,cap,cap+1,-1))
 vel=F(rng.uniform(-.5,.5));stiff=F(rng.uniform(-1,1));s7=F(rng.uniform(-1,2));s6=F(rng.uniform(-1,2))
 m.mem_write(B,b'\0'*0x1100);u.wf(B+0x740,vy);m.mem_write(B+0x274,bytes([active]));u.w32(B+0xc4,age);u.w32(S+0x30,mode);u.wf(B+0xce8,vel);u.wf(B+0xcf8,stiff)
 m.reg_write(UC_ARM64_REG_X22,B);m.reg_write(UC_ARM64_REG_X21,B+0xccc);m.reg_write(UC_ARM64_REG_X26,S);m.reg_write(UC_ARM64_REG_X8,dokan);m.reg_write(UC_ARM64_REG_SP,sp);u.wq(sp+0x168,S)
 rfreg(6,s6);rfreg(7,s7)
 m.emu_start(0x710248e14c,RET_MAGIC,count=1000)
 ev,es=vel,stiff
 if active and vy<0:
  s=F(-vy);t=F(1) if mode==4 else ramp(s,J,T);k=F(a0+F(t*F(a1-a0)));target=F(s7+F(F(s6-s7)*t))
  if dokan:k=max(k,amin);target=min(target,stmax)
  q=ramp(F(age),0,F(cap));ev=F(vel-F(F(k*q)*min(s,J)));es=F(stiff+F(q*F(target-stiff)))
 got=bytes(m.mem_read(B+0xce8,4))+bytes(m.mem_read(B+0xcf8,4));expect=struct.pack('<ff',ev,es)
 out['landing_cases']+=1;out['landing_fields']+=2
 if got!=expect and len(out['mismatch'])<10:out['mismatch'].append({'i':i,'input':[vy,active,mode,dokan,age,vel,stiff,s7,s6],'got':got.hex(),'expected':expect.hex()})
m.hook_del(hook)
for i in range(1600):
 x,y,z,vx,vy,vz,h,hv,k,s7,s6=[F(rng.uniform(-1,1)) for j in range(11)]
 for off,val in zip((0,4,8,0xc,0x10,0x14,0x18,0x1c,0x2c),(x,y,z,vx,vy,vz,h,hv,k)):u.wf(B+0xccc+off,val)
 m.reg_write(UC_ARM64_REG_X21,B+0xccc);rfreg(0,z);rfreg(1,x);rfreg(2,y);rfreg(3,vz);rfreg(4,vx);rfreg(5,vy);rfreg(16,h);rfreg(17,hv);rfreg(7,s7);rfreg(6,s6)
 m.emu_start(0x710248d7a0,0x710248d7f4,count=100)
 nx,ny,nz,nh=F(x+vx),F(y+vy),F(z+vz),F(h+hv);ek=F(k+F(s6*F(s7-k)))
 expected=struct.pack('<fff',nx,ny,nz)+struct.pack('<ff',nh,hv)+struct.pack('<fff',nx,F(nh+ny),nz)+struct.pack('<f',ek)
 got=bytes(m.mem_read(B+0xccc,12))+bytes(m.mem_read(B+0xce4,8))+bytes(m.mem_read(B+0xcec,16))
 out['integration_cases']+=1;out['integration_fields']+=9
 if got!=expected and len(out['mismatch'])<10:out['mismatch'].append({'integration':i,'got':got.hex(),'expected':expected.hex()})
out.update(null_calls=sum(u.null_calls.values()),auto_pages=u.auto_pages,plt_stubbed=u.plt_stubbed)
Path('analysis/completion/r8/player_landing_spring_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))


