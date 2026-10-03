"""r8 original face normal 3c49f10 triangle branch on original mesh vertices.
Synthetic triangle wrapper RTTI getter, transform identity and witness point; no nativecontact/TOI.
Actual math+08a9020 transform run, original f32 cross/dot expected independently.
"""
import json,struct,sys
from pathlib import Path
import numpy as np
from r5_gfx_char_uc import GUC
from network_uc import BASE as B,STUB,STACK
from collision_mesh import load_blobs,decode_mesh
from collision_tag0 import open_bphsh
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8');F=lambda x:float(np.float32(x));M=lambda a,b:F(F(a)*F(b));S=lambda a,b:F(F(a)-F(b));A=lambda a,b:F(F(a)+F(b));pk=lambda v:struct.pack('<'+'f'*len(v),*v)
h=GUC();m=h.mu;m.mem_map(0x40000000,0x1000000);h.heap_next=0x40000000
tri=h.alloc(0x100);vt=h.alloc(16);h.wq(tri,vt);h.wq(vt,STUB+0x800);h.u32(tri+0x40,0x20);h.f32(tri+0x20,0);P=h.alloc(16);DR=h.alloc(16);TR=h.alloc(48);W=h.alloc(16);NR=h.alloc(16);OUT=h.alloc(16)
m.mem_write(TR,pk([0,0,0,0,0,0,0,1,1,1,1,1]));m.mem_write(W,pk([1,2,3,0]));m.mem_write(P,pk([0,0,0,0]));m.mem_write(DR,pk([0,-1,0,0]));m.mem_write(NR,pk([0,1,0,0]))
def hook(mu,a,z,d):
 mu.reg_write(UC_ARM64_REG_X1,B+0x5467070);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
m.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x800,end=STUB+0x800)
out={'cases':0,'fields':0,'mismatch':[],'scope':__doc__,'files':[]}
try:
 for pack in ('Fld_VSLobby','Mpt_Fld_VSLobbyExterior','Fld_Yagara'):
  for name,raw in load_blobs(R/f'extracted/romfs/Pack/Actor/{pack}.pack.zs'):
   tf=open_bphsh(raw);t,off=tf.item_offsets(1);mesh=decode_mesh(tf,tf.read(t,off[0]));c=0
   for ix in range(0,len(mesh['tri']),3):
    verts=mesh['pos'][mesh['tri'][ix]].tolist();m.mem_write(tri+0x60,pk(sum(verts,[])))
    a,b,c0=verts;v=[S(b[j],a[j]) for j in range(3)];w=[S(c0[j],a[j]) for j in range(3)]
    n=[S(M(v[1],w[2]),M(v[2],w[1])),S(M(v[2],w[0]),M(v[0],w[2])),S(M(v[0],w[1]),M(v[1],w[0]))]
    # Quaternion transform identity preserves normal, scalar += dot(n,W).
    n=[A(0,x) for x in n] # 08a90a8 identity transform adds +0 translation, including signed-zero.
    exp=n+[A(A(A(0,M(n[0],1)),M(n[1],2)),M(n[2],3))]
    m.mem_write(STACK+0xf0000,struct.pack('<Q',1));h.call(B+0x3c49f10,tri,0,P,DR,TR,W,NR,OUT)
    got=bytes(m.mem_read(OUT,16));ex=pk(exp);out['cases']+=1;out['fields']+=4;c+=1
    if got!=ex:out['mismatch'].append({'file':name,'ix':ix,'got':got.hex(),'exp':ex.hex()})
   out['files'].append({'name':name,'cases':c})
 out['status']='success'
except Exception as e:out.update(status='error',error=repr(e),pc=hex(m.reg_read(UC_ARM64_REG_PC)))
out['plt_stubbed']=sorted(set(h.plt_stubbed));(R/'analysis/completion/r8/player_face_normal_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({**out,"mismatch_count":len(out["mismatch"]),"mismatch":out["mismatch"][:5]},ensure_ascii=False))

