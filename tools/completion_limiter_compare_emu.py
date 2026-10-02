"""Alto 제한기 비교 3개 원본 실행. 필드의 게임 의미/정렬 뒤 정지 순서는 별도 미확정."""
import json,random,struct
from pathlib import Path
from network_uc import UC
ROOT=Path(__file__).resolve().parents[2]
u=UC(); m=u.mu; A=u.alloc(0x240); B=u.alloc(0x240); XA=u.alloc(0x30); XB=u.alloc(0x30)
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
wq=lambda a,x:m.mem_write(a,struct.pack('<Q',x))
base=0x710599aa80; gate=0x71057349d0
rng=random.Random(0x3848c88)
def priority(v,g,bit):
    other=v['flags']&~(1<<(bit&31))
    if (g[0] and (v['state']&0xfffffffe)==6) or (g[1] and other): return -1
    p=f32(f32(v['c4']*v['cc'])*v['factor'])
    if g[2] and v['flags'] and not other:p=f32(p-1)
    return int(f32(p*255))
def raw_priority(v):return int(f32(f32(f32(v['c4']*v['cc'])*v['factor'])*255))
def order(v,g,bit,invert):
    other=v['flags']&~(1<<(bit&31))
    if (g[0] and (v['state']&0xfffffffe)==6) or (g[1] and other):return -(1<<63)
    o=(~v['order']&0xffffffff) if invert else v['order']
    if g[2] and v['flags'] and not other:o-=0xffffffff
    return o
counts={hex(x):0 for x in [0x7103848c88,0x7103848e34,0x7103849000]}
for i in range(768):
    g=[bool((i>>k)&1) for k in range(3)]; bit=(i//8)%5
    m.mem_write(base,bytes([g[0],0,0,0,g[1],0,0,0,g[2]]));u.u32(gate,bit)
    vs=[]
    for a,ext in [(A,XA),(B,XB)]:
        v={'state':rng.choice([0,1,6,7,8]),'flags':rng.choice([0,1<<bit,1,3,0xff]),'order':rng.choice([0,1,22,0x7fffffff,0x80000000,0xffffffff]),'c4':f32(rng.uniform(-.5,1.5)),'cc':f32(rng.uniform(.01,1.5)),'factor':f32(rng.uniform(.01,1.5))}
        vs.append(v);u.u32(a+4,v['state']);u.u32(a+8,v['order']);m.mem_write(a+0xe,bytes([v['flags']&0xff]));u.f32(a+0xc4,v['c4']);u.f32(a+0xcc,v['cc']);wq(a+0x210,ext);u.f32(ext+0x18,v['factor'])
    a,b=vs
    for fn,invert in [(0x7103848c88,None),(0x7103848e34,True),(0x7103849000,False)]:
        if invert is None:exp=priority(b,g,bit)-priority(a,g,bit)
        else:
            oa=order(a,g,bit,invert);ob=order(b,g,bit,invert)
            exp=-1 if oa>ob else (1 if oa<ob else raw_priority(b)-raw_priority(a))
        got=u.call(fn,A,B)&0xffffffff;got=got-(1<<32) if got&(1<<31) else got
        assert got==exp,(i,hex(fn),g,bit,a,b,got,exp)
        counts[hex(fn)]+=1
for fn in [0x7103848c88,0x7103848e34,0x7103849000]:
    assert (u.call(fn,0,B)&0xffffffff)==0
    assert (u.call(fn,A,0)&0xffffffff)==0
out={'comparison_bit_matches':counts,'null_cases':6,'stubs':[],'inputs':'global guard flags 599aa80/84/88 all 8 combinations, bit selector 0..4; state 6/7, flags 0/type bit/other, order boundaries; factor from voice+210->+18','limits':['+180 vtable factor branch not executed','runtime guard flag writers, voice+8 meaning and sorted survival not executed']}
(ROOT/'analysis/completion/fx_limiter_compare_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
