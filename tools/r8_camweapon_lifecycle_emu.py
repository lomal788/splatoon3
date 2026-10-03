"""Original actor request→manager transition and two bullet sphere setters.
Synthetic minimal actors; callbacks/locks/jobs isolated. No renderer/hardware.
"""
import sys,struct,json,itertools,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STUB
B=0x7100000000
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.a=self.u.alloc(0x700);self.m=self.u.alloc(0x600);self.vt=self.u.alloc(0x300);self.w=self.u.alloc(0x50);self.sh=[self.u.alloc(0x100),self.u.alloc(0x100)];self.enq=0;self.events=[];self.mode=''
  self.ptr(B+0x59a37c8,self.m);self.ptr(self.a,self.vt);self.ptr(self.vt+0xf0,STUB+0x400);self.ptr(self.vt+0xc0,STUB+0x408);self.ptr(self.w+0x20,self.sh[0]);self.ptr(self.w+0x28,self.sh[1]);self.u.u32(self.m+0x9c,0x300)
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def ret(self,v=None):
  if v is not None:self.mu.reg_write(UC_ARM64_REG_X0,v)
  self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,mu,pc,n,_):
  if pc==B+0x3c88280:self.ret(1)
  elif pc==B+0x3c88cd8:self.enq+=1;self.ret()
  elif pc in [STUB+0x400,STUB+0x408]:self.events.append(pc-STUB);self.ret()
  elif pc==B+0x3c897cc:self.events.append('detach');self.ret()
  elif pc==B+0x3c88084:mu.mem_write(mu.reg_read(UC_ARM64_REG_X0),b'\0'*24);self.ret()
 def request(self,phase,flags,pending,ownerphase):
  self.mu.mem_write(self.a+0x18,b'\0'*0x680);self.u.u32(self.a+0x24,phase);self.u.u32(self.a+0x28,flags);self.u.u32(self.a+0x4d4,pending);self.u.u32(self.a+0x4d0,ownerphase);self.enq=0;self.events=[]
  got=self.u.call(B+0xf721b8,self.a,0)
  accept=phase in [4,5] and not(flags&(1<<11|1<<9)) and not(pending&1) and ownerphase!=3
  expflag=((flags|1)&~0x1800)|0x800 if accept and flags&255==0 else flags|1 if accept else flags
  gotrow=[got,self.u.ru32(self.a+0x28),self.u.ru32(self.a+0x4d4),self.enq]
  ref=[int(accept),expflag,pending|1 if accept else pending,int(accept and flags&255==0)]
  if gotrow!=ref:raise AssertionError((phase,flags,pending,ownerphase,gotrow,ref))
  if accept and flags==0:
   self.u.call(B+0x3c7f810,self.a)
   if self.u.ru32(self.a+0x24)!=6 or self.events!=[0x400,'detach',0x408]:raise AssertionError(('transition',self.events,self.u.ru32(self.a+0x24)))
  return 1
 def radius(self,which,r,old):
  self.u.f32(self.sh[which]+0xe4,old);self.u.u32(self.sh[which]+0x14,0x20);self.u.call(B+(0x16cb590 if which==0 else 0x16cb5ec),self.w,fargs=(r,))
  got=self.u.ru32(self.sh[which]+0xe4)
  import numpy as np
  delta=np.float32(np.float32(r)-np.float32(old));eps=np.float32(2**-23)
  ref=old if abs(delta)<=eps else min(max(np.float32(r),np.float32(.05)),np.float32(2000))
  if not np.isfinite(ref):ref=np.float32(1)
  bits=struct.unpack('<I',struct.pack('<f',ref))[0]
  if got!=bits:raise AssertionError(('radius',which,r,old,hex(got),hex(bits)))
  return 1
r=Run();n=sum(r.request(*c) for c in itertools.product([3,4,5,6],[0,1,2,0x200,0x800],[0,1],[0,3]));rng=random.Random(88832)
nr=sum(r.radius(i,v,old) for i in [0,1] for old in [.3,2,30] for v in [.01,.05,.3,2,30,2000,3000,float('nan'),float('inf')]+[rng.uniform(.01,40) for _ in range(70)])
out={'request0':{'pass':n,'mismatch':0},'radius':{'pass':nr,'mismatch':0},'boundaries':['minimal synthetic actor component table absent; async4d4bit14excluded','manager thread/mutex wrapper/enqueue/detach-job callback stubbed; actual request, flags and lifecycle6 transition execute','two sphere setters and radius clamp whole original execute; shape dirtybit5set; no dirtyqueues/resourceworld','native actor lifecycle6 component detach callback statically read in3cc74dc, not executed with real components']}
Path('analysis/completion/r8/weapon_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
