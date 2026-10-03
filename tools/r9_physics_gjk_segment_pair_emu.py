"""r9 A2/B2 original closest-feature segment pair AED618.
Independent scalar f32 cross guards, clamping, endpoint in-place reducer.
Synthetic original stack/constants; stops before AEE4D4. Not whole TOI.
"""
import struct,random,json
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r9_physics_gjk_point_segment_emu import F,M,A,D,U,B,dot,cross,ref as segment_ref
from r9_physics_gjk_point_triangle_emu import sub
clamp=lambda v:F(max(F(0),min(F(1),v)))
neg=lambda v:[F(-x) for x in v]
def pair_ref(aa,bb):
 a=[v[:] for v in aa];b=[v[:] for v in bb];ea=sub(a[1],a[0]);eb=sub(b[1],b[0]);n=cross(ea,eb)+[F(0)]
 a2=dot(ea,ea);b2=dot(eb,eb);product=M(a2,b2);nsq=dot(n,n);r=sub(b[0],a[0]);point=[F(0)]*4
 if nsq>=M(product,B(0x3b23d70b)):
  ca=cross(n,ea);cb=cross(n,eb)
  side=[dot(sub(a[0],b[0]),cb),dot(sub(b[0],a[1]),cb),dot(sub(a[0],b[0]),ca),dot(sub(b[1],a[0]),ca)]
  approx=lambda c:B((U(dot(c,c))>>1)+0x1fbb4000)
  thB=M(approx(cb),B(0x3727c5ac));thA=M(approx(ca),B(0x3727c5ac))
  if all(v>q for v,q in zip(side,[thB,thB,thA,thA])):
   t=F(side[0]/A(side[0],side[1]));point=[A(a[0][k],M(ea[k],t)) for k in range(4)]
   if dot(sub(a[0],b[0]),n)<0:n=neg(n)
   return a,b,2,2,n,point,'cross-interior'
  mask=sum(1<<i for i,v in enumerate(side) if v>0)
  if mask in (7,11):
   if mask==7:b[0]=b[1][:]
   count,selected,normal,br=segment_ref(a[0],a[1],b[0],True);a[0]=selected[:]
   return a,b,count,1,normal,point,f'side{mask}:'+br
  if mask in (13,14):
   if mask==13:a[0]=a[1][:]
   count,selected,normal,br=segment_ref(b[0],b[1],a[0],False);b[0]=selected[:]
   return a,b,1,count,normal,point,f'side{mask}:'+br
  mode='cross-clamp'
 else:mode='parallel-clamp'
 c=cross(eb,ea);csq=dot(c,c);m=cross(c,eb)
 t=clamp(M(dot(r,m),F(F(1)/csq))) if csq!=0 else F(0)
 ab=dot(ea,eb);ar=dot(ea,r);br=dot(eb,r);invA=F(F(1)/a2) if a2!=0 else F(0);invB=F(F(1)/b2) if b2!=0 else F(0)
 uraw=M(D(M(t,ab),br),invB);u=clamp(uraw);tnew=clamp(M(A(ar,M(u,ab)),invA))
 if u!=uraw or csq==0:t=tnew
 point=[A(a[0][k],M(ea[k],t)) for k in range(4)]
 mask=(1 if t==1 else 0)|(2 if t==0 else 0)|(4 if u==1 else 0)|(8 if u==0 else 0)
 if mask:
  ac=1 if mask&3 else 2;bc=1 if mask&12 else 2
  if mask&1:a[0]=a[1][:]
  if mask&4:b[0]=b[1][:]
  if ac==1 and bc==1:n=sub(a[0],b[0]);path='points'
  elif ac==1:
   bc,b[0],n,path=segment_ref(b[0],b[1],a[0],False)
  else:
   ac,a[0],n,path=segment_ref(a[0],a[1],b[0],True)
  return a,b,ac,bc,n,point,mode+':endmask'+str(mask)+':'+path
 delta=[D(point[k],A(b[0][k],M(eb[k],u))) for k in range(4)]
 if nsq<M(product,B(0x2b8cbccc)):n=delta;mode+=':deltaNormal'
 else:
  if dot(n,delta)<0:n=neg(n)
  mode+=':crossNormal'
 return a,b,2,2,n,point,mode

def main():
 u=PhysicsUC();S=u.alloc(0x600);rng=random.Random(0xaed618);seen=[];branches={};fields=0
 def hook(mu,pc,size,user):seen.append(pc);mu.emu_stop()
 u.mu.hook_add(UC_HOOK_CODE,hook,begin=0x7100aee4d4,end=0x7100aee4d4)
 for i in range(8192):
  aa=[[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000000|j)] for j in range(2)];bb=[[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000004|j)] for j in range(2)]
  if i%5==0:bb[1]=[A(bb[0][k],D(aa[1][k],aa[0][k])) for k in range(3)]+[bb[1][3]]
  if i%11==0:aa[1]=aa[0][:]
  if i%13==0:bb[1]=bb[0][:]
  if i<16:
   if i<8:
    eps=F([1e-6,1e-4,.001,.01,.03,.049,.051,.1][i]);aa=[[F(-1),F(0),F(0),B(0x3f000000)],[F(1),F(0),F(0),B(0x3f000001)]];bb=[[F(-1),F(-eps),F(.25),B(0x3f000004)],[F(1),eps,F(.25),B(0x3f000005)]]
   else:
    x=F(-1+([1e-7,3e-7,1e-6,3e-6,1e-5,3e-5,1e-4,3e-4][i-8]));aa=[[F(-1),F(0),F(0),B(0x3f000000)],[F(1),F(0),F(0),B(0x3f000001)]];bb=[[x,F(-1),F(.25),B(0x3f000004)],[x,F(1),F(.25),B(0x3f000005)]]
  if i>=4096:aa=[[F(float(v)*1.134567) for v in p[:3]]+[p[3]] for p in aa];bb=[[F(float(v)*.9876543) for v in p[:3]]+[p[3]] for p in bb]
  u.mu.mem_write(S,bytes(0x600));u.mu.mem_write(S+0x170,struct.pack('<8f',*map(float,sum(aa,[]))));u.mu.mem_write(S+0x1d0,struct.pack('<8f',*map(float,sum(bb,[]))))
  u.w32(S+0x334,2);u.w32(S+0x330,2);u.mu.mem_write(S+0x160,struct.pack('<4f',1,0,1,0))
  for reg,val in ((UC_ARM64_REG_SP,S),(UC_ARM64_REG_X29,S+0x380),(UC_ARM64_REG_X13,S+0x170),(UC_ARM64_REG_X25,S+0x1d0),(UC_ARM64_REG_X6,0x7104997000),(UC_ARM64_REG_X28,0x7104a8af8e),(UC_ARM64_REG_X2,0x7104a8afce),(UC_ARM64_REG_X9,2),(UC_ARM64_REG_X10,2),(UC_ARM64_REG_X12,0x3727c5ac),(UC_ARM64_REG_X27,0x3b23d70b),(UC_ARM64_REG_Q1,0),(UC_ARM64_REG_Q3,0),(UC_ARM64_REG_Q12,0),(UC_ARM64_REG_Q31,0x1fbb4000),(UC_ARM64_REG_Q5,int.from_bytes(struct.pack('<4f',1,1,1,1),'little'))):u.mu.reg_write(reg,val)
  seen.clear();u.mu.emu_start(0x7100aed618,0x7100aee4d8,count=2048)
  a,b,ac,bc,n,point,path=pair_ref(aa,bb);gotn=u.mu.reg_read(UC_ARM64_REG_Q0).to_bytes(16,'little')
  assert gotn==struct.pack('<4f',*map(float,n)),(i,'normal',path,aa,bb,np.frombuffer(gotn,dtype='<f4').tolist(),n)
  for off,arr,label in ((0x170,a,'A'),(0x1d0,b,'B')):assert bytes(u.mu.mem_read(S+off,32))==struct.pack('<8f',*map(float,sum(arr,[]))),(i,label,path,arr,np.frombuffer(bytes(u.mu.mem_read(S+off,32)),dtype='<f4').tolist())
  assert (u.r32(S+0x334),u.r32(S+0x330))==(ac,bc),(i,'count',path,ac,bc)
  assert bytes(u.mu.mem_read(S+0x260,16))==struct.pack('<4f',*map(float,point)),(i,'point',path,np.frombuffer(bytes(u.mu.mem_read(S+0x260,16)),dtype='<f4').tolist(),point)
  assert seen==[0x7100aee4d4]
  fields+=26;branches[path]=branches.get(path,0)+1
 out={'date':'2026-10-03','scope':__doc__,'cases':8192,'fields':fields,'mismatch':0,'branches':branches,'original_blocks':['AED618..AED9FC and endpoint/classifier reducers'],'fixture':'synthetic original stack, source constant +1/zero/seed/guards/tables; stop AEE4D4','null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed}
 Path('analysis/completion/r9/physics_gjk_segment_pair_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='scope'},ensure_ascii=False))
if __name__=='__main__':main()