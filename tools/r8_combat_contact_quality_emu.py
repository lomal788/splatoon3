"""Original contact-cache hardcoded coefficients block0A21A9C..AE4, not full native contact solver."""
import random,json,struct
from pathlib import Path
from r6_player_uc import PUC
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X13,UC_ARM64_REG_PC,UC_ARM64_REG_LR
u=PUC();p=u.alloc(0x120);rng=random.Random(0x8a21ae4);bad=[];samples=[]
def end(mu,addr,size,user):mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
u.mu.hook_add(UC_HOOK_CODE,end,begin=0x7100a21ae8,end=0x7100a21ae8)
for i in range(1024):
 flags=i if i<256 else rng.randrange(2**32);u.mu.mem_write(p,bytes(0x120));u.mu.reg_write(UC_ARM64_REG_X13,flags)
 error=u.call(0x7100a21a9c,0,p,0x2000001000)
 want=struct.pack('<4I',0 if flags&0x80 else 0x3f800000,0 if flags&0x80 else 0x3f800000,0 if flags&0x80 else 0xbd4ccccd,0 if flags&0x80 else 0xbd4ccccd)
 got=bytes(u.mu.mem_read(p+0xd0,16))
 if error or got!=want:bad.append(dict(i=i,flags=hex(flags),got=got.hex(),expected=want.hex(),error=error))
 if i<4 or i in [127,128,255]:samples.append(dict(i=i,flags=hex(flags),values=struct.unpack('<4f',got)))
out=dict(cases=1024,f32_fields=4096,mismatch=bad,samples=samples,null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__,boundary='stop immediately at0a21ae8;fixturex1base,qualityflagsW13;actualproducer LDRx4+2C read separately')
Path('analysis/completion/r8/contact_quality_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));assert not bad
