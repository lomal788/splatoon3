"""Original ColPaint shared triangle edge and full 2D strip endpoint projection. No algorithm stubs."""
import json,random,struct
from pathlib import Path
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_S0,UC_ARM64_REG_S1
from r7_paint_display_emu import Run,F,add,sub,mul,fb,dot
r=Run();rng=random.Random(0x2c057e4);R=Path(__file__).resolve().parents[2]
a=r.e.alloc(0x40);b=r.e.alloc(0x40);seg=r.e.alloc(0x20);thirdA=r.e.alloc(16);thirdB=r.e.alloc(16)
counts={}
for k in range(2048):
 A=[[F(rng.randint(-8,8)) for j in range(3)] for i in range(3)]
 if len(set(map(tuple,A)))<3:continue
 B=[[F(rng.randint(12,20)) for j in range(3)] for i in range(3)]
 order=list(range(3));rng.shuffle(order)
 n=k%4
 for j in range(n):B[j]=list(A[order[j]])
 rng.shuffle(B)
 if k%9==0 and n:B[0][0]=add(B[0][0],F(rng.choice([.0009,.001,.0011])))
 r.vec(a+8,sum(A,[]));r.vec(b+8,sum(B,[]));r.mu.mem_write(seg,b'\0'*32);r.mu.mem_write(thirdA,b'\0'*16);r.mu.mem_write(thirdB,b'\0'*16)
 match=[]
 for i,v in enumerate(A):
  for j,w in enumerate(B):
   d=[sub(v[t],w[t]) for t in range(3)];ln=F(F(add(add(mul(d[0],d[0]),mul(d[1],d[1])),mul(d[2],d[2])))**F(.5))
   if ln<F(.001):match.append((i,j));break
  if len(match)==2:break
 r.e.call(0x7102c057e4,a,b,seg,thirdA,thirdB);got=r.mu.reg_read(UC_ARM64_REG_X0)&1;assert got==int(len(match)>=2),(k,A,B,match,got)
 if got:
  ex=struct.pack('<6f',*(A[match[0][0]]+A[match[1][0]]));assert bytes(r.mu.mem_read(seg,24))==ex,(k,'segment')
  ia=next((i for i in range(3) if i not in [t[0] for t in match]),0);ib=next((i for i in range(3) if i not in [t[1] for t in match]),0)
  assert bytes(r.mu.mem_read(thirdA,12))==struct.pack('<3f',*A[ia]) and bytes(r.mu.mem_read(thirdB,12))==struct.pack('<3f',*B[ib])
counts['shared_edge']=2048
M=r.e.alloc(16);N=r.e.alloc(16);vptr=r.e.alloc(16);pan=[r.e.alloc(0x200) for _ in range(2)]
for k in range(2048):
 ds=[rng.randrange(42),rng.randrange(42)];Ms=[[F(rng.uniform(-1,1)) for j in range(4)] for i in range(2)];boxes=[];v=[F(rng.uniform(-20,20)) for j in range(3)]
 for i,p in enumerate(pan):
  lo=[F(rng.uniform(-6,0)) for j in range(3)];hi=[F(rng.uniform(0,6)) for j in range(3)];boxes.append((lo,hi));r.vec(p+0x3c,lo);r.vec(p+0x48,hi);r.mu.mem_write(p+0x54,bytes([ds[i]]))
 r.vec(M,Ms[0]);r.vec(N,Ms[1]);r.vec(vptr,v)
 projected=[]
 for i,d in enumerate(ds):
  B=r.basis(d);u=mul(sub(dot(v,B[0]),mul(add(boxes[i][0][0],boxes[i][1][0]),.5)),8);w=mul(sub(dot(v,B[1]),mul(add(boxes[i][0][1],boxes[i][1][1]),.5)),8)
  m=Ms[i];projected.append([add(mul(m[0],u),mul(m[1],w)),add(mul(m[2],u),mul(m[3],w))])
 want=struct.pack('<2f',*[sub(projected[0][j],projected[1][j]) for j in range(2)])
 r.e.call(0x7102bfd864,pan[0],M,pan[1],N,vptr)
 got=struct.pack('<2I',r.mu.reg_read(UC_ARM64_REG_S0)&0xffffffff,r.mu.reg_read(UC_ARM64_REG_S1)&0xffffffff);assert got==want,(k,ds,got.hex(),want.hex())
counts['strip_endpoint_2D']=2048
opp=struct.unpack('<4Q',r.mu.mem_read(0x710499cad8,32))
result={'cases':counts,'mismatch':0,'stubs':[],'original_sdk':['sinf','cosf'],'opposite_directions':opp,'limits':'shared-edge nondegenerate triangles and strip projection only; octree and full connector driver are 판독'}
(R/'analysis/completion/r8/paint_connect_geometry_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(counts,'mismatch0 opposite',opp)
