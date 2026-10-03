"""r7 physics: original bphsh->hknpShape.userData attachment + shooter/rigid shape-row filtering.
Runs 3a715b4,3c55ed8,3c34e14,3c34ce8,3ad658c,3ad6a70. Original bphsh fields/rows retained.
Stubs: allocator; TAG0 object loader/type introspection/context cleanup; Havok leaf supplies selected shapeTag;
shape IsA=0, shape type=1 and get-hknp wrapper pointers; bullet/rigid/table type checks=1; mutex PLT.
No geometry/TOI emulation is claimed.
"""
import json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X3,UC_ARM64_REG_X8,UC_ARM64_REG_PC,UC_ARM64_REG_LR
from r5_gfx_char_uc import GUC
from network_uc import BASE as B,STUB
from collision_mesh import load_blobs
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8')
h=GUC();m=h.mu;m.mem_map(0x40000000,0x8000000);h.heap_next=0x40000000;h.wq(B+0x59975c0,0)
state={'H':0,'tag':0};rets={}
def ret(v):m.reg_write(UC_ARM64_REG_X0,v);m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def stub(addr,val):rets[addr]=val;m.mem_write(addr,struct.pack('<I',0xd65f03c0));return addr
def hook(mu,a,s,d):
    if a==B+0x83d2f0:ret(h.alloc(m.reg_read(UC_ARM64_REG_X0)))
    elif a==B+0xbb3edc:
        out=m.reg_read(UC_ARM64_REG_X8);h.wq(out,state['H']);h.wq(out+8,h.alloc(0x30));h.wq(out+16,0);ret(0)
    elif a==B+0xbb3eb8:m.mem_write(m.reg_read(UC_ARM64_REG_X0),b'\0'*24);ret(0)
    elif a==B+0xbb3ec4:ret(0)
    elif a==B+0x8b45c0:ret(1)
    elif a==B+0x8b4834:ret(0)
    elif a==STUB+0xa00:
        m.mem_write(m.reg_read(UC_ARM64_REG_X3)+0xbf8,struct.pack('<H',state['tag']));ret(0)
    elif a in rets:ret(rets[a]() if callable(rets[a]) else rets[a])
for a in [B+x for x in (0x83d2f0,0xbb3edc,0xbb3eb8,0xbb3ec4,0x8b45c0,0x8b4834)]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
m.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x800,end=STUB+0xb00)
m.mem_write(STUB+0xa00,struct.pack('<I',0xd65f03c0))
R0=stub(STUB+0x810,0);R1=stub(STUB+0x820,1)
def vt(slots):
    v=h.alloc(0x400)
    for i in range(0x80):h.wq(v+i*8,R0)
    for off,fn in slots.items():h.wq(v+off,fn)
    return v
def u32(a):return h.ru32(a)
# backend blocking tables are output of original parser from r7_physics_table_emu.py
D=json.loads((R/'analysis/completion/r7/physics_table_emu.json').read_text(encoding='utf-8'))
module=h.alloc(0x200);world=h.alloc(0x500);prov=h.alloc(0x80);table=h.alloc(0x400)
h.wq(B+0x599dfa8,module);h.wq(module+0xe8,world);h.wq(world+0xb8,prov);h.wq(prov+0x28,table);h.wq(table,vt({8:R1}))
for tt,off in zip(D['tables'],(0x190,0x210,0x290)):m.mem_write(table+off,struct.pack('<29I',*tt['items']['Default']['block']))
for x in (0x599f7e0,0x580b9f8,0x5828210,0x580b9c8):m.mem_write(B+x,b'\1')
dispatch=h.alloc(16*0x200);h.wq(B+0x57dd738,dispatch);h.wq(dispatch+8*0x200+0xc0,STUB+0xa00)
fa=h.alloc(0x40);fb=h.alloc(0x40);bullet=h.alloc(0x198);rigid=h.alloc(0x300);contact=h.alloc(0x80)
h.wq(bullet,vt({0:R1,0x38:B+0x3b0b350}));h.wq(bullet+0x138,fa);h.wq(bullet+0xf8,h.alloc(0x40));h.wq(rigid,vt({0x28:R1}));h.wq(rigid+0x180,fb)
for F in (fa,fb):h.u32(F+0x18,0xffffffff);h.u32(F+0x1c,0xffffffff);m.mem_write(F+0x30,struct.pack('<H',1))
h.u32(fa+8,8);h.u32(fb+8,3|(1<<28));h.wq(rigid+0x88,0)
out={'attachment':[],'filter_cases':0,'filter_mismatches':[],'examples':[],'stubs':__doc__.split('Stubs:')[1].strip(),'functions':['0x7103a715b4','0x7103c55ed8','0x7103c34e14','0x7103c34ce8','0x7103ad658c','0x7103ad6a70']}
try:
    for pack in ('Fld_VSLobby','Mpt_Fld_VSLobbyExterior','Fld_Yagara'):
      for name,raw in load_blobs(R/f'extracted/romfs/Pack/Actor/{pack}.pack.zs'):
        p=h.alloc(len(raw));m.mem_write(p,raw);owner=h.alloc(0x100);H=h.alloc(0x100);state['H']=H
        m.mem_write(H+0x18,b'\x08');h.u32(H+0x94,1)
        h.call(B+0x3a715b4,owner,p,len(raw),0)
        N=min(struct.unpack_from('<I',raw,0x20)[0]//16,struct.unpack_from('<I',raw,0x24)[0]//8)
        mo,fo=struct.unpack_from('<II',raw,0x10)
        got=[u32(owner+0x28),h.rq(owner+0x30),u32(owner+0x50),h.rq(owner+0x58),h.rq(H+0x28),h.rq(owner+0x70)]
        exp=[N,p+mo,N,p+fo,owner+0x48,H]
        out['attachment'].append({'pack':pack,'name':name,'rows':N,'match':got==exp,'got':[hex(x) for x in got],'expected':[hex(x) for x in exp]})
        # Phive shape wrapper's original getter path lands on attachment owner's +20 wrapper.
        shp=h.alloc(0x100);pwrap=h.rq(owner+0x20);svt=vt({0:R0,0x10:R1,0x70:stub(STUB+0x830,pwrap)})
        h.wq(shp,svt);h.wq(rigid+0x28,shp)
        # The wrapper getter interface is replaced by a pointer stub; attachment writer outputs remain original.
        # Override the wrapper method with an explicit pointer stub; attachment owner/pointers remain original outputs.
        h.wq(pwrap,vt({0x10:stub(STUB+0x840,H)}))
        for tag in range(N):
          mask=struct.unpack_from('<Q',raw,fo+tag*8)[0];state['tag']=tag
          for layer,sub in [(8,0),(9,0),(5,3),(5,4),(5,5),(5,6),(7,0)]:
            h.u32(fa+8,layer|(sub<<6));m.mem_write(contact+0x68,b'\0\0')
            h.call(B+0x3c55ed8,contact,bullet,tag,rigid,tag)
            got=(struct.unpack('<H',m.mem_read(contact+0x68,2))[0]>>1)&1
            T=D['tables'][1]['items']['Default']['block']
            exp=((T[layer]>>3)&1)*((mask>>(layer&31))&1)*((mask>>(32+(sub&31)))&1)
            # function also checks bullet table's reverse row via original filter path (tables are symmetric for these layers).
            out['filter_cases']+=1
            if got!=exp:out['filter_mismatches'].append({'pack':pack,'tag':tag,'layer':layer,'sub':sub,'got':got,'expected':exp,'mask':hex(mask)})
            if layer==8 and mask&0xffffffff in (0x62,0x1fffff9e):out['examples'].append({'pack':pack,'tag':tag,'mask':hex(mask),'bullet_bit1':got})
    out['status']='success'
except Exception as e:out['status']='error';out['error']=str(e);out['pc']=hex(m.reg_read(UC_ARM64_REG_PC))
out['plt_stubbed']=sorted(set(h.plt_stubbed))
(R/'analysis/completion/r7/physics_mesh_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('stubs','attachment')},ensure_ascii=False));print([(a['pack'],a['rows'],a['match']) for a in out['attachment']])
