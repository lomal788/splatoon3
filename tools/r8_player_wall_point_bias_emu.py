"""r8 wall-contact point Y bias original 2c5c308/2c5d0b0 instruction ranges.
Synthetic input point Y and B a44/a48; no contact solver result claimed.
"""
import json,random,struct
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,RET_MAGIC,STACK,STACK_SZ
from unicorn.arm64_const import *
u=PUC();m=u.mu;B=u.alloc(0xb000);sp=STACK+STACK_SZ-0x20000;F=lambda x:float(np.float32(x));out={'cases':0,'mismatch':[],'scope':__doc__};rng=random.Random(308)
for i in range(4000):
 y=F(rng.uniform(-100,100));a=F(rng.choice((0,1,.95,rng.uniform(-2,2))));b=F(rng.choice((-.7,-1,0,rng.uniform(-2,2))));exp=F(y+F(a*b));u.wf(B+0xa44,a);u.wf(B+0xa48,b);m.reg_write(UC_ARM64_REG_X9,B);m.reg_write(UC_ARM64_REG_SP,sp)
 if i%2==0:
  m.reg_write(UC_ARM64_REG_S2,struct.unpack('<I',struct.pack('<f',y))[0]);m.emu_start(0x7102c5c308,0x7102c5c318,count=20);got=m.reg_read(UC_ARM64_REG_S2).to_bytes(4,'little')
 else:
  m.reg_write(UC_ARM64_REG_S0,struct.unpack('<I',struct.pack('<f',y))[0]);m.reg_write(UC_ARM64_REG_S2,struct.unpack('<I',struct.pack('<f',b))[0]);m.emu_start(0x7102c5d0b0,0x7102c5d0c0,count=20);got=bytes(m.mem_read(sp+0x60,4))
 out['cases']+=1
 if got!=struct.pack('<f',exp):out['mismatch'].append({'i':i,'got':got.hex(),'exp':struct.pack('<f',exp).hex()})
out.update(null_calls=sum(u.null_calls.values()),auto_pages=u.auto_pages,plt_stubbed=u.plt_stubbed);Path('analysis/completion/r8/player_wall_point_bias_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out))
