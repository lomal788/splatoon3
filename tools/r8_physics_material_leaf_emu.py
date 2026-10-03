"""r8: original Havok mesh leaf + Phive 16B material reader on unmodified original TAG0 geometry.
Runs 093149c(D+18) to initialize actual function dispatch, then 0997078 via 12acb38.
Only wrapper type/get-H getters are synthetic; mesh leaf, tag binary search, geometry, material pointer are original.
No broadphase, cast/TOI, solver, or game-on-ground execution is claimed.
"""
import json,struct,bisect,sys
from pathlib import Path
from r5_gfx_char_uc import GUC
from network_uc import BASE as B,STUB
from collision_mesh import load_blobs,decode_mesh
from collision_tag0 import open_bphsh
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_LR,UC_ARM64_REG_PC
R=Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding='utf-8')
h=GUC();m=h.mu;m.mem_map(0x40000000,0x8000000);h.heap_next=0x40000000
D=h.alloc(0x5000);h.call(B+0x93149c,D+0x18);h.wq(B+0x57dd738,D)
assert h.rq(D+8*0x200+0xc0)==B+0x997078
rets={}
def ret(v):m.reg_write(UC_ARM64_REG_X0,v);m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def stub(a,v):m.mem_write(a,struct.pack('<I',0xd65f03c0));rets[a]=v;return a
def hook(mu,a,s,d):
    if a in rets:ret(rets[a]() if callable(rets[a]) else rets[a])
m.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x800,end=STUB+0xa00)
R0=stub(STUB+0x810,0);R1=stub(STUB+0x820,1)
def vt(slots):
    v=h.alloc(0x90)
    for o in range(0,0x90,8):h.wq(v+o,R0)
    for o,a in slots.items():h.wq(v+o,a)
    return v
state={'H':0,'inner':0,'fallback':0}
SH=stub(STUB+0x830,lambda:state['H']);SI=stub(STUB+0x840,lambda:state['inner']);SF=stub(STUB+0x850,lambda:state['fallback'])
wrap=h.alloc(0x100);inner=h.alloc(0x30);h.wq(wrap,vt({0x10:R1,0x18:SF,0x70:SI}));h.wq(inner,vt({0x10:SH}));state['inner']=inner
keyp=h.alloc(16);res=h.alloc(0xc20)
out={'dispatch_type8_leaf':hex(h.rq(D+8*0x200+0xc0)),'cases':0,'leaf_cases':0,'geometry_fields':0,'material_mismatches':[],'leaf_mismatches':[],'files':[],'stubs':__doc__.split('Only')[1].strip()}
try:
 for pack in ('Fld_VSLobby','Mpt_Fld_VSLobbyExterior','Fld_Yagara'):
  for name,raw in load_blobs(R/f'extracted/romfs/Pack/Actor/{pack}.pack.zs'):
   tf=open_bphsh(raw);t,offs=tf.item_offsets(1);root=tf.read(t,offs[0]);mesh=decode_mesh(tf,root)
   P=h.alloc(len(raw)+16);m.mem_write(P,raw);H=P+offs[0];I=h.alloc(0x30);state['H']=H
   N=min(struct.unpack_from('<I',raw,0x20)[0]//16,struct.unpack_from('<I',raw,0x24)[0]//8);mo,fo=struct.unpack_from('<II',raw,0x10)
   h.wq(H+0x28,I);h.u32(I+8,N);h.wq(I+0x10,P+fo);h.u32(I+0x18,N);h.wq(I+0x20,P+mo);h.wq(I+0x28,H)
   nb=int(root['numShapeKeyBits']);sects=tf.rel(root['geometrySections']);fb=h.alloc(16);state['fallback']=fb
   f={'pack':pack,'name':name,'triangles':len(mesh['key']),'keys':len(set(mesh['key'].tolist())),'rows':N,'key_bits':nb,'interior_yes':0,'interior_no':0}
   for ix,(localkey,tag) in enumerate(zip(mesh['key'].tolist(),mesh['tag'].tolist())):
    key=(((localkey+1)<<(32-nb))-1)&0xffffffff;h.u32(keyp,key)
    got=h.call(B+0x12acb38,H,keyp);exp=P+mo+(tag&0x1fff)*16 if (tag&0x1fff)<N else 0
    out['cases']+=1
    if got!=exp or bytes(m.mem_read(got,16))!=raw[mo+tag*16:mo+tag*16+16]:out['material_mismatches'].append({'file':name,'key':hex(key),'local':localkey,'tag':tag,'got':hex(got),'expected':hex(exp)})
    if ix%37==0 or (localkey&1):
     m.mem_write(res,b'\0'*0xc20);m.mem_write(res+0x170,struct.pack('<4f',1,1,1,1));h.call(B+0x997078,H,keyp,1,res)
     leafTag=struct.unpack('<H',m.mem_read(res+0xbf8,2))[0];flags=struct.unpack('<H',m.mem_read(res+0xb90,2))[0]
     si=localkey>>9;pi=(localkey>>1)&255;g=sects[si];bits=tf.rel_raw(g['interiorPrimitiveBitField'])[0]; interior=((bits[pi>>3]>>(pi&7))&1) if bits else 0
     out['leaf_cases']+=1;f['interior_yes' if interior else 'interior_no']+=1
     # Original leaf vertices are f32 triples at +9b0/+9bc/+9c8. Decoder chooses original a,b,c or a,c,d.
     gotv=bytes(m.mem_read(res+0x9b0,36));expv=mesh['pos'][mesh['tri'][ix]].tobytes();out['geometry_fields']+=9
     if leafTag!=tag or ((flags>>5)&1)!=interior or gotv!=expv:out['leaf_mismatches'].append({'file':name,'key':hex(key),'local':localkey,'tag':tag,'got_tag':leafTag,'flags':hex(flags),'interior':interior,'geometry_match':gotv==expv})
   for special in (0xffffffff,):
    h.u32(keyp,special);got=h.call(B+0x12acb38,H,keyp);out['cases']+=1
    if got!=0:out['material_mismatches'].append({'key':hex(special),'got':hex(got),'expected':'0x0'})
    got=h.call(B+0x12ac5e0,wrap,keyp);out['cases']+=1
    if got!=fb:out['material_mismatches'].append({'fallback':True,'got':hex(got),'expected':hex(fb)})
   out['files'].append(f)
 out['status']='success'
except Exception as e:out['status']='error';out['error']=str(e);out['pc']=hex(m.reg_read(UC_ARM64_REG_PC))
out['plt_stubbed']=sorted(set(h.plt_stubbed))
(R/'analysis/completion/r8/physics_material_leaf_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('stubs','files')},ensure_ascii=False));print(json.dumps(out['files'],ensure_ascii=False))
