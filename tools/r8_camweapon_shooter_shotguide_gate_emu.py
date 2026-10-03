"""Actual normal-shooter ShotGuide caller gate and secondary vtable dispatch.
Synthetic player records supply raw input flags. No resource loading or Havok executed.
"""
import itertools,json,struct,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STACK
B=0x7100000000
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;u=self.u;self.b=u.alloc(0xb000);self.i=u.alloc(0x400);self.g=u.alloc(0x100);self.user=u.alloc(0x200);self.demo=u.alloc(0x100);self.peri=u.alloc(0x200);self.pipe=u.alloc(0x100);self.vehicle=u.alloc(0x100);self.coop=u.alloc(0x1400);self.special=u.alloc(0x1000);self.dummy=u.alloc(0x400);self.dvt=u.alloc(0x200);self.source=u.alloc(0x200);self.stepP=u.alloc(0xa0);self.stepQ=u.alloc(0xa0);self.stepH=u.alloc(0x10);self.parentH=u.alloc(0x10)
  self.ptr(self.i+0x30,B+0x5637898);self.ptr(self.b+0x588,self.i+0x30);self.ptr(self.b+0x590,self.i+0x30);u.u32(self.b+0x658,1)
  for off,obj in [(0xa650,self.demo),(0xa818,self.peri),(0xa6d0,self.pipe),(0xa6d8,self.vehicle),(0xa830,self.coop),(0xa7c0,self.special),(0xa670,self.dummy),(0xa880,self.dummy),(0xa6a8,self.dummy),(0xa6c8,self.dummy),(0xa860,self.dummy),(0xa898,self.g),(0xa820,self.dummy)]:self.ptr(self.b+off,obj)
  u.u32(self.vehicle+0x88,-1);self.ptr(self.dummy,self.dvt);self.ptr(self.dvt+0x140,0x30000400);self.ptr(self.g+0x38,self.user);self.ptr(self.i+0x2a8,self.source);self.ptr(self.i+0x2b0,self.g)
  self.ptr(B+0x5863d00,0);self.mu.mem_write(B+0x58bbb9a,b'\0');self.ptr(self.stepP,B+0x564c740);self.ptr(self.stepQ,B+0x564c740);self.ptr(self.stepH,self.stepP);u.u32(self.stepH+0xc,17);self.ptr(self.i+0x48,self.stepH);u.u32(self.i+0x50,17);self.ptr(self.parentH,self.stepQ);u.u32(self.parentH+0xc,29)
  for guard,obj,vt in [(0x58009e8,0x58009e0,0x553d070),(0x58504c8,0x58504c0,0x555cdc0),(0x58005a0,0x5800598,0x553d070),(0x58005b0,0x58005a8,0x553d070)]:self.mu.mem_write(B+guard,b'\1');self.ptr(B+obj,B+vt)
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def rp(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def cs(self,a):
  z=bytearray()
  while self.mu.mem_read(a,1)!=b'\0':z+=self.mu.mem_read(a,1);a+=1
  return z.decode('utf8')
 def ret(self,v=0):self.mu.reg_write(UC_ARM64_REG_X0,v);self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,m,pc,n,_):
  if pc==B+0x24c7234:self.ret(0)
  elif pc==0x30000400:self.ret(0)
  elif pc==B+0x24ef164:self.ret(0)
  elif pc==B+0x2586aa0:self.dispatch.append(tuple(m.reg_read(r) for r in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2]))
  elif pc==B+0x253c9a0:self.false_getter+=1
  elif pc==B+0x2585bd8:self.pred+=1;self.u.u32(self.i+0xcc,self.kind);self.ret(0)
  elif pc in [B+0x267739c,B+0x267ceb4]:self.stops.append((hex(pc),hex(m.reg_read(UC_ARM64_REG_X0))));self.ret()
  elif pc in [B+0x2677578,B+0x267d090]:
   a=m.reg_read(UC_ARM64_REG_X2);b=m.reg_read(UC_ARM64_REG_X3);self.emits.append((hex(pc),self.cs(self.rp(a)),self.cs(self.rp(b)),m.reg_read(UC_ARM64_REG_W4)));self.ret()
  elif pc in [B+0x26779a8,B+0x2676cc0]:self.ret()
 def callgate(self,flags,timer,enabled,wait,block,kind=2):
  u=self.u;self.pred=0;self.kind=kind;self.emits=[];self.stops=[];self.dispatch=[];self.false_getter=0
  u.u32(self.b+0x4e0,flags[0]);u.u32(self.b+0x518,flags[4]);u.u32(self.b+0xab8,timer)
  for off,val in zip([0x532,0x533,0x4f2,0x534,0x535,0x52a],flags[1:4]+flags[5:8]):self.mu.mem_write(self.b+off,bytes([val]))
  self.mu.mem_write(self.b+0x1054,bytes([enabled]));u.u32(self.b+0x1058,wait);u.u32(self.b+0xd60,1 if block==1 else 0);self.mu.mem_write(self.demo+0x34,bytes([0 if block==2 else 1]));u.u32(self.peri+0x38,1 if block==3 else 0);self.mu.mem_write(self.peri+0xb0,bytes([1 if block==4 else 0]));u.u32(self.pipe+0x38,1 if block==5 else 0)
  self.mu.mem_write(self.g+0x30,b'\0');u.u32(self.g+0x58,0);u.u32(self.user+0xf8,0);self.mu.mem_write(self.i+0xf0,b'\0'*0x58)
  sp=STACK+0xf0000
  for off,val in [(0,self.b+0xd58),(8,self.demo),(16,self.g),(24,self.dummy),(32,self.dummy)]:self.ptr(sp+off,val)
  try:u.call(B+0x24c0fbc,self.b+0xa5f9,self.b+0x588,self.b+0x678,self.dummy,self.b+0x4e0,self.b+0x518,self.b+0x784,self.b+0x1054)
  except Exception:
   print("debug",hex(self.mu.reg_read(UC_ARM64_REG_PC)),[(hex(self.mu.reg_read(z))) for z in [UC_ARM64_REG_X0,UC_ARM64_REG_X8,UC_ARM64_REG_X19,UC_ARM64_REG_X21,UC_ARM64_REG_X27]],flags,timer,enabled,wait,block);raise
  a=bool(enabled and wait==0 and block!=1);h=timer<=0 and any(flags);show=int(a and not h and block==0)
  assert self.dispatch==[(self.i+0x30,show,show)],(flags,timer,enabled,wait,block,self.dispatch,show)
  assert self.false_getter==1 and self.pred==show
  assert self.mu.mem_read(self.g+0x30,1)==bytes([a])
  if show:
   assert self.emits==[(hex(B+0x2677578),'Shooter_Center','Shooter_HitMarker',kind),(hex(B+0x267d090),'Shooter_BiasLeft','Shooter_BiasRight',kind)],self.emits
   assert not self.stops
  else:assert self.stops==[(hex(B+0x267739c),hex(self.i+0xf0)),(hex(B+0x267ceb4),hex(self.i+0x120))] and not self.emits,self.stops
  return 1
 def steps(self,own,parent,valid,value):
  u=self.u;u.u32(self.i+0x98,0);u.u32(self.stepP+0x64,value);u.u32(self.stepQ+0x64,value^0xa5a5a5a5);self.mu.mem_write(self.stepP+0x96,bytes([own]));self.mu.mem_write(self.stepQ+0x96,bytes([parent]));self.ptr(self.stepP+0x10,1);self.ptr(self.stepP+0x18,self.parentH);u.u32(self.stepP+0x20,29 if valid else 28)
  sp=STACK+0xe0000
  for reg,val in [(UC_ARM64_REG_X19,self.i),(UC_ARM64_REG_W0,0),(UC_ARM64_REG_W25,0),(UC_ARM64_REG_SP,sp)]:self.mu.reg_write(reg,val)
  try:self.mu.emu_start(B+0x25860c4,B+0x2586264,count=3000)
  except Exception:
   print("stepdebug",hex(self.mu.reg_read(UC_ARM64_REG_PC)),[(hex(self.mu.reg_read(z))) for z in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X8,UC_ARM64_REG_LR]],own,parent,valid);raise
  expected=(value^0xa5a5a5a5) if not own and valid else value
  assert u.ru32(sp+0x80)==expected,(own,parent,valid,value,u.ru32(sp+0x80),expected)
  return 1
r=Run();gate=0
for flags in itertools.product([0,1],repeat=8):
 for timer in [-1,0,1]:gate+=r.callgate(list(flags),timer,1,0,0)
# Enable/delay and each raw hide gate plus effect kinds 0/1/2.
for enabled,wait,block,kind in itertools.product([0,1],[-1,0,1],range(6),range(3)):gate+=r.callgate([0]*8,0,enabled,wait,block,kind)
rng=random.Random(83018);values=[0,1,8,0xffffffff,0x7fffffff,0x80000000]+[rng.getrandbits(32) for _ in range(58)]
steps=sum(r.steps(*x,value) for x in itertools.product([0,1],repeat=3) for value in values)
out={'normal_shooter_gate_dispatch_effect':{'pass':gate,'mismatch':0},'actual_shooter_step_inheritance':{'pass':steps,'mismatch':0},'boundaries':['Full24c0fbc→actual267f934→secondaryVT5637898+60 actual2586aa0→258683c executes,including actual253c9a0 false getter','Normal Main shooter only; special active pointers absent,respawn manager absent,vehicle handle=-1,guide tracked list count0;SDK input records synthesized','24c7234 andInk-vt140 return actionallowedfalse;prediction2585bd8 returns supplied kinds0/1/2;XLink emit/update/stop engine boundary captured,not actual renderer/Havok','Actual25860c4..2586264 withactualWeaponShooterParamRTTI2813b24/parent generation flag consumesP64 ShotGuideFrame;existingmetadata/factorynameproof reused,not rerun as new']}
Path('analysis/completion/r8/shooter_shotguide_gate_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
