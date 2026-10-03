"""R7: original human shooter walk rate block + original AS slot writer.
Synthetic SM/body/wrapper; no animation state chooser, asset binder, or GPU execution.
Entry 2445dd0 follows state/aux selection. Exit after original 2450510 return.
Finite f32 values; all six reachable shooter walk states and out-of-range cases.
"""
from pathlib import Path
import json,struct,random,sys
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC
ROOT=Path(__file__).resolve().parents[2]
F=np.float32

def bits(v):return struct.unpack('<I',struct.pack('<f',float(v)))[0]
def frombits(v):return F(struct.unpack('<f',struct.pack('<I',v))[0])
def lerp(a,b,t):return F(a+F(F(b-a)*t))
def ref(state,v,stick,prev,factor):
 v,stick,prev,factor=map(F,(v,stick,prev,factor))
 if not 0x5e<=state<=0x81:return F(0),None
 threshold=frombits(0x3a83126e) if stick>0 else frombits(0x3b449ba6)
 target=F(0)
 if state==0x5e:
  hi=frombits(0x3c75c290)
  if v<=threshold:rate=F(.0625)
  elif v>=hi:rate=F(3.125)
  else:rate=F(F(F(v-threshold)/F(hi-threshold))*F(3.0625)+F(.0625))
 else:
  lateral=0x70<=state<=0x81
  low,mid,high,maximum=map(F,(.2,.9375,.7,.9) if lateral else (.04,.625,.5,.8))
  if v>=F(.027):
   if v>=F(.05):
    target=F(1)
    if v<=F(.05):base=high
    elif v>=F(.096):base=maximum
    else:base=lerp(high,maximum,F(F(v+F(-.05))/F(F(.096)+F(-.05))))
    rate=F(factor*base)
   else:
    target=F(0) if v<=F(.027) else F(F(v+F(-.027))/F(.023))
    rate=F(mid+F(target*F(F(high*factor)-mid)))
  else:
   if v<=threshold:rate=low
   elif v>=F(.027):rate=mid
   else:rate=lerp(low,mid,F(F(v-threshold)/F(F(.027)-threshold)))
 return lerp(prev,target,F(.2)),rate

class Harness:
 def __init__(self):
  self.e=UC();e=self.e;m=e.mu
  self.sm=e.alloc(0x500);self.beh=e.alloc(0x200);self.body=e.alloc(0xb000)
  self.wrapper=e.alloc(0x600);self.asobj=e.alloc(0x100);self.slots=e.alloc(0x90);self.slot=e.alloc(0x200)
  self.dash=e.alloc(0x100);self.weapon=e.alloc(0x200)
  def q(a,v):m.mem_write(a,struct.pack('<Q',v))
  q(self.sm+0x20,self.beh);q(self.beh+0x108,self.body);q(self.sm+0x18,self.wrapper)
  q(self.body+0x588,self.weapon);q(self.body+0x590,self.weapon);e.u32(self.body+0x658,1)
  q(self.body+0xa698,self.dash);q(self.wrapper,self.asobj);e.u32(self.asobj+0x18,2)
  q(self.asobj+0x20,self.slots);q(self.slots,self.slot)
  e.u32(0x71058bb8f4,0);e.f32(0x71058bbda8,.096)
  m.hook_add(UC_HOOK_CODE,lambda mu,a,s,u:mu.emu_stop(),begin=0x7102447294,end=0x7102447294)
 def walk(self,state,v,stick,prev,factor):
  e=self.e;m=e.mu
  e.u32(self.sm+0xc8,state);e.u32(self.sm+0xd0,0xffffffff)
  for addr,val in [(self.sm+0xd4,v),(self.body+0x47c,stick),(self.sm+0xe0,prev),(self.sm+0xe4,factor),(self.slot+0xd4,123.)]:e.f32(addr,float(val))
  m.reg_write(UC_ARM64_REG_X19,self.sm);m.reg_write(UC_ARM64_REG_X23,self.sm+0x20)
  m.reg_write(UC_ARM64_REG_X20,0x71058bb000);m.reg_write(UC_ARM64_REG_SP,0x100f0000)
  m.emu_start(0x7102445dd0,0x7102446e1c,count=4000)
  pc=m.reg_read(UC_ARM64_REG_PC)
  assert pc in [0x7102446e1c,0x7102447294],hex(pc)
  return e.ru32(self.sm+0xe0),e.ru32(self.slot+0xd4)

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 h=Harness();e=h.e;m=e.mu
 m.reg_write(UC_ARM64_REG_X19,h.sm);m.emu_start(0x710243d674,0x710243d67c,count=2)
 initial=e.ru32(h.sm+0xe4);assert initial==bits(1.25)
 states=[0x5e,0x5f,0x60,0x69,0x72,0x7b]
 speeds=[F(-.01),F(0),F(.2)]
 for u in [0x3a83126e,0x3b449ba6,0x3c75c290,bits(.027),bits(.05),bits(.096)]:
  speeds.extend([frombits(u-1),frombits(u),frombits(u+1)])
 cases=[(s,v,k,p,f) for s in states for v in speeds for k in [0.,1.] for p in [0.,.3,1.] for f in [.75,1.25]]
 rng=random.Random(70031)
 cases += [(rng.choice(states),F(rng.uniform(0,.25)),rng.choice([0.,1.]),F(rng.uniform(0,1)),F(rng.uniform(.5,1.5))) for _ in range(4000)]
 cases += [(s,F(.1),1.,F(.6),F(1.25)) for s in [0x56,0x82,0x99]]
 mismatch=[];samples=[]
 for i,(s,v,k,p,f) in enumerate(cases):
  got=h.walk(s,v,k,p,f);blend,rate=ref(s,v,k,p,f);expected=(bits(blend),bits(123.) if rate is None else bits(rate))
  if got!=expected and len(mismatch)<8:mismatch.append({'case':i,'input':[s,float(v),k,float(p),float(f)],'got':list(map(hex,got)),'expected':list(map(hex,expected))})
  if i%400==0:samples.append({'state':hex(s),'v':float(v),'blend_bits':hex(got[0]),'slot_rate_bits':hex(got[1])})
 # Continuous acceleration, held speed, deceleration and restart; previous blend feeds next step.
 seq=0;seqmis=[]
 for s in states:
  prev=F(0)
  for v in [*np.linspace(0,.096,60,dtype=F),*([F(.096)]*30),*np.linspace(.096,0,60,dtype=F),*([F(0)]*30),*np.linspace(0,.096,60,dtype=F)]:
   got=h.walk(s,v,1. if v else 0.,prev,1.25);nxt,rate=ref(s,v,1. if v else 0.,prev,1.25)
   if got!=(bits(nxt),bits(rate)) and len(seqmis)<8:seqmis.append(seq)
   prev=nxt;seq+=1
 output={'address_entry':'0x7102445dd0','rate_writer':'0x7102450510','init_factor_write':'0x710243d674..0x710243d67c','init_factor_bits':hex(initial),'independent_cases':len(cases),'sequence_steps':seq,'mismatches':mismatch,'sequence_mismatches':seqmis,'stubs':[],'synthetic':['SM/body/wrapper/AS slot/weapon/dash objects','K=1; dash flags=0; no sub/special input; finite f32'],'limits':['Instruction block entry after state selection; state selector/asset binding/animation advance not run','Other weapon rate branches and NaN not tested'],'samples':samples}
 p=ROOT/'analysis/completion/r7/player_walk_emu.json';p.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in output.items() if k not in ['samples']},ensure_ascii=False))
 assert not mismatch and not seqmis
if __name__=='__main__':main()