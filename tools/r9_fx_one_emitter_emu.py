"""Native OneEmitter matrix queue/CPU capacity admission; synthetic memory, no callable stubs."""
import sys,struct,json,random
from pathlib import Path
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_PC
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import END
R=Path(__file__).resolve().parents[2];e=GUC();rng=random.Random(0x137f558);F=np.float32
slot=e.alloc(0x100);handle=e.alloc(16);S=e.alloc(0x2c0);E=e.alloc(0x900);D=e.alloc(0xf00);buf=e.alloc(0x60*8);mat=e.alloc(48)
e.wq(slot+8,handle);e.wq(handle,S);e.u32(handle+8,37);e.u32(S+0x54,37);e.wq(S+0x280,buf);e.wq(E+0xb0,D)
cases=0;adds=0
for k in range(2048):
 vals=[F(rng.uniform(-20,20)) for j in range(12)];raw=struct.pack('<12f',*vals);e.mu.mem_write(mat,raw)
 n=k%8;idx=(k//8)%9;gen=37 if k%13 else 38;flag=(k//13)%2;cpu=(k//26)%2;linked=k%5!=0
 alive=k%103;pcap=(k*13)%140;count=(k*17)%160;dt=F((k%7)/3);rate=F((k%5)/2);mult=F((k%4)/2)
 e.u32(handle+8,gen);e.u32(slot+0x14,count);e.wq(S+0x180,E if linked else 0);e.u32(S+0x288,n);e.u32(S+0x28c,idx);e.f32(S+0x7c,dt);e.mu.mem_write(S+0x3d,bytes([flag]));e.wq(S+0x10,0x400);e.mu.mem_write(S+0x3a,b'\0');e.mu.mem_write(slot+0x10,b'\x01')
 e.mu.mem_write(D+0xa92,bytes([cpu]));e.f32(D+0xb48,rate);e.f32(E+0x79c,rate);e.f32(E+0x64,mult);e.u32(E+0x2c,alive);e.u32(E+0x24,pcap);e.wq(E+0x88,0)
 e.mu.mem_write(buf,b'\xa5'*(0x60*8));token=rng.getrandbits(64)
 ready=gen==37 and (not linked or cpu!=0 or count>=alive+int(F(dt*rate)))
 admit=ready and flag!=0 and idx<n and (not linked or cpu!=0 or pcap>=alive+int(F(F(mult*dt)*rate)))
 expected=bytearray(b'\xa5'*(0x60*8))
 if admit:
  r=idx*96;words=struct.unpack('<12I',raw);cols=[]
  for c in range(4):cols.extend((words[c],words[4+c],words[8+c],0))
  struct.pack_into('<16I',expected,r,*cols);struct.pack_into('<4fQfB',expected,r+0x40,1,1,1,0,token,float(dt),1);adds+=1
 e.call(0x710137f558,slot,mat,token)
 assert e.mu.reg_read(UC_ARM64_REG_PC)==END,('no LR',k)
 assert bytes(e.mu.mem_read(buf,len(expected)))==expected,('record',k,ready,admit)
 assert struct.unpack('<I',e.mu.mem_read(S+0x28c,4))[0]==idx+int(admit),(k,'count')
 assert bytes(e.mu.mem_read(slot+0x10,1))==bytes([0 if ready else 1]),(k,'slotflag')
 assert bytes(e.mu.mem_read(S+0x3a,1))==bytes([int(ready)]),(k,'enabled')
 assert e.rq(S+0x10)==(0x400|int(ready)),(k,'bits')
 cases+=1
out={'date':'2026-10-03','cases':cases,'records_added':adds,'mismatch':0,'original':['137F558','137F4BC','0817E40','08178B0','080EBE4','0817B28','080EED8'],'callable_stubs':[],'unhandled_plt':e.plt_stubbed,'boundary':'synthetic valid handle/set/emitter memory; resource allocation, full frame birth/GPU render not executed'}
assert not e.plt_stubbed
(R/'analysis/completion/r9/fx_one_emitter_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
