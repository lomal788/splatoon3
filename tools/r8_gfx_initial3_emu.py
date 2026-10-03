"""r8 InitialFrame3 original full function vs independent f32 seed formula; no stubs."""
from pathlib import Path
import json,random,struct
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_PC
from r5_gfx_stage_emu import Emu,BASE,RET
F=np.float32;R=Path(__file__).resolve().parents[2];e=Emu();rng=random.Random(81019);n=0
for case in range(1536):
 e.reset_heap();node=e.alloc(32);body=e.alloc(64);ctx=e.alloc(64);slot=e.alloc(256);leaf=e.alloc(32);holder=e.alloc(256);entry=e.alloc(64);g=e.alloc(16)
 e.w(node+24,'Q',body);e.w(ctx+8,'Q',slot);e.w(body,'I',3);fixed=case%2;force=case%3==0;e.w(body+28,'II',0,int(force));e.w(body+36,'II',0,fixed);e.w(slot+204,'I',8 if case%5==0 else 0)
 seeds=[rng.randrange(2**32) for _ in range(4)];word=rng.randrange(2**32);start=F(rng.uniform(-50,50));end=F(rng.uniform(-50,200));e.w(ctx+40,'I',word);e.w(BASE+0x5997950,'Q',g);e.w(g,'4I',*seeds);old=case&0x7f;e.w(entry,'I',old)
 expseeds=seeds[:]
 if not fixed:
  t=seeds[0]^((seeds[0]<<11)&0xffffffff);word=(t^(t>>8)^seeds[3]^(seeds[3]>>19))&0xffffffff;expseeds=seeds[1:]+[word]
 unit=F((word>>9)/2**23);exp=F(F(F(end-start)*unit)+start)
 m=e.call(BASE+0x39c9fcc,[node,ctx,leaf,holder,entry,0],[start,end,F(123)])
 assert m.reg_read(UC_ARM64_REG_PC)==RET
 got=m.reg_read(UC_ARM64_REG_S0)&0xffffffff;bits=struct.unpack('<I',struct.pack('<f',exp))[0];assert got==bits,(case,hex(got),hex(bits));assert e.r(g,'4I')==tuple(expseeds);assert e.r(entry,'I')[0]==(old|128);n+=1
out={'date':'2026-10-03','function':'71039c9fcc','case':'InitialFrame mode3','count':n,'bit_mismatch':0,'stubs':[],'input':'synthetic finite start/end including reversed interval, fixed-context seed/global-seed paths; original bool getter','limits':'mode1/2/4/5/6/7 not covered; full ASB/GPU pose not executed'}
(R/'analysis/completion/r8/graphics_initial3_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))

