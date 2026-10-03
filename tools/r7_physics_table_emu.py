"""r7 physics: original PhiveConfig BYML table parser and backend copy in Unicorn.
Original 3b16ad8 + BYML readers run. Stub only allocation, string intern (identity), external PLT helpers.
"""
import json, struct, sys, zstandard as zstd
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_LR,UC_ARM64_REG_PC
from r5_gfx_char_uc import GUC
R=Path(__file__).resolve().parents[2];B=0x7100000000
sys.stdout.reconfigure(encoding='utf-8')
h=GUC();m=h.mu
m.mem_map(0x40000000,0x8000000);h.heap_next=0x40000000
h.wq(B+0x59975c0,0)
def ret(mu,v):
    mu.reg_write(UC_ARM64_REG_X0,v);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def hook(mu,a,s,d):
    if a==B+0x83d2f0:ret(mu,h.alloc(mu.reg_read(UC_ARM64_REG_X0)))
    elif a==B+0x351ffe0:
        c=mu.reg_read(UC_ARM64_REG_X0);o=h.alloc(16);h.wq(o,c);ret(mu,o)
for a in [B+0x83d2f0,B+0x351ffe0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
raw=zstd.ZstdDecompressor().decompress((R/'extracted/romfs/Phive/Config/PhiveConfig.byml.zs').read_bytes())
p=h.alloc(len(raw));m.mem_write(p,raw)
def u32(a):return struct.unpack('<I',m.mem_read(a,4))[0]
D=json.loads((R/'analysis/gimmick/PhiveConfig.json').read_text(encoding='utf-8'))
out={'source':'original PhiveConfig.byml.zs','raw_bytes':len(raw),'functions':['0x7103b16ad8','0x7103b1ae90'],'tables':[],'stubs':['allocation 0x710083d2f0','string intern 0x710351ffe0','GUC external PLT'],'mismatches':[]}
parsed=[]
try:
    for nm,dstoff in [('LayerEntityParamTableSet',0x190),('LayerEntityParamTableSetSame',0x210),('LayerEntityParamTableSetOther',0x290)]:
        o=h.alloc(0x200);arr=h.alloc(0x20);tree=h.alloc(0x20)
        v=h.call(B+0x3b16ad8,o,arr,tree,p,h.cstr(nm),0)
        names=[];kvs={}
        for i in range(u32(arr)):
            names.append(h._cstr(h.rq(h.rq(arr+8)+i*8)).decode())
        # Tree traversal contains string key +0x20 and rows object +0x28.
        def walk(n):
            if not n:return
            walk(h.rq(n+8));t=h.rq(n+0x28);key=h._cstr(h.rq(n+0x20)).decode()
            N=u32(t);P=h.rq(t+8);N2=u32(t+0x10);P2=h.rq(t+0x18)
            A=[u32(P+i*4) for i in range(N)];F=[u32(P2+i*4) for i in range(N2)]
            T=D[nm][key]['LayerEntityFilterTable'];ea=[sum((1<<c) for c,vv in enumerate(row) if vv in (1,2)) for row in T];ef=[sum((1<<c) for c,vv in enumerate(row) if vv==2) for row in T]
            ok=A==ea and F==ef
            if not ok:out['mismatches'].append({'table':nm,'key':key,'allow':A,'expected_allow':ea,'block':F,'expected_block':ef})
            kvs[key]={'rows':N,'allow':A,'block':F,'match':ok}
            walk(h.rq(n+0x10))
        walk(h.rq(tree))
        out['tables'].append({'name':nm,'return':v,'names':names,'items':kvs})
        parsed.append((arr,tree))
    cfg=h.alloc(0x300);backend=h.alloc(0x400)
    m.mem_write(cfg+0xb0,b'\1');h.u32(cfg+0x168,u32(parsed[0][0]));h.wq(cfg+0x170,h.rq(parsed[0][0]+8))
    for off, (_,tree) in zip((0x188,0x1e8,0x248),parsed):h.wq(cfg+off,h.rq(tree))
    h.call(B+0x3b1ae90,backend,cfg)
    bad=[]
    for table,ao,bo in zip(out['tables'],(0x10,0x90,0x110),(0x190,0x210,0x290)):
        d=table['items']['Default'];ga=[u32(backend+ao+i*4) for i in range(d['rows'])];gf=[u32(backend+bo+i*4) for i in range(d['rows'])]
        if ga!=d['allow'] or gf!=d['block']:bad.append(table['name'])
    out['backend']={'rows':87,'fields':174,'mismatches':bad}
    out['status']='success'
except Exception as e:
    out['status']='error';out['error']=str(e);out['pc']=hex(m.reg_read(UC_ARM64_REG_PC))
out['plt_stubbed']=sorted(set(h.plt_stubbed))
(R/'analysis/completion/r7/physics_table_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='tables'},ensure_ascii=False));print([(t['name'],len(t['items']),sum(x['rows'] for x in t['items'].values())) for t in out['tables']])

