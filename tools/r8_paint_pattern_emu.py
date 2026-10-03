"""r8 ColPaint new connect predicates and fallback5 original execution. No policy stub."""
import json,struct,random
from pathlib import Path
from unicorn.arm64_const import UC_ARM64_REG_X0
from r7_paint_display_emu import Run,F,sub,mul,add,div,fb
R=Path(__file__).resolve().parents[2];r=Run();rng=random.Random(0x2bfab40)
ps=[r.e.alloc(0x200) for _ in range(8)];states=[r.e.alloc(8) for _ in ps];adj=[r.e.alloc(4*40) for _ in ps];recs=[r.e.alloc(0x48) for _ in ps];trees=[r.e.alloc(0x20) for _ in ps];nodes=[r.e.alloc(0x38) for _ in ps];pairs=[r.e.alloc(16) for _ in ps]
def init(d,du,dv,pat=0):
 for j,p in enumerate(ps):
  r.mu.mem_write(p,b'\0'*0x200);r.mu.mem_write(adj[j],b'\0'*160);r.mu.mem_write(recs[j],b'\0'*0x48);r.mu.mem_write(trees[j],b'\0'*32);r.mu.mem_write(nodes[j],b'\0'*56);r.mu.mem_write(states[j],b'\0'*8)
  r.mu.mem_write(p+0x38,bytes([d[j] if isinstance(d,list) else d]));w=du[j] if isinstance(du,list) else du;h=dv[j] if isinstance(dv,list) else dv;r.vec(p+0x20,[0,0,0,w,h,1]);r.vec(p+0x3c,[0,0,0,w,h,1]);r.e.u32(p+0x9c,pat)
  r.ptr(p+0x88,trees[j]);r.ptr(p+0xa0,p);r.ptr(p+0xa8,states[j]);r.e.u32(p+0xb0,4);r.ptr(p+0xb8,adj[j]);r.ptr(recs[j]+0x28,p);r.ptr(recs[j]+0x30,states[j]);r.e.u32(recs[j]+0x38,4);r.ptr(recs[j]+0x40,adj[j])
def link(j,k,axis):r.ptr(adj[j]+axis*40,recs[k])
def got(fn):r.e.call(0x7100000000+fn,ps[0]);return r.mu.reg_read(UC_ARM64_REG_X0)&0xffffffff
height={0:F(0),1:F(-.7853982),2:F(.5890486),3:F(.98174775),4:F(2*F(.7853982)),5:F(3*F(.7853982)),6:F(4*F(.7853982))}
def level(d):return 0 if d==40 else 6 if d==41 else (d>>3)+1
def ref12(ds,ws,hs,v,kind):
 if ds[0]>=16 if kind==1 else not (16<=ds[0]<32):return 0
 if v:return 0
 ls=[level(x) for x in ds];changed=any(x!=ls[0] for x in ls);mono=all((b>=a if kind==1 else b<=a) for a,b in zip(ls,ls[1:]));width=all(abs(sub(ws[0],x))<=F(.2) for x in ws)
 area=F(0);vertical=F(0)
 for d,w,h in zip(ds,ws,hs):area=add(area,mul(w,h));vertical=add(vertical,mul(fb(r.sdk.call('sinf',height[level(d)])),h))
 return int(changed and mono and width and vertical>F(3) and area>F(10))
counts={}
for kind,fn in [(1,0x2bfab40),(2,0x2bfacc8)]:
 for k in range(2048):
  ds=([8,16,24] if kind==1 else [24,16,8]) if k%4 else [rng.randrange(42) for _ in range(3)];ws=[F(rng.choice([.5,1,2,4,5,10]))]*3;ws[1]=add(ws[1],rng.choice([0,.1999,.2,.2001]));hs=[F(rng.choice([.5,1,1.5,2,3,4])) for _ in range(3)];v=bool(k%7==0)
  init(ds+[0]*5,ws+[1]*5,hs+[1]*5);link(0,1,0);link(1,2,0)
  if v:link(0,2,2)
  want=ref12(ds,ws,hs,v,kind);assert got(fn)==want,(kind,k,ds,ws,hs,v,want)
  assert bytes(r.mu.mem_read(states[0],1))==b'\0'
 counts[str(kind)]=2048
# Pattern15 exact tree neighbor rules including ceilings and floor skip.
for k in range(2048):
 d=rng.randrange(42);w=F(rng.choice([1,4,5]));h=F(rng.choice([1,4,5]));others=[rng.randrange(42) for _ in range(k%6)];init([d]+others+[0]*(7-len(others)),w,h)
 if others:r.ptr(trees[0]+8,nodes[0])
 for j,od in enumerate(others):
  r.ptr(nodes[j]+0x28,pairs[j]);r.ptr(pairs[j],ps[0]);r.ptr(pairs[j]+8,ps[j+1]);r.ptr(nodes[j]+0x10,nodes[j+1] if j+1<len(others) else 0)
 want=int(d<16 and mul(w,h)<=20 and (any(x<16 for x in others if x!=40) or sum(x!=40 for x in others)>1));assert got(0x2bfb094)==want,(k,d,others,w,h,want)
counts['15']=2048
# Mesh fallback5 maximum overlap / map area > .1, strict first maximum; reciprocal old1/2 clears.
for k in range(2048):
 pat=k%5;w=F(rng.choice([0,1,4,10]));h=F(rng.choice([1,4]));areas=[F(rng.choice([0,.1,.100001,.4,4])) for _ in range(3)];init(8,w,h,pat)
 r.ptr(ps[0]+0xc8,nodes[0])
 for j,a in enumerate(areas):r.ptr(nodes[j]+0x10,nodes[j+1] if j<2 else 0);r.ptr(nodes[j]+0x20,ps[j+1]);r.vec(nodes[j]+0x28,[a]);r.e.u32(ps[j+1]+0x9c,1+j%2)
 ma=F(0);idx=None
 for j,a in enumerate(areas):
  if ma<a:ma=a;idx=j
 area=mul(w,h);changes=pat in(1,2) and abs(area)>F(2**-23) and div(ma,area)>F(.1)
 got(0x2bef220);out=struct.unpack('<I',r.mu.mem_read(ps[0]+0x9c,4))[0];assert out==(5 if changes else pat),(k,pat,w,h,areas,changes,out)
 if changes:assert struct.unpack('<Q',r.mu.mem_read(ps[0]+0x1c8,8))[0]==ps[idx+1] and struct.unpack('<I',r.mu.mem_read(ps[idx+1]+0x9c,4))[0]==0
counts['fallback5']=2048
# Pattern4: ordered V callback picks last az0/4/6 areas, exactly one floor40 connected.
for k in range(1024):
 du=F(rng.choice([1,2,4,5]));dv=F(rng.choice([1,2,3,5]));rootarea=mul(du,dv);ds=[26,6,0,4,40,40,0,0];ws=[du]*8;hs=[dv]*8;ws[4]=du;hs[4]=du
 if k%5==0:hs[1]=add(dv,F(.011)/du)
 if k%7==0:hs[3]=add(dv,F(.011)/du)
 if k%11==0:hs[4]=add(du,F(.101)/du)
 init(ds,ws,hs);link(0,1,2);link(1,2,2);link(2,3,2)
 nfloor=0 if k%13==0 else 2 if k%17==0 else 1
 if nfloor:r.ptr(trees[0]+8,nodes[0])
 for j in range(nfloor):r.ptr(nodes[j]+0x28,pairs[j]);r.ptr(pairs[j],ps[0]);r.ptr(pairs[j]+8,ps[4+j]);r.ptr(nodes[j]+0x10,nodes[j+1] if j+1<nfloor else 0)
 da=sub(rootarea,mul(ws[1],hs[1]));db=sub(mul(ws[2],hs[2]),mul(ws[3],hs[3]));dc=sub(mul(ws[4],hs[4]),mul(ws[1],ws[2]));want=int(-F(.01)<=da<=F(.01) and -F(.01)<=db<=F(.01) and nfloor==1 and -F(.1)<=dc<=F(.1));assert got(0x2bfae50)==want,(k,da,db,dc,nfloor,want)
counts['4']=1024
weight=struct.unpack('<11i',r.mu.mem_read(0x7104aa2af0,44))
res={'connect_predicates':counts,'matching':sum(counts.values()),'stubs':[],'libm':'sinf executes original SDK in separate Unicorn; same result reused as reference angle table only','mesh_neighbor_pattern6_weights':dict(zip(range(6,17),weight)),'limits':'recognizeMeshConnectPattern model walk and pattern4 shape are 판독, not whole-scene execution; legacy independentRecognizer not new-counted'}
(R/'analysis/completion/r8/paint_pattern_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Connect1/2/15+Mesh5',sum(counts.values()),'mismatch0',weight)

