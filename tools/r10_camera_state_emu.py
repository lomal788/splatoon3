"""r10 native camera input producers; actual ARM64 blocks, no math/PLT stubs.

Inputs are synthetic fixtures. This does not execute an ordinary Lby frame or
prove which actor/event supplies them. All output files remain in this repo.
"""
import json
import random
import struct
from pathlib import Path

import numpy as np
from unicorn.arm64_const import *
from network_uc import UC, BASE, STACK

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'
F = np.float32


def fb(x):
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]


def affine(a, b):
    # SDK12548f0: translation first, then three basis columns; FMUL/FADD,
    # never FMA. For translation add A.translation after the three products.
    out = []
    for c in range(4):
        for r in range(3):
            p = F(F(a[3+r] * b[c*3]) + F(a[6+r] * b[c*3+1]))
            p = F(p + F(a[9+r] * b[c*3+2]))
            if c == 0:
                p = F(p + a[r])
            out.append(p)
    return out


def input_expected(v):
    # Exact ARM branch tests. fcmp NaN + b.gt / b.ls both do NOT branch.
    if not (v['p9210'] or v['p9212'] or v['control34']): return 1
    if v['mission'] not in (0, 5): return 1
    frame = v['frames'][v['index'] if v['index'] in (0, 1) else 0]
    if v['sm'] in (0xef, 0xf0) and frame <= F(95): return 1
    if v['sm'] == 0xf1: return 1
    if v['sm'] == 0xf2 and frame <= F(50): return 1
    if v['a860'] in (3, 4) or v['coop_gate'] in (5, 6, 7, 8): return 1
    if not v['control34'] or v['controlbf4'] > F(0): return 1
    if v['dokan'] in (1, 2) or v['active']: return 1
    if not 0 <= v['coop'] <= 9: return 1
    return (0x1fc >> v['coop']) & 1


def main():
    uc = UC()
    mu = uc.mu
    rng = random.Random(101031)
    b = uc.alloc(0xb000)
    s = b + 0x92f8
    actor = uc.alloc(0x400)
    affine_cases, clear_cases, predicate_cases = [], [], []
    # Direct entry at247b43c supplies X8=resolved actor, X20=S=B92f8;
    # stop before counter/SM dispatch at247b4e4. Actual SDK12548f0 executes.
    for i in range(512):
        a = [F(rng.uniform(-20, 20)) for _ in range(12)]
        local = [F(rng.uniform(-4, 4)) for _ in range(12)]
        if i == 0:
            a = list(map(F, [10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1]))
            local = list(map(F, [2, 3, 4, 1, 0, 0, 0, 1, 0, 0, 0, 1]))
        mu.mem_write(actor + 0x28c, struct.pack('<3f', *a[:3]))
        # Actor's physical 3x3 is row-major; producer repacks basis columns.
        mu.mem_write(actor + 0x298, struct.pack('<9f', *[a[3+c*3+r] for r in range(3) for c in range(3)]))
        mu.mem_write(s + 0x38, struct.pack('<12f', *local))
        mu.mem_write(s + 0x1c, b'\x7e')
        mu.reg_write(UC_ARM64_REG_X8, actor)
        mu.reg_write(UC_ARM64_REG_X20, s)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xe0000)
        mu.reg_write(UC_ARM64_REG_X29, STACK + 0xef000)
        mu.emu_start(BASE + 0x247b43c, BASE + 0x247b4e4, count=2000)
        exp = affine(a, local)
        expected = [fb(x) for x in exp[:3] + exp[9:12]]
        actual = list(struct.unpack('<6I', mu.mem_read(s, 24)))
        active = mu.mem_read(s + 0x1c, 1)[0]
        assert actual == expected and active == 1, (i, actual, expected, active)
        affine_cases.append({'input_actor_bits':[fb(x) for x in a],
                             'input_local_bits':[fb(x) for x in local],
                             'output_bits':actual,'active':active})
    for counter in (1, 2, 3, 15, 100, 0x7fffffff):
        for prior in (0, 1, 0xff):
            mu.mem_write(s + 0x1c, bytes([prior]))
            uc.u32(s+0x30, 0xffffffff)
            mu.reg_write(UC_ARM64_REG_W8, counter)
            mu.reg_write(UC_ARM64_REG_X20, s)
            mu.emu_start(BASE + 0x247b280, BASE + 0x247b294, count=30)
            actual = mu.mem_read(s + 0x1c, 1)[0]
            assert actual == 0
            clear_cases.append({'counter':counter,'prior':prior,'actual':actual})
    control, mission, sm, frames, a860, coop, dokan = [uc.alloc(n) for n in (0xc00,0x100,0x100,0x80,0x100,0x100,0x100)]
    p0 = b + 0xa5f9
    for off, obj in [(0x57,control),(0xcf,mission),(0x2cf,sm),(0x267,a860),(0x237,coop)]: mu.mem_write(p0+off,struct.pack('<Q',obj))
    mu.mem_write(sm+0x18,struct.pack('<Q',frames))
    base = dict(p9210=0,p9212=0,control34=1,mission=0,sm=0x82,frames=[F(96),F(96)],index=0,a860=0,coop_gate=0,controlbf4=F(0),dokan=0,active=0,coop=0)
    cases = [base.copy()]
    # Exact threshold/frame-index, signed state/uint gate, nonboolean byte,
    # and NaN branches, followed by deterministic combined fixtures.
    choices = dict(p9210=[0,1,255],p9212=[0,1,255],control34=[0,1,255],mission=[-1,0,1,2,4,5,6],
                   sm=[0x82,0xee,0xef,0xf0,0xf1,0xf2,0xf3],index=[-1,0,1,2,7],a860=[-1,0,2,3,4,5],
                   coop_gate=[-1,0,4,5,6,7,8,9],controlbf4=[F(-1),F(-0.0),F(0),F(1),F(float('nan'))],
                   dokan=[-1,0,1,2,3,4],active=[0,1,255],coop=[-1,0,1,2,3,8,9,10,32,0x7fffffff])
    for k, values in choices.items():
        for x in values: cases.append(dict(base, **{k:x}))
    for state, threshold in [(0xef,95),(0xf0,95),(0xf2,50)]:
        for f in [F(threshold-1),F(threshold),np.nextafter(F(threshold),F(float('inf'))),F(float('nan')),F(float('inf'))]:
            for idx in [-1,0,1,2]: cases.append(dict(base,sm=state,frames=[f,F(0)],index=idx))
    for _ in range(2048):
        v = {k:rng.choice(values) for k,values in choices.items()}
        v['frames'] = [rng.choice([F(-1),F(50),F(51),F(95),F(96),F(float('nan'))]) for _ in range(2)]
        cases.append(v)
    for v in cases:
        mu.mem_write(b+0x9210,bytes([v['p9210']]))
        mu.mem_write(b+0x9212,bytes([v['p9212']]))
        mu.mem_write(control+0x34,bytes([v['control34']]))
        uc.u32(mission+0x38,v['mission']); uc.u32(sm+0xc8,v['sm'])
        uc.f32(frames+0x30,v['frames'][0]); uc.f32(frames+0x34,v['frames'][1])
        uc.u32(BASE+0x58bb8f4,v['index']); uc.u32(a860+0x38,v['a860'])
        # param4 can be different from B+a830; keep both inputs explicit.
        uc.u32(coop+0x38,v['coop_gate']); coop_arg=uc.alloc(0x40) if not predicate_cases else coop_arg
        uc.u32(coop_arg+0x38,v['coop'])
        uc.f32(control+0xbf4,v['controlbf4']); uc.u32(dokan+0x30,v['dokan'])
        mu.mem_write(s+0x1c,bytes([v['active']]))
        actual = uc.call(BASE+0x24c99f0,p0,control,dokan,coop_arg,s) & 0xffffffff
        expected = input_expected(v)
        assert actual == expected, (v,actual,expected)
        enc={k:([fb(z) for z in x] if k=='frames' else fb(x) if k=='controlbf4' else x) for k,x in v.items()}
        predicate_cases.append({'input':enc,'actual':actual,'expected':expected})
    out = dict(scope='synthetic raw producer inputs, actual native ARM instructions; no SDK/PLT/math stubs; not scene/caller event execution',
               producer_range=['0x710247b43c','0x710247b4e4'],native_math='0x71012548f0',
               counts={'affine_active':len(affine_cases),'clear_active':len(clear_cases),'input_predicate':len(predicate_cases)},
               mismatch=0,serialization='F32 input/output encoded as uint32 bits',
               affine_cases=affine_cases,clear_cases=clear_cases,predicate_cases=predicate_cases)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'native_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'counts':out['counts'],'mismatch':0,'output':str(OUT/'native_results.json')}))


if __name__ == '__main__': main()
