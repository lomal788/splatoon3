"""Original helper creation and BulletSplashShooter wall-drop handle binding."""
import struct,json,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STUB
B=0x7100000000
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.a=self.u.alloc(0x1230);self.lst=self.u.alloc(0x20);self.reg=self.u.alloc(0x20);self.guard=self.u.alloc(0x10);self.nodes=[self.u.alloc(0x40) for _ in range(3)];self.objs=[]
  self.ptr(B+0x5790638,self.reg);self.ptr(B+0x5790630,self.guard);self.mu.mem_write(self.guard,b'\1');self.ptr(self.rptr(B+0x578ff50),0)
  self.names=[0x4873313,0x48e054f,0x48bbd5e];self.fns=[0x1e65a7c,0x16d994c,0x1e3d53c];self.vts=[0x55ebff8,0x55a0b30,0x55ea2e8];self.hashes=[self.u.call(B+0x38a0d98,B+n) for n in self.names]
  self.t=self.u.alloc(0x30);self.vt=self.u.alloc(0x90);self.rec=[self.u.alloc(0x30) for _ in range(2)];self.h=[self.u.alloc(0x10) for _ in range(2)];self.out=[self.u.alloc(0x10) for _ in range(2)]
  self.ptr(self.a+0x170,self.t);self.ptr(self.t,self.vt);self.ptr(self.vt+0x80,STUB+0x500);self.lookups=[];self.present=(1,1);self.baseok=1
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def rptr(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def ret(self,v=None):
  if v is not None:self.mu.reg_write(UC_ARM64_REG_X0,v)
  self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,mu,pc,n,_):
  if pc==B+0x83d2f0:
   size=mu.reg_read(UC_ARM64_REG_X0);a=self.u.alloc(size,fill=b'\xa5');self.objs.append((a,size));self.ret(a)
  elif pc==B+0x3e99f10:
   a=mu.reg_read(UC_ARM64_REG_X0);v=mu.reg_read(UC_ARM64_REG_X1)&255;n=mu.reg_read(UC_ARM64_REG_X2);mu.mem_write(a,bytes([v])*n);self.ret(a)
  elif pc==B+0x1762d44:self.ret(self.baseok)
  elif pc==STUB+0x500:
   p=self.rptr(mu.reg_read(UC_ARM64_REG_X1));name=bytes(mu.mem_read(p,40)).split(b'\0')[0].decode();idx=['WallDropMoveParam','WallDropCollisionPaintParam'].index(name);self.lookups.append(name);self.ret(self.rec[idx] if self.present[idx] else 0)
 def helper(self,presence):
  self.mu.mem_write(self.a+0x158,b'\0'*16);self.ptr(self.a+0x11b0,0);self.mu.mem_write(self.lst,b'\0'*32);self.u.u32(self.lst+0x14,0x10);self.objs=[]
  active=sorted([i for i in range(3) if presence[i]],key=lambda i:self.hashes[i])
  for n in self.nodes:self.mu.mem_write(n,b'\0'*64)
  self.ptr(self.reg+8,self.nodes[active[0]] if active else 0)
  for k,i in enumerate(active):self.ptr(self.nodes[i]+0x20,self.hashes[i]);self.ptr(self.nodes[i]+0x28,B+self.fns[i]);self.ptr(self.nodes[i]+0x10,self.nodes[active[k+1]] if k+1<len(active) else 0)
  got=self.u.call(B+0x15315d0,self.a,self.lst,0)
  count=next((i for i,v in enumerate(presence) if not v),3);expected_sizes=[0x38,0x40,0x220][:count]
  assert got==int(count==3) and [s for a,s in self.objs]==expected_sizes,(presence,got,self.objs)
  assert self.u.ru32(self.lst+0x10)==count
  for i,(a,size) in enumerate(self.objs):assert self.rptr(a)==B+self.vts[i];assert self.rptr(self.a+[0x11b0,0x158,0x160][i])==a
  head=self.rptr(self.lst)
  for a,size in reversed(self.objs):assert head==a+0x10;head=self.rptr(head)
  assert head==0
  return 1
 def splash(self,base,presence,old):
  self.baseok=base;self.present=presence;self.lookups=[]
  for i in range(2):
   self.ptr(self.rec[i]+0x28,self.h[i]);self.ptr(self.h[i],self.rec[i]);self.u.u32(self.h[i]+0xc,123+i);self.ptr(self.a+0x11c8+i*0x10,0x123456789+old);self.u.u32(self.a+0x11d0+i*0x10,997+i)
  got=self.u.call(B+0x1811a74,self.a,0);assert got==base
  self.u.call(B+0x1812574,self.a,*self.out)
  for i in range(2):
   ptr,gen=struct.unpack('<QI',self.mu.mem_read(self.out[i],12));assert (ptr,gen)==((self.h[i] if presence[i] else 0,123+i if presence[i] else 997+i) if base else (0x123456789+old,997+i)),(base,presence,ptr,gen)
  assert len(self.lookups)==2*base
  return 1
r=Run();nh=sum(r.helper(p) for p in itertools.product([0,1],repeat=3) for _ in range(16));ns=sum(r.splash(b,p,o) for b in [0,1] for p in itertools.product([0,1],repeat=2) for o in range(16))
out={'helper_factory':{'pass':nh,'mismatch':0,'sizes':[56,64,544],'hashes':r.hashes},'splash_table_binding':{'pass':ns,'mismatch':0},'boundaries':['synthetic class registry populated with original factory addresses; real hash/tree lookup/factories/list stores run','allocation and libc memset isolated; runtime registrar constructor not run','splash common base1762d44 stub success/failure, table virtual name lookup mock records; original1811a74→38b3510 preallocated-handle branch→1812574 run','resource handle allocation slowpath/thread mutex not run']}
Path('analysis/completion/r8/weapon_helper_splash_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))

