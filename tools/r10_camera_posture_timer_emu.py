"""Original B+ad0 post-shot writer, gated countdown and main-stage drain blocks.

PostDelay n=4 is an explicit existing-data input after the original getter BLR.
The countdown activation predicate is supplied; its prior SM/input calculation
is not executed. Selected original writes are not a whole game frame.
"""
from pathlib import Path
import itertools, json, random
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ


def s32(v):
    v &= 0xffffffff
    return v-0x100000000 if v & 0x80000000 else v


def main():
    u=PUC(); m=u.mu; b=u.alloc(0xb000)
    sp=STACK+STACK_SZ-0x4000
    rng=random.Random(0x24b29d4)
    bad=[]; samples=[]
    counts=dict(postShot=2048, countdown=3072, mainDrain=512)
    fields=[0xad0,0xad4,0xad8,0xadc,0xabc,0xab8,0xac4]
    literals={0x58bbc20:u.r32(BASE+0x58bbc20),0x58bbf2c:u.r32(BASE+0x58bbf2c),
              0x58bbf30:u.r32(BASE+0x58bbf30),0x58bbf3c:u.r32(BASE+0x58bbf3c)}
    assert list(literals.values())==[4,90,12,4], literals

    def run(start,end):
        m.reg_write(UC_ARM64_REG_SP,sp)
        m.emu_start(BASE+start,BASE+end,count=1000)
        assert m.reg_read(UC_ARM64_REG_PC)==BASE+end

    def check(group,i,got,expected,inp):
        if got!=expected:bad.append(dict(group=group,case=i,got=got,expected=expected,input=inp))

    boundaries=[-0x80000000,-1,0,1,3,4,5,81,82,83,90,0x7fffffff]
    for i in range(counts['postShot']):
        old=[boundaries[(i+j)%len(boundaries)] for j in range(7)] if i<96 else [rng.randint(-100,300) for _ in fields]
        for off,v in zip(fields,old):u.w32(b+off,v)
        m.reg_write(UC_ARM64_REG_X21,b); m.reg_write(UC_ARM64_REG_W0,4)
        run(0x24b29b0,0x24b2a40)
        thresholds=[82,4,4,8,4,4,4]
        got=[u.rs32(b+off) for off in fields]
        expected=[max(v,t) for v,t in zip(old,thresholds)]
        check('postShot',i,got,expected,old)

    for i in range(counts['countdown']):
        old=boundaries[i%len(boundaries)] if i<128 else rng.randint(-100,300)
        air=[-1,0,1,3,4,5,99][i%7]; active=(i//7)%2
        u.w32(b+0xad0,old);u.w32(b+0xc0,air)
        m.reg_write(UC_ARM64_REG_X19,b);m.reg_write(UC_ARM64_REG_X22,b+0xad0)
        m.reg_write(UC_ARM64_REG_W11,active)
        run(0x24a03f8,0x24a0444)
        floor=90 if active else 0
        expected=max(s32(old-1),floor) if air<4 else max(old,floor)
        got=u.rs32(b+0xad0)
        check('countdown',i,got,expected,[old,air,active])
        if i<14:samples.append(dict(old=old,air=air,active=active,result=got))

    for i in range(counts['mainDrain']):
        old=[boundaries[(i+j)%len(boundaries)] for j in range(4)] if i<48 else [rng.randint(-100,300) for _ in range(4)]
        for off,v in zip(fields[:4],old):u.w32(b+off,v)
        m.reg_write(UC_ARM64_REG_X27,b);m.reg_write(UC_ARM64_REG_W14,4)
        run(0x2481aac,0x2481b08)
        got=[u.rs32(b+off) for off in fields[:4]]
        expected=[max(v,4)-4 for v in old]
        check('mainDrain',i,got,expected,old)

    result=dict(scope=__doc__,cases=counts,totalCases=sum(counts.values()),mismatches=bad,
                literalConstants={hex(k):v for k,v in literals.items()},samples=samples,
                null=u.null_calls,auto=u.auto_pages,fault=u.faults,plt=u.plt_stubbed,libm=u.libm_used,
                boundaries=['post-shot pre-block common side effects/getter skipped; n=4 existing actual Shooter data',
                            'activation bool and air count supplied; raw producer bool not fully executed',
                            'main-stage drain entry condition not executed; four writes/integers only',
                            'all other state writers, live Lby actor and whole frame remain unresolved'])
    out=Path('analysis/camera_100_r10/timer');out.mkdir(parents=True,exist_ok=True)
    (out/'timer_native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['scope','samples','mismatches','boundaries']}))
    print('mismatches',len(bad),bad[:4])
    assert not (bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or u.libm_used)


if __name__=='__main__':
    main()
