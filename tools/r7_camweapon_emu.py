"""r7 camweapon: original PlayerCamera boom ratio/forward coefficient and camera projection.
Original main.reloc.img code executes unmodified; SDK logf/expf/sinf/cosf/tanf are executed in a separate Unicorn instance at PLT calls.
Fragments consume synthetic finite inputs / cast outputs. They do not execute collision queries, broadphase filters, active poser selection, or a full game frame.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC,STACK
from r5_player_libm_emu import Sdk,bits
ROOT=Path(__file__).resolve().parents[2]
F=np.float32

def fb(b):return F(struct.unpack('<f',struct.pack('<I',b))[0])
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
def dot(a,b):return add(add(mul(a[0],b[0]),mul(a[1],b[1])),mul(a[2],b[2]))
def norm(a):
 n=F(np.sqrt(dot(a,a)))
 return [mul(x,div(1,n)) for x in a] if n>0 else a

def clamp(x):return F(0 if x<0 else min(x,F(1)))
def cross(a,b):return [sub(mul(a[1],b[2]),mul(a[2],b[1])),sub(mul(a[2],b[0]),mul(a[0],b[2])),sub(mul(a[0],b[1]),mul(a[1],b[0]))]

class Run:
 def __init__(self):
  self.u=UC();self.s=Sdk();self.mu=self.u.mu
  self.plt={0x7103e9c2a0:'logf',0x7103e9be20:'expf',0x7103e9be40:'sinf',0x7103e9be30:'cosf',0x7103e9c1f0:'tanf'}
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
  self.c=self.u.alloc(0x2000);self.b=self.u.alloc(0xb000);self.beh=self.u.alloc(0x200);self.sm=self.u.alloc(0x200);self.par=self.u.alloc(0x600)
  self.pose=self.u.alloc(0x80);self.view=self.u.alloc(0x100);self.proj=self.u.alloc(0x200);self.out=self.u.alloc(0x40)
  self.fr=STACK+0xe8000;self.sp=STACK+0xe7000
 def hook(self,mu,pc,size,_):
  if pc in self.plt:
   x=fb(mu.reg_read(UC_ARM64_REG_S0)&0xffffffff)
   mu.reg_write(UC_ARM64_REG_S0,self.s.call(self.plt[pc],x));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 def sdk(self,n,x):return fb(self.s.call(n,x))
 def power(self,x,exp):
  if abs(float(x))<float(F(.001)):return F(0)
  v=self.sdk('expf',mul(self.sdk('logf',abs(x)),exp))
  return F(-v) if x<0 else v
 def vec(self,a,v):self.mu.mem_write(a,struct.pack('<3f',*v))
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def regs(self,d):
  for n,v in d.items():
   r=globals()['UC_ARM64_REG_'+n.upper()]
   self.mu.reg_write(r,bits(v) if n.startswith('s') and n[1:].isdigit() else int(v))
 def setup(self,d):
  u=self.u;c=self.c;b=self.b
  self.mu.mem_write(c,b'\0'*0x2000);self.mu.mem_write(b,b'\0'*0xb000)
  self.ptr(c+0x1968,self.beh);self.ptr(self.beh+0x108,b);self.ptr(c+0x68,c+0x3c);self.ptr(b+0xa8c8,self.sm)
  self.vec(c+0x120,d['move']);self.vec(c+0x12c,[0,0,0]);self.vec(c+0x54,d['basis']);self.vec(c+0x14b0,d['prevBasis'])
  self.vec(c+0x18c,d['aim']);self.vec(c+0x1770,d['camDelta']);self.vec(c+0x177c,d['atDelta'])
  self.vec(b+0x114,d['vel']);u.f32(b+0x73c,d['vy']);u.f32(b+0xdc,d['dc']);u.u32(b+0xc0,d['air']);u.u32(b+0xad0,d['ad0'])
  self.mu.mem_write(c+0x15d9,bytes([d['d9']]));self.mu.mem_write(b+0x7a0,bytes([d['wall']]))
  for k,v in [(0x13c,d['normalY']),(0x14cc,d['length']),(0x14c8,d['target']),(0x14c4,d['ratio']),(0x14c0,d['rate']),(0x14f4,d['speed']),(0x14bc,d['angle']),(0x14d0,d['d0']),(0x1760,d['blend'])]:u.f32(c+k,v)
  u.u32(self.par+0xa8,4);u.f32(self.par+0x4e0,fb(0x3f24360c))
  self.vec(self.fr-0x68,d['dir']);u.f32(self.fr-0x6c,d['minimum']);u.f32(self.sp+0x68,d['hitN'][0]);u.f32(self.sp+0x70,d['hitN'][1]);u.f32(self.sp+0x7c,d['hitN'][2]);u.f32(self.sp+0x80,d['hitDist'])
 def gate(self,d):
  self.setup(d);self.regs({'x19':self.c,'x24':self.par,'x26':self.c+0x1520,'x28':self.par,'sp':self.sp,'x29':self.fr})
  self.mu.emu_start(0x71024dd3e0,0x71024dd418,count=200)
  return self.mu.reg_read(UC_ARM64_REG_W24)
 def boom_expected(self,d):
  mn=div(d['minimum'],d['length']);t=F(d['target']);r=F(d['ratio'])
  if mn<=1:q=F(0) if t<=mn else F(1) if t>=1 else div(sub(t,mn),sub(1,mn))
  else:q=sub(1,F(0) if t<=1 else F(1) if t>=mn else div(sub(t,1),sub(mn,1)))
  mv=list(map(F,d['move']))
  if d['air']>=4:mv[1]=sub(mv[1],d['vy'])
  dp=mul(dot(mv,d['dir']),add(mul(d['dc'],F(-.7)),1));proj=mul(dp,F(-.5) if dp<0 else F(.5))
  wallSpeed=mul(F(np.sqrt(dot(mv,mv))),F(.5)) if d['wall'] and d['normalY']<fb(0x3f24360c) else F(0)
  cr=cross(d['basis'],d['prevBasis']);ln=F(np.sqrt(add(add(mul(cr[0],cr[0]),mul(cr[1],cr[1])),mul(cr[2],cr[2]))))
  self.u.call(0x7101252998,fargs=(ln,dot(d['basis'],d['prevBasis'])))
  ai=self.mu.reg_read(UC_ARM64_REG_W0)
  aa=mul(F(ai),fb(0x30c90fdb));wrap=F(max(add(aa,fb(0xc0c90fdb)),fb(0xc0490fdb))) if aa>fb(0x40490fdb) else aa
  ar=clamp(div(wrap,F(.01)));ang=add(d['angle'],mul(sub(ar,d['angle']),F(.2)))
  # Retain the original zero-multiplication term in base speed.
  z=mul(sub(1,mul(sub(1,d['d0']),sub(1,d['d0']))),0)
  k=add(z,F(.05));rotSpeed=mul(ang,add(k,mul(q,sub(F(.01),k))))
  spd=F(max(wallSpeed,rotSpeed))
  if d['ad0']>0 and not d['d9']:spd=F(max(spd,mul(F(np.sqrt(dot(mv,mv))),add(mul(q,F(-.4)),F(.5)))))
  speed=spd if spd>d['speed'] else add(d['speed'],mul(sub(spd,d['speed']),F(.02)))
  pre=add(t,div(max(speed,proj),max(mul(d['length'],t),d['minimum'])))
  finalPre=F(min(pre,clamp(div(d['hitDist'],d['length']))))
  if r<=finalPre:
   delta=sub(finalPre,r);base=F(.1) if delta<=0 else F(.25) if delta>=1 else add(mul(delta,F(.15)),F(.1))
   rate=add(base,mul(finalPre,sub(1,base)))
   if d['rate']<=rate:rate=add(d['rate'],mul(sub(rate,d['rate']),F(.05)))
  else:
   n=d['hitN'];dc=list(map(F,d['camDelta']));da=list(map(F,d['atDelta']));diff=[sub(a,b) for a,b in zip(dc,da)]
   nd=dot(n,diff);perp=[sub(a,mul(b,nd)) for a,b in zip(diff,n)]
   daim=[sub(a,b) for a,b in zip(d['aim'],n)]
   turn=add(add(mul(daim[0],perp[0]),mul(daim[1],perp[1])),mul(daim[2],perp[2]))
   fwd=max(dot(d['aim'],d['vel']),F(0));approach=sub(mul(max(turn,F(0)),mul(fwd,F(.5))),dot(n,dc))
   atApproach=dot(n,da)
   w0=sub(div(add(r,F(-.5)),F(-.45)),max(sub(r,finalPre),F(0)))
   w1=F(1) if w0<0 else sub(1,min(w0,F(1)))
   w=clamp(mul(w1,clamp(div(approach,F(.3)))))
   wa=clamp(div(atApproach,F(-.2)))
   p=self.power(w,fb(0x3fc1dd88));pa=self.power(wa,fb(0x3fc1dd88))
   h=sub(F(-1),div(approach,atApproach)) if atApproach<F(-.001) else F(1)
   cap=F(.35) if h<0 else add(mul(min(h,F(1)),F(.35)),F(.35))
   rate=F(min(add(mul(p,F(.9)),F(.1)),cap))
   lower=F(min(add(mul(pa,F(.9)),F(.1)),F(.35))) # asm 0x71024de590: fmin, omitted in old decompile
   align=abs(dot(n,d['aim']));pAlign=self.power(F(align),fb(0x3fde54e3))
   rate=add(rate,mul(sub(F(.25),rate),pAlign))
   if rate>F(.25) and finalPre<pre:rate=add(rate,mul(sub(F(.25),rate),self.power(sub(pre,finalPre),fb(0x3fde54e3))))
   rate=F(max(rate,lower))
  blend=F(0) if d['blend']<=F(.1) else F(1) if d['blend']>=1 else div(add(d['blend'],F(-.1)),F(.9))
  target=min(add(pre,mul(blend,sub(1,pre))),div(d['hitDist'],d['length']))
  rate=add(rate,mul(sub(F(.25),rate),blend));ratio=add(r,mul(rate,sub(target,r)))
  return [q,ang,speed,rate,target,ratio]
 def boom(self,d):
  expect=self.boom_expected(d)
  self.setup(d);self.regs({'x19':self.c,'x24':int(d['wall'] and d['normalY']<fb(0x3f24360c)),'x26':self.c+0x1520,'x28':self.par,'sp':self.sp,'x29':self.fr,'s9':d['length'],'s12':0})
  try:self.mu.emu_start(0x71024dde2c,0x71024de70c,count=10000)
  except Exception:
   print('FAIL PC',hex(self.mu.reg_read(UC_ARM64_REG_PC)), 'X19',hex(self.mu.reg_read(UC_ARM64_REG_X19)), 'X26',hex(self.mu.reg_read(UC_ARM64_REG_X26)))
   raise
  got=[self.u.rf32(self.c+k) for k in (0x14f0,0x14bc,0x14f4,0x14c0,0x14c8,0x14c4)]
  return [bits(x) for x in got],[bits(x) for x in expect]
 def forward(self,vel,aim,state,k):
  ln=F(np.sqrt(dot(vel,vel)));vv=[mul(x,div(1,ln)) for x in vel] if ln>0 else vel
  c=F(max(F(-1),min(F(1),dot(vv,aim))));v=self.power(F(abs(c)),fb(0x3ea4d3c1))
  h=F(min(div(add(mul(ln,v),fb(0xba83126e)),fb(0x3d48b43a)),F(2.5)))
  expected=F(k)
  if c<=0:expected=mul(add(mul(h,fb(0xbcf5c280)),1),expected)
  elif expected<h and (0x82<=state<=0x90 or 0xaa<=state<=0xac or state in (0xed,0xee,0x10c)):expected=add(expected,mul(sub(h,expected),F(.2)))
  expected=mul(expected,F(.97))
  self.vec(self.b+0xe4,vel);self.vec(self.c+0x18c,aim);self.u.f32(self.c+0x14ec,k);self.u.u32(self.sm+0xc8,state)
  self.ptr(self.b+0xa8c8,self.sm);self.ptr(self.beh+0x108,self.b);self.ptr(self.sp+0x200,self.beh)
  self.regs({'x19':self.c,'x8':self.beh,'x27':self.sp+0x200,'x29':self.fr,'sp':self.sp,'s15':1})
  self.mu.emu_start(0x71024dd4d8,0x71024dd68c,count=2000)
  return bits(self.u.rf32(self.c+0x14ec)),bits(expected)
 def projection(self,n,f,angle,aspect,ox,oy):
  u=self.u;p=self.proj
  # Original pose→LookAt→Perspective setup, including original SDK trig calls.
  self.mu.mem_write(self.pose,b'\0'*0x80);self.mu.mem_write(self.view,b'\0'*0x100);self.mu.mem_write(p,b'\0'*0x200)
  self.ptr(self.view,0x7105721238);u.f32(self.pose+0x18,1);u.f32(self.pose+0x28,1)
  for off,val in ((0x1c,n),(0x20,f),(0x24,angle)):u.f32(self.pose+off,val)
  for off,val in ((0xb0,aspect),(0xb4,ox),(0xb8,oy)):u.f32(p+off,val)
  u.call(0x7101017434,self.pose,self.view,p)
  u.call(0x7103589d74,p,self.out)
  got=struct.unpack('<16I',self.mu.mem_read(self.out,64))
  tan=self.sdk('tanf',mul(angle,F(.5)))
  width=mul(mul(add(n,n),tan),aspect);height=mul(add(n,n),tan)
  midx=mul(width,ox);midxh=mul(width,F(.5));left=sub(midx,midxh);right=add(midxh,midx)
  midy=mul(height,oy);midyh=mul(height,F(.5));top=add(midyh,midy);bottom=sub(midy,midyh)
  idx=div(1,sub(right,left));idy=div(1,sub(top,bottom));idz=div(1,sub(f,n))
  exp=[mul(add(n,n),idx),0,mul(add(right,left),idx),0, 0,mul(idy,add(n,n)),mul(add(top,bottom),idy),0, 0,0,mul(F(-add(n,f)),idz),mul(idz,mul(mul(f,F(-2)),n)), 0,0,-1,0]
  view=struct.unpack('<12f',self.mu.mem_read(self.view+8,48))
  return list(got),[bits(x) for x in exp],view

def main():
 r=Run();rng=random.Random(0x71024dde);res={};fail=[]
 n=640;fields=(0x14f0,0x14bc,0x14f4,0x14c0,0x14c8,0x14c4)
 gateCount=0
 for i in range(n):
  vec=lambda scale:[F(rng.uniform(-scale,scale)) for _ in range(3)]
  d=dict(move=vec(.25),basis=norm(vec(1)),prevBasis=norm(vec(1)),aim=norm(vec(1)),dir=norm(vec(1)),hitN=norm(vec(1)),camDelta=vec(.3),atDelta=vec(.2),vel=vec(.2),vy=F(rng.uniform(-.1,.15)),dc=F(rng.random()),air=i%7,ad0=i%3,d9=(i//3)%2,wall=i%2,normalY=F(rng.uniform(-.1,1)),length=F(rng.uniform(.2,9)),minimum=F(rng.uniform(.05,.9)),target=F(rng.random()),ratio=F(rng.random()),rate=F(rng.random()),speed=F(rng.uniform(0,.2)),angle=F(rng.random()),d0=F(rng.random()),blend=F([0,.1,.5,1][i%4]),hitDist=F(rng.uniform(.01,9)))
  g=r.gate(d);eg=int(d['wall'] and d['normalY']<fb(0x3f24360c));gateCount+=g==eg
  a,b=r.boom(d)
  if a!=b:fail.append(dict(i=i,got=[hex(x) for x in a],expected=[hex(x) for x in b],input={k:[float(x) for x in v] if isinstance(v,list) else float(v) for k,v in d.items()}))
 res['boom']=dict(cases=n,matching=n-len(fail),fields=[hex(x) for x in fields],gate_matching=gateCount,failures=fail[:6])
 print('boom',n-len(fail),'/',n,'gate',gateCount,'/',n)
 ff=[]
 for i in range(480):
  a,b=r.forward([F(rng.uniform(-.2,.2)) for _ in range(3)],norm([F(rng.uniform(-1,1)) for _ in range(3)]),[0x42,0x82,0x90,0xaa,0xed,0x10c][i%6],F(rng.uniform(0,2.5)))
  if a!=b:ff.append(dict(i=i,got=hex(a),expected=hex(b)))
 res['forward']=dict(cases=480,matching=480-len(ff),failures=ff[:8]);print('forward',480-len(ff),'/',480)
 pf=[];vs=[]
 for i in range(256):
  n0=F(rng.uniform(.01,1));far=F(rng.uniform(50,2500));angle=mul(F(rng.uniform(20,110)),F(.017453292));aspect=F(rng.uniform(.7,2.5));ox=F(rng.uniform(-.25,.25));oy=F(rng.uniform(-.25,.25))
  a,b,v=r.projection(n0,far,angle,aspect,ox,oy)
  if a!=b:pf.append(dict(i=i,got=[hex(x) for x in a],expected=[hex(x) for x in b]))
  if i==0:vs=list(v)
 res['projection']=dict(cases=256,matching=256-len(pf),failures=pf[:4],identity_pose_view=vs)
 print('projection',256-len(pf),'/',256,'view',vs)
 res['limits']='Synthetic finite boom/cast inputs; original SDK calls; no cast/filter/poser selection/full game frame. LookAt function reused from r5 paint.'
 p=ROOT/'analysis/completion/r7/camweapon_emu.json';p.write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf-8')
 if fail or ff or pf:sys.exit(1)
if __name__=='__main__':main()
