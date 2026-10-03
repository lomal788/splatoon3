"""Original cloth dt call boundary; explicit TLS/allocator/hcl-step fixtures, no solver claim."""
import sys,struct,json,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import STUB,END
R=Path(__file__).resolve().parents[2];e=GUC();F=np.float32;rng=random.Random(0x3c0c0bc)
O=e.alloc(0x120);rows=e.alloc(0x58*2);inst=e.alloc(0x180);world=e.alloc(0x128);mgr=e.alloc(0x100);vt=e.alloc(0x30);threads=e.alloc(0x100);buf=e.alloc(0x100)
e.wq(mgr,vt);e.wq(vt+0x10,STUB+0x810);e.wq(0x710599dfa8,mgr);e.wq(threads+0x38,world);e.f32(0x71057236f0,100)
e.wq(O+0x18,rows);e.wq(O+0x28,world);e.wq(rows,inst);e.f32(rows+0x44,1);e.u32(O+0x10,1)
trace=[]
def hook(mu,a,size,user):
 if a==STUB+0x810:mu.reg_write(UC_ARM64_REG_X0,threads);return
 if a==0x7103c10648:
  x=mu.reg_read(UC_ARM64_REG_X0);e.wq(x,buf);e.u32(x+8,0);e.u32(x+12,0x80000004)
 elif a==0x7100cd3eac:trace.append(('step',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff))
 elif a==0x7103c0aae0:trace.append(('pre',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff))
 else:return
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
for a in [STUB+0x810,0x7103c10648,0x7100cd3eac,0x7103c0aae0]:e.mu.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
def invalid(mu,access,address,size,value,user):
 print("invalid",hex(mu.reg_read(UC_ARM64_REG_PC)),hex(address),size);return False
e.mu.hook_add(UC_HOOK_MEM_INVALID,invalid)
cases=0
for i in range(768):
 dt=F([0,1/60,1/30,-1/60,2/60][i%5] if i<32 else rng.uniform(-.05,.2));scale=F([0,1,.5,-1,2][i%5] if i<32 else rng.uniform(-2,3));warm=i%7==0
 e.mu.mem_write(O+0x48,struct.pack('<I',0x4000 if warm else 0));e.f32(rows+0x48,scale);e.mu.mem_write(O+0x50,bytes(0x70));trace.clear()
 e.call(0x7103c0c0bc,O,0,0,fargs=(float(dt),))
 bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0]
 expected=[('step',0x3d088889)]+[q for k in range(29) for q in [('pre',0x3d088889),('step',0x3d088889)]] if warm else [('step',bits(F(scale*dt)))]
 assert trace==expected,(i,dt,scale,trace,expected)
 assert e.mu.reg_read(UC_ARM64_REG_PC)==END
 assert e.ru32(O+0x48)&0x4000==0
 cases+=1
out={'date':'2026-10-03','cases':cases,'mismatch':0,'normal_step_dt':'f32(record+0x48 * frame_dt)','warmup_step_bits':'0x3D088889','warmup_steps':30,'warmup_pre_updates':29,'original':['3C0C0BC','CD3EA4'],'fixtures':['hcl step CD3EAC capture (solver excluded)','preupdate3C0AAE0 capture in warmup','3C10648 array allocator','thread-provider vt10','TLS returns0/current-core0 via named PLT'],'plt_fixtures':sorted(set(e.plt_stubbed)),'boundary':'synthetic cloth record; original dt/conditions/call order executed, SDK operators and actual frame dt writer only disassembly'}
assert set(e.plt_stubbed)<= {'_ZN2nn2os11GetTlsValueENS0_7TlsSlotE','_ZN2nn2os20GetCurrentCoreNumberEv'},set(e.plt_stubbed)
(R/'analysis/completion/r9/graphics_cloth_dt_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
