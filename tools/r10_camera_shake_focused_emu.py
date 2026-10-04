"""r10 original SubjectiveType producer, message receiver and five-user copy.
Profile virtual methods are synthetic inputs. Native Team encoding/decoding and RTTI execute.
The PlayerModel block starts at 251589c with x19 at the real enclosing model structure.
No original instructions are patched; message queue scheduling and renderer are outside scope.
"""
import sys, json, struct, random
from collections import Counter
from pathlib import Path
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R']
class E(H):
 def _block(self,mu,a,size,user):
  self.recent.append(hex(a));self.recent=self.recent[-20:]
  if a in [R.RETADDR+0x100,R.RETADDR+0x104,R.RETADDR+0x108]:
   self.inputs[a]+=1
   value=self.profile_index if a==R.RETADDR+0x100 else (0xd0000001+self.profile_team if a==R.RETADDR+0x104 else 8)
   mu.reg_write(UC_ARM64_REG_X0,value&0xffffffffffffffff)
   mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  try:super()._block(mu,a,size,user)
  except Exception:print('native recent blocks',self.recent);raise
e=E([0x710275e99c]);e.executed=set();e.sdklog=Counter();e.stublog=Counter();e.inputs=Counter();e.recent=[]
def no_null(mu,access,a,size,value,user):
 if a<0x400000:raise RuntimeError(f'null read {a:#x} pc={mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
B=R.BASE;count=Counter();rng=random.Random(0x275e99)
view=e.alloc(0x400);msg=e.alloc(0x80);packet=e.alloc(0x20);actor=e.alloc(0x900);body=e.alloc(0xac00);comp=e.alloc(0x200);model=e.alloc(0x2900);root=e.alloc(0x310);graphic=e.alloc(0xe400);gstate=e.alloc(0x1800)
e.w64(comp+0x108,body);e.w64(body+8,actor);e.w64(actor+0x780,root);e.w64(body+0xa690,graphic);e.w64(graphic+0xe378,gstate);e.w64(gstate+0x1368,0)
e.w64(model+0x27d8,comp);e.w64(model+0x27e0,root);e.w64(msg,B+0x5624888);e.w32(packet+4,0x6c2b6a01);e.w64(packet+0x10,msg)
profile=e.alloc(0x30);vt=e.alloc(0x40);e.w64(profile,vt);e.w64(vt+0x20,R.RETADDR+0x100);e.w64(vt+0x28,R.RETADDR+0x104);e.w64(vt+0x30,R.RETADDR+0x108);e.w64(B+0x5801cb8,profile)
users=[]
for off in [0x1d8,0x200,0x278,0x2a0,0x2c8]:
 u=e.alloc(0x100);p=e.alloc(0x40);e.w64(root+off,u);e.w64(u+0x80,p);users.append((u,p))
examples=[]
# Native selector outputs classified with real Team constructors/getter; no decoded Team stub.
for selected in [0,1,7]:
 for player in [0,1,7]:
  for selected_team in [0,1,2]:
   for player_team in [0,1,2]:
    for mode in [0,1,2]:
     for disabled in [0,1]:
      for previous_visible in [0,1]:
       e.profile_index=selected;e.profile_team=selected_team
       e.w32(actor+0x798,player);e.w32(actor+0x668,player_team);e.w32(view+0x280,mode);e.mu.mem_write(view+0x391,bytes([disabled]));e.mu.mem_write(body+0x1054,bytes([previous_visible]))
       e.w32(msg+0x44,2);e.call(B+0x275e99c,[view,msg,comp,selected])
       expected=0 if player==selected else (1 if selected_team==player_team else 2)
       visible=0 if disabled else (int(player==selected) if mode==0 else (1 if mode==1 else previous_visible))
       assert e.r32(msg+0x44)==expected,(selected,player,selected_team,player_team,e.r32(msg+0x44),expected)
       assert e.mu.mem_read(msg+0x40,1)[0]==visible
       e.w32(body+0x1058,99);e.w32(root+0x2f0,99);e.mu.mem_write(body+0xf58,b'\0')
       e.call(B+0x234f518,[comp,packet]);assert e.mu.reg_read(UC_ARM64_REG_W0)==1
       assert e.r32(body+0x1058)==expected and e.r32(root+0x2f0)==expected
       assert e.mu.mem_read(body+0x1054,1)[0]==visible and e.mu.mem_read(body+0xf58,1)[0]==1
       assert e.mu.mem_read(gstate+0x25,1)[0]==visible
       # Five different old values and high dirty bits, with original block copy.
       old=[]
       for u,p in users:
        v=rng.randrange(3);dirty=rng.getrandbits(64);e.w32(p,v);e.w64(u+0x70,dirty);e.w32(p+4,0x12345678);old.append((v,dirty))
       e.mu.reg_write(UC_ARM64_REG_X19,model);e.mu.emu_start(B+0x251589c,B+0x2515960,count=500)
       assert e.mu.reg_read(UC_ARM64_REG_PC)==B+0x2515960
       for (u,p),(v,dirty) in zip(users,old):
        assert e.r32(p)==expected and e.r32(p+4)==0x12345678
        assert e.r64(u+0x70)==(dirty if v==expected else dirty|1)
       count['producer_receiver_copy']+=1
       if len(examples)<6:examples.append(dict(selected=selected,player=player,selected_team=selected_team,player_team=player_team,subjective=expected,visible=visible))
# Unknown/unselected team path preserves payload default2; admission flags still update.
for selected in [-1,0,7]:
 for profile_index in [-1,0]:
  for profile_team in [0,1,2,3]:
   e.profile_index=profile_index;e.profile_team=profile_team;e.w32(view+0x280,1);e.mu.mem_write(view+0x391,b'\0');e.w32(actor+0x798,7);e.w32(actor+0x668,0);e.w32(msg+0x44,2)
   e.call(B+0x275e99c,[view,msg,comp,selected]);actual=e.r32(msg+0x44)
   expected=2 if selected<0 or profile_index<0 or profile_team==3 else (0 if selected==7 else (1 if profile_team==0 else 2))
   assert actual==expected,(selected,profile_index,profile_team,actual,expected);count['unknown_selected_boundary']+=1
out=dict(counts=dict(count),mismatches=0,null_reads=0,code_patch=0,SDK_stubs=dict(e.sdklog),nonSDK_stubs={hex(k):v for k,v in e.stublog.items()},profile_virtual_input_calls={hex(k):v for k,v in e.inputs.items()},executed_blocks=len(e.executed),examples=examples,boundaries=['Original275e99c whole selector +146cb20/146d164 Team encoding/decoding; profileVT20 synthetic selected player index and VT28 direct Team reference D0000001+team inputs','Original234f518 whole message dispatcher, native RTTI; graphics list1368=null synthetic; no live queue dispatch','Original251589c..2515960 enclosing2515488 five-user SubjectiveType copy block; x19=model supplied, no render/animation execution','Game original constants/branch bytes unchanged; no controller device or full range scene executes'])
(ROOT/'analysis/camera_100_r10/shake/focused_native.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='examples'},ensure_ascii=False))
