"""r9 original point/tetrahedron face selection and triangle reducer.
Native AEDA68/AEDA78 to AEE4D4 or explicit nearzero/recovery entry.
Independent f32 signed-distance scores, tie and in-place slot ordering.
Synthetic original stack. Not whole convex/rotation TOI.
"""
import struct,random,json
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r9_physics_gjk_point_segment_emu import F,M,A,D,U,B,dot,cross
from r9_physics_gjk_point_triangle_emu import sub,triangle_ref

def tetra_ref(tetra,pt,reverse):
 t=[v[:] for v in tetra];s=F(-1 if reverse else 1)
 normals=[cross(sub(t[2],t[1]),sub(t[3],t[1])),cross(sub(t[0],t[2]),sub(t[3],t[2])),cross(sub(t[1],t[0]),sub(t[3],t[0]))]
 r=[M(s,D(pt[k],t[3][k])) for k in range(3)]
 def sum3(p,i):return A(p[2],A(p[1],p[0])) if i<2 else A(A(p[0],p[1]),p[2])
 ds=[sum3([M(r[k],n[k]) for k in range(3)],i) for i,n in enumerate(normals)]
 squares=[sum3([M(z,z) for z in n],i) for i,n in enumerate(normals)]
 scores=[M(F(F(1)/sq),M(d,F(abs(d)))) if sq!=0 else B(0x7f7fffee) for d,sq in zip(ds,squares)]
 maxscore=F(max(scores));mask=sum(1<<i for i,v in enumerate(scores) if v>=maxscore)
 if maxscore<B(0x2edbe6fe):return 'nearzero',t,None,None,4,scores,ds,'nearzero'
 idx=[0,0,1,1,2,2,2,2][mask];rem=scores[:];rem[idx]=B(0xff7fffee)
 path='isolatedFace'
 if maxscore<=M(F(max(rem)),B(0x3f8ccccd)):
  m=sum(1<<i for i,v in enumerate(ds) if v>=0);path='multiFace'
  if (m&3)==3:
   r2=sub(pt,t[2]);e0=sub(t[0],t[2]);e1=sub(t[1],t[2]);ed=sub(t[3],t[2]);l=M(dot(r2,e1),dot(e0,ed));rgt=M(dot(r2,e0),dot(e1,ed));m&=(-3 if l>rgt else -2);path+=':01'
  if (m&6)==6:
   r0=sub(pt,t[0]);e1=sub(t[1],t[0]);e2=sub(t[2],t[0]);ed=sub(t[3],t[0]);l=M(dot(r0,e1),dot(e2,ed));rgt=M(dot(r0,e2),dot(e1,ed));m&=(-5 if rgt>l else -3);path+=':12'
  if (m&5)==5:
   r1=sub(pt,t[1]);e2=sub(t[2],t[1]);e0=sub(t[0],t[1]);ed=sub(t[3],t[1]);l=M(dot(r1,e2),dot(e0,ed));rgt=M(dot(r1,e0),dot(e2,ed));m&=(-2 if rgt>l else -5);path+=':02'
  idx=[-1,0,1,0,2,0,1,0][m&7]
 if idx<0:return 'recovery',t,None,None,4,scores,ds,path+':recovery'
 t[idx]=tetra[3][:];count,tri,n,coords,br=triangle_ref(t[:3],pt,reverse);t[:3]=tri
 return 'normal',t,n,coords,count,scores,ds,path+':slot'+str(idx)+':'+br

def main():
 u=PhysicsUC();S=u.alloc(0x600);rng=random.Random(0xaeda68);seen=[];capture={};branches={};fields=0
 def hook(mu,a,size,user):
  if a==0x7100aedbd8:
   capture['scores']=mu.reg_read(UC_ARM64_REG_Q25).to_bytes(16,'little');capture['ds']=mu.reg_read(UC_ARM64_REG_Q26).to_bytes(16,'little')
  if a in (0x7100aee4d4,0x7100aedc48,0x7100aee230):seen.append(a);mu.emu_stop()
 for pc in (0x7100aedbd8,0x7100aee4d4,0x7100aedc48,0x7100aee230):u.mu.hook_add(UC_HOOK_CODE,hook,begin=pc,end=pc)
 for reverse in (False,True):
  for i in range(4096):
   t=[[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000000|j)] for j in range(4)];pt=[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000009)]
   if i<10:
    t=[[F(0),F(0),F(0),B(0x3f000000)],[F(4),F(0),F(0),B(0x3f000001)],[F(0),F(4),F(0),B(0x3f000002)],[F(0),F(0),F(4),B(0x3f000003)]];p=[(1,1,1),(-1,-1,-1),(6,0,0),(0,6,0),(0,0,6),(3,3,3),(4,4,-4),(-4,4,4),(4,-4,4),(0,0,0)][i];pt=list(map(F,p))+[B(0x3f000009)]
   if i==10:t=[[F(0),F(0),F(0),B(0x3f000000|j)] for j in range(4)]
   if i>=2048:t=[[F(float(v)*1.134567) for v in p[:3]]+[p[3]] for p in t];pt=[F(float(v)*.9876543) for v in pt[:3]]+[pt[3]]
   u.mu.mem_write(S,bytes(0x600));seg=0x170 if reverse else 0x1d0;point=0x1d0 if reverse else 0x170
   u.mu.mem_write(S+seg,struct.pack('<16f',*map(float,sum(t,[]))));u.mu.mem_write(S+point,struct.pack('<4f',*map(float,pt)))
   u.w32(S+0x334,4 if reverse else 1);u.w32(S+0x330,1 if reverse else 4)
   u.mu.mem_write(S+0x78,struct.pack('<2f',1,1));u.mu.mem_write(S+0x80,struct.pack('<2f',-1,-1));u.mu.mem_write(S+0x60,struct.pack('<4I',*([0xff7fffee]*4)));u.mu.mem_write(S+0xa0,struct.pack('<4I',*([0x7f7fffee]*4)))
   for reg,val in ((UC_ARM64_REG_SP,S),(UC_ARM64_REG_X29,S+0x380),(UC_ARM64_REG_X13,S+0x170),(UC_ARM64_REG_X25,S+0x1d0),(UC_ARM64_REG_X6,0x7104997000),(UC_ARM64_REG_X10,4 if reverse else 1),(UC_ARM64_REG_Q3,0),(UC_ARM64_REG_Q5,int.from_bytes(struct.pack('<4f',1,1,1,1),'little'))):u.mu.reg_write(reg,val)
   seen.clear();capture.clear();u.mu.emu_start(0x7100aeda78 if reverse else 0x7100aeda68,0x7100aee4d8,count=2048)
   kind,tt,n,coords,count,scores,ds,path=tetra_ref(t,pt,reverse)
   for key,v in [('scores',scores+[scores[2]]),('ds',ds+[ds[2]])]:
    want=struct.pack('<4f',*map(float,v));assert capture[key]==want,(reverse,i,key,path,np.frombuffer(capture[key],dtype='<f4').tolist(),v,t,pt)
   fields+=8
   assert seen==[{'normal':0x7100aee4d4,'nearzero':0x7100aedc48,'recovery':0x7100aee230}[kind]],(reverse,i,'stop',kind,path,seen)
   assert bytes(u.mu.mem_read(S+seg,64))==struct.pack('<16f',*map(float,sum(tt,[]))),(reverse,i,'tetra',path,tt,np.frombuffer(bytes(u.mu.mem_read(S+seg,64)),dtype='<f4').tolist())
   assert u.r32(S+(0x334 if reverse else 0x330))==count,(reverse,i,'count',path)
   fields+=17
   if kind=='normal':
    gotn=u.mu.reg_read(UC_ARM64_REG_Q0).to_bytes(16,'little');assert gotn==struct.pack('<4f',*map(float,n)),(reverse,i,'normal',path,np.frombuffer(gotn,dtype='<f4').tolist(),n)
    assert bytes(u.mu.mem_read(S+0x230,16))==struct.pack('<4f',*map(float,coords)),(reverse,i,'coords',path)
    fields+=8
   key=('A4/B1:' if reverse else 'A1/B4:')+path;branches[key]=branches.get(key,0)+1
 out={'date':'2026-10-03','scope':__doc__,'cases':8192,'fields':fields,'mismatch':0,'branches':branches,'original_blocks':['AEDA68/AEDA78..AEDFE0 and AEE1A8..AEE230 + point-triangle reducer'],'fixture':'original constant +1/-1, finite positive/negative max, Q3=0; synthetic stack/points; stop shared normalization or recovery entry','null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed}
 Path('analysis/completion/r9/physics_gjk_point_tetrahedron_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='scope'},ensure_ascii=False))
if __name__=='__main__':main()