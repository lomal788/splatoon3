"""r8 original ImpactAndReject receiver and update, finite synthetic inputs.
No original code modifications. No stubbed arithmetic. Modes/projector host objects are
synthetic memory. The final strength fallback constant 5826ce0 is supplied as 1.0;
this test does not establish its runtime parameter value or a full Havok/game frame.
"""
import json, math, random, struct, sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC
ROOT=Path(__file__).resolve().parents[2]
F=np.float32
A=lambda x,y:F(F(x)+F(y))
M=lambda x,y:F(F(x)*F(y))
S=lambda x,y:F(F(x)-F(y))
D=lambda x,y:F(F(x)/F(y))
def bits(x):return struct.pack('<f',F(x))
def dot(v,w):return A(A(M(v[0],w[0]),M(v[1],w[1])),M(v[2],w[2]))
def ln(v):return F(np.sqrt(dot(v,v)))
def norm(v):
 n=ln(v)
 return [M(x,D(1,n)) for x in v] if n>0 else v
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu
  self.data=self.u.alloc(0x80);self.comp=self.u.alloc(0x80);self.input=self.u.alloc(0x30);self.v=self.u.alloc(0x30)
  self.step=self.u.alloc(0x80);self.ctx=self.u.alloc(0x20);self.body=self.u.alloc(0x80);self.state=self.u.alloc(0x80);self.kind=self.u.alloc(0x30);self.output=self.u.alloc(0x80)
  for a,b in [(self.comp+0x28,self.data),(self.data,self.output),(self.step+0x58,self.ctx),(self.ctx+8,self.body),(self.body+0x40,self.state),(self.state+0x28,self.kind)]:self.ptr(a,b)
  self.u.u32(self.state+0x40,3);self.u.u32(self.kind+8,0);self.u.f32(0x7105826ce0,1)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def vec(self,a,v):self.mu.mem_write(a,struct.pack('<3f',*v))
 def read(self,a,n):return list(struct.unpack('<'+'f'*n,self.mu.mem_read(a,n*4)))
 def fields(self):return self.read(self.data+8,25)
 def receiver(self,old,new,t,t2,mode,choose,times,initialt,initialt2):
  self.vec(self.data+8,old[0]);self.vec(self.data+0x24,old[1]);self.u.f32(self.data+0x18,initialt);self.u.f32(self.data+0x1c,initialt2)
  self.vec(self.input,new)
  for k,x in enumerate(times):self.u.f32(self.data+0x30+4*k,x)
  self.u.call(0x71012ad75c,self.data,self.input,mode,choose,fargs=(t,t2))
  vv=[list(map(F,old[0])),list(map(F,old[1]))]
  tt,tt2=F(initialt),F(initialt2);times=list(map(F,times));strength=F(0)
  if any(F(x)!=0 for x in new):
   target=choose&1
   magnitude=F(np.sqrt(max(dot(new,new),dot(vv[target],vv[target]))))
   vv[target]=[A(x,y) for x,y in zip(vv[target],new)];n=ln(vv[target])
   if n>0:vv[target]=[M(x,D(magnitude,n)) for x in vv[target]]
   tt=F(max(F(t),tt));tt2=F(max(F(t2),tt2));idx=mode if mode<4 else 0;times[idx]=F(max(times[idx],F(t)))
   if tt2>0:strength=F(1)
  out=self.fields()
  for off,val in [(8,vv[0]),(0x24,vv[1]),(0x18,[tt,tt2]),(0x30,times)]:
   got=self.read(self.data+off,len(val));assert b''.join(map(bits,got))==b''.join(map(bits,val)),('receiver',off,old,new,got,val)
  return vv,tt,tt2,times,strength
 def setup(self,imp,rej,dec,t,t2,strength,times,cneg,cpos,last,vel,dt,up):
  self.mu.mem_write(self.data+8,b'\0'*0x60);self.mu.mem_write(self.output,b'\0'*0x80)
  self.vec(self.data+8,imp);self.u.f32(self.data+0x14,dec);self.u.f32(self.data+0x18,t);self.u.f32(self.data+0x1c,t2);self.u.f32(self.data+0x20,strength);self.vec(self.data+0x24,rej)
  for k,x in enumerate(times):self.u.f32(self.data+0x30+4*k,x)
  self.vec(self.data+0x40,last);self.vec(self.data+0x4c,cneg);self.vec(self.data+0x58,cpos);self.vec(self.v,vel);self.u.f32(self.step+0x44,dt);self.vec(self.step+0x24,up)
 def update_ref(self,inp):
  imp,rej,dec,t,t2,strength,times,cneg,cpos,last,vel,dt,up=inp
  imp=list(map(F,imp));rej=list(map(F,rej));vel=list(map(F,vel));dt=F(dt);t=F(t);t2=F(t2);strength=F(strength)
  if strength>0 and t>0:
   p=dot(up,imp);horizontal=norm([S(x,M(y,p)) for x,y in zip(imp,up)]);p=dot(horizontal,vel)
   if p<0:vel=[S(x,M(M(y,p),strength)) for x,y in zip(vel,horizontal)]
  vel=[A(x,M(dt,y)) for x,y in zip(vel,imp)];vel=[A(x,M(dt,y)) for x,y in zip(vel,rej)]
  correction=[M(A(x,y),D(1,dt)) for x,y in zip(cneg,cpos)]
  vel=[A(x,y) for x,y in zip(vel,correction)]
  if math.isnan(dec):
   if t>0:
    factor=F(max(S(1,D(dt,t)),F(0)));imp=[M(factor,x) for x in imp];rej=[M(factor,x) for x in rej]
   else:imp=[F(0)]*3;rej=[F(0)]*3
  else:
   imp=[M(dec,x) for x in imp];rej=[M(dec,x) for x in rej]
   if dot(imp,imp)<F(.0001):imp=[F(0)]*3
   if dot(rej,rej)<F(.0001):rej=[F(0)]*3
  t=F(max(S(t,dt),F(0)));rawt2=S(t2,dt);t2=F(max(rawt2,F(0)));times=[F(max(S(x,dt),F(0))) for x in times]
  if rawt2<=0:strength=F(max(A(strength,D(dt,M(F(1),F(-.016666668)))),F(0)))
  out=imp+[F(dec),t,t2,strength]+rej+times+[A(x,y) for x,y in zip(cneg,cpos)]+[F(0)]*6
  return vel,out,correction
 def update(self,inp):
  self.setup(*inp);self.u.call(0x71012adb58,self.comp,self.body,self.v,self.step)
  want,states,corr=self.update_ref(inp);got=self.read(self.v,3);state=self.fields()
  assert b''.join(map(bits,got))==b''.join(map(bits,want)),('velocity',inp,got,want)
  for i,(a,b) in enumerate(zip(state,states)):
   assert (math.isnan(a) and math.isnan(b)) or bits(a)==bits(b),('state',i,inp,a,b)
  assert b''.join(map(bits,self.read(self.output+0x40,3)))==b''.join(map(bits,corr)),('correction',inp)
  return got,state
r=Run();rng=random.Random(0x803);rc=uc=0
for i in range(1400):
 old=[[F(rng.uniform(-1500,1500)) for _ in range(3)] for _ in range(2)];new=[F(rng.uniform(-1500,1500)) for _ in range(3)] if i%11 else [F(0)]*3
 r.u.f32(r.data+0x20,0)
 r.receiver(old,new,F(rng.uniform(.01,2)),F(rng.uniform(.01,2)),rng.randrange(7),rng.randrange(2),[F(rng.uniform(0,2)) for _ in range(4)],F(rng.uniform(0,2)),F(rng.uniform(0,2)));rc+=1
for i in range(2200):
 v=lambda n=3:[F(rng.uniform(-1500,1500)) for _ in range(n)]
 imp=v();rej=v();vel=v();dec=float('nan') if i%2 else F(rng.choice([0,.1,.8,.98,1]))
 inp=(imp,rej,dec,F(rng.choice([0,.01,.5,1,2])),F(rng.choice([0,.01,.5,1,2])),F(rng.choice([0,.5,1])),[F(rng.uniform(0,2)) for _ in range(4)],v(),v(),v(),vel,F(rng.choice([1/60,1/120,.2,1])),[0,1,0])
 r.update(inp);uc+=1
chron=[];imp=[0,0,280];rej=[0,0,0];t=F(1);t2=F(1);strength=F(1);times=[F(1)]*4
for frame in range(1,65):
 out,state=r.update((imp,rej,float('nan'),t,t2,strength,times,[0]*3,[0]*3,[0]*3,[0]*3,F(1/60),[0,1,0]));uc+=1
 imp=state[:3];t,t2,strength=state[4:7];rej=state[7:10];times=state[10:14]
 chron.append({'frame':frame,'delta_velocity':out,'acceleration':imp,'remaining':t})
result={'date':'2026-10-03','receiver_cases':rc,'update_cases':uc,'mismatches':0,'original_functions':['0x71012ad75c','0x71012adb58'],'scope':'finite input arithmetic; synthetic surrounding objects; no engine frame; fallback constant 5826ce0 supplied 1.0','chronology':chron}
p=ROOT/'analysis/completion/r8/combat_impact_emu.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='chronology'},ensure_ascii=False));print('chronology60',chron[59]);print('chronology61',chron[60])
