"""R7 shooter upper-layer selection: original 244a260/ab70/b030/b190/d5fc.
Stubs are explicit boundary inputs (clip end, ink sufficiency, shot-wait scalar),
rail=false, and output request capture; ASB request application is not emulated.
"""
import json,random,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r7_player_walk_emu import Harness,F,bits,frombits,ROOT
LONG_SUB={0xd,0x12,0x23,0x36,0x38,0x39}
LATCH_SUB={0xd,0x12,0x23,0x36}
LONG_MAIN={0x59,0xc2,0xc5}

def ng_ref(main,sub,previous,changed,held,locked,ink,end,q):
 long=main in LONG_MAIN or sub in LONG_SUB or (changed and (previous in LONG_MAIN or sub in LATCH_SUB))
 if long and F(end)<F(12):return False
 threshold=F(12 if long else 3)
 return True if locked or not held or not ink else F(q)>threshold

def select_ref(c):
 main,sub,previous,changed,air,v,stick,shoot,held,locked,ink,end,q=c
 if not air:
  if main not in [0xe2,0xe3] and sub==0x31:return None
  threshold=frombits(0x3a83126e) if stick>0 else frombits(0x3b449ba6)
  if F(v)<threshold or 0x4c<=main<=0x5d:return None
  if main in [0x54,0x5e,0xe2]:return None
  if not shoot:return None if main==0x5f else 0x45
 elif not shoot:return None
 return 0x37 if ng_ref(main,sub,previous,changed,held,locked,ink,end,q) else 0x36

class Upper:
 def __init__(self):
  self.h=Harness();e=self.h.e;self.e=e;m=e.mu;self.request=[]
  def q(a,v):m.mem_write(a,struct.pack('<Q',v))
  self.actor=e.alloc(0x300);q(self.h.body+8,self.actor);q(self.h.body+0xa8c8,self.h.sm)
  rail=e.alloc(0x200);vt=e.alloc(0x200);stub=e.alloc(16)
  m.mem_write(stub,bytes.fromhex('00008052c0035fd6'));q(rail,vt);q(vt+0x100,stub);q(self.h.body+0xa670,rail)
  self.stub_calls={hex(x):0 for x in [0x710245064c,0x71024bb75c,0x7102580a74,0x7102448400]}
  for fn in [0x710245064c,0x71024bb75c,0x7102580a74,0x7102448400]:m.hook_add(UC_HOOK_CODE,self.hook,begin=fn,end=fn)
 def hook(self,m,a,size,unused):
  self.stub_calls[hex(a)]+=1
  if a==0x710245064c:m.reg_write(UC_ARM64_REG_S0,bits(self.end))
  elif a==0x71024bb75c:m.reg_write(UC_ARM64_REG_W0,int(self.ink))
  elif a==0x7102580a74:m.reg_write(UC_ARM64_REG_S0,bits(self.q))
  elif a==0x7102448400:self.request.append(m.reg_read(UC_ARM64_REG_W1))
  m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
 def configure(self,c):
  main,sub,previous,changed,air,v,stick,shoot,held,locked,ink,end,q=c
  self.ink,self.end,self.q=ink,end,q;self.request=[]
  e=self.e;b=self.h.body;s=self.h.sm
  e.u32(s+0xc8,main);e.u32(s+0xcc,previous);e.u32(s+0xd0,sub)
  e.mu.mem_write(s+0x1fd,bytes([changed]));e.f32(s+0xd4,float(v));e.f32(b+0x47c,float(stick))
  e.u32(b+0xad8,8 if shoot else 0);e.u32(b+0x4d8,8 if shoot else 0)
  e.u32(b+0x4d0,1 if held else 0);e.u32(b+0xab4,1 if locked else 0)
 def select(self,c):
  self.configure(c);self.e.call(0x710244a260,self.h.sm,c[4]);assert len(self.request)<=1
  return self.request[0] if self.request else None
 def ng(self,c):
  self.configure(c);return bool(self.e.call(0x710244b190,self.h.sm)&1)

def main():
 sys.stdout.reconfigure(encoding='utf-8');u=Upper();rng=random.Random(70032)
 mains=[0x54,0x56,0x59,0x5a,0x5e,0x5f,0x60,0x69,0x72,0x7b,0x99,0x9b,0xa0,0xa6,0xe2,0xe3]
 cases=[]
 for sub in [0xffffffff,0x31,0x36,0x37,0xd]:
  for air in [0,1]:
   for state in mains:
    for v in [0.,float(frombits(0x3a83126e)),.003,.096]:
     cases.append((state,sub,0x56,0,air,v,1.,True,True,False,True,40.,3.))
 for _ in range(6000):
  cases.append((rng.choice(mains),rng.choice([0xffffffff,0x31,0x36,0x37,0xd]),rng.choice(mains),rng.randrange(2),rng.randrange(2),rng.choice([0.,.0005,.001,.003,.05,.096]),rng.choice([0.,1.]),rng.choice([False,True]),rng.choice([False,True]),rng.choice([False,True]),rng.choice([False,True]),rng.choice([0.,11.,12.,40.]),rng.choice([0.,3.,float(npnext3),12.,float(npnext12),999.])))
 mis=[];ngmis=[];counts={};samples=[]
 for i,c in enumerate(cases):
  got=u.select(c);exp=select_ref(c);counts[str(got)]=counts.get(str(got),0)+1
  if got!=exp and len(mis)<8:mis.append({'i':i,'input':c,'got':got,'expected':exp})
  expectedng=ng_ref(c[0],c[1],c[2],c[3],c[8],c[9],c[10],c[11],c[12]);gotng=u.ng(c)
  if gotng!=expectedng and len(ngmis)<8:ngmis.append({'i':i,'input':c,'got':gotng,'expected':expectedng})
  if i%700==0:samples.append({'input':c,'request':got,'ng':gotng})
 out={'selection_cases':len(cases),'ng_predicate_cases':len(cases),'selection_mismatches':mis,'ng_mismatches':ngmis,'request_histogram':counts,'boundary_stub_calls':u.stub_calls,'original_functions':['0x710244a260','0x710244ab70','0x710244b030','0x710244b190','0x710246d5fc'],'stubs':{'0x710245064c':'clip end value','0x71024bb75c':'ink sufficiency bool','0x7102580a74':'shot-wait scalar','0x7102448400':'capture request; no ASB apply','rail vt+0x100':'false'},'limits':['K=1; no sub/special input; no rail','Normal human main states; selector request only','Other weapon branches, ASB lifetime and state priority application not executed'],'samples':samples}
 (ROOT/'analysis/completion/r7/player_upper_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in out.items() if k!='samples'},ensure_ascii=False));assert not mis and not ngmis
npnext3=frombits(bits(3.)+1);npnext12=frombits(bits(12.)+1)
if __name__=='__main__':main()