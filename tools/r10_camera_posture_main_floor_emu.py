"""Original main-stage Bad0..adc drain followed by stack-byte floor writers.

Stack3cd/3ce/3cf producers are supplied bytes. This is the original arithmetic
contract, not a proof of the producer or a whole PlayerBehavior frame.
"""
import json, random
from pathlib import Path
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ


def main():
    u=PUC();m=u.mu;b=u.alloc(0xb000);sp=STACK+STACK_SZ-0x4000
    rng=random.Random(0x2481b48);bad=[];samples=[]
    values=[-0x80000000,-1,0,1,3,4,5,7,8,9,81,82,90,0x7fffffff]
    for i in range(1024):
        old=[values[(i+j)%len(values)] for j in range(4)] if i<128 else [rng.randint(-100,400) for _ in range(4)]
        holds=[([0,1,2,255][(i//(4**j))%4]) for j in range(3)] if i<256 else [rng.randint(0,255) for _ in range(3)]
        for off,v in zip([0xad0,0xad4,0xad8,0xadc],old):u.w32(b+off,v)
        for off,v in zip([0x3cd,0x3ce,0x3cf],holds):u.w8(sp+off,v)
        for off in [0x3ca,0x3c9,0x3c8]:u.w8(sp+off,0)
        u.w32(b+0x524,0)
        m.reg_write(UC_ARM64_REG_X27,b);m.reg_write(UC_ARM64_REG_SP,sp)
        m.reg_write(UC_ARM64_REG_W14,4);m.reg_write(UC_ARM64_REG_W15,0)
        m.reg_write(UC_ARM64_REG_W13,0)
        m.emu_start(BASE+0x2481aac,BASE+0x2481b8c,count=200)
        assert m.reg_read(UC_ARM64_REG_PC)==BASE+0x2481b8c
        got=[u.rs32(b+off) for off in [0xad0,0xad4,0xad8,0xadc]]
        expect=[max(max(v,4)-4,4*h) for v,h in zip(old,[*holds,holds[2]])]
        if got!=expect:bad.append(dict(case=i,old=old,holds=holds,got=got,expected=expect))
        if i<8:samples.append(dict(old=old,holds=holds,got=got))
    result=dict(scope=__doc__,cases=1024,mismatches=bad,samples=samples,null=u.null_calls,
                auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used,
                expression='max(max(s32(old),4)-4,4*supplied_stack_byte); ad8/adc share3cf')
    Path('analysis/camera_100_r10/timer/main_floor_native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['scope','mismatches','samples']}))
    print('mismatches',len(bad),bad[:2])
    assert not (bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or u.libm_used)


if __name__=='__main__':main()
