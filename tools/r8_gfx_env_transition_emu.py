"""Execute original environment-transition tick. Only component scheduler and apply sink are hooks."""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import BASE
ROOT=Path(__file__).resolve().parents[2]
e=GUC();o=e.alloc(0x800);g=e.alloc(0x100);p=e.alloc(8);env=e.alloc(8);a=e.alloc(8);b=e.alloc(8);s=e.alloc(32);d=e.alloc(32)
e.wq(BASE+0x59a7838,g);e.wq(g+0x48,p);e.wq(p,env)
seen=[]
def hook(mu,pc,sz,u):
 if pc==BASE+0x10bf154:mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif pc==BASE+0x2b5fe88:
  seen.append((mu.reg_read(UC_ARM64_REG_S0),mu.reg_read(UC_ARM64_REG_X0),mu.reg_read(UC_ARM64_REG_X1),mu.reg_read(UC_ARM64_REG_X2)))
  mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
rg=random.Random(0x2b5c250);cases=0;early=0
for k in range(3072):
 n=rg.randrange(1,100000);c=rg.randrange(n)
 if k<8:n=(1,2,3,60,1,2,10,10000)[k];c=(0,0,2,59,0,1,1,9999)[k]
 e.mu.mem_write(o,b'\0'*0x800);e.wq(o+0x570,a);e.wq(o+0x578,b);e.u32(o+0x580,c);e.u32(o+0x584,n);e.mu.mem_write(o+0x6d1,b'\1')
 e.wq(o+0x590,s);e.u32(o+0x598,32);e.wq(o+0x628,d);e.u32(o+0x630,32)
 seen.clear();e.call(BASE+0x2b5c250,o)
 t=np.float32(1) if n==1 else np.float32(np.float32(c)/np.float32(np.float32(n)-np.float32(1)))
 bits=struct.unpack('<I',struct.pack('<f',t))[0]
 assert seen==[(bits,a,env,b)],(k,n,c,seen,bits)
 assert e.ru32(o+0x580)==c+1
 assert e.rq(o+0x578)==(0 if c+1>=n else b)
 cases+=1
for c,n,ap,bp in ((0,0,a,b),(2,2,a,b),(3,2,a,b),(0,2,0,b),(0,2,a,0),(-1,-2,a,b)):
 e.mu.mem_write(o,b'\0'*0x800);e.wq(o+0x570,ap);e.wq(o+0x578,bp);e.u32(o+0x580,c);e.u32(o+0x584,n);e.mu.mem_write(o+0x6d1,b'\1');seen.clear();e.call(BASE+0x2b5c250,o);assert not seen;assert e.ru32(o+0x580)==(c&0xffffffff);early+=1
out={'tick':'0x7102b5c250','cases':cases,'early_cases':early,'float32_bit_match':True,'writer':'0x7102b5af20 prefix N=int(duration), counter=0, old/new pointer selector','formula':'N==1 ? 1 : float32(counter)/(float32(N)-1)','services':['10bf154 generic component scheduler no-op','2b5fe88 apply sink records t,new,environment,old','libc memcpy exact copy'],'plt_stubbed':sorted(set(e.plt_stubbed)),'limits':['resource ready flag fixed true','optional sky model alpha branch disabled; not tested','transition request setup read, not executed']}
(ROOT/'analysis/completion/r8/env_transition_emu.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
