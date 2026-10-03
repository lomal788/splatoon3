"""r8 original interior-triangle enum values and actual narrowphase pair-cache gate.
Only a5c678..a5c68c instruction block is executed, not full manifolds/solver.
"""
import json,struct,random,sys
from pathlib import Path
from network_uc import UC,BASE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8');h=UC();m=h.mu;img=(R/'extracted/exefs/main.reloc.img').read_bytes();rec=h.alloc(0x30)
rows=[]
for i in range(15):
 n,v=struct.unpack_from('<Q',img,0x5468288+8*i)[0]-BASE,struct.unpack_from('<Q',img,0x5468300+8*i)[0]-BASE
 rows.append(dict(name=img[n:img.index(0,n)].decode(),value=struct.unpack_from('<I',img,v)[0]))
quality=[]
for i in range(20):
 n,v=struct.unpack_from('<Q',img,0x546a940+8*i)[0]-BASE,struct.unpack_from('<Q',img,0x546a9e0+8*i)[0]-BASE
 quality.append(dict(name=img[n:img.index(0,n)].decode(),value=struct.unpack_from('<I',img,v)[0]))
out={'shape_enum':rows,'quality_enum':quality,'gate_cases':0,'gate_mismatches':[],'scope':__doc__}
rng=random.Random(805)
for i in range(20000):
 a,b,p=[rng.randrange(65536) for _ in range(3)]
 m.reg_write(UC_ARM64_REG_X6,rec);m.reg_write(UC_ARM64_REG_W12,a);m.reg_write(UC_ARM64_REG_W11,b);m.reg_write(UC_ARM64_REG_W15,p);m.mem_write(rec+10,struct.pack('<H',p));m.emu_start(BASE+0xa5c678,BASE+0xa5c68c,count=8)
 got=struct.unpack('<H',m.mem_read(rec+10,2))[0];ex=p if not(p&8) or ((a&64) and (b&32)) else p&~8
 if got!=ex:out['gate_mismatches'].append([a,b,p,got,ex])
 out['gate_cases']+=1
(R/'analysis/completion/r8/physics_interior_gate_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('gate',out['gate_cases'],'mismatch',len(out['gate_mismatches']));print(rows);print(quality)
