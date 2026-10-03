"""r8 original audio parameter initialization block + getters + 60Hz setup/tick write blocks.
Synthetic already-allocated System/parameter buffers. Native audio backend not executed.
"""
import sys,struct,json,random
from pathlib import Path
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC,STACK,END
import numpy as np
B=0x7100000000;u=UC();mu=u.mu;s=u.alloc(0x200);p=u.alloc(0x1a0);cfg=u.alloc(0x180);game=u.alloc(0x30);rng=random.Random(8040320)
def ptr(a,v):mu.mem_write(a,struct.pack('<Q',v))
def run(a,end,args={}):
 for r,v in args.items():mu.reg_write(r,v)
 mu.reg_write(UC_ARM64_REG_SP,STACK+0xf0000);mu.reg_write(UC_ARM64_REG_LR,END);mu.emu_start(B+a,B+end,count=2000)
 assert mu.reg_read(UC_ARM64_REG_PC)==B+end
n=0
for i in range(256):
 mu.mem_write(p,rng.randbytes(0x1a0));mu.mem_write(s,b'\0'*0x200)
 run(0x38402e4,0x3840370,{UC_ARM64_REG_X0:p,UC_ARM64_REG_X19:s,UC_ARM64_REG_X20:0,UC_ARM64_REG_X21:cfg})
 assert bytes(mu.mem_read(p+0x20,4))==struct.pack('<f',1)
 assert struct.unpack('<Q',mu.mem_read(s+0x10,8))[0]==p
 ptr(B+0x599a3f8,s);assert u.call(B+0x37e11d8)==p
 u.call(B+0x38551f4,p);assert mu.reg_read(UC_ARM64_REG_S0)==0x3f800000
 run(0x3e071b4,0x3e071f8)
 assert u.rf32(p+0x14)==60 and bytes(mu.mem_read(p+0x1c,4))==struct.pack('<f',np.float32(1/60))
 assert bytes(mu.mem_read(p+0x2c,4))==struct.pack('<f',np.float32(np.float32(340)*np.float32(1)/np.float32(60)))
 n+=1
nt=0
ptr(B+0x59a7430,game)
for speed in [-2.,-0.,0.,.25,.5,1.,1.5,2.,10.,float('nan')]:
 for init in [0.,.125,1.,20.]:
  u.f32(p+0x18,init);u.f32(p+0x1c,init);u.f32(game+8,speed)
  run(0x3e0749c,0x3e074dc,{UC_ARM64_REG_X0:cfg})
  want=np.float32(speed) if speed>0 else np.float32(init)
  wantdt=np.float32(np.float32(speed)/np.float32(60)) if speed>0 else np.float32(init)
  assert bytes(mu.mem_read(p+0x18,4))==struct.pack('<f',want)
  assert bytes(mu.mem_read(p+0x1c,4))==struct.pack('<f',wantdt)
  assert u.rf32(p+0x20)==1;nt+=1
out={'initialization_block_getters_setup_cases':n,'tick_write_cases':nt,'mismatches':0,'unit_bits':'0x3f800000','unit':1.0,'stubs':[], 'original_blocks':['38402e4..3840370 parameter init (stop before383f418)','3e071b4..3e071f8 60Hz setup','3e0749c..3e074dc positive game speed update'],'whole_functions':['37e11d8 system parameter getter','38551f4 unit getter'],'scope':'synthetic already-allocated buffers; exact original blocks/getters; native renderer/SDK and remainder of engine initialization/tick not executed'}
Path('analysis/completion/r8/sound_unit_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
