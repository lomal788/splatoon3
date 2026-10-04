"""Original Bad0 pre-block: 24a0038..00f4 using actual PlayerGrindRail VT.

G=[B+a670], actual VT5635660. No replacement predicate or instruction patch.
This does not execute 245aa00/24c8ee8 or supply a live Lby frame.
The old active harness key 'weapon' denotes this compound GrindRail result;
it is not a Weapon interface result.
"""
import json, random
from pathlib import Path
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ


def expected(d, threshold):
    state=d['state']
    excluded=(0x82 <= state <= 0x90 or 0xaa <= state <= 0xac or state in [0xed,0xee,0x10c])
    if d['173'] and not excluded:
        return 1
    if d['1c8'] & 1 and 0 <= d['1f0'] <= threshold:
        return 1
    return int(bool(d['1c0'] & 1) and bool(d['1d0'] & 0x80000000))


def main():
    u=PUC();m=u.mu;b=u.alloc(0xb000);g=u.alloc(0x600);sm=u.alloc(0x200)
    sp=STACK+STACK_SZ-0x4000
    u.wq(b+0xa670,g);u.wq(g,BASE+0x5635660);u.wq(b+0xa8c8,sm)
    threshold=u.rs32(BASE+0x58bd688)
    rng=random.Random(0x24a0038);bad=[];samples=[];coverage={'rail':0,'148':0,'108_sign':0,'false':0}
    states=[0,0x81,0x82,0x90,0x91,0xa9,0xaa,0xac,0xad,0xec,0xed,0xee,0xef,0x10b,0x10c,0x10d,0x10e,0x11d,0x11e]
    for i in range(4096):
        d={k:rng.choice([0,1,2,255]) for k in ['173','1c8','1c0']}
        d.update(state=states[i%len(states)] if i<1024 else rng.randint(0,0x120),
                 **{'1f0':rng.choice([-0x80000000,-1,0,1,threshold,threshold+1,0x7fffffff]),
                    '1d0':rng.choice([0,1,-1,-0x80000000,0x7fffffff])})
        for off in [0x173,0x1c8,0x1c0]:u.w8(g+off,d[f'{off:x}'])
        for off in [0x1f0,0x1d0]:u.w32(g+off,d[f'{off:x}'])
        u.w32(sm+0xc8,d['state']);u.wq(sp+0x98,g)
        m.reg_write(UC_ARM64_REG_SP,sp);m.reg_write(UC_ARM64_REG_X19,b)
        m.emu_start(BASE+0x24a0038,BASE+0x24a00f4,count=300)
        assert m.reg_read(UC_ARM64_REG_PC)==BASE+0x24a00f4
        got=m.reg_read(UC_ARM64_REG_W8);want=expected(d,threshold)
        if got!=want:bad.append(dict(case=i,input=d,got=got,expected=want))
        ex=0x82<=d['state']<=0x90 or 0xaa<=d['state']<=0xac or d['state'] in [0xed,0xee,0x10c]
        key='rail' if d['173'] and not ex else '148' if d['1c8']&1 and 0<=d['1f0']<=threshold else '108_sign' if want else 'false'
        coverage[key]+=1
        if i<12:samples.append(dict(input=d,got=got))
    result=dict(scope=__doc__,cases=4096,mismatches=bad,threshold=threshold,
                vtable='0x7105635660',slots={'100':'2530fe0','148':'2529960','120':'2531038','108':'2531020','1c8':'25310d0'},
                coverage=coverage,samples=samples,null=u.null_calls,auto=u.auto_pages,
                faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used)
    Path('analysis/camera_100_r10/timer/grind_gate_native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['scope','samples','mismatches']}))
    print('mismatches',len(bad),bad[:3])
    assert not (bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or u.libm_used)


if __name__=='__main__':main()
