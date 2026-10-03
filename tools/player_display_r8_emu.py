"""New ordinary display boundaries; reuses r2 native harness, never overwrites r2 outputs."""
import sys, json, random, struct, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'web/tools'))
import numpy as np
from unicorn.arm64_const import *
from squid_visibility_r2_emu import Harness, DENTRY, DSTOP, HOLDER, STACK, f2u
OUT = ROOT / 'analysis/port_character_r8/display'
OUT.mkdir(parents=True, exist_ok=True)
F = np.float32

class R8Harness(Harness):
 def hook(self, uc, a, size, ud):
  super().hook(uc, a, size, ud)
  if self.mode == 'corner' and a == self.corner_stop: uc.emu_stop()
 def producer_input(self, i, old):
  b=self.body; p=b+0x784
  for off,v in [(0xc0,i['airFrames']),(0x774,i['chargeFrames']),(0xa40,i['ceilingTimer']),(0x794,old['delay']),(0x798,old['age'])]:self.w32(b+off,v)
  self.wb(b+0x7a0,old['hidden']);self.w32(self.sm+0xc8,i['state']);self.w32(self.squidmove+0x30,i['paintClass']);self.w32(self.dokan+0x30,i['dokanKind']);self.wb(self.grind+0x1f4,i['grindActive'])
  for off,key in [(0x781,'b781'),(0x7f4,'b7f4'),(0x7f9,'b7f9'),(0x9210,'forceByte'),(0x782,'wallChargeRelease')]:self.wb(b+off,i[key])
  self.wb(self.launch+0xb4,i['launchActive']);self.wb(self.rail+0x1e0,i['railLatch']);self.wb(self.warp+0xeec,0)
  for off,key in [(0x1b4,'supportNormalYBits'),(0xe8,'verticalVelocityBits'),(0xa74,'edgeBlendBits'),(0xa78,'edgeTargetBits')]:self.w32(b+off,i[key])
  self.w32(self.pp+0x13c,i['chargeMaxBits'])
  for off,key in [(0x180,'normalBits'),(0x198,'rawNormalBits')]:
   for j,bits in enumerate(i[key]):self.w32(b+off+j*4,bits)
  self.w64(STACK+0x180,p);self.w64(STACK+0x168,0);self.w64(STACK+0x138,0);self.uc.reg_write(UC_ARM64_REG_X19,self.smref);self.uc.reg_write(UC_ARM64_REG_X22,self.misc)
  self.mode='producer';self.run(0x710248c16c);self.mode='';assert self.uc.reg_read(UC_ARM64_REG_PC)==DSTOP
  return {'candidate':bool(self.candidate_read),'match':bool(self.match_read),'state':{'hidden':bool(self.rb(b+0x7a0)),'delay':self.rs32(b+0x794),'age':self.rs32(b+0x798)}}
 def holder_input(self, flags, i):
  for o,v in zip([0xf4,0xf5,0xf6,0xf8],flags):self.wb(self.sm+o,v)
  for j,v in enumerate(i['old']):self.wb(self.holder+0x60+j,v)
  self.w32(self.sm+0xc8,i['state']);self.w32(self.sm+0xcc,i['previousState']);self.wf(self.wrap+0x30,i['cur'])
  for o,key in [(0xde0,'de0'),(0xdf0,'df0'),(0xe04,'e04'),(0xe0c,'e0c'),(0xe1c,'e1c'),(0xd60,'d60'),(0xd5c,'d5c')]:self.w32(self.body+o,i[key])
  for o,key in [(0x30,'life30'),(0x31,'life31'),(0x35,'life35')]:self.wb(self.life+o,i[key])
  self.wf(self.life+0x38,i['life38']);self.wb(self.body+0xa5f4,i['debug']);self.w32(self.body+0x65c,i['special']);self.wb(self.body+0x926c,i['specialDisabled'])
  self.w64(self.body+0x678,0x1234 if i['selected'] else 0);self.w64(self.body+0x688,0x1234 if i['selected'] else 0);self.w64(self.body+0x588,0);self.w64(self.body+0x598,0)
  self.run(HOLDER,x=(self.holder,));return [bool(self.rb(self.holder+0x60+j)) for j in range(4)]

def basic(**extra):
 i={'state':0x85,'paintClass':0,'airFrames':0,'ceilingTimer':0,'chargeFrames':0,'chargeMaxBits':f2u(45),'normalBits':list(map(f2u,[0,1,0])),'rawNormalBits':list(map(f2u,[0,1,0])),'supportNormalYBits':f2u(1),'verticalVelocityBits':0,'edgeBlendBits':0,'edgeTargetBits':0,'b781':False,'b7f4':False,'b7f9':False,'railLatch':False,'forceByte':False,'launchActive':False,'wallChargeRelease':False,'debugForce':False,'dokanKind':0,'grindActive':False,'warpActive':False,'specialCandidate':False}
 i.update(extra);return i

def holder_basic(**extra):
 i={'state':0x85,'previousState':0x85,'cur':0,'old':[False]*4,'de0':0,'df0':0,'e04':0,'e0c':0,'e1c':0,'d60':0,'d5c':0,'life30':False,'life31':False,'life35':True,'life38':0,'debug':False,'special':0,'selected':False,'specialDisabled':False};i.update(extra);return i

def main():
 e=R8Harness();r=random.Random(0x7a008);producer=[];smrows=[];holders=[];corner=[];traces=[];probe=[];radii=[]
 for n in range(2048):
  y=r.choice([0,.25,.5,1,2]);normal=list(map(f2u,[0,y,0]));raw=normal[:] if n%3 else list(map(f2u,[0,1,0]))
  i=basic(state=r.choice([0x82,0x84,0x85,0x87,0x88,0x8f,0x90,0x91,0xaa,0xac,0xed,0xee,0x10c]),paintClass=r.choice([0,1,2,3,4,0xffffffff]),airFrames=r.choice([-1,0,1,2,3,4,5]),ceilingTimer=r.choice([-1,0,0,1]),chargeFrames=r.choice([-10,0,9,10,11,12,14,15,21,22,23,24,45,55,0x7fffffff,-0x80000000]),chargeMaxBits=f2u(r.choice([45,18,5,0,-5,-45])),normalBits=normal,rawNormalBits=raw,supportNormalYBits=r.choice([f2u(0),f2u(.64144969),f2u(1),0x7fc00000]),verticalVelocityBits=f2u(r.choice([0,.05,.05000001,.1])),edgeBlendBits=r.choice([f2u(-.5),0,f2u(.25),f2u(1),0x7fc00000]),edgeTargetBits=r.choice([0,f2u(.5),0x7fc00000]),b781=bool(r.randrange(2)),b7f4=bool(r.randrange(2)),b7f9=bool(r.randrange(2)),railLatch=n%17==0,forceByte=n%19==0,launchActive=n%23==0,wallChargeRelease=n%13==0,dokanKind=r.choice([0,0,1,2]),grindActive=n%11==0)
  old={'hidden':bool(r.randrange(2)),'delay':r.choice([-0x80000000,-3,-1,0,1,2,3,5,10,0x7fffffff]),'age':r.choice([-1,0,9999,0x7fffffff])};got=e.producer_input(i,old);producer.append({'input':i,'old':old,'expected':got})
 for n in range(384):
  old=[bool(r.randrange(2)) for _ in range(4)];i={'hidden':bool(r.randrange(2)),'humanCommand':bool(r.randrange(2)),'squidCommand':bool(r.randrange(2)),'formCounter':r.choice([-1,59,60,61,62,90,140]),'modelKind':r.choice([0,4,18]),'dead':bool(r.randrange(2)),'state':r.choice([0x82,0x85,0x91,0x96]),'old':old}
  flags,count,calls=e.display(i['hidden'],i['humanCommand'],i['squidCommand'],i['formCounter'],i['modelKind'],i['dead'],i['state'],old)
  caches=[{'model':m,'team':t,'bits':e.r32(e.bind[m]+8+t*4),'setterBits':v} for m,t,v in calls]
  smrows.append({'input':i,'flags':list(map(bool,flags)),'counter':count,'resetCalls':calls,'resetCaches':caches})
 for n in range(384):
  f=[bool(r.randrange(2)) for _ in range(4)];i=holder_basic(state=r.choice([0x85,0x91,0x98,0xad,0xae,0xf1,0xf2]),previousState=r.choice([0x82,0x84,0x85]),cur=r.choice([0,1,-1]),old=[bool(r.randrange(2)) for _ in range(4)],special=r.choice([0,0xf,0x1a]),selected=bool(r.randrange(2)),specialDisabled=bool(r.randrange(2)))
  for key in ['de0','df0','e04','e0c','e1c','d60','d5c']:i[key]=r.choice([-1,0,0,0,1])
  for key in ['life30','life31','life35','debug']:i[key]=bool(r.randrange(2))
  i['life38']=r.choice([-1,0,1]);holders.append({'input':i,'flags':f,'expected':e.holder_input(f,i)})
 # Probe consumer block + threshold-zero branch + min update, with query result supplied.
 for n in range(512):
  q=e.alloc(0x20);pre=F(r.choice([0,.001,.01,.05,.3,1]));hit=True;lo=F(r.choice([.06,.1,.2,.3]));prior=F(r.uniform(0,1));inc=F(r.choice([.01,.05]));e.wf(q+0x14,pre);e.w64(STACK+0x178,q);e.uc.reg_write(UC_ARM64_REG_X29,STACK+0x200);e.uc.reg_write(UC_ARM64_REG_X0,hit);e.uc.reg_write(UC_ARM64_REG_S14,f2u(pre));e.uc.reg_write(UC_ARM64_REG_S15,f2u(.01));e.corner_stop=0x71024ac7cc;e.mode='corner';e.run(0x71024ac784);e.mode='';after=e.rf(q+0x14)
  e.uc.reg_write(UC_ARM64_REG_X26,q);e.uc.reg_write(UC_ARM64_REG_W8,f2u(lo));e.corner_stop=0x71024accb4;e.mode='corner';e.run(0x71024acc10);e.mode='';target=e.r32(q+0x10)
  e.wf(q+0xc,prior);e.uc.reg_write(UC_ARM64_REG_S0,f2u(inc));e.corner_stop=0x71024afe5c;e.mode='corner';e.run(0x71024afe48);e.mode='';blend=e.r32(q+0xc)
  assert target==0 and blend==0,(pre,after,lo,target,blend);corner.append({'preBits':f2u(pre),'hit':True,'afterBits':f2u(after),'loBits':f2u(lo),'priorBits':f2u(prior),'increaseBits':f2u(inc),'expectedBlendBits':blend,'expectedTargetBits':target})
 pc=e.alloc(0x2400);edge=e.alloc(0x20)
 for n in range(384):
  contact=list(map(F,[r.uniform(-10,10),r.uniform(-2,2),r.uniform(-10,10)]));body=contact[:]
  if n%6:body[0]=F(body[0]+r.choice([.0099999,.01,.0100001,r.uniform(-2,2)]));body[2]=F(body[2]+r.uniform(-1,1))
  platform=list(map(F,[r.uniform(-.1,.1),r.uniform(-.1,.1),r.uniform(-.1,.1)]));dx=F(body[0]-contact[0]);dz=F(body[2]-contact[2]);e.uc.reg_write(UC_ARM64_REG_X19,0);e.uc.reg_write(UC_ARM64_REG_X21,e.body);e.uc.reg_write(UC_ARM64_REG_X26,pc);e.uc.reg_write(UC_ARM64_REG_X20,edge);e.uc.reg_write(UC_ARM64_REG_X29,STACK+0x200);e.w64(STACK+0x178,edge)
  e.uc.reg_write(UC_ARM64_REG_S0,0);e.uc.reg_write(UC_ARM64_REG_S1,f2u(F(dz*dz)));e.uc.reg_write(UC_ARM64_REG_S9,0);e.uc.reg_write(UC_ARM64_REG_S12,f2u(dz));e.uc.reg_write(UC_ARM64_REG_S13,f2u(dx))
  for j,v in enumerate(contact):e.wf(pc+0xa0+j*4,v)
  for j,v in enumerate(platform):e.wf(e.body+0x108+j*4,v)
  e.corner_stop=0x71024ac780;e.mode='corner';e.run(0x71024ac680);e.mode='';probe.append({'contactBits':list(map(f2u,contact)),'bodyBits':list(map(f2u,body)),'platformBits':list(map(f2u,platform)),'startBits':[e.r32(pc+0x14b8+j*4) for j in range(3)],'endBits':[e.r32(pc+0x14c4+j*4) for j in range(3)]})
 singleton=e.alloc(0x200);world=e.alloc(0x300);e.w64(singleton+0xe8,world)
 for val in [None,.01,.001,.05,.3,2001,float('inf'),-float('inf'),float('nan'),-1]:
  e.w64(0x710599dfa8,0 if val is None else singleton)
  if val is not None:e.wf(world+0x21c,val)
  e.w32(STACK+0x2c,f2u(.01));e.uc.reg_write(UC_ARM64_REG_X19,pc);e.uc.reg_write(UC_ARM64_REG_X20,0xffffffffffffffff);e.uc.reg_write(UC_ARM64_REG_X29,STACK+0x200);e.corner_stop=0x71024f140c;e.mode='corner';e.run(0x71024f1358);e.mode='';radii.append({'toleranceBits':None if val is None else f2u(val),'expectedBits':e.uc.reg_read(UC_ARM64_REG_S0)&0xffffffff})
 # Actual-data charge maxima 45/18/5, floor -> wall-like -> air -> emerge sequences.
 for maximum in [45,18,5]:
  old={'hidden':False,'delay':0,'age':9999};vis=[False,False,True,False];out=[]
  for frame in range(96):
   own=frame<20 or 30<=frame<74;i=basic(paintClass=0 if own else 2,chargeMaxBits=f2u(maximum),chargeFrames=max(0,frame-40) if 40<=frame<68 else 0,airFrames=max(0,frame-68) if 68<=frame<74 else 0)
   if 30<=frame<40:i.update(normalBits=list(map(f2u,[1,0,0])),rawNormalBits=list(map(f2u,[1,0,0])),supportNormalYBits=0)
   p=e.producer_input(i,old);flags,counter,calls=e.display(p['state']['hidden'],0,1,0,0,0,i['state'],vis);hi=holder_basic(state=i['state'],old=vis);final=e.holder_input(flags,hi)
   out.append({'frame':frame,'input':i,'old':dict(old),'expected':p,'sm':list(map(bool,flags)),'holder':final,'counter':counter,'resetCalls':calls});old=dict(p['state']);vis=list(map(bool,flags))
  traces.append({'chargeMax':maximum,'frames':out})
 fixture={'source':'main.reloc.img','sha256':hashlib.sha256((ROOT/'extracted/exefs/main.reloc.img').read_bytes()).hexdigest(),'producer':producer,'sm':smrows,'holder':holders,'cornerZero':corner,'cornerProbe':probe,'cornerRadius':radii,'traces':traces,'scope':'Native c16c..c7dc producer block -> actual 2458cfc/2531028; explicit raw fixture inputs. Native SM and holder whole, four material setter capture callbacks. Corner probe result supplied. Probe geometry/radius separate native blocks. Not whole slot19/Phive/GPU.'}
 dest=ROOT/'web/games/splatoon3/tests/fixtures/player_display_r8.json';dest.write_text(json.dumps(fixture,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 summary={'producer_new_boundaries':len(producer),'SM_whole_new_boundaries':len(smrows),'holder_whole_new_boundaries':len(holders),'corner_zero_sequences':len(corner),'corner_geometry_blocks':len(probe),'corner_radius_blocks':len(radii),'linked_frames':sum(len(t['frames']) for t in traces),'PLT_calls':len(e.calls),'faults':len(e.faults),'material_reset_capture_calls':sum(len(row['resetCalls']) for row in smrows),'fixture':str(dest.relative_to(ROOT)),'scope':fixture['scope']}
 (OUT/'native_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False));assert not e.calls and not e.faults
if __name__=='__main__':main()
