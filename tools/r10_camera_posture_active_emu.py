"""Original 24a0100..0444 activation predicate followed by B+ad0 countdown.

The two 245aa00 results, Jetpack predicate result and compound PlayerGrindRail
virtual predicate result are explicit pre-block inputs. The historical key
'weapon' means the GrindRail result (corrected 2026-10-03). Their suppliers and
the whole frame are not executed. Body-relative fields and original globals are real
layouts. No instruction patch, helper replacement or null recovery is used.
"""
import json, math, random, struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def s32(x):
    x &= 0xffffffff
    return x - 0x100000000 if x & 0x80000000 else x


def reference(d, thresholds):
    gates = ((d['aim0'] | d['jetpack']) & 1) or (d['weapon'] & 1) or (
        d['state'] in [0x95, 0xe2] and d['b80c'] < 1)
    if gates:
        return True
    attack = (d['ab4'] < 1 and (d['aCount'] > 0 or d['a0'] or d['a1'])) or (
        d['ab8'] < 1 and (d['bCount'] > 0 or d['b0'] or d['b1'] or d['bExtra'])) or (
        d['ab8'] < 1 and (d['cCount'] > 0 or d['c0'] or d['c1'] or d['cExtra']))
    if attack:
        return False
    # FCSEL LT negates an unordered NaN too; subsequent GE is false for NaN.
    if abs(d['x']) >= thresholds['x'] or abs(d['y']) >= thresholds['y']:
        return True
    if d['air'] >= thresholds['air']:
        return False
    # FCMP/B.LT and B.PL/B.HI do take the following NaN paths.
    if math.isnan(d['b184']) or d['b184'] < thresholds['b184']:
        return False
    v = d['velocity']
    dot = f32(f32(f32(v[0]*v[0]) + f32(v[1]*v[1])) + f32(v[2]*v[2]))
    if math.isnan(dot) or dot >= thresholds['speed2']:
        return False
    if math.isnan(d['b47c']) or d['b47c'] > 0:
        return False
    return True


def main():
    u = PUC(); m = u.mu; b = u.alloc(0xb000); sm = u.alloc(0x200)
    sp = STACK+STACK_SZ-0x4000; fp = sp+0x130
    thresholds = dict(x=u.rf(BASE+0x58bbd80), y=u.rf(BASE+0x58bbd84),
                      air=u.rs32(BASE+0x58bbc20), b184=u.rf(BASE+0x58bbb60),
                      speed2=struct.unpack('<f', struct.pack('<I', 0x3716feb5))[0])
    rng = random.Random(0x24a0100); mismatches=[]; samples=[]; active_sample={}
    saw={'active':0,'inactive':0,'NaN':0}

    def trace(mu, pc, size, data):
        if pc == BASE+0x24a03bc:
            active_sample['value'] = mu.reg_read(UC_ARM64_REG_W11)
    h = m.hook_add(UC_HOOK_CODE, trace, begin=BASE+0x24a03bc, end=BASE+0x24a03bc)
    ints=[-0x80000000,-1,0,1,3,4,5,81,82,90,91,0x7fffffff]
    floats=[-1.,-0.,0.,.002,.003,.01,.02,.03,1.,float('nan')]
    for i in range(4096):
        d={key:rng.choice([0,0,0,1,2,3]) for key in ['aim0','aim1','jetpack','weapon']}
        d.update({key:rng.choice([-1,0,0,0,1,4]) for key in [
            'b80c','ab4','ab8','aCount','bCount','cCount']})
        d.update({key:rng.choice([0,0,0,1,255]) for key in [
            'a0','a1','b0','b1','bExtra','c0','c1','cExtra']})
        d.update(state=rng.choice([0,0x95,0xe2,0x85,0x94,0xe1,0x100]),
                 x=rng.choice(floats), y=rng.choice(floats),
                 air=rng.choice([-1,0,1,3,4,5,99]), old=rng.choice(ints),
                 b184=rng.choice(floats), b47c=rng.choice(floats),
                 velocity=[rng.choice(floats[:8]) for _ in range(3)])
        # Deterministic ordinary predicate cases include all exceptional compares.
        if i < 32:
            d.update({key:0 for key in ['aim0','aim1','jetpack','weapon','a0','a1',
                         'b0','b1','bExtra','c0','c1','cExtra','aCount','bCount','cCount']})
            d.update(state=0,b80c=0,ab4=0,ab8=0,air=0,old=82,x=0.,y=0.,
                     b184=1.,b47c=0.,velocity=[0.,0.,0.])
            if i < 10:d['x']=floats[i]
            elif i<20:d['b184']=floats[i-10]
            elif i<30:d['b47c']=floats[i-20]
            elif i==30:d['velocity'][0]=float('nan')
            else:d['aCount']=1
        scalar_ints={0x80c:'b80c',0xab4:'ab4',0xab8:'ab8',0x4d0:'aCount',
                     0x4e0:'bCount',0x518:'cCount',0xc0:'air',0xad0:'old'}
        for off,key in scalar_ints.items():u.w32(b+off,d[key])
        for off,key in {0x530:'a0',0x531:'a1',0x532:'b0',0x533:'b1',0x4f2:'bExtra',
                        0x534:'c0',0x535:'c1',0x52a:'cExtra'}.items():u.w8(b+off,d[key])
        for off,key in {0xaa4:'x',0xaa0:'y',0x184:'b184',0x47c:'b47c'}.items():
            d[key]=f32(d[key]);u.wf(b+off,d[key])
        d['velocity']=[f32(x) for x in d['velocity']]
        for off,v in zip([0x114,0x118,0x11c],d['velocity']):u.wf(b+off,v)
        u.w32(sm+0xc8,d['state']);u.wq(fp-0x80,sm)
        u.w32(fp-0x88,0);u.w32(fp-0x90,0);u.w32(fp-0x68,d['aim0'])
        for off in [0x40,0x50,0x60]:u.w32(fp-off,0)
        u.wq(sp+0x68,b+0xaa4)
        for reg,val in [(UC_ARM64_REG_SP,sp),(UC_ARM64_REG_X29,fp),
                        (UC_ARM64_REG_X19,b),(UC_ARM64_REG_X27,b),
                        (UC_ARM64_REG_X22,b+0xad0),(UC_ARM64_REG_X28,b+0x4d0),
                        (UC_ARM64_REG_X23,b+0x4e0),(UC_ARM64_REG_X21,b+0x518),
                        (UC_ARM64_REG_W26,d['jetpack']),(UC_ARM64_REG_W25,d['aim1']),
                        (UC_ARM64_REG_W8,d['weapon'])]:m.reg_write(reg,val)
        active_sample.clear()
        m.emu_start(BASE+0x24a0100,BASE+0x24a0444,count=500)
        assert m.reg_read(UC_ARM64_REG_PC)==BASE+0x24a0444
        active=reference(d,thresholds);floor=90 if active else 0
        expected=max(s32(d['old']-1),floor) if d['air']<4 else max(d['old'],floor)
        got=[active_sample.get('value'),u.rs32(b+0xad0)]
        if got != [int(active),expected]:mismatches.append(dict(case=i,input=d,got=got,expected=[int(active),expected]))
        saw['active' if active else 'inactive']+=1
        saw['NaN']+=int(any(math.isnan(x) for x in [d['x'],d['y'],d['b184'],d['b47c'],*d['velocity']]))
        if i<32:samples.append(dict(input=d,active=active,result=got[1]))
    m.hook_del(h)
    result=dict(scope=__doc__,cases=4096,mismatches=mismatches,thresholds=thresholds,
                outcomes=saw,samples=samples,null=u.null_calls,auto=u.auto_pages,
                faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used,
                boundary='pre-block aim0/aim1/Jetpack/GrindRail compound predicate results supplied; legacy key weapon is GrindRail; whole frame not executed')
    out=Path('analysis/camera_100_r10/timer/active_native.json')
    out.write_text(json.dumps(result,indent=2,allow_nan=True)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['scope','mismatches','samples']}))
    print('mismatches',len(mismatches),mismatches[:3])
    assert not (mismatches or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or u.libm_used)


if __name__=='__main__':main()
