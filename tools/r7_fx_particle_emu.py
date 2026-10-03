"""r7 fx: original 081e3e4 point-particle creation, designatedDirScale and particleScale.
Writer copy 080ced4 is instruction reading, not executed here. Emitter/table/arrays synthetic.
All 081e3e4 + shape0 081fa94 code executes unchanged; no callback/child or function stubs.
"""
import json,random,struct,sys
import numpy as np
from unicorn.arm64_const import *
from unicorn import UC_HOOK_MEM_UNMAPPED
from r7_fx_transform_emu import VM,F,ROOT,HEAP,STACK
ID=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
LCG=lambda x:(x*0x41c64e6d+0x3039)&0xffffffff
def main():
 sys.stdout.reconfigure(encoding='utf-8'); vm=VM();m=vm.mu; rng=random.Random(2026100702)
 m.hook_add(UC_HOOK_MEM_UNMAPPED, lambda mu,access,addr,size,value,ud: print("FAULT",hex(mu.reg_read(UC_ARM64_REG_PC)),hex(addr)) or False)
 E,R,ES,ER,A,PI,CH,TAB=[HEAP+x for x in (0,0x2000,0x4000,0x5000,0x6000,0x7000,0x8000,0x9000)]
 out={'function':'0x710081e3e4','shape':'0x710081fa94','stubs':[],'designatedDirScale':{'ok':0,'bad':0},'particleScale':{'ok':0,'bad':0},'examples':[]}
 for case in range(402):
  for p,n in ((E,0x1000),(R,0x1000),(ES,0x800),(ER,0x500),(A,0x300),(PI,0x100),(CH,0x200)):
   m.mem_write(p,bytes(n))
  vm.q(E+0xb0,R);vm.q(E+0x80,ES);vm.q(E+0x250,ER);vm.q(ER+0x10,R)
  m.mem_write(R+0xa93,b'\1');m.mem_write(R+0xbe8,b'\1');vm.w(E+0x240,1)
  vm.q(0x71057d52f8,TAB);vm.q(0x71057d52f0,TAB);vm.fs(TAB,[0,1,0,0]);vm.fs(E+0x460,ID);vm.fs(E+0x360,ID)
  for k,off in enumerate((0,8,0x10,0x18,0x20,0x28)):
   ptr=HEAP+0xa000+k*0x100;vm.q(A+off,ptr);m.mem_write(ptr,bytes(0x100))
  base=list(map(F,[rng.uniform(-2,4) for _ in range(3)]));dyn=list(map(F,[rng.uniform(-2,4) for _ in range(3)]))
  if case==0:base=list(map(F,[1,1,1]));dyn=list(map(F,[1,1,1]))
  rand=[F(rng.choice([0,30,70,100,150]))]*3 if case%2==0 else list(map(F,[rng.uniform(0,130) for _ in range(3)]))
  vm.fs(R+0xd60,base);vm.fs(E+0x7e4,base);vm.fs(R+0xd6c,rand);vm.fs(ES+0x160,dyn)
  direct=list(map(F,[rng.uniform(-2,2) for _ in range(3)]));s=F(rng.uniform(-3,3));ds=F(rng.uniform(-2,2))
  if case==0:direct=list(map(F,[0,1,0]));s=F(2);ds=F(.5)
  vm.fs(R+0xcfc,direct);vm.fs(R+0xcf8,[s]);vm.fs(E+0x7d8,[s]);vm.fs(ES+0x240,[ds]);vm.fs(ES+0x21c,[0])
  seed=rng.getrandbits(32);vm.w(E+0xbc,seed)
  m.mem_write(STACK+0xf0000,bytes(0x30))
  ret=vm.call(0x710081e3e4,E,0,PI,CH,A,0,0,0,fargs=(0,0,0))
  vel=bytes(m.mem_read(HEAP+0xa100,12));scale=bytes(m.mem_read(HEAP+0xa300,12))
  # Initial random sample is consumed by velRandom even when 0; scale begins with LCG(seed).
  rs=LCG(seed); exp=[]
  if rand[0]==rand[1]==rand[2]:
   u=F(F(rs)*F(2**-32));factor=F(F(F(F(rand[0]/F(-100))*F(rs))*F(2**-32))+F(1))
   exp=[F(F(base[i]*factor)*dyn[i]) for i in range(3)]
  else:
   for i in range(3):
    u=F(F(rs)*F(2**-32));factor=F(F(1)-F(F(rand[i]/F(100))*u));exp.append(F(F(base[i]*factor)*dyn[i]));rs=LCG(rs)
  expvel=[F(F(F(x*F(s*ds))+F(0))*F(1)) for x in direct]
  for key,actual,expected in (('particleScale',scale,exp),('designatedDirScale',vel,expvel)):
   match=actual==struct.pack('<3f',*expected) and ret==1
   out[key]['ok' if match else 'bad']+=1
   if not match and len(out['examples'])<6:out['examples'].append({'case':case,'key':key,'ret':ret,'actual':list(struct.unpack('<3f',actual)),'expected':list(map(float,expected)),'rand':list(map(float,rand))})
 out['scope']='shape0; angle=0; B3B=0; follow=NONE; no inheritance, child emitters, callbacks, random velocity or momentum. Initializer writer disassembled separately.'
 (ROOT/'analysis/completion/r7/fx_particle_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
 if out['designatedDirScale']['bad'] or out['particleScale']['bad']:raise SystemExit(1)
if __name__=='__main__':main()


