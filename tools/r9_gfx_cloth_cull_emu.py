"""Original actor after-phase CullFrame gate; exact dt, explicit step/interpolation fixtures."""
import sys,struct,json,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import END
R=Path(__file__).resolve().parents[2];e=GUC();F=np.float32;rng=random.Random(0xf73368)
A=e.alloc(0x800);arr=e.alloc(11*8);B=e.alloc(0x40);M=e.alloc(0x180);P=e.alloc(0x180);PC=e.alloc(0x90);rec=e.alloc(0x38);G=e.alloc(0x120)
e.u32(A+0x200,11);e.wq(A+0x208,arr);e.wq(arr+0x50,B);e.wq(B+0x18,M);e.wq(M+0x148,P);e.wq(A+0x510,PC);e.wq(PC+0x70,rec)
trace=[]
def hook(mu,a,size,user):
 if a==0x7103db1704:trace.append(('step',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff,mu.reg_read(UC_ARM64_REG_S1)&0xffffffff))
 else:trace.append(('interpolation',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff,mu.reg_read(UC_ARM64_REG_X1)&1))
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
for a in [0x7103db1704,0x71012cf69c]:e.mu.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0]
cases=0
for i in range(2048):
 period=[1,2,4,6][i%4];phase=(i//4)%period;frame=(i//24)%41;disabled=(i//984)%2;null=i%17==0;dt=F([1/60,1/30,0,-1/60][i%4] if i<64 else rng.uniform(-.2,.2));dframes=F(dt*60)
 e.wq(0x7105827e20,0 if null else G);e.u32(G+0xf0,frame);e.u32(rec+0x28,period);e.u32(rec+0x2c,phase);e.u32(rec+0x34,4 if disabled else 1);trace.clear()
 e.call(0x7100f73368,A,fargs=(float(dt),float(dframes)))
 do=disabled or period<2 or null or frame%period==phase
 sd=dt if disabled or period<2 else F(F(period)*dt)
 expected=([('step',bits(sd),bits(dframes))] if do else [])+[('interpolation',bits(dt),0)]
 assert trace==expected,(i,trace,expected)
 assert e.mu.reg_read(UC_ARM64_REG_PC)==END;cases+=1
out={'date':'2026-10-03','cases':cases,'mismatch':0,'original':'0F73368 whole','rule':'normal: global.frame%period==phase then dt=f32(period*inputdt); bypass flag4/period<2 unscaled; null global scaled call','fixtures':['3DB1704 downstream step boundary','12CF69C post bone interpolation boundary','nn::os read lock/unlock no-op'],'plt_fixtures':sorted(set(e.plt_stubbed)),'boundary':'synthetic actor slots/cloth record; downstream native chain independently disassembled, pose not simulated'}
assert set(e.plt_stubbed)<= {'_ZN2nn2os15AcquireReadLockEPNS0_20ReaderWriterLockTypeE','_ZN2nn2os15ReleaseReadLockEPNS0_20ReaderWriterLockTypeE'},set(e.plt_stubbed)
(R/'analysis/completion/r9/graphics_cloth_cull_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
