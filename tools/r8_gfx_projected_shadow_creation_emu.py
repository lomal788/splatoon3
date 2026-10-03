"""Original projected-shadow allocation/record-constructor block, explicit bounds."""
import json,math,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import BASE,STACK,END
ROOT=Path(__file__).resolve().parents[2]
e=GUC(); scene=e.alloc(0x5000);manager=scene+0xf00;cfg=e.alloc(0x1a00);records=e.alloc(0x7f8*4);result=[];accepted=[];counts=[]
e.wq(BASE+0x59975c0,0);e.wq(BASE+0x5999210,0)
fnstop=BASE+0x374d330

def hook(mu,pc,n,ctx):
 if pc==fnstop:mu.emu_stop();return
 if pc==BASE+0x083d2f0:
  counts.append(mu.reg_read(UC_ARM64_REG_X0));mu.reg_write(UC_ARM64_REG_X0,records);accepted.append('native allocator boundary')
 elif pc in [BASE+0x3e9be40,BASE+0x3e9be30]:
  x=struct.unpack('<f',struct.pack('<I',mu.reg_read(UC_ARM64_REG_S0)))[0];v=math.sin(x) if pc==BASE+0x3e9be40 else math.cos(x)
  mu.reg_write(UC_ARM64_REG_S0,struct.unpack('<I',struct.pack('<f',v))[0]);accepted.append('sinf/cosf external math')
 else:return
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
identity=b''.join(e.mu.mem_read(BASE+x,16) for x in [0x4997c90,0x4998180,0x4997170])
for i in range(64):
 count=i%5;sp=STACK+0x80000;e.mu.mem_write(scene,bytes(0x5000));e.mu.mem_write(records,bytes([i+1])*(0x7f8*4));e.u32(cfg+0x19e0,count);e.wq(sp+0x80,manager);e.mu.reg_write(UC_ARM64_REG_SP,sp);e.mu.reg_write(UC_ARM64_REG_X25,cfg);e.mu.reg_write(UC_ARM64_REG_X26,manager);counts.clear()
 e.mu.emu_start(BASE+0x374d134,END,count=2000000)
 assert e.mu.reg_read(UC_ARM64_REG_PC)==fnstop
 assert e.ru32(scene+0x27f8)==count
 assert e.rq(scene+0x2800)==(records if count else 0)
 assert counts==([count*0x7f8] if count else [])
 for j in range(count):
  p=records+j*0x7f8
  assert e.rq(p)==BASE+0x572cc18
  assert bytes(e.mu.mem_read(p+0x5ac,12))==struct.pack('<3f',1,1,1)
  assert bytes(e.mu.mem_read(p+0x5b8,2))==b'\0\1'
  assert bytes(e.mu.mem_read(p+0x530,48))==identity
  assert bytes(e.mu.mem_read(p+0x360,8))==struct.pack('<2f',1,1)
  assert e.ru32(p+0x4e8)==0
 result.append({'count':count,'pointer':e.rq(scene+0x2800)})
known={'sinf','cosf'};unknown=set(e.plt_stubbed)-known
assert not unknown,unknown
out={'date':'2026-10-03','block_cases':64,'record_cases':sum(x['count'] for x in result),'mismatch':0,'original_block':'710374d134..710374d32c','native_base_ctor':'7103756cc8 whole;360154c/35b7160/35ebef8 also native','services':sorted(set(accepted)),'known_PLT':sorted(set(e.plt_stubbed)),'unknown_PLT':sorted(unknown),'checks':'actualmalloc size 7f8*count, Scene27f8/2800,pairDensity1,flags0/1,matrix48B,VT572cc18,Scale1,Factor0','limits':'scene manager init other than this block/config resource loader/liveLobby allocation not executed;officialC++symbol stripped;identity tag aglprojsdw/projection_shadow native'}
(ROOT/'analysis/completion/r8/projected_shadow_creation_emu.json').write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps(out,indent=2))
