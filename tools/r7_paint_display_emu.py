"""r7 paint: original display vertex UV/switch/tangent writes and panel→display-buffer chain.
Unmodified main instructions; original SDK sinf/cosf via separate Unicorn.
Synthetic model-work virtual getter only; no panel matching/build/render/GPU execution.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC,STUB
from r5_player_libm_emu import Sdk,bits
ROOT=Path(__file__).resolve().parents[2];F=np.float32
add=lambda a,b:F(F(a)+F(b));sub=lambda a,b:F(F(a)-F(b));mul=lambda a,b:F(F(a)*F(b));div=lambda a,b:F(F(a)/F(b))
def fb(b):return F(struct.unpack('<f',struct.pack('<I',b))[0])
def dot(a,b):return add(add(mul(a[0],b[0]),mul(a[1],b[1])),mul(a[2],b[2]))
def trunc(x):
 x=float(x)
 return 0 if np.isnan(x) else max(-2147483648,min(2147483647,int(x)))
def uvpack(uv):return struct.pack('<4H',*(trunc(mul(x,32767))&65535 for x in uv))
def swpack(x):return bytes([trunc(mul(x,127))&255])
def tp(v,M):
 q=[]
 for row in M:
  s=mul(dot(v,row),511);s=add(s,.5 if s>=0 else -.5);a=trunc(s)&0xffffffff;q.append(((a>>6)&0x200)|(a&0x1ff))
 return struct.pack('<I',q[0]|q[1]<<10|q[2]<<20)
class Run:
 def __init__(self):
  self.e=UC();self.mu=self.e.mu;self.sdk=Sdk();self.plt={0x7103e9be30:'cosf',0x7103e9be40:'sinf'}
  self.meta=[self.e.alloc(0x28) for _ in range(3)];self.pp=[self.e.alloc(8) for _ in range(3)];self.out=[self.e.alloc(0x1000) for _ in range(3)];self.cb=[self.e.alloc(0x28) for _ in range(3)]
  self.M=self.e.alloc(0x30);self.ins=self.e.alloc(0x100);self.pan=[self.e.alloc(0x200) for _ in range(3)];self.uv=[self.e.alloc(0x20) for _ in range(3)];self.pv=self.e.alloc(0x60)
  self.mesh=self.e.alloc(8);self.vt=self.e.alloc(0x100);self.info=self.e.alloc(0x80);self.shape=self.e.alloc(0x20);self.vertex=self.e.alloc(0x50);self.refs=self.e.alloc(0x20);self.tris=[self.e.alloc(0x18) for _ in range(3)]
  self.ptr(self.mesh,self.vt);self.ptr(self.vt+0x58,STUB+0xe00);self.e.u32(self.info+0x10,1);self.ptr(self.info+0x18,self.shape);self.e.u32(self.shape+0x10,1);self.ptr(self.shape+0x18,self.vertex);self.ptr(self.vertex+0x18,self.refs)
  for i,vt in enumerate((0x710567c3f8,0x710567c430,0x710567c468)):
   self.ptr(self.cb[i],vt);self.ptr(self.cb[i]+8,self.pp[i]);self.ptr(self.pp[i],self.out[i]);self.ptr(self.cb[i]+0x10,self.meta[i])
  self.ptr(self.cb[2]+0x18,self.M);self.mat([[1,0,0],[0,1,0],[0,0,1]])
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def vec(self,a,v):self.mu.mem_write(a,struct.pack('<%df'%len(v),*v))
 def hook(self,mu,pc,sz,_):
  if pc in self.plt:
   mu.reg_write(UC_ARM64_REG_S0,self.sdk.call(self.plt[pc],fb(mu.reg_read(UC_ARM64_REG_S0)&0xffffffff)));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
  elif pc==STUB+0xe00:
   mu.reg_write(UC_ARM64_REG_X0,self.info);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 def mat(self,M):
  for i,row in enumerate(M):self.vec(self.M+i*16,[*row,0])
 def desc(self,i,stride,offset):self.ptr(self.meta[i]+0x10,stride);self.ptr(self.meta[i]+0x18,offset)
 def basis(self,d):
  self.mu.mem_write(self.ins,bytes([d]));self.e.call(0x7102bd7b2c,self.ins,self.pv,self.pv+16,self.pv+32)
  return [struct.unpack('<3f',self.mu.mem_read(self.pv+j*16,12)) for j in range(3)]
 def panel(self,i,d,m,lo,hi,id):
  p=self.pan[i];self.ptr(p+0x18,self.uv[i]);self.vec(self.uv[i],m);self.vec(p+0x3c,lo);self.vec(p+0x48,hi);self.mu.mem_write(p+0x54,bytes([d]));self.mu.mem_write(p+0x38,bytes([d]));self.e.u32(p+0x10,id)
 def uvref(self,B,p,m,lo,hi):
  u=sub(dot(B[0],p),mul(add(lo[0],hi[0]),.5));v=sub(dot(B[1],p),mul(add(lo[1],hi[1]),.5))
  return [add(m[2],add(mul(u,m[0]),mul(v,m[1]))),add(m[5],add(mul(u,m[3]),mul(v,m[4])))]
 def tangentref(self,B,m):
  det=sub(mul(m[0],m[4]),mul(m[1],m[3]));inv=div(1,det);x=mul(m[4],inv);y=mul(inv,F(-m[3]));ln=F(np.sqrt(add(mul(x,x),mul(y,y))))
  if ln>0:q=div(1,ln);x=mul(x,q);y=mul(y,q)
  return [add(add(mul(x,B[0][j]),mul(y,B[1][j])),mul(B[2][j],0)) for j in range(3)]
 def chain(self,data):
  n=len(data);self.mu.mem_write(self.vertex+0xc,b'\0');self.e.u32(self.vertex+0x10,n)
  for i,a in enumerate(data):
   self.panel(i,a['d'],a['m'],a['lo'],a['hi'],a['id']);self.ptr(self.tris[i]+0x10,self.pan[i]);self.ptr(self.refs+i*8,self.tris[i])
  self.vec(self.vertex,data[0]['p'])
  for i in range(3):self.mu.mem_write(self.out[i],b'\0'*64)
  self.desc(0,8,0);self.desc(1,1,0);self.desc(2,4,0);self.mat([[1,0,0],[0,1,0],[0,0,1]])
  self.e.call(0x7102be2de4,self.mesh,*self.cb,0,0)
  a=sorted(data,key=lambda x:x['id']);u=[self.uvref(self.basis(x['d']),x['p'],x['m'],x['lo'],x['hi']) for x in a];t=self.tangentref(self.basis(a[0]['d']),a[0]['m'])
  if n==1:uv=[*u[0],*u[0]];sw=0;flag=0
  else:uv=[*u[0],*u[1]];sw=0;flag=(2 if n>2 else 0)|(1 if any(abs(sub(u[0][j],u[1][j]))>F(.005) for j in range(2)) else 0)
  expected=[uvpack(uv),swpack(sw),tp(t,[[1,0,0],[0,1,0],[0,0,1]]),bytes([flag])]
  got=[bytes(self.mu.mem_read(self.out[0],8)),bytes(self.mu.mem_read(self.out[1],1)),bytes(self.mu.mem_read(self.out[2],4)),bytes(self.mu.mem_read(self.vertex+0xc,1))]
  return got,expected

def main():
 r=Run();rng=random.Random(0x2be59f0);res={};bad=[]
 for i in range(4096):
  idx=i%31;offset=i%7;stride=16+i%8
  for j in range(3):r.desc(j,stride,offset);r.mu.mem_write(r.out[j],b'\xa5'*0x1000)
  uv=[F(rng.uniform(-1.2,1.2)) for _ in range(4)];sw=F(rng.choice([-1,0,1]) if i%2 else rng.uniform(-1.2,1.2));v=[F(rng.uniform(-1.1,1.1)) for _ in range(3)];M=[[F(rng.uniform(-1,1)) for _ in range(3)] for _ in range(3)];r.mat(M)
  r.vec(r.ins,uv);r.e.call(0x7102be59f0,r.cb[0],idx,r.ins,r.ins+8);r.e.call(0x7102be5ae8,r.cb[1],idx,fargs=(sw,));r.vec(r.ins,v);r.e.call(0x7102be5ba4,r.cb[2],idx,r.ins)
  got=[bytes(r.mu.mem_read(r.out[j]+stride*idx+offset,n)) for j,n in enumerate((8,1,4))];ex=[uvpack(uv),swpack(sw),tp(v,M)]
  if got!=ex:bad.append(dict(i=i,got=[x.hex() for x in got],expected=[x.hex() for x in ex]))
 res['writers']=dict(cases=4096,matching=4096-len(bad),failures=bad[:5]);print('writers',4096-len(bad),'/4096')
 bad=[]
 for i in range(1200):
  p=[F(rng.uniform(-20,20)) for _ in range(3)];data=[]
  for j in range(1+i%3):
   d=rng.randrange(42);theta=rng.uniform(-3,3);c=F(np.cos(theta));s=F(np.sin(theta));scale=F(rng.uniform(.001,.02));m=[mul(c,scale),mul(F(-s),scale),F(rng.uniform(.2,.8)),mul(s,scale),mul(c,scale),F(rng.uniform(.2,.8))]
   lo=[F(rng.uniform(-5,0)) for _ in range(3)];hi=[F(rng.uniform(0,5)) for _ in range(3)];data.append(dict(p=p,d=d,m=m,lo=lo,hi=hi,id=[4,1,9][j]))
  a,b=r.chain(data)
  if a!=b:bad.append(dict(i=i,got=[x.hex() for x in a],expected=[x.hex() for x in b]))
 res['panel_to_display']=dict(cases=1200,matching=1200-len(bad),panels='1/2/3 distinct panels, ids4/1/9, 42 directions; no model triangles (single vertex)',failures=bad[:6]);print('panel_to_display',1200-len(bad),'/1200')
 res['limits']='Synthetic model-work getter (vt58) only. Original basis and original SDK sinf/cosf; no BFRES resource lookup/map/unmap, model-to-panel matching, model triangles seam postpass, GPU rendering, or whole ColPaint build. No original shader/GPU execution.'
 (ROOT/'analysis/completion/r7/paint_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if any(x.get('failures') for x in res.values() if isinstance(x,dict)):sys.exit(1)
if __name__=='__main__':main()
