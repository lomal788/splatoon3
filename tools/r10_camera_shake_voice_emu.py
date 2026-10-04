"""Execute original game rumble update with its actual selected voice vtable.
Synthetic manager/handle/SDKplayer graph; SDK IsLoop/Play/Stop are captured boundaries.
No instruction patches, device output, scene or voice-wave decoder execution.
"""
import json, struct, sys
from pathlib import Path
from collections import Counter
import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R'];B=R.BASE;F=np.float32
def bits(f):return struct.unpack('<I',struct.pack('<f',float(f)))[0]
class E(H):
 def _block(self,mu,a,size,user):
  if a in [B+0x3e9dda0,B+0x3e9ddb0,B+0x3e9ddd0]:
   self.sdk_voice[self._plt_name(a)]+=1
   self.current_sdk.append(self._plt_name(a))
   mu.reg_write(UC_ARM64_REG_X0,int(self.loop) if a==B+0x3e9ddd0 else 0)
   mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  super()._block(mu,a,size,user)
e=E([B+0x130fffc]);e.executed=set();e.sdklog=Counter();e.stublog=Counter();e.sdk_voice=Counter();e.current_sdk=[];e.loop=0
def no_null(mu,access,a,size,value,user):
 if a<0x400000:raise RuntimeError(f'null read {a:#x} pc={mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
mgr=e.alloc(0x1a0);backend=e.alloc(0x250);h=e.alloc(0x68);voice=e.alloc(0xd8);sdkplayer=e.alloc(0xe8);owner=e.alloc(0x28)
e.w64(B+0x582a710,mgr);e.w64(B+0x59a3790,backend);e.wf(backend+0x74,F(1/60))
e.w64(voice,B+0x5759658);e.w64(voice+0xd0,sdkplayer)
gain=[F(.7),F(.5),F(.3)];counts=Counter();examples=[]
for loop in [0,1]:
 for state in [1,2,3,4,5,6]:
  for follow in [0,1]:
   for ownerkind in ['valid','stale','missing']:
    for muted in [0,1]:
     for category in [0,1,2,3]:
      e.loop=loop;e.current_sdk=[]
      for j,g in enumerate(gain):e.wf(mgr+0x108+8*j,g);e.mu.mem_write(mgr+0x10c+8*j,bytes([muted]))
      e.w32(h+0x10,category);e.mu.mem_write(h+0x14,b'\0');e.wf(h+0x24,.8);e.wf(h+0x28,.6);e.wf(h+0x2c,.9);e.wf(h+0x34,.8);e.wf(h+0x38,.7)
      e.w64(h+0x40,voice);e.w32(h+0x48,7);e.mu.mem_write(h+0x50,bytes([follow]));e.w64(h+0x58,0 if ownerkind=='missing' else owner);e.w32(h+0x60,9);e.w32(owner+0x20,8 if ownerkind=='stale' else 9)
      e.w32(voice+0x10,7);e.w32(voice+0x14,state);e.mu.mem_write(voice+0x20,b'\0');e.wf(voice+0x40,1);e.wf(voice+0x48,.75)
      e.call(B+0x130fffc,[h])
      expired=loop and follow and ownerkind!='valid' and state not in [5,6]
      expectedstate=(6 if state<3 else 5) if expired else state
      assert e.r32(voice+0x14)==expectedstate,(loop,state,follow,ownerkind,muted,category,e.r32(voice+0x14),expectedstate)
      assert e.mu.mem_read(voice+0x20,1)[0]==(15 if loop and muted else 0)
      assert e.r32(voice+0x64)==bits(F(F(F(F(.8)*F(.6))*F(.9))*gain[category if category<3 else 0]))
      assert e.r32(voice+0x6c)==bits(F(F(.8)*F(.7)))
      stopcount=sum('4Stop' in x for x in e.current_sdk)
      assert stopcount==int(loop and muted and state in [3,4,5])+int(expired and state<3)
      assert not any('4Play' in x for x in e.current_sdk)
      counts['actual_voice_vtable_full_handle_update']+=1
      if len(examples)<12 and loop and follow and muted==0 and category==0:examples.append(dict(loop=loop,state=state,owner=ownerkind,outputstate=expectedstate,sdk_calls=e.current_sdk))
# Delay start virtual28 modifies existing voice state only.
for state in range(-2,8):
 for delay in [-2,-1,0,.01,.1,1,10]:
  e.w32(voice+0x14,state);e.wf(voice+0x2c,99);e.mu.reg_write(UC_ARM64_REG_S0,bits(delay));e.call(B+0x3c7b7e4,[voice])
  expect=state if state>2 else (1 if delay>0 else 2)
  assert e.r32(voice+0x14)==(expect&0xffffffff)
  assert e.mu.reg_read(UC_ARM64_REG_W0)==int(state<=2)
  assert e.r32(voice+0x2c)==bits(99 if state>2 else max(delay,0))
  counts['existing_voice_arm']+=1
# Stretch virtual18 writes speed to existing SDKplayer only for positive input.
for present in [0,1]:
 for speed in [-10,-1,0,.01,.1,1,2,10,100,1000]:
  e.w64(voice+0xd0,sdkplayer if present else 0);e.wf(sdkplayer+0xd0,99);e.mu.reg_write(UC_ARM64_REG_S0,bits(speed));e.call(B+0x3c7dce8,[voice])
  assert e.r32(voice+0x70)==bits(speed)
  assert e.r32(sdkplayer+0xd0)==bits(speed if present and speed>0 else 99)
  counts['existing_voice_speed']+=1
out={'counts':dict(counts),'total':sum(counts.values()),'mismatches':0,'null_reads':0,'code_patch':0,
 'actual_vtable':'0x7105759658','SDK_voice_boundaries':dict(e.sdk_voice),'SDK_stubs':dict(e.sdklog),
 'nonSDK_stubs':{hex(k):v for k,v in e.stublog.items()},'executed_blocks':len(e.executed),'examples':examples,
 'correction':'voiceVT+38=IsLoop, not IsPlaying/validity. Category flags and followed-owner cancellation require true loop; gain/pitch writes follow independently.',
 'limits':['Synthetic live manager/handle/voice/SDKplayer graph and loop return input','Native130FFFC whole plus actual voice virtual38/10/78; SDK IsLoop/Play/Stop captured','No native SDK playback, thread or live range scene','Finite listed states and float inputs, not all-bit proof']}
(ROOT/'analysis/camera_100_r10/shake/voice_native.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='examples'},ensure_ascii=False))
