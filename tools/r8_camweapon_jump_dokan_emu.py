"""r8: actual secondary-interface Jump dispatch and Dokan yaw branch original fragments."""
import json,struct,itertools,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STACK
from r5_player_libm_emu import Sdk,bits
B=0x7100000000;F=np.float32
def fb(v):return F(struct.unpack('<f',struct.pack('<I',v))[0])
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.sdk=Sdk();self.i=self.u.alloc(0x300);self.p=self.u.alloc(0x100);self.h=self.u.alloc(0x10);self.pvt=self.u.alloc(0x10);self.iref=self.u.alloc(0x10);self.c=self.u.alloc(0x2000);self.d=self.u.alloc(0x500);self.b=self.u.alloc(0xb000);self.beh=self.u.alloc(0x200);self.ref=self.u.alloc(0x10);self.trace=[];self.atan=[]
  self.ptr(self.i+0x30,B+0x5637898);self.ptr(self.i+0x48,self.h);self.ptr(self.h,self.p);self.u.u32(self.h+0xc,9);self.u.u32(self.i+0x50,9);self.ptr(self.p,self.pvt);self.ptr(self.pvt,0x30000600);self.mu.mem_write(self.p+0x93,b'\1');self.ptr(self.iref,self.i+0x30)
  self.ptr(self.ref,self.beh);self.ptr(self.beh+0x108,self.b);self.ptr(self.b+0xa880,self.d);self.ptr(self.c+0x1920,self.d)
  self.mu.mem_write(self.rptr(B+0x5797ef0),b'\1')
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def rptr(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def ret(self,v=None):
  if v is not None:self.mu.reg_write(UC_ARM64_REG_X0,v)
  self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,mu,pc,n,_):
  if pc==0x30000600:self.ret(1)
  if pc in [B+0x2580e60,B+0x2580c50]:self.trace.append((hex(pc),hex(mu.reg_read(UC_ARM64_REG_X0))))
  if pc==B+0x1252998:self.atan.append((mu.reg_read(UC_ARM64_REG_S0)&0xffffffff,mu.reg_read(UC_ARM64_REG_S1)&0xffffffff))
  if pc in [B+0x3e9c2a0,B+0x3e9be20]:
   name='logf' if pc==B+0x3e9c2a0 else 'expf';mu.reg_write(UC_ARM64_REG_S0,self.sdk.call(name,fb(mu.reg_read(UC_ARM64_REG_S0)&0xffffffff)));self.ret()
 def regs(self,d):
  for n,v in d.items():self.mu.reg_write(globals()['UC_ARM64_REG_'+n.upper()],bits(v) if n.startswith('s') and n[1:].isdigit() else v)
 def jump(self,j):
  self.trace=[];self.u.u32(self.p+0x40,j);self.u.u32(self.i+0x88,0xdeadbeef);self.regs({'x21':self.iref,'sp':STACK+0xe0000});self.mu.emu_start(B+0x24a80b0,B+0x24a80c4,count=5000)
  assert self.u.ru32(self.i+0x88)==j and self.trace==[(hex(B+0x2580e60),hex(self.i+0x30)),(hex(B+0x2580c50),hex(self.i))]
  return 1
 def yaw(self,kind,t,aim,pre,land):
  self.atan=[];self.u.u32(self.d+0x30,3);self.ptr(self.d+0x88,1);self.u.u32(self.d+0xc0,kind);self.u.u32(self.d+0x104,100);self.u.f32(self.d+0x110,mul(t,100));self.u.f32(self.d+0xe8,pre[0]);self.u.f32(self.d+0xf0,pre[1]);self.u.f32(self.d+0x90,land[0]);self.u.f32(self.d+0x98,land[1]);self.u.f32(self.c+0x18c,aim[0]);self.u.f32(self.c+0x194,aim[1]);self.regs({'x19':self.c,'x25':self.ref,'x8':self.d,'w9':3,'s0':.37,'s14':.41,'sp':STACK+0xe0000})
  self.mu.emu_start(B+0x24e3394,B+0x24e35f4,count=5000)
  tt=F(min(div(mul(t,100),100),F(1)));target=None
  if kind==2 and tt<=F(.4):target=pre;rate=F(.1)
  elif kind!=2 and tt<=F(.1):rate=mul(.37,fb(0x3cf5c28f))
  else:
   target=land;v=F(1) if (kind==2 and tt>=fb(0x3f59999a)) or tt>=1 else div(sub(tt,F(.4 if kind==2 else .1)),fb(0x3ee66667 if kind==2 else 0x3f666666))
   pow=F(0) if abs(v)<fb(0x3a83126f) else fb(self.sdk.call('expf',div(fb(self.sdk.call('logf',abs(v))),fb(0x3ed47fcc))))
   rate=mul(pow,F(.1 if kind==2 else .2))
  got=self.mu.reg_read(UC_ARM64_REG_S0)&0xffffffff;assert got==bits(rate),(kind,t,hex(got),hex(bits(rate)))
  expected=[] if target is None else [(bits(sub(mul(target[1],aim[0]),mul(target[0],aim[1]))),bits(add(mul(target[0],aim[0]),mul(target[1],aim[1]))))]
  assert self.atan==expected,(kind,t,self.atan,expected)
  return 1
 def phase2(self,phase,flag):
  self.u.u32(self.d+0x30,phase);sp=STACK+0xe0000;self.ptr(sp+0x230,self.d);self.mu.mem_write(sp+0x4ec,bytes([flag]));self.u.u32(sp+0x4e8,37);self.regs({'sp':sp});self.mu.emu_start(B+0x24818e4,B+0x2481910,count=50);assert self.u.ru32(self.d+0x30)==(2 if phase in [1,2] and flag else phase);assert self.u.ru32(self.d+0x130)==37;return 1
r=Run();nj=sum(r.jump(j) for j in range(0,128));np2=sum(r.phase2(*v) for v in itertools.product(range(6),[0,1]));rng=random.Random(1088);ny=sum(r.yaw(k,t,[rng.uniform(-1,1),rng.uniform(-1,1)],[.3,-.9],[-.6,.8]) for k in [0,1,2,3] for t in [0,.05,.1,.100001,.2,.399999,.4,.400001,.5,.849999,.85,.9,1,1.2] for _ in range(8))
out={'jump_interface':{'pass':nj,'mismatch':0},'dokan_phase2':{'pass':np2,'mismatch':0},'dokan_yaw':{'pass':ny,'mismatch':0},'boundaries':['Jump original24a80b0..c4 dispatch to actual secondaryVT5637898+40→2580e60→2580c50 whole; param RTTI returns true, synthetic generation-valid parameter','Dokan original yaw24e3394..35f4 plus out-ofline3d08/404c/4064; atan2 original main executes, math PLT delegated to original SDK logf/expf','Dokan phase2 writer block only; lifecycle1/3/4 and warp setup statically read, no complete warp trajectory/frame']}
Path('analysis/completion/r8/camera_jump_dokan_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
