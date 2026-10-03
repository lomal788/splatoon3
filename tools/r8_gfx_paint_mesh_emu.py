"""r8 new ColPaint triangle postpass and original candidate comparator; reuse old writer proof."""
import random,struct,json
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
from r7_paint_display_emu import Run,F,add,sub,mul,dot,uvpack,swpack,tp
R=Path(__file__).resolve().parents[2];r=Run();rng=random.Random(0x2be135c)
# Replace synthetic getter with actual setupper getter2bcf540.
r.ptr(r.vt+0x58,0x7102bcf540);r.ptr(r.mesh+0x18,r.info)
vs=r.e.alloc(9*0x50);ts=r.e.alloc(4*0x18);refs=[r.e.alloc(16) for _ in range(9)]
r.ptr(r.shape+0x18,vs);r.e.u32(r.shape+0x10,9);r.e.u32(r.shape,4);r.ptr(r.shape+8,ts)
for j in range(3):r.out[j]=r.e.alloc(0x200);r.ptr(r.pp[j],r.out[j]);r.desc(j,[8,1,4][j],0)
triidx=[[0,1,2],[0,3,4],[1,5,6],[2,7,8]];cases=[]
for k in range(384):
 d=k%42;short=bool(k%2);mode=3 if k%3==0 else 0;a=F(.05 if short else 2);p=[[0,0,0],[a,0,0],[0,0,a],[7,2,0],[0,5,9],[13,3,4],[1,8,15],[21,2,1],[1,17,23]]
 maps=[[F(.01),0,F(.2),0,F(.01),F(.3)],[F(.01),0,F(.8),0,F(.01),F(.9)]]
 for j in range(2):r.panel(j,d,maps[j],[-10,-10,-10],[10,10,10],j+1)
 for j,ids in enumerate(triidx):r.mu.mem_write(ts+j*24,struct.pack('<III4xQ',*ids,r.pan[0 if j==0 else 1]))
 for j in range(9):
  r.mu.mem_write(vs+j*80,b'\0'*80);r.vec(vs+j*80,p[j]);adj=[0,j+1] if j<3 else [1+(j-3)//2];r.e.u32(vs+j*80+0x10,len(adj));r.ptr(vs+j*80+0x18,refs[j]);r.mu.mem_write(refs[j],struct.pack('<%dQ'%len(adj),*(ts+i*24 for i in adj)))
 for j in range(3):r.mu.mem_write(r.out[j],b'\0'*0x200)
 r.e.call(0x7102be2de4,r.mesh,*r.cb,0,mode)
 for j in range(9):
  B=r.basis(d);uv=[r.uvref(B,p[j],m,[-10,-10,-10],[10,10,10]) for m in maps];ch=0 if j<3 and not short else 1
  if j<3 and mode==3:want=uvpack([*uv[0],*uv[1]]);ch=0
  else:want=uvpack([*uv[ch if j<3 else 1],*uv[ch if j<3 else 1]])
  tangent=r.tangentref(B,maps[ch if j<3 else 1]);got=bytes(r.mu.mem_read(r.out[0]+j*8,8));assert got==want,(k,j,mode,short,got.hex(),want.hex())
  assert bytes(r.mu.mem_read(r.out[2]+j*4,4))==tp(tangent,[[1,0,0],[0,1,0],[0,0,1]])
 cases.append({'d':d,'mode':mode,'short':short})
# Independent candidate-comparator f32 conditions including equal priority.
res=r.e.alloc(32);query=r.e.alloc(0x58);nv=r.e.alloc(12);pn=[r.e.alloc(0x58) for _ in range(2)]
EPS=F(2**-23);A=F(.001);D=F(.05)
def choose(oldp,newp,oldnorm,newnorm,olda,newa,oldl,newl,c,q,zd,zd2,cl,cl2,slender,imode,empty):
 if oldp<newp:return False
 if oldp!=newp or empty:return True
 da=sub(newa,olda);dl=sub(newl,oldl);dp=sub(abs(sub(dot(newnorm,c),mul(add(*zd2),.5))),abs(sub(dot(oldnorm,c),mul(add(*zd),.5))))
 if slender in (1,2):
  if imode==6:return newnorm[1]>oldnorm[1]
  if da>A:return True
  if da<=-A:return False
  if dl>A:return True
  if dl<=-A:return False
  if dp<-D:return True
  if dp>=D:return False
  return newnorm[1]>oldnorm[1]
 if cl==cl2:
  if dp<-D:return True
  if dp>=D:return False
 else:
  dd=sub(dot(newnorm,q),dot(oldnorm,q))
  if dd>EPS:return True
  if dd<=-EPS:return False
 if da>A:return True
 if da<=-A:return False
 return dl>A
for k in range(4096):
 op=k%12;npv=op if k%4 else rng.randrange(12);n=[F(rng.uniform(-1,1)) for i in range(3)];nn=[F(rng.uniform(-1,1)) for i in range(3)];c=[F(rng.uniform(-8,8)) for i in range(3)];q=[F(rng.uniform(-1,1)) for i in range(3)];a0=F(rng.uniform(0,3));a1=F(a0+rng.choice([-2,-.001,0,.001,2]));l0=F(rng.uniform(0,3));l1=F(l0+rng.choice([-2,-.001,0,.001,2]));z0=[F(rng.uniform(-2,2)),F(rng.uniform(-2,2))];z1=[F(rng.uniform(-2,2)),F(rng.uniform(-2,2))];cl=k%42;cl2=cl if k%2 else (cl+1)%42;sl=k%3;im=k%7;empty=k%17==0
 r.mu.mem_write(res,struct.pack('<QfffIff',0 if empty else pn[0],*n,op,a0,l0));r.vec(query,q);r.vec(query+20,c);r.e.u32(query+0x48,sl);r.e.u32(query+0x4c,im);r.vec(nv,nn)
 for j,z,cd in [(0,z0,cl),(1,z1,cl2)]:r.vec(pn[j]+0x28,[z[0]]);r.vec(pn[j]+0x34,[z[1]]);r.mu.mem_write(pn[j]+0x38,bytes([cd]))
 want=choose(op,npv,n,nn,a0,a1,l0,l1,c,q,z0,z1,cl,cl2,sl,im,empty);before=bytes(r.mu.mem_read(res,32));r.e.call(0x7102bdfb18,res,query,nv,pn[1],npv,fargs=(a1,l1));expected=struct.pack('<QfffIff',pn[1],*nn,npv,a1,l1) if want else before;assert bytes(r.mu.mem_read(res,32))==expected,(k,want,sl,im)
out={'triangle_postpass':{'cases':len(cases),'vertices':len(cases)*9,'matching':len(cases)*9,'triangles_per_case':4,'directions':42,'modes':[0,3],'short_and_large_adjacent':True,'stubs':['SDK sinf/cosf executed in original SDK emulator, no synthetic getter used (2bcf540 original)'],'limits':'normal all-three seam path tested; >70floor/>50type7or8 bulk path read only'},'candidate_comparator':{'cases':4096,'matching':4096,'stubs':[]},'prior_small_leaves':'r8 graphics_paint_event_emu shortedge1024/largestadjacent1024; original r7 writer4096 and no-trianglechain1200 not new-counted'}
(R/'analysis/completion/r8/paint_display_mesh_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('triangle384 vertices3456 comparator4096 mismatch0')
