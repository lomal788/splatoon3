"""Execute original Phive pair-mask predicates; synthetic tables, no solver claims."""
import json, random, struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0
from network_uc import UC, BASE
ROOT=Path(__file__).resolve().parents[2]

def run():
    h=UC(); mu=h.mu
    A=h.alloc(0x200); B=h.alloc(0x200); fa=h.alloc(0x40); fb=h.alloc(0x40)
    module=h.alloc(0x200); world=h.alloc(0x500); provider=h.alloc(0x80); table=h.alloc(0x400); vt=h.alloc(0x20)
    def q(a,v): mu.mem_write(a,struct.pack('<Q',v))
    def u(a,v): mu.mem_write(a,struct.pack('<I',v & 0xffffffff))
    q(A+0x180,fa); q(B+0x180,fb)
    q(BASE+0x599dfa8,module); q(module+0xe8,world); q(world+0xb8,provider);q(provider+0x28,table)
    q(table,vt); q(vt+8,0x30000300)
    mu.mem_write(BASE+0x599f7e0,b'\1')
    stub_calls=0
    def hook(m,a,s,d):
        nonlocal stub_calls
        stub_calls+=1; m.reg_write(UC_ARM64_REG_X0,1)
    mu.hook_add(UC_HOOK_CODE,hook,begin=0x30000300,end=0x30000300)
    rng=random.Random(20261003); cases=[]; mismatches=[]; passed=0
    groups=[(0,0),(0,1),(1,0),(1,1),(1,2),(2,1),(65535,65535),(65535,1)]
    for i in range(4096):
        ga,gb=groups[i % len(groups)]; la=rng.randrange(29);lb=rng.randrange(29);sa=rng.randrange(27);sb=rng.randrange(27)
        if i<64: la=(i//8)%8;lb=i%8;sa=(i//8)%8;sb=i%8
        rows=[[rng.getrandbits(32) for _ in range(32)] for _ in range(3)]
        for block,off in zip(rows,[0x190,0x210,0x290]):
            mu.mem_write(table+off,struct.pack('<32I',*block))
        ma=rng.getrandbits(32);mb=rng.getrandbits(32);na=rng.getrandbits(32);nb=rng.getrandbits(32)
        if i%16<4: ma=mb=na=nb=0xffffffff
        u(fa+8,la|(sa<<6));u(fb+8,lb|(sb<<6));u(fa+0x18,ma);u(fb+0x18,mb);u(fa+0x1c,na);u(fb+0x1c,nb)
        mu.mem_write(fa+0x30,struct.pack('<H',ga));mu.mem_write(fb+0x30,struct.pack('<H',gb))
        ti=0 if ga==0 or gb==0 else (1 if ga==gb else 2)
        bit=lambda word,n:(word>>(n&31))&1
        forward=bit(rows[ti][la],lb);reverse=bit(rows[ti][lb],la)
        expected=forward & bit(ma,lb) & bit(na,sb) & reverse & bit(mb,la) & bit(nb,sa)
        got_select=h.call(BASE+0x3af44e8,A,B) & 0xffffffff
        got=h.call(BASE+0x3c4dd30,A,B) & 0xffffffff
        ok=(got_select==forward and got==expected)
        passed+=ok
        case={'i':i,'groups':[ga,gb],'layer':[la,lb],'sublayer':[sa,sb],'table_index':ti,'select_expected':forward,'select_original':got_select,'pair_expected':expected,'pair_original':got}
        if i<16: cases.append(case)
        if not ok: mismatches.append(case)
    out={'original_functions':['0x7103af44e8','0x7103c4dd30'],'cases':4096,'passed':passed,'mismatches':mismatches,'sample':cases,'stub_calls':stub_calls,'stubs':['table vt+0x8 type-query returns 1; original bit predicates execute unchanged'],'unverified':['shapeTag decoding and shape-specific overrides','world+0x18 bit3 optional callback/debug exclusions','table loading from PhiveConfig','solver and task scheduling'],'synthetic_state':'packed indices layer 0..28, sublayer 0..26; arbitrary 32-bit masks; groups 0,1,2,65535'}
    p=ROOT/'analysis/completion/collision_filter_emu.json'; p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Phive original predicate: {passed}/4096 exact integer matches; mismatches={len(mismatches)}; result={p}')
    if mismatches: raise SystemExit(1)
if __name__=='__main__':run()

def run_shape_tag():
    from unicorn.arm64_const import UC_ARM64_REG_X3
    h=UC();mu=h.mu
    shape=h.alloc(0x40);info=h.alloc(0x40);mesh=h.alloc(0x40);table=h.alloc(8192*8);dispatch=h.alloc(16*0x200);out1=h.alloc(4);out2=h.alloc(4);key=h.alloc(4)
    q=lambda a,v:mu.mem_write(a,struct.pack('<Q',v))
    q(shape+0x28,info);q(info+0x10,table);q(info+0x28,mesh);mu.mem_write(shape+0x18,b'\10');mu.mem_write(mesh+0x18,b'\10')
    q(BASE+0x57dd738,dispatch);q(dispatch+8*0x200+0xc0,0x30000398)
    rng=random.Random(20261003);rows=[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(8192)];mu.mem_write(table,b''.join(struct.pack('<II',*r) for r in rows));h.u32(key,123)
    tag=0
    def leaf(m,a,s,d):m.mem_write(m.reg_read(UC_ARM64_REG_X3)+0xbf8,struct.pack('<H',tag))
    mu.hook_add(UC_HOOK_CODE,leaf,begin=0x30000398,end=0x30000398)
    mismatches=[];passed=0;sample=[]
    for i in range(1024):
        tag=[0,1,31,32,8191,8192,0xffff,rng.randrange(65536)][i%8];count=[0,1,32,8192][(i//8)%4]
        h.u32(info+8,count);h.u32(out1,0xa1b2c3d4);h.u32(out2,0x12345678)
        index=tag&0x1fff;exp=(1,*rows[index]) if index<count else (0,0xa1b2c3d4,0x12345678)
        got=(h.call(BASE+0x3ad6a70,out1,out2,shape,key,0)&0xffffffff,h.ru32(out1),h.ru32(out2))
        ok=exp==got;passed+=ok;row={'tag':tag,'index':index,'count':count,'expected':exp,'original':got}
        if i<16:sample.append(row)
        if not ok:mismatches.append(row)
    out={'function':'0x7103ad6a70','cases':1024,'passed':passed,'mismatches':mismatches,'sample':sample,'stubs':['Havok dispatch type8 slot+0xc0 supplies synthetic shapeTag at result+0xbf8'],'unverified':['actual mesh leaf and shapeTag decoding','bphsh loader attaching filter table','compound shape type15 path']}
    p=ROOT/'analysis/completion/collision_shape_tag_emu.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'original leaf filter indexing: {passed}/1024 exact integer matches; mismatches={len(mismatches)}; result={p}')
    if mismatches:raise SystemExit(1)
if __name__=='__main__':run_shape_tag()
