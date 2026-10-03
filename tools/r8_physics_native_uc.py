"""Reusable native Havok execution environment for r8 analysis only.
Gamefactory344af54 is previously analyzed; reuse only. Native09bff14 is newly read.
This probe does not execute actual collision manifold/Jacobian math.
"""
import json
from pathlib import Path
from r6_player_uc import PUC,BASE
import struct
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_PC,UC_ARM64_REG_LR,UC_ARM64_REG_TPIDR_EL0
class PhysicsUC(PUC):
 def __init__(self):
  self.tls={};self.os_calls={}
  super().__init__()
  self.elf_tls=self.alloc(0x1000);self.mu.reg_write(UC_ARM64_REG_TPIDR_EL0,self.elf_tls)
 def _plt(self,mu,addr,size,user):
  w0=struct.unpack_from("<I",self.img,addr-BASE)[0]
  if (w0&0x9f000000)!=0x90000000:return
  w1=struct.unpack_from("<I",self.img,addr+4-BASE)[0]
  imm=(((w0>>5)&0x7ffff)<<2)|((w0>>29)&3);imm=imm-(1<<21) if imm&(1<<20) else imm
  got=(addr&~0xfff)+(imm<<12)+((w1>>10)&4095)*8;name=self.got.get(got,"")
  x0,x1,x2=(mu.reg_read(r) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2))
  ret=0
  if "AllocateTlsSlot" in name:self.w32(x0,len(self.tls)+1)
  elif "SetTlsValue" in name:self.tls[x0]=x1
  elif "GetTlsValue" in name:ret=self.tls.get(x0,0)
  elif "GetSystemTickFrequency" in name:ret=1
  else:return super()._plt(mu,addr,size,user)
  self.os_calls[name]=self.os_calls.get(name,0)+1
  mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))

def init_native():
 u=PhysicsUC();u.wq(0x71059975c0,0);C=u.alloc(0x60);errors=[]
 for label,fn,args in (("libraryCinfo",0x7100923a60,(C,0)),("libraryInit",0x71008f28c0,(C,)),("shapeDefaults",0x71009313b0,(0x71057dd738,))):
  errors.append([label,u.call(fn,*args)])
 errors.append(['SimdTreeFeature',u.call(0x71009153d8,0x71057e5398)])
 return u,errors

def make_world(u,mode=1,substeps=8,dt=1/60):
 D=u.alloc(0x180);W=u.alloc(0x9b0);A=u.alloc(0x70);errors=[]
 errors.append(["Cinfo",u.call(0x7100a454cc,D)])
 errors.append(["blockAllocator",u.call(0x7100922a88,A,0x100000,0)])
 u.wq(D+8,A);u.w32(D+0x10c,substeps);u.w8(D+0x70,mode);u.wf(D+0x104,.6);u.wf(D+0x108,1);u.wf(D+0x12c,dt)
 errors.append(["world",u.call(0x71009bff14,W,D)])
 return W,D,A,errors
