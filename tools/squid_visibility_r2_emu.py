"""Native B7a0 delayed tail -> whole SM display -> whole holder, fixture boundaries explicit."""
import sys,struct,json,random,itertools,hashlib
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/tools'))
from weapon_ink_emu import Emu,STACK,RET_MAGIC,f2u
F=np.float32;OUT=ROOT/'analysis/visual_gap_r2/squid';OUT.mkdir(parents=True,exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
DENTRY=0x710248c5c0;DSTOP=0x710248c7dc;SMFN=0x710243e2dc;HOLDER=0x71014595b0
class Harness(Emu):
 def __init__(self):
  super().__init__();self.mode='';self.stopped=0;self.setcalls=[];self.othercalls=[];self.candidate_read=None;self.match_read=None
  self.sm=self.alloc(0x400);self.smref=self.alloc(0x100);self.human=self.alloc(0x50);self.squid=self.alloc(0x50);self.wrap=self.alloc(0x60);self.info=self.alloc(0x1000);self.rail=self.alloc(0x300);self.life=self.alloc(0x100);self.holder=self.alloc(0x100);self.launch=self.alloc(0x100);self.vt=self.alloc(0x100);self.bind=[self.alloc(0x80) for _ in range(4)]
  self.w64(self.smref,self.sm);self.w64(self.wrap+0x108,self.body);self.w64(self.holder+0x50,self.wrap);self.w64(self.holder+0x58,self.sm);self.w64(self.body+8,self.info);self.w64(self.body+0xa668,self.rail);self.w64(self.body+0xa650,self.life);self.w32(self.rail+0x1b8,0xffffffff);self.uc.mem_write(self.life+0x35,b'\x01');self.w64(self.sm+8,self.human);self.w64(self.sm+0x10,self.squid);self.w64(self.sm+0x20,self.wrap);self.w64(self.sm+0x18,self.wrap)
  self.w64(self.vt+0x10,RET_MAGIC+0x80)
  for o,p in zip([0x1b0,0x1b8,0x1c0,0x1c8],self.bind):self.w64(self.sm+o,p);self.w64(p,self.vt)
  const=json.loads((ROOT/'analysis/player/bss_consts_58bb000.json').read_text())
  for key,val in const.items():self.w32(int(key,16),val['u32'])
  self.w32(0x71058bc128,0)
  self.grind=self.alloc(0x300);self.squidmove=self.alloc(0x100);self.dokan=self.alloc(0x600);self.warp=self.alloc(0x1000);self.geyser=self.alloc(0x100);self.periscope=self.alloc(0x100);self.pipeline=self.alloc(0x100);self.vehicle=self.alloc(0x100);self.misc=self.alloc(0x100)
  self.w64(self.grind,0x7105635660);self.w32(self.vehicle+0x88,-1)
  for off,p in [(0xa670,self.grind),(0xa688,self.squidmove),(0xa880,self.dokan),(0xa7c0,self.warp),(0xa808,self.geyser),(0xa818,self.periscope),(0xa6d0,self.pipeline),(0xa6d8,self.vehicle),(0xa6a8,self.launch),(0xa8c8,self.sm),(0xa830,self.pp),(0xa658,self.pp)]:self.w64(self.body+off,p)
  self.wf(self.pp+0x13c,60)
  self.w32(0x71058bb8f4,0)
  self.uc.hook_add(UC_HOOK_CODE,self.hook)
 def wb(self,a,v):self.uc.mem_write(a,bytes([v&255]))
 def rb(self,a):return self.uc.mem_read(a,1)[0]
 def hook(self,uc,a,size,ud):
  if self.mode in ['delay','producer'] and a==DSTOP:self.stopped+=1;uc.emu_stop()
  if (self.mode=='restart_init' and a==0x7102354dac) or (self.mode=='ctor_init' and a==0x7102457638):uc.emu_stop()
  if self.mode=='coordinate' and a==0x710248c2e4:self.match_read=uc.reg_read(UC_ARM64_REG_X26);uc.emu_stop()
  if self.mode=='producer' and a==DENTRY:self.candidate_read=uc.reg_read(UC_ARM64_REG_X19)|uc.reg_read(UC_ARM64_REG_X22);self.match_read=uc.reg_read(UC_ARM64_REG_X26)
  if a==RET_MAGIC+0x80:
   p=uc.reg_read(UC_ARM64_REG_X0);team=uc.reg_read(UC_ARM64_REG_X1);bits=uc.reg_read(UC_ARM64_REG_S0)&0xffffffff
   call=(self.bind.index(p),team,bits);lr=uc.reg_read(UC_ARM64_REG_LR)
   (self.setcalls if 0x710243e488<=lr<=0x710243e644 else self.othercalls).append(call);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
 def delay(self,candidate,state,match,y,ma,mb,force,old,delay,age):
  b=self.body;p=b+0x784;self.wb(b+0x7a0,old);self.w32(b+0x794,delay);self.w32(b+0x798,age);self.w32(self.sm+0xc8,state);self.wf(b+0x184,y);self.wf(b+0xa74,ma);self.wf(b+0xa78,mb)
  self.wb(b+0x9210,force==1);self.wb(self.launch+0xb4,force==2);self.wb(b+0x782,force==3);self.wb(self.rail+0x1e0,force==4)
  self.w64(STACK+0x180,p);self.w64(STACK+0x168,0);self.w64(STACK+0x138,0);self.w64(STACK+0x190,self.sm);self.w32(STACK+0x140,force==5);self.w32(STACK+0x170,force==6)
  for n,v in {19:candidate,20:self.launch,21:b,22:0,23:self.rail,25:p,26:match,27:self.smref}.items():self.uc.reg_write(getattr(sys.modules['unicorn.arm64_const'],'UC_ARM64_REG_X'+str(n)),v)
  self.mode='delay';self.run(DENTRY);self.mode='';assert self.uc.reg_read(UC_ARM64_REG_PC)==DSTOP
  return (self.rb(b+0x7a0),self.rs32(b+0x794),self.rs32(b+0x798))
 def coordinate(self,n,m):
  for j in range(3):self.wf(self.body+0x180+j*4,n[j]);self.wf(self.body+0x198+j*4,m[j])
  self.uc.reg_write(UC_ARM64_REG_X21,self.body);self.uc.reg_write(UC_ARM64_REG_X22,1);self.uc.reg_write(UC_ARM64_REG_X0,1)
  self.mode='coordinate';self.run(0x710248c250);self.mode='';return self.match_read
 def producer(self,state,air,paint,kind,grindactive,old,delay,age,y=1):
  b=self.body;p=b+0x784;self.w32(self.sm+0xc8,state);self.w32(b+0xc0,air);self.w32(self.squidmove+0x30,paint);self.w32(self.dokan+0x30,kind);self.wb(self.grind+0x1f4,grindactive);self.wb(b+0x7a0,old);self.w32(b+0x794,delay);self.w32(b+0x798,age)
  self.wb(b+0x9210,0);self.wb(self.launch+0xb4,0);self.wb(b+0x782,0);self.wb(self.rail+0x1e0,0);self.wb(b+0x781,0);self.wb(b+0x7f4,0);self.w32(b+0x774,0);self.wf(b+0xa74,0);self.wf(b+0xa78,0)
  for j,v in enumerate([0,y,0]):self.wf(b+0x180+j*4,v);self.wf(b+0x198+j*4,v)
  self.w64(STACK+0x180,p);self.w64(STACK+0x168,0);self.w64(STACK+0x138,0);self.uc.reg_write(UC_ARM64_REG_X19,self.smref);self.uc.reg_write(UC_ARM64_REG_X22,self.misc)
  self.mode='producer';self.run(0x710248c16c);self.mode='';assert self.uc.reg_read(UC_ARM64_REG_PC)==DSTOP
  return self.candidate_read,self.match_read,(self.rb(b+0x7a0),self.rs32(b+0x794),self.rs32(b+0x798))
 def display(self,hidden,human,squid,f0,kind,dead,state,oldflags):
  self.wb(self.body+0x7a0,hidden);self.w32(self.human+8,0 if human else -1);self.w32(self.squid+8,0 if squid else -1);self.w32(self.sm+0xf0,f0);self.w32(self.info+0x7a0,kind);self.w32(self.sm+0xc8,state);self.wf(self.body+0xcb8,0);self.wf(self.sm+0x1d0,0);self.w32(self.info+0x668,0);self.wb(self.body+0x926c,0)
  for o,v in zip([0xf4,0xf5,0xf6,0xf8],oldflags):self.wb(self.sm+o,v)
  for p in self.bind:
   for i in range(3):self.w32(p+8+i*4,0)
  self.setcalls=[];self.othercalls=[];self.run(SMFN,x=(self.sm,dead))
  return [self.rb(self.sm+o) for o in [0xf4,0xf5,0xf6,0xf8]],self.rs32(self.sm+0xf0),list(self.setcalls)

def s32(v):return (v+0x80000000)%0x100000000-0x80000000

def factor(match,y,ma,mb):return F(min(F(1),F(F(F(1)-F(y))+F(ma if F(ma)>F(mb) else mb)))) if match else F(1)

def py_delay(candidate,state,match,y,ma,mb,force,old,delay,age):
 f=factor(match,y,ma,mb)
 if candidate==old:
  minimum=int(F(F(f*F(4))+F(1))) if old else 5
  return old,max(s32(delay-1),minimum),s32(age+1)
 in_group=0x82<=state<=0x90 or 0xaa<=state<=0xac or state in [0xed,0xee,0x10c]
 if not in_group:delay=int(min(F(delay),F(3)))
 forced=force in [1,2,4,5] or (force==3 and state==0x87) or (force==6 and candidate==0)
 if forced:delay=int(min(F(delay),F(1)))
 delay=max(s32(delay-1),0)
 if delay:return old,delay,s32(age+1)
 return candidate,(int(F(F(f*F(7))+F(3))) if candidate else 10),0

def py_display(hidden,human,squid,f0,kind,dead,state,oldflags):
 hlf=bool(not hidden and human and f0>=61 and kind!=4);body=bool(not hidden and human and not hlf);sq=bool(not hidden and squid)
 if not dead and not body and not hlf:f0=140 if state==0x96 else 90
 flags=[int(body),int(hlf),int(sq),0];resets=[]
 for m,off,new in [(0,0,body),(1,1,hlf),(3,2,sq)]:
  if oldflags[off] and not new:resets.extend((m,i,0) for i in range(3))
 if (oldflags[0] or oldflags[1]) and not body and not hlf:resets.extend((2,i,0) for i in range(3))
 return flags,f0,resets

def py_holder(flags,state,prev,cur,old,timers,life,debug,special,selected,special_disable):
 de0,df0,e04,e0c,e1c,d60,d5c=timers;l30,l31,l35,l38=life
 if de0>0 or (df0>=1 and e04>0) or (e0c>=1 and e1c>=1):return [0]*4
 if d60>0:return old[:2]+[0,0]
 if not(l35 and (not(l30 or l31) or l38>0)) or d5c>0 or debug:return [0]*4
 f=flags[:]
 active=selected and not special_disable
 if active and special==0x1a:f[2]=0
 if active and special==0xf:
  if f[0]:f[:2]=[0,1]
  elif not f[1]:return f
 elif not(f[0] or f[1]):return f
 if f[2]:
  human_state=0x91<=state<=0x98 or state in [0xad,0xae,0xf1,0xf2]
  if human_state and not(cur==0 and 0x82<=prev<=0x84):f[2]=0
  else:f[:2]=[0,0]
 return f

def main():
 e=Harness();rnd=random.Random(0x7a0);rows=[];bad=[];initcases=0
 for mode,entry,reg in [('restart_init',0x7102354d90,UC_ARM64_REG_X19),('ctor_init',0x7102457620,UC_ARM64_REG_X22)]:
  for i in range(256):
   e.w32(e.body+0x794,rnd.getrandbits(32));e.w32(e.body+0x798,rnd.getrandbits(32));e.wb(e.body+0x7a0,rnd.randrange(256));e.uc.reg_write(reg,e.body);e.mode=mode;e.run(entry);e.mode=''
   assert (e.rb(e.body+0x7a0),e.r32(e.body+0x794),e.r32(e.body+0x798))==(0,0,9999);initcases+=1
 for i in range(8192):
  inp=(rnd.randrange(2),rnd.choice(list(range(0x7f,0x94))+[0xaa,0xac,0xad,0xed,0xee,0xef,0x10b,0x10c,0x10d,0]),rnd.randrange(2),rnd.choice([0,.25,.5,1,2,3,rnd.uniform(-2,4)]),rnd.choice([0,-.5,.25,rnd.uniform(-1,2)]),rnd.choice([0,-.5,.25,rnd.uniform(-1,2)]),rnd.randrange(7),rnd.randrange(2),rnd.choice([-10,-1,0,1,2,3,5,10,40]),rnd.choice([-3,0,5,100,0x7fffffff]))
  got=e.delay(*inp);exp=py_delay(*inp)
  if got!=exp:bad.append({'input':inp,'got':got,'expected':exp})
 assert not bad,bad[:4]
 delay_result={'cases':8192,'bad':0,'field_checks':24576,'entry':hex(DENTRY),'stop':hex(DSTOP),'candidate_supplied':True,'w26_coordinate_match_supplied':True,'external_calls':len(e.calls),'faults':len(e.faults)}
 coordcases=0
 for i in range(4096):
  base=[F(rnd.uniform(-1,1)) for _ in range(3)];n=list(base);m=list(base);axis=rnd.randrange(3);m[axis]=F(m[axis]+rnd.choice([-2,-1,0,1,2])*F(2**-23));got=e.coordinate(n,m);exp=all(-F(2**-23)<=F(a-b)<=F(2**-23) for a,b in zip(n,m));assert got==exp;coordcases+=1
 producer_cases=0
 for state,air,paint,kind,grindactive,old,delay,y in itertools.product([0x85,0x88,0x91,0xaa,0xed],[0,1,3,4,5],[0,1,2,3],[0,1,2],[0,1],[0,1],[0,1,5],[0,.5,1]):
  candidate,match,got=e.producer(state,air,paint,kind,grindactive,old,delay,10,y)
  in_group=0x82<=state<=0x90 or 0xaa<=state<=0xac or state in [0xed,0xee,0x10c]
  expected_candidate=int(in_group and state!=0x88 and paint<2 and kind not in [1,2] and not grindactive and air<4)
  assert candidate==expected_candidate and match==1,(state,air,paint,kind,grindactive,candidate,expected_candidate)
  exp=py_delay(expected_candidate,state,1,y,0,0,0,old,delay,10);assert got==exp,(got,exp);producer_cases+=1
 producerresult={'cases':producer_cases,'bad':0,'entry':'0x710248c16c','stop':hex(DSTOP),'native_dependencies':['0x7102458cfc','0x7102531028'],'stubs':0,'fields_supplied':'StepPaint mode/squid state/airFrames/support normals/warp type/grind byte/playerparam13c=60 and inactive special invalid handles; original sampler/whole slot19 not executed'}
 smcases=0;smcalls=0;smother=0;nanfields=0
 for hidden,human,squid,f0,kind,dead,state,oldbits in itertools.product([0,1],[0,1],[0,1],[0,60,61,90],[0,4],[0,1],[0x85,0x96],range(8)):
  old=[(oldbits>>i)&1 for i in range(3)]+[0];got,f,cb=e.display(hidden,human,squid,f0,kind,dead,state,old);ex,ef,ecb=py_display(hidden,human,squid,f0,kind,dead,state,old)
  assert got==ex and f==ef,(got,ex,f,ef);assert cb==ecb,(cb,ecb)
  for m,team,_ in ecb:assert e.r32(e.bind[m]+8+4*team)==0x7fc00000;nanfields+=1
  smcases+=1;smcalls+=len(cb);smother+=len(e.othercalls)
 smresult={'cases':smcases,'bad':0,'whole_function':hex(SMFN),'native_helper':'0x7102448878 actually executed','reset_setter_stub_calls':smcalls,'other_stain_setter_stub_calls':smother,'total_setter_stub_calls':smcalls+smother,'nan_cache_fields_checked':nanfields,'scope':'ordinary invalid rail, bodyCB8=0, four material setter callbacks only are capture/return fixtures; whole GPU/material updater excluded'}
 hc=0
 for i in range(4096):
  flags=[rnd.randrange(2) for _ in range(4)];old=[rnd.randrange(2) for _ in range(4)];state=rnd.choice([0x85,0x90,0x91,0x92,0x98,0x99,0xad,0xae,0xf1,0xf2]);prev=rnd.choice([0x81,0x82,0x84,0x85]);cur=rnd.choice([0,1,-1]);timers=[rnd.choice([-1,0,0,0,1]) for _ in range(7)];life=[rnd.randrange(2),rnd.randrange(2),rnd.randrange(2),rnd.choice([-1,0,1])];debug=rnd.randrange(2);special=rnd.choice([0,0xf,0x1a]);selected=rnd.randrange(2);disable=rnd.randrange(2)
  for o,v in zip([0xf4,0xf5,0xf6,0xf8],flags):e.wb(e.sm+o,v)
  for j,v in enumerate(old):e.wb(e.holder+0x60+j,v)
  e.w32(e.sm+0xc8,state);e.w32(e.sm+0xcc,prev);e.wf(e.wrap+0x30,cur)
  for o,v in zip([0xde0,0xdf0,0xe04,0xe0c,0xe1c,0xd60,0xd5c],timers):e.w32(e.body+o,v)
  for o,v in zip([0x30,0x31,0x35],life[:3]):e.wb(e.life+o,v)
  e.wf(e.life+0x38,life[3]);e.wb(e.body+0xa5f4,debug);e.w32(e.body+0x65c,special);e.wb(e.body+0x926c,disable);e.w64(e.body+0x678,0x1234 if selected else 0);e.w64(e.body+0x688,0x1234 if selected else 0);e.w64(e.body+0x588,0);e.w64(e.body+0x598,0)
  e.run(HOLDER,x=(e.holder,));got=[e.rb(e.holder+0x60+j) for j in range(4)];exp=py_holder(flags,state,prev,cur,old,timers,life,debug,special,selected,disable)
  assert got==exp,(got,exp,flags,old,timers,life)
  hc+=1
 holderresult={'cases':hc,'bad':0,'field_checks':hc*4,'whole_function':hex(HOLDER),'stubs':0,'scope':'runtime fields are fixture inputs; no actual producer/state/death pipeline executed'}
 # Deterministic full lifecycle, native tail -> whole display -> whole holder each frame.
 for o in [0xde0,0xdf0,0xe04,0xe0c,0xe1c,0xd60,0xd5c]:e.w32(e.body+o,0)
 e.wb(e.life+0x30,0);e.wb(e.life+0x31,0);e.wb(e.life+0x35,1);e.wf(e.life+0x38,0);e.wb(e.body+0xa5f4,0);e.w64(e.body+0x678,0);e.w64(e.body+0x688,0)
 for name,y,seq in [('flat_Ny1',1,[0]*8+[1]*20+[0]*20+[1]*20),('slope_Ny_half',.5,[0]*8+[1]*20+[0]*20+[1]*20),('negative_factor',2,[0]*8+[1]*20+[0]*20+[1]*20),('flicker',0,[0]*8+[1,0]*10+[1]*20+[0]*20)]:
  old,delay,age=0,5,0;vis=[0,0,1,0];trace=[]
  for frame,cand in enumerate(seq):
   candidate,match,(hidden,delay,age)=e.producer(0x85,0,0 if cand else 2,0,0,old,delay,age,y);assert candidate==cand;display,f0,calls=e.display(hidden,0,1,0,0,0,0x85,vis);e.run(HOLDER,x=(e.holder,));holder=[e.rb(e.holder+0x60+j) for j in range(4)];assert holder==display
   trace.append({'frame':frame,'candidate':cand,'hidden':hidden,'delay':delay,'age':age,'sm':display,'holder':holder,'f0':f0,'callbacks':calls});old=hidden;vis=display
  rows.append({'name':name,'factor':float(factor(1,y,0,0)),'trace':trace})
 result={'native_delay':delay_result,'coordinate_match':{'cases':coordcases,'bad':0,'entry':'0x710248c250','stop':'0x710248c2e4','stubs':0},'initialization':{'block_cases':initcases,'bad':0,'fields':{'B7a0':0,'B794':0,'B798':9999},'scope':'known ctor/restart field-write blocks only; existing whole constructors not reanalyzed'},'ordinary_producer':producerresult,'whole_display':smresult,'whole_holder':holderresult,'linked_trace_frames':sum(len(x['trace']) for x in rows),'linked_traces':rows,'scope':'ordinary producer block c16c through native delay + whole display + whole holder manually sequenced; candidate/match actually produced; original sampler and whole slot19/249648c caller not executed','PLT_calls':len(e.calls),'faults':len(e.faults),'code_sha256':hashlib.sha256((ROOT/'extracted/exefs/main.reloc.img').read_bytes()).hexdigest()}
 (OUT/'native_visibility.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k not in ['linked_traces']},ensure_ascii=False))
if __name__=='__main__':main()





