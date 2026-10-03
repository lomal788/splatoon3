"""Replay existing 10325d4 native CPU SH packer for WebGL port fixtures, no stubs."""
import json, random, struct, sys
from pathlib import Path
from r5_gfx_stage_emu import Emu, re_readback_sh, f32_flush

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'analysis/port_common_r5/sh_pack_native.json'
rnd=random.Random(503128)
e=Emu(); cases=[]; mismatches=[]
def bits(v): return struct.unpack('<I',struct.pack('<f',float(v)))[0]
for i in range(128):
    e.reset_heap(); obj=e.alloc(0xd00);e.w(obj+2000,'H',0x2e);tex=[]
    for j in range(7):
        rec=obj+0x728+j*0xb0
        l1,l2,data=e.alloc(0x20),e.alloc(0x110),e.alloc(0x40)
        e.w(rec,'I',0x10);e.w(rec+0x10,'Q',l1);e.w(l1+0x18,'Q',l2);e.w(l2+0x100,'Q',data);e.w(rec+0xa8,'H',0x2e)
        raw=[bits(rnd.uniform(-12,12)) for _ in range(4)]
        if i%7==0:raw[j%4]=rnd.getrandbits(32)&0x807fffff # native reader flushes subnormal to signed zero
        e.w(data+0x10,'4I',*raw)
        tex.append([struct.unpack('<f',struct.pack('<I',f32_flush(v)))[0] for v in raw])
    dst=e.alloc(0x80);e.call(0x71010325d4,x=(obj,),x8=dst)
    got=list(e.r(dst,'28I'));flag=e.r(dst+0x70,'B')[0]
    expected=[bits(v) for v in re_readback_sh(tex)]
    if got!=expected or flag!=1:mismatches.append(i)
    cases.append({'texels':tex,'bits':got,'valid':flag})
result={'nativeFunction':'0x71010325d4 + 0x7101034608','originalExecutions':len(cases),'comparedBits':len(cases)*28,'stubs':0,'mismatches':mismatches,'cases':cases}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
fixture=ROOT/'web/games/splatoon3/tests/fixtures/common_sh_native.json'
fixture.write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='cases'}));sys.exit(bool(mismatches))
