"""r8 original AS float-param cache and degree/radian limiter; SDK id-getter stub only."""
from pathlib import Path
import random,struct,json,math
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
R=Path(__file__).resolve().parents[2];F=np.float32;e=Emu();rng=random.Random(83917)
INV=F(struct.unpack('<f',bytes.fromhex('83f9223e'))[0]);TAU=F(struct.unpack('<f',bytes.fromhex('db0fc940'))[0]);PI=F(struct.unpack('<f',bytes.fromhex('db0f4940'))[0]);EPS=F(2**-23)
RAD=F(.017453292);DEG=F(57.295776)
def wrap(v):
 q=F(v*INV);z=math.floor(float(q));u=F(v-F(F(z)*TAU));return u if F(0)<u<TAU else F(0)
def angle(target,rate,dt,current):
 t=wrap(target);c=wrap(current);d=F(t-c)
 if -EPS<=d<=EPS:return t
 if d>PI:c=F(c+TAU)
 elif d<-PI:t=F(t+TAU)
 s=F(rate*dt)
 if c<t:
  n=F(c+s);c=t if n>=t or n<c else n
 elif t<c:
  n=F(c-s);c=t if n<=t or n>c else n
 c=wrap(c)
 return t if -EPS<=F(t-c)<=EPS else c
stand=[]
for k in range(2048):
 e.reset_heap();cur=F(rng.uniform(-900,900));target=F(rng.uniform(-900,900));rate=F(rng.uniform(-.1,20));dt=F(rng.uniform(-2,2));p=e.alloc(4);e.w(p,'f',cur);expected=struct.pack('<f',angle(target,rate,dt,cur));m=e.call(BASE+0x3997c10,[p],[target,rate,dt]);assert m.reg_read(UC_ARM64_REG_PC)==RET;got=bytes(m.mem_read(p,4));assert got==expected,(k,cur,target,rate,dt,got.hex(),expected.hex());stand.append(1)
state={};fake=RET+0x100;e.mu.mem_write(fake,bytes.fromhex('000080d2c0035fd6'))
def hook(mu,a,s,u):
 if a==fake:mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
cases=[]
for k in range(1536):
 e.reset_heap();ctx=e.alloc(0x220);mgr=e.alloc(32);vt=e.alloc(32);node=e.alloc(64);asb=e.alloc(0x80);row=e.alloc(32);cache=e.alloc(4);tree=e.alloc(0x60);root=e.alloc(8);tag=e.alloc(8)
 target=F(rng.uniform(-600,600));cur=F(float('inf') if k%7==0 else rng.uniform(-600,600));initial=F(-1 if k%11 else 20);rate=F([0,-1,.01,2,90][k%5]);mode=k%3;dt=F(rng.uniform(0,2));scale=F(rng.uniform(.2,2));off=F(rng.uniform(-3,3));lo=F(-1000);hi=F(1000)
 e.w(ctx+0x20,'Q',mgr);e.w(mgr,'Q',vt);e.w(vt+0x18,'Q',fake);e.w(ctx+0x70,'Q',root);e.w(root,'Q',tree);e.w(tree+0x20,'I',123);e.w(tree+0x40,'I4xQHH',1,cache,0,1);e.w(cache,'f',cur);e.w(ctx+0x1dc,'f',target);e.w(node+10,'H',123);e.w(node+0x10,'Q',asb);e.w(asb+0x58,'Q',row);e.w(tag,'If',0xd0000000,0);e.w(row,'IfIfffff',0x82000000,rate,mode,initial,scale,off,lo,hi)
 v=target if np.isinf(cur) and initial<0 else (initial if np.isinf(cur) else cur)
 if rate>0:
  if mode==1:v=F(angle(F(target*RAD),F(rate*RAD),dt,F(v*RAD))*DEG)
  elif mode==2:v=angle(target,rate,dt,v)
  elif v<target:v=min(target,F(v+F(rate*dt)))
  elif target<v:v=max(target,F(v-F(rate*dt)))
 else:v=target
 expected=F(off+F(scale*v));expected=min(hi,max(lo,expected));m=e.call(BASE+0x3997de0,[ctx,tag+4,node,0,0,0,0],[dt]);assert m.reg_read(UC_ARM64_REG_PC)==RET;actual=m.reg_read(UC_ARM64_REG_S0);want=struct.unpack('<I',struct.pack('<f',expected))[0];assert actual==want,(k,mode,rate,cur,target,v,hex(actual),hex(want));assert bytes(m.mem_read(cache,4))==struct.pack('<f',v),(k,'cache',v);cases.append({'mode':mode,'rate':float(rate)})
out={'angle_leaf':{'function':'7103997c10','cases':len(stand),'mismatch':0,'stubs':[]},'float_parameter':{'function':'7103997de0','cases':len(cases),'mismatch':0,'stubs':['ctx+20 vtable+18 synthetic blackboard table identifier=0; actual desired-value source builtin0 ctx+1DC']},'limits':'finite inputs, cache-hit single parameter, not entire ASB instance; GPU/poses excluded'}
(R/'analysis/completion/r8/graphics_angle_rate_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('angle2048 float-param1536 mismatch0')
