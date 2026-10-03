"""r8 new evidence: ResA00 resource-copy block -> original whole point birth attr5.
Original key interpolation helper, not GPU rendering. Reuses r7 VM constant binding only.
"""
import sys,struct,json,random
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r7_fx_transform_emu import VM,F,ROOT,HEAP,STACK
vm=VM();m=vm.mu; rng=random.Random(8190360)
E,R,ES,ER,A,PI,CH,TAB=[HEAP+x for x in (0,0x2000,0x4000,0x5000,0x6000,0x7000,0x8000,0x9000)]
ID=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
rot=0
for i in range(768):
 for p,n in [(E,0x1000),(R,0x1000),(ES,0x800),(ER,0x500),(A,0x300),(PI,0x100),(CH,0x200)]:m.mem_write(p,bytes(n))
 vm.q(E+0xb0,R);vm.q(E+0x80,ES);vm.q(E+0x250,ER);vm.q(ER+0x10,R)
 m.mem_write(R+0xa93,b'\1');m.mem_write(R+0xbe8,b'\1');vm.w(E+0x240,1)
 vm.q(0x71057d52f8,TAB);vm.q(0x71057d52f0,TAB);vm.fs(TAB,[0,1,0,0]);vm.fs(E+0x460,ID);vm.fs(E+0x360,ID)
 for k in range(6):vm.q(A+8*k,HEAP+0xa000+k*0x100);m.mem_write(HEAP+0xa000+k*0x100,bytes(0x100))
 base=[F(rng.uniform(-16,16)) for _ in range(3)];dyn=[F(rng.uniform(-16,16)) for _ in range(3)]
 if i<3:base=[F(0)]*3;base[i]=F(1);dyn=[F(0)]*3
 vm.fs(R+0xa00,base);vm.fs(ES+0x140,dyn)
 m.reg_write(UC_ARM64_REG_X8,R);m.reg_write(UC_ARM64_REG_X19,ER)
 m.emu_start(0x710081a0a0,0x710081a0b8,count=20)
 assert bytes(m.mem_read(ER+0x360,16))==struct.pack('<3fI',*base,0)
 vm.w(E+0xbc,rng.getrandbits(32));m.mem_write(STACK+0xf0000,bytes(0x30))
 assert vm.call(0x710081e3e4,E,0,PI,CH,A,0,0,0,fargs=(0,0,0))==1
 assert bytes(m.mem_read(HEAP+0xa500,12))==struct.pack('<3f',*[F(base[j]+dyn[j]) for j in range(3)])
 rot+=1
O,Done,K=HEAP+0xc000,HEAP+0xc100,HEAP+0xc200
keys=0;unsupported=0
for count in range(1,9):
 times=[F(i/max(count-1,1)) for i in range(count)]
 vals=[[F(rng.uniform(-20,20)) for j in range(3)] for i in range(count)]
 raw=b''.join(struct.pack('<4f',*v,t) for v,t in zip(vals,times));m.mem_write(K,raw)
 ts=[F(-.1),F(1.1)]+times+[F((times[i]+times[i+1])/2) for i in range(count-1)]
 for mode in [0,1,2,255]:
  for t in ts:
   initial=[F(91),F(92),F(93)];vm.fs(O,initial);m.mem_write(Done,b'\0')
   vm.call(0x7100822290,O,Done,K,count,mode,fargs=(t,))
   finished=0
   if count==1 or t<times[0]:expected=vals[0]
   elif t>=times[-1]:expected=vals[-1];finished=1
   else:
    q=next(i for i in range(count-1) if times[i]<=t<times[i+1])
    if mode==0:
     a=F(F(t-times[q])/F(times[q+1]-times[q]));expected=[F(vals[q][j]+F(F(vals[q+1][j]-vals[q][j])*a)) for j in range(3)]
    elif mode==1:expected=vals[q]
    else:expected=initial;unsupported+=1
   assert bytes(m.mem_read(O,12))==struct.pack('<3f',*expected)
   assert bytes(m.mem_read(Done,1))==bytes([finished]);keys+=1
out={'rotate_copy_block_then_birth_attr5':rot,'key_helper_cases':keys,'unsupported_mode_interior_retains_output':unsupported,'mismatches':0,'stubs':[],'scope':'exact original081a0a0..b8 copy block, whole081e3e4+point081fa94 with synthetic constant tables/nochildren, whole0822290 monotonic finite1..8keys; shader position5 read is static original program evidence'}
(ROOT/'analysis/completion/r8/vfx_rotate_keys_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
