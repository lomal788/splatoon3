"""r9 native closest feature point/segment blocks aedd78 and aedc64.
Independent f32 endpoint selection / triple cross / bit inverse approximation.
Synthetic stack/state. Not whole convex/rotation TOI.
"""
import struct,random,json
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
F=np.float32;M=lambda a,b:F(F(a)*F(b));A=lambda a,b:F(F(a)+F(b));D=lambda a,b:F(F(a)-F(b))
U=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0];B=lambda x:F(struct.unpack('<f',struct.pack('<I',int(x)&0xffffffff))[0])
dot=lambda a,b:A(A(M(a[0],b[0]),M(a[1],b[1])),M(a[2],b[2]))
def cross(a,b):return [D(M(a[1],b[2]),M(a[2],b[1])),D(M(a[2],b[0]),M(a[0],b[2])),D(M(a[0],b[1]),M(a[1],b[0]))]
def ref(p0,p1,pt,reverse):
 e=[D(p1[k],p0[k]) for k in range(4)];r0=[D(p0[k],pt[k]) for k in range(4)];r1=[D(p1[k],pt[k]) for k in range(4)];g1=dot(e,r1);g0=dot(e,r0)
 if M(g1,g0)<0:
  v=[D(M(r0[k],g1),M(r1[k],g0)) for k in range(3)];cc=cross(e,v);w=cross(cc,e) if reverse else cross(e,cc)
  # Native sums z² + (x²+y²), and subtracts float-bit integers.
  sq=A(M(e[2],e[2]),A(M(e[0],e[0]),M(e[1],e[1])))
  inv=B(0x7ef504f3-U(sq));scale=M(inv,inv);normal=[M(z,scale) for z in w]+[F(0)];return 2,p0,normal,'inside'
 chosen=p1 if g1<=0 else p0;normal=[D(chosen[k],pt[k]) if reverse else D(pt[k],chosen[k]) for k in range(4)]
 return 1,chosen,normal,'endpoint1' if g1<=0 else 'endpoint0'
def main():
 u=PhysicsUC();S=u.alloc(0x600);rng=random.Random(0xaedd78);seen=[]
 def stop(mu,a,size,user):seen.append(a);mu.emu_stop()
 u.mu.hook_add(UC_HOOK_CODE,stop,begin=0x7100aee4d4,end=0x7100aee4d4)
 branch={};fields=0
 for reverse in (False,True):
  for i in range(4096):
   p0=[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000001)];p1=[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000002)];pt=[F(rng.randint(-64,64)/8) for _ in range(3)]+[B(0x3f000004)]
   if i<4:p0=[F(0),F(0),F(0),B(0x3f000001)];p1=[F(2),F(0),F(0),B(0x3f000002)];pt=[F([1,-1,3,0][i]),F(1),F(0),B(0x3f000004)]
   u.mu.mem_write(S,bytes(0x600));A0,B0=(0x170,0x1d0);seg=A0 if reverse else B0;point=B0 if reverse else A0
   u.mu.mem_write(S+seg,struct.pack('<8f',*map(float,p0+p1)));u.mu.mem_write(S+point,struct.pack('<4f',*map(float,pt)))
   u.w32(S+0x334,2 if reverse else 1);u.w32(S+0x330,1 if reverse else 2);u.mu.reg_write(UC_ARM64_REG_SP,S);u.mu.reg_write(UC_ARM64_REG_X29,S+0x380);u.mu.reg_write(UC_ARM64_REG_Q3,0);seen.clear()
   u.mu.emu_start(0x7100aedc64 if reverse else 0x7100aedd78,0x7100aee4d8,count=256)
   count,selected,n,b=ref(p0,p1,pt,reverse);gotn=u.mu.reg_read(UC_ARM64_REG_Q0).to_bytes(16,'little');wantn=struct.pack('<4f',*map(float,n))
   assert gotn==wantn,(reverse,i,'normal',np.frombuffer(gotn,dtype='<f4').tolist(),n)
   assert bytes(u.mu.mem_read(S+seg,16))==struct.pack('<4f',*map(float,selected)),(reverse,i,'selected')
   assert u.r32(S+(0x334 if reverse else 0x330))==count,(reverse,i,'count')
   assert seen==[0x7100aee4d4]
   fields+=9;key=('A2/B1:' if reverse else 'A1/B2:')+b;branch[key]=branch.get(key,0)+1
 out={'date':'2026-10-03','scope':__doc__,'cases':8192,'f32_integer_fields':fields,'mismatch':0,'branches':branch,'original_blocks':['AEDD78..AEDE7C','AEDC64..AEDD68'],'fixture':'synthetic original stack; Q3 zero, stop at shared join AEE4D4','null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed}
 Path('analysis/completion/r9/physics_gjk_point_segment_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='scope'},ensure_ascii=False))
if __name__=='__main__':main()
