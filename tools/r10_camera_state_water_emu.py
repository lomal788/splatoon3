"""Actual WaterFall camera-input blocks. Synthetic contact/actor fixtures.

No query, lifecycle, SDK math, or PLT stub is substituted. Execution ends at
documented block boundaries; this is not a native collision/whole frame run.
"""
import json
import random
import struct
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC, BASE, STACK

F=np.float32
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/camera_100_r10/state'
def bits(v): return struct.unpack('<I',struct.pack('<f',float(v)))[0]
def putq(mu,a,v): mu.mem_write(a,struct.pack('<Q',v))
def getf(mu,a,n=1): return list(struct.unpack('<'+'I'*n,mu.mem_read(a,n*4)))

def main():
 uc=UC();mu=uc.mu;rng=random.Random(101032)
 b=uc.alloc(0xb000);t=b+0xd58;pc=uc.alloc(0xe500);contact=uc.alloc(0x100);pair=uc.alloc(0x20);node=uc.alloc(0x20)
 putq(mu,node,pair);putq(mu,pair,contact)
 # Native static-ctor data are reused, not new runtime discoveries.
 consts=json.loads((ROOT/'analysis/player/bss_consts_58bb000.json').read_text(encoding='utf-8'))
 for a in [0x58bbf88,0x58bbf8c,0x58bc078]: uc.u32(BASE+a,consts[hex(BASE+a)]['u32'])
 maxcases=[];heightcases=[];timercases=[];normalcases=[]
 for i in range(512):
  rawy=F(rng.uniform(-4,4));dist=F(rng.uniform(-1,1));ny=F(rng.uniform(-1,1));old=F(rng.uniform(-4,4))
  flag=i&1;e0=(i>>1)&1;e1=(i>>2)&1;add=flag if e0==e1 else 1-flag
  candidate=F(rawy+F(dist*ny)) if add else rawy
  expected=candidate if old<candidate else old
  uc.f32(contact+4,rawy);uc.f32(contact+0x30,dist);uc.f32(contact+0x10,ny);uc.f32(pc+0x1d8,old)
  uc.u32(contact+0x38,0x11);uc.u32(contact+0x48,0x22);uc.u32(contact+0x40,4);uc.u32(contact+0x50,4)
  mu.mem_write(pair+8,bytes([flag]));mu.mem_write(node+8,bytes([e0,e1]))
  mu.reg_write(UC_ARM64_REG_SP,STACK+0xe0000);putq(mu,STACK+0xe0008,pc);putq(mu,STACK+0xe0010,node)
  mu.emu_start(BASE+0x24f84ec,BASE+0x24f862c,count=100)
  actual=getf(mu,pc+0x1d8)[0]
  mat=uc.ru32(pc+0x1d4)
  emat=0x11 if add else 0x22
  assert actual==bits(expected) and mat==emat,(i,actual,bits(expected),mat,emat)
  maxcases.append(dict(rawy=bits(rawy),dist=bits(dist),ny=bits(ny),old=bits(old),flag=flag,e0=e0,e1=e1,actual=actual,material=mat))
 # Height source/latch prefix. Hook only marks the two original block exits;
 # it neither writes state nor replaces called functions.
 stop={'pc':None}
 def endhook(mu,address,size,user):
  if address in [BASE+0x248e6cc,BASE+0x248e708]: stop['pc']=address;mu.emu_stop()
 hook=mu.hook_add(UC_HOOK_CODE,endhook,begin=BASE+0x2483134,end=BASE+0x248f800)
 values=[F(-np.finfo(np.float32).max),F(-2),F(0),F(1),F(4),F(float('nan'))]
 for pcheight in values:
  for old in values:
   for posy in values:
    for active in [0,1]:
     uc.f32(pc+0x1d8,pcheight);uc.f32(t+0x9c,old);uc.f32(b+0x14,posy)
     uc.u32(t+0x88,0);uc.u32(t+0x98,active);uc.u32(t+0xb4,0)
     slot=pc+0xe400;putq(mu,slot,pc)
     mu.reg_write(UC_ARM64_REG_X20,t);mu.reg_write(UC_ARM64_REG_X22,b);mu.reg_write(UC_ARM64_REG_X23,slot)
     mu.reg_write(UC_ARM64_REG_SP,STACK+0xe0000);putq(mu,STACK+0xe0150,t)
     stop['pc']=None;mu.emu_start(BASE+0x248a89c,BASE+0x248f800,count=100)
     expected=old
     if not active:
      # b.le treats unordered as true in this signed ARM branch.
      if not np.isnan(pcheight) and pcheight>F(-np.finfo(np.float32).max): expected=pcheight
      elif not np.isnan(posy) and not np.isnan(old) and posy>old: expected=F(-np.finfo(np.float32).max)
     actual=getf(mu,t+0x9c)[0]
     assert actual==bits(expected),(pcheight,old,posy,active,actual,bits(expected))
     heightcases.append(dict(pcheight=bits(pcheight),old=bits(old),posy=bits(posy),active=active,actual=actual,exit=hex(stop['pc'])))
 mu.hook_del(hook)
 dokan=uc.alloc(0x1000);pos=uc.alloc(0x10);vel=uc.alloc(0x10)
 putq(mu,b+0xa7c0,dokan)
 for initial in [-100,0,1,159,160,161,299,300,301,390,1000]:
  for vy in [F(-1),F(-.1),F(0),F(.5),F(float('nan'))]:
   for alternate in [0,1]:
    py=F(2.5);uc.f32(pos+4,py);uc.f32(vel+4,vy);mu.mem_write(dokan+0xeec,bytes([alternate]))
    mu.reg_write(UC_ARM64_REG_W8,initial);mu.reg_write(UC_ARM64_REG_X23,t);mu.reg_write(UC_ARM64_REG_X24,pos);mu.reg_write(UC_ARM64_REG_X25,vel);mu.reg_write(UC_ARM64_REG_X28,b)
    mu.emu_start(BASE+0x2461d30,BASE+0x2461d90,count=100)
    actual=getf(mu,t+0x98,4);extra=uc.ru32(t+0xac)
    expectedvy=F(float('nan')) if np.isnan(vy) else max(vy,F(-.1))
    # qNaN stays qNaN; UINT words encode float-only height/velocity fields.
    assert actual[0]==max(160,min(initial,300)) and actual[2:]==[bits(py),bits(expectedvy)]
    assert extra==(1 if alternate else 0xfffffff6)
    timercases.append(dict(initial=initial,vy=bits(vy),alternate=alternate,timer=actual[0],height=actual[2],velocity=actual[3],ac=extra))
 camera=uc.alloc(0x1a00);behavior=uc.alloc(0x200);slot=uc.alloc(8)
 putq(mu,slot,behavior);putq(mu,behavior+0x108,b)
 for i in range(512):
  n=[F(rng.uniform(-1,1)) for _ in range(3)];water=F(rng.uniform(-3,3));follow=F(rng.uniform(-3,3));active=i%3-1
  if i==0: n=[F(0),F(0),F(0)]
  mu.mem_write(b+0x180,struct.pack('<3f',*n));uc.f32(b+0xdf4,water);uc.u32(b+0xdf0,active);uc.f32(camera+0x124,follow)
  mu.reg_write(UC_ARM64_REG_X8,b);mu.reg_write(UC_ARM64_REG_X19,camera);mu.reg_write(UC_ARM64_REG_X27,slot)
  mu.reg_write(UC_ARM64_REG_SP,STACK+0xe0000);mu.mem_write(STACK+0xe0090,struct.pack('<3f',*n))
  mu.emu_start(BASE+0x24da0b0,BASE+0x24da160,count=150)
  expected=n.copy()
  if active>=1:
   d=F(water-follow);d=max(d,F(0));expected[1]=F(n[1]+F(d*F(.4)))
   lensq=F(F(expected[0]*expected[0])+F(expected[1]*expected[1]));lensq=F(F(expected[2]*expected[2])+lensq)
   length=F(np.sqrt(lensq))
   if length>F(0): expected=[F(x*F(F(1)/length)) for x in expected]
   if length<F(.01): expected=n.copy()
  actual=getf(mu,STACK+0xe0090,3)
  assert actual==[bits(x) for x in expected],(i,actual,[bits(x) for x in expected])
  normalcases.append(dict(normal=[bits(x) for x in n],water=bits(water),follow=bits(follow),active=active,actual=actual))
 result=dict(scope='synthetic contact/field inputs; actual original block instructions, no function or math stubs; not whole physics/scene execution',counts={'water_contact_max':len(maxcases),'water_height_latch':len(heightcases),'water_timer_initializer':len(timercases),'camera_normal_target':len(normalcases)},mismatch=0,maxcases=maxcases,heightcases=heightcases,timercases=timercases,normalcases=normalcases)
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'water_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(dict(counts=result['counts'],mismatch=0,output=str(OUT/'water_results.json'))))

if __name__=='__main__':main()
