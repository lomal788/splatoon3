"""r7 physics: descriptor mask -> original rigid/character filter writers, randomized u32 comparison.
Original 3a5fe40,3af6088,3a85a8c execute. Mock world/provider, shape build hook, backend body creation stub.
Allocation is a host stub. This proves descriptor C0/C4/C8 -> F+10/+18/+1c, not BYML mask-name resolution.
"""
import json,random,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
from r5_gfx_char_uc import GUC
from network_uc import BASE as B,STUB
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8')
h=GUC();m=h.mu;m.mem_map(0x40000000,0x2000000);h.heap_next=0x40000000;h.wq(B+0x59975c0,0);state={};rets={}
def ret(v):m.reg_write(UC_ARM64_REG_X0,v);m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def hook(mu,a,s,d):
    if a==B+0x83d2f0:
        n=m.reg_read(UC_ARM64_REG_X0);p=h.alloc(n);state['last_alloc']=p;ret(p)
    elif a==B+0x3c4e8c4:ret(state['backend_body'])
    elif a in rets:ret(rets[a])
m.hook_add(UC_HOOK_CODE,hook,begin=B+0x83d2f0,end=B+0x83d2f0);m.hook_add(UC_HOOK_CODE,hook,begin=B+0x3c4e8c4,end=B+0x3c4e8c4)
m.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x810,end=STUB+0x900)
def stub(a,v):m.mem_write(a,struct.pack('<I',0xd65f03c0));rets[a]=v;return a
def vt(slots):
    v=h.alloc(0x100)
    for off,fn in slots.items():h.wq(v+off,fn)
    return v
module=h.alloc(0x200);world=h.alloc(0x500);prov=h.alloc(0x80);table=h.alloc(0x400);cfg=h.alloc(0x80);scfg=h.alloc(0x20)
h.wq(B+0x599dfa8,module);h.wq(module+0xe8,world);h.wq(world+0xb8,prov);h.wq(prov+0x28,table);h.wq(table,vt({8:stub(STUB+0x810,1)}))
h.wq(module+0x18,cfg);h.wq(cfg+0x48,scfg);h.u32(scfg+8,0x13579bdf);m.mem_write(B+0x599f7e0,b'\1')
D=json.loads((R/'analysis/completion/r7/physics_table_emu.json').read_text(encoding='utf-8'))
m.mem_write(table+0x190,struct.pack('<29I',*D['tables'][0]['items']['Default']['block']))
shape=h.alloc(0x40);h.wq(shape,vt({0x48:stub(STUB+0x820,1)}));state['backend_body']=h.alloc(0x200)
rng=random.Random(20261003);bad=[];samples=[]
for i in range(1024):
    desc=h.alloc(0x140);L=rng.randrange(29);S=rng.randrange(27)
    en,block,sub=[rng.getrandbits(32) for _ in range(3)]
    h.u32(desc+0x88,L);h.u32(desc+0x8c,S);h.u32(desc+0xbc,0x98765432);h.u32(desc+0xc0,en);h.u32(desc+0xc4,block);h.u32(desc+0xc8,sub);h.wq(desc+0x10,shape)
    if i&1:
        owner=h.alloc(0x400);h.call(B+0x3a85a8c,owner,desc,0);F=h.rq(owner+0x18);kind='character'
    else:h.call(B+0x3af6088,desc,0);F=state['last_alloc'];kind='rigid'
    got=[h.ru32(F+8)&0xfff,h.ru32(F+0xc),h.ru32(F+0x10),h.ru32(F+0x18),h.ru32(F+0x1c)]
    exp=[L|(S<<6),0x98765432,en,block,sub]
    if got!=exp:bad.append({'i':i,'kind':kind,'got':got,'expected':exp})
    if i<4:samples.append({'kind':kind,'got':got,'expected':exp})
out={'cases':1024,'fields':5120,'mismatches':bad,'samples':samples,'stubs':['allocation 0x710083d2f0','shape vt+48 returns 1','table IsA returns 1','hknp backend creation 0x7103c4e8c4 returns synthetic body'],'unverified':['BYML string mask -> numeric parameter fields','dynamic target-vs-player full solver'],'plt_stubbed':sorted(set(h.plt_stubbed))}
(R/'analysis/completion/r7/physics_mask_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('mask writer',out['cases'],'fields',out['fields'],'mismatches',len(bad),'PLT',out['plt_stubbed'])
