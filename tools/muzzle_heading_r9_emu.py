"""Original isolated 2579244..92c8 heading reader. Bone producer/caller excluded."""
import json, random, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'web/tools'))
from network_uc import UC, STACK
from unicorn.arm64_const import UC_ARM64_REG_X19, UC_ARM64_REG_SP
f = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]
bits = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
u = UC(); b = u.alloc(0x4000); a = u.alloc(0x200); body = u.alloc(0x600); w = u.alloc(0x200); h = u.alloc(0x80)
u.mu.mem_write(b+0x3aa8, struct.pack('<Q', a)); u.mu.mem_write(a+0x108, struct.pack('<Q', body))
u.mu.mem_write(b+0x88, struct.pack('<Q', w)); u.mu.mem_write(w+0x100, struct.pack('<Q', h))
r = random.Random(0x9244); rows = []
inputs = [([0,0,0],[0,0,1]),([-0.0,0,-0.0],[0,0,1]),([1e-30,0,-1e-30],[.2,.3,.4])]
inputs += [([f(r.uniform(-8,8)) for _ in range(3)], [f(r.uniform(-2,2)) for _ in range(3)]) for _ in range(2045)]
for col,d in inputs:
    col = list(map(f,col)); d = list(map(f,d))
    u.mu.reg_write(UC_ARM64_REG_X19,b); u.mu.reg_write(UC_ARM64_REG_SP,STACK+0x80000)
    u.mu.mem_write(STACK+0x80010,struct.pack('<f',col[0])); u.mu.mem_write(STACK+0x80030,struct.pack('<f',col[2]))
    u.mu.mem_write(body+0x538,struct.pack('<3f',*d))
    u.mu.emu_start(0x7102579244,0x71025792cc,count=100)
    actual = struct.unpack('<I',u.mu.mem_read(h+0x60,4))[0]
    length = f(f(f(col[0]*col[0])+0)+f(col[2]*col[2])); length = f(length**.5)
    x,z = f(-col[0]),f(-col[2]); y = 0.0
    if length > 0:
        k = f(1/length); x,y,z = f(k*x),f(k*0),f(k*z)
    expected = bits(f(f(f(x*d[0])+f(y*d[1]))+f(z*d[2])))
    assert actual == expected, (col,d,actual,expected)
    rows.append({'columnX':col,'rigForward':d,'expectedBits':actual})
(ROOT/'web/games/splatoon3/tests/fixtures/muzzle_heading_r9.json').write_text(json.dumps({'scope':'isolated original reader; selected bone producer and caller excluded; no external calls','rows':rows},separators=(',',':')),encoding='utf-8')
report = {'pass':True,'cases':len(rows),'mismatches':0,'begin':'0x7102579244','stop':'0x71025792cc','externalCalls':0,'producerExecuted':False,'scope':'synthetic M00/M20 and rig vector in fake behavior/body/holder; original instructions unchanged'}
(ROOT/'analysis/port_graphics_r9/muzzle_heading_emu.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
