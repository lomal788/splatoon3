"""Original final integration block0a4c12c..188: double COM += promoted f32(v*dt), then f32 cache. This is a block proof, not whole collision step."""
import json,struct,random
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,STACK,STACK_SZ
from unicorn.arm64_const import UC_ARM64_REG_SP,UC_ARM64_REG_X10,UC_ARM64_REG_Q0,UC_ARM64_REG_D3
u=PUC();M=u.alloc(0x80);SP=STACK+STACK_SZ-0x10000;rng=random.Random(0xa4c12c);mismatch=[];samples=[]
for i in range(2048):
 scale=rng.choice([.01,1.,1e4,1e10,1e15]);old=[rng.uniform(-scale,scale) for j in range(3)];v=[np.float32(rng.uniform(-100,100)) for j in range(3)];dt=np.float32(rng.choice([0.,1/60,1/480,1/120,1.,-1/60]))
 u.mu.mem_write(M+0x10,struct.pack('<3d',*old));u.mu.mem_write(SP+0x160,struct.pack('<4f',dt,dt,dt,0.));u.mu.reg_write(UC_ARM64_REG_SP,SP);u.mu.reg_write(UC_ARM64_REG_X10,M);u.mu.reg_write(UC_ARM64_REG_Q0,int.from_bytes(struct.pack('<4f',*v,0.),'little'));u.mu.reg_write(UC_ARM64_REG_D3,int.from_bytes(struct.pack('<d',old[2]),'little'))
 u.mu.emu_start(0x7100a4c12c,0x7100a4c188,count=100)
 expect=[old[j]+float(np.float32(v[j]*dt)) for j in range(3)];e=struct.pack('<3d',*expect);ef=struct.pack('<3f',*(np.float32(x) for x in expect));got=bytes(u.mu.mem_read(M+0x10,24));gf=bytes(u.mu.mem_read(SP+0xf0,12))
 if got!=e or gf!=ef:mismatch.append(dict(i=i,old=old,v=[float(x) for x in v],dt=float(dt),got=got.hex(),expected=e.hex(),f32=gf.hex(),expected_f32=ef.hex()))
 if i<3:samples.append(dict(i=i,old=old,v=[float(x) for x in v],dt=float(dt),com=struct.unpack('<3d',got)))
r=dict(cases=2048,f64_fields=6144,f32_fields=6144,mismatch=mismatch,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,scope=__doc__)
Path('analysis/completion/r8/physics_com_integrate_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
