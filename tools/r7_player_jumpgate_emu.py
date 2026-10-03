"""R7: Jump_St -> ground state request gate, original 2447bfc.
Stub animation ended flag and final request application only; synthesized AS slot.
"""
import json,struct,sys
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r7_player_walk_emu import Harness,F,bits,frombits,ROOT

def main():
 sys.stdout.reconfigure(encoding='utf-8');h=Harness();e=h.e;m=e.mu
 def q(a,v):m.mem_write(a,struct.pack('<Q',v))
 q(h.sm+8,h.wrapper);q(h.sm+0x10,e.alloc(0x600));q(h.sm+0x18,h.wrapper)
 engine=e.alloc(0x300);p=struct.unpack('<Q',m.mem_read(0x7105790698,8))[0];q(p,engine)
 context={};requests=[]
 def hook(mu,a,size,unused):
  if a==0x710244fed8:mu.reg_write(UC_ARM64_REG_W0,context['ended'])
  else:requests.append(mu.reg_read(UC_ARM64_REG_W1))
  mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 for addr in [0x710244fed8,0x710244128c]:m.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr)
 cases=0;mis=[];table=[]
 for cur in [0x99,0x9a]:
  for target in [0x56,0x59,0x5e,0x5f,0x60,0x69,0x72,0x7b]:
   flags=e.ru32(0x7105630270+target*0x20+0x18)
   for rate in [F(1.),F(.6),F(.001)]:
    boundary=F(rate*F(6.));frames=[F(0),F(rate),frombits(bits(boundary)-1),boundary,frombits(bits(boundary)+1),F(20)]
    for frame in frames:
     for ended,blend,force in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]:
      context['ended']=ended;requests.clear();e.u32(h.sm+0xc8,cur);e.u32(h.sm+0xd0,0xffffffff)
      e.f32(h.wrapper+0x30,float(frame));e.f32(h.slot+0xd4,float(rate))
      got=e.call(0x7102447bfc,h.sm,target,blend,force,fargs=(1.,))&1
      predicted=F(frame+rate)
      expected=bool(ended or blend or force or (predicted>0 if flags&4 else predicted>=F(rate*F(7.))))
      if got!=expected or requests!=([target] if expected else []):
       if len(mis)<8:mis.append({'input':[cur,target,float(rate),float(frame),ended,blend,force],'got':got,'expected':expected,'requests':list(requests)})
      if rate==1 and ended==blend==force==0 and frame in [0,6]:table.append({'from':hex(cur),'to':hex(target),'frame':float(frame),'target_bit2':bool(flags&4),'allowed':bool(got)})
      cases+=1
 out={'cases':cases,'mismatches':mis,'table':table,'function':'0x7102447bfc','stubs':{'0x710244fed8':'animation ended input','0x710244128c':'capture final apply request'},'limits':['Jump_St/Jump_St_Shoot to normal human ground states only','Full jump/physics frame and animation application not executed']}
 (ROOT/'analysis/completion/r7/player_jumpgate_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in out.items() if k!='table'},ensure_ascii=False));assert not mis
if __name__=='__main__':main()