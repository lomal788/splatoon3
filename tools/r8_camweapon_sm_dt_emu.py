"""Original Player initialization SM+204 and actual actor phase→vt300 setter.
Unrelated model/squid constructors, malloc/memset/TLS SDK are explicit boundaries.
"""
import struct,json,random,itertools
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC
B=0x7100000000;F=np.float32
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.actor=self.u.alloc(0x900);self.step=self.u.alloc(0x20);self.spare=self.u.alloc(0x100);self.heapbase=self.u.heap_next;self.phase='ctor';self.allocs=[];self.setter_count=0
  self.ptr(self.rp(B+0x578ff50),0);self.mu.mem_write(B+0x58e8784,b'\0');self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def rp(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def ret(self,v=0):self.mu.reg_write(UC_ARM64_REG_X0,v);self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,m,pc,n,_):
  if pc==B+0x083d2f0:
   sz=m.reg_read(UC_ARM64_REG_X0);a=self.u.alloc(sz,bytes([self.dirty]));self.allocs.append((sz,a));self.ret(a)
  elif pc==B+0x3e99f10:
   a=m.reg_read(UC_ARM64_REG_X0);val=m.reg_read(UC_ARM64_REG_X1)&255;sz=m.reg_read(UC_ARM64_REG_X2);m.mem_write(a,bytes([val])*sz);self.ret(a)
  elif pc in [B+0x26b1fa8,B+0x2639aa8,B+0x3e9aa00,B+0x3e9aa10]:self.ret()
  elif self.phase=='ctor' and pc==B+0x2439d0c:m.emu_stop()
  elif pc==B+0x243a45c:self.setter_count+=1
  elif self.phase=='post' and pc==B+0x0f7717c:m.emu_stop()
 def ctor(self,dirty,name,kind):
  self.dirty=dirty;self.phase='ctor';self.allocs=[];self.u.heap_next=self.heapbase;self.mu.mem_write(self.actor,b'\0'*0x900);self.ptr(self.actor+0x18,B+(0x4873b31 if name else 0x497b27c));self.u.u32(self.actor+0x4d0,kind);self.u.call(B+0x24397bc,self.actor,0)
  assert [sz for sz,a in self.allocs]==[0x47c0,0x39f8,0x210];self.sm=self.rp(self.actor+0x778);assert self.sm==self.allocs[2][1];assert self.rp(self.sm)==B+0x5630260;assert self.u.ru32(self.sm+0x204)==0x3f800000;assert self.u.ru32(self.sm+0x208)==0
 def consume(self,dt,scale,flag,guard,post):
  self.phase='post' if post else 'pre';self.setter_count=0;self.ptr(self.actor,B+0x562ff08);self.u.u32(self.actor+0x4cc,flag);self.u.u32(self.actor+0x4d4,(1<<19 if post else 0)|(1<<8 if guard else 0));self.u.f32(self.actor+0x4d8,scale);self.u.f32(self.step+4,dt);self.u.u32(self.sm+0x204,0xdeadbeef)
  if post:
   # Execute the original branch from its entry through the setter call; transforms before this are normal identity fixtures.
   self.u.call(B+0x0f76f78,self.actor,self.step,0,self.spare,0,0,0,0)
  else:self.u.call(B+0x0f76a78,self.actor,self.step,0,self.spare,0,0,0,0)
  expected=struct.unpack('<I',struct.pack('<f',F(F(dt)*F(scale))))[0] if flag&2 and not guard else 0xdeadbeef
  assert self.u.ru32(self.sm+0x204)==expected,(dt,scale,flag,guard,post,hex(self.u.ru32(self.sm+0x204)),hex(expected));assert self.setter_count==int(bool(flag&2 and not guard))
r=Run();ctorcases=0
for vals in itertools.product([0,1,85,170,205,255],[0,1],[0,2]):r.ctor(*vals);ctorcases+=1
rng=random.Random(804204);cases=0
for post,flag,guard in itertools.product([False,True],[0,2],[0,1]):
 for k in range(64):
  # Reset unrelated actor memory to initialized zero; the existing SM ptr remains valid.
  sm=r.sm;r.mu.mem_write(r.actor,b'\0'*0x900);r.ptr(r.actor+0x778,sm);r.consume(F(rng.uniform(0,4)),F(rng.uniform(0,2)),flag,guard,post);cases+=1
out={'original_ctor_prefix':{'pass':ctorcases,'mismatch':0,'sm204_bits':'0x3f800000','sm208_bits':0},'original_actor_phase_setter':{'pass':cases,'mismatch':0},'boundary':['Existing24397bc constructor source reused;execute original entry through SM attachment2439d08,then stop at2439d0c. Full later component creation is excluded.','malloc/memset are memory boundaries,allocations dirtied;26b1fa8/2639aa8 unrelated model/squid construction and TLS are return stubs;scene configuration/actor component arrays null.','Real PlayerVT562ff08+300243a45c used;original actor first phase whole and second phase prefix through setter;no live actor scheduler or phase-info producer. dt and actor4d8 scale supplied finitefloat32,default scale/phase dt1 are not asserted.','Prior r6 producer formula dt×actor4d8 is reused;new evidence is original SM ctor default1 plus source-to-real setter execution,gating and exactfloat32 product.']}
Path('analysis/completion/r8/sm_dt_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
