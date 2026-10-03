"""New native hknpWorld constructor with game default solver Cinfo fields.
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
prior=json.loads(Path('analysis/completion/r8/physics_world_solver_probe.json').read_text(encoding='utf-8'))
u=PhysicsUC();u.wq(0x71059975c0,0);errors=[]
C=u.alloc(0x60)
errors.append(['nativeLibraryCinfo',u.call(0x7100923a60,C,0)])
errors.append(['nativeLibraryInit',u.call(0x71008f28c0,C)])
errors.append(['shapeDefaults',u.call(0x71009313b0,0x71057dd738)])
e=u.call(0x710344af54,0,15,0);Cfg=u.x(0);errors.append(['factory',e]);D=u.alloc(0x180);W=u.alloc(0x9b0)
e=u.call(0x7100a454cc,D);errors.append(['desc',e])
# Original game bootstrap mappings, actual Cfg default source.
u.w32(D+0x10c,u.r32(Cfg+0x94));u.w32(D+0x104,u.r32(Cfg+0x98));u.w32(D+0x108,u.r32(Cfg+0x9c))
e=u.call(0x71009bff14,W,D);errors.append(['nativeWorld',e]);S=W+0x530
out={'scope':__doc__,'first_uninitialized_attempt':prior,'external_boundary':{'single_thread_tls':True,'elf_tls_tpidr_el0':hex(u.elf_tls),'tickFrequency':1,'os_calls':u.os_calls},'library':{'allocator':hex(u.rq(0x71057d7088)),'shapeDispatch':hex(u.rq(0x71057dd738))},'errors':errors,'config_fields':{'numSubsteps':u.rs32(Cfg+0x94),'solverTau':u.rf(Cfg+0x98),'solverDamp':u.rf(Cfg+0x9c)},'desc':{'mode':u.r8(D+0x70),'microsteps':u.rs32(D+0x110)},'native':{'substeps':u.rs32(S+0x70),'microsteps':u.rs32(S+0x78),'tau':u.rf(S),'damp':u.rf(S+8),'simulation':hex(u.rq(W+0x4a8)),'simulationVT':hex(u.rq(u.rq(W+0x4a8)))},'null':{str(k):v for k,v in u.null_calls.items()},'auto':u.auto_pages,'plt':{str(k):v for k,v in u.plt_stubbed.items()},'faults':u.faults}
Path('analysis/completion/r8/physics_world_solver_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
