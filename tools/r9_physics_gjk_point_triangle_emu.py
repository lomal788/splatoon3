"""r9 original point/triangle closest feature AEE260/AEDFF8.
Independent f32 signed-mask and full vec4 in-place reduction order.
Synthetic original stack; stops before AEE4D4 shared normalization. Not whole TOI.
"""
import struct,random,json
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r9_physics_gjk_point_segment_emu import F,M,A,D,U,B,dot,cross,ref as segment_ref
sub=lambda a,b:[D(a[k],b[k]) for k in range(4)]
def triangle_ref(tri,pt,reverse):
 t=[p[:] for p in tri];e12=sub(t[2],t[1]);e20=sub(t[0],t[2]);e01=sub(t[1],t[0]);n=cross(e12,e20)+[F(0)]
 r1=sub(pt,t[1]);r2=sub(pt,t[2]);r0=sub(pt,t[0])
 # Native t0/t1 sum z+(y+x); t2 (x+y)+z. Exact commuted add, no FMA.
 def signed(r,e,commuted):
  c=cross(r,e);p=[M(n[k],c[k]) for k in range(3)]
  return A(p[2],A(p[1],p[0])) if commuted else A(A(p[0],p[1]),p[2])
 tc=[signed(r1,e12,True),signed(r2,e20,True),signed(r0,e01,False)];coords=tc+[tc[2]]
 mask=sum(1<<i for i,v in enumerate(tc) if v<0);path=f'mask{mask}'
 if mask==7:
  orient=dot(sub(t[0],pt) if reverse else sub(pt,t[0]),n)
  if orient<0:
   n=[F(-v) for v in n];t[0],t[1]=t[1],t[0];coords[0],coords[1]=coords[1],coords[0];path+=':swap01'
  else:path+=':keep'
  return 3,t,n,coords,path
 k=[-1,0,1,-6,2,-7,-8,-1][mask];count=2
 if k<0:
  if k>=-5:return 1,t,sub(t[0],pt) if reverse else sub(pt,t[0]),coords,path+':point0'
  t[k+8]=tri[2][:];path+=':neg-edge'
 else:
  c=[2,0,1][k];a=[1,2,0][k];r=sub(pt,t[k]);dC=dot(r,sub(t[c],t[k]))
  if dC>=0:t[a]=tri[2][:];path+=':edgeC'
  else:
   dA=dot(r,sub(t[a],t[k]));t[c]=tri[2][:]
   if dA<0:
    dest=c if a==2 else a;t[dest]=t[1][:]
    return 1,t,sub(t[0],pt) if reverse else sub(pt,t[0]),coords,path+':point'+str(k)
   path+=':edgeA'
 count,selected,n,br=segment_ref(t[0],t[1],pt,reverse);t[0]=selected[:]
 return count,t,n,coords,path+':'+br
def main():
 u=PhysicsUC();S=u.alloc(0x600);rng=random.Random(0xaee260);seen=[];branches={};fields=0
 def stop(mu,a,size,user):seen.append(a);mu.emu_stop()
 u.mu.hook_add(UC_HOOK_CODE,stop,begin=0x7100aee4d4,end=0x7100aee4d4)
 for reverse in (False,True):
  for i in range(4096):
   tri=[[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000000|j)] for j in range(3)];pt=[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000009)]
   if i<10:
    tri=[[F(0),F(0),F(0),B(0x3f000000)],[F(4),F(0),F(0),B(0x3f000001)],[F(0),F(4),F(0),B(0x3f000002)]];p=[(1,1,1),(1,1,-1),(-1,-1,1),(6,-1,1),(-1,6,1),(4,4,1),(0,0,1),(1,0,1),(2,2,0),(1,1,0)][i];pt=list(map(F,p))+[B(0x3f000009)]
   if i==10:tri=[[F(0),F(0),F(0),B(0x3f000000|j)] for j in range(3)]
   if i>=2048:
    # Additional rounded, non-dyadic positions preserve finite modest range.
    tri=[[F(float(v)*1.134567) for v in p[:3]]+[p[3]] for p in tri];pt=[F(float(v)*.9876543) for v in pt[:3]]+[pt[3]]
   u.mu.mem_write(S,bytes(0x600));seg=0x170 if reverse else 0x1d0;point=0x1d0 if reverse else 0x170
   u.mu.mem_write(S+seg,struct.pack('<12f',*map(float,sum(tri,[]))));u.mu.mem_write(S+point,struct.pack('<4f',*map(float,pt)))
   u.w32(S+0x334,3 if reverse else 1);u.w32(S+0x330,1 if reverse else 3);u.mu.reg_write(UC_ARM64_REG_SP,S);u.mu.reg_write(UC_ARM64_REG_X29,S+0x380);u.mu.reg_write(UC_ARM64_REG_X13,S+0x170);u.mu.reg_write(UC_ARM64_REG_Q3,0);seen.clear()
   u.mu.emu_start(0x7100aedff8 if reverse else 0x7100aee260,0x7100aee4d8,count=1024)
   count,t,n,coords,path=triangle_ref(tri,pt,reverse);gotn=u.mu.reg_read(UC_ARM64_REG_Q0).to_bytes(16,'little');wantn=struct.pack('<4f',*map(float,n))
   assert gotn==wantn,(reverse,i,'normal',path,tri,pt,np.frombuffer(gotn,dtype='<f4').tolist(),n)
   assert bytes(u.mu.mem_read(S+seg,48))==struct.pack('<12f',*map(float,sum(t,[]))),(reverse,i,'tri',path,t,np.frombuffer(bytes(u.mu.mem_read(S+seg,48)),dtype='<f4').tolist())
   assert bytes(u.mu.mem_read(S+0x230,16))==struct.pack('<4f',*map(float,coords)),(reverse,i,'coords',path,coords,np.frombuffer(bytes(u.mu.mem_read(S+0x230,16)),dtype='<f4').tolist())
   assert u.r32(S+(0x334 if reverse else 0x330))==count,(reverse,i,'count',path)
   assert seen==[0x7100aee4d4]
   fields+=21;key=('A3/B1:' if reverse else 'A1/B3:')+path;branches[key]=branches.get(key,0)+1
 out={'date':'2026-10-03','scope':__doc__,'cases':8192,'fields':fields,'mismatch':0,'branches':branches,'original_blocks':['AEE260..AEE4C8 + AEDD78 reducer','AEDFF8..AEE25C + AEDC64 reducer'],'fixture':'synthetic original stack, X13=A0, Q3=0; stop AEE4D4','null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed}
 Path('analysis/completion/r9/physics_gjk_point_triangle_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='scope'},ensure_ascii=False))
if __name__=='__main__':main()