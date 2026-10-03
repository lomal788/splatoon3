"""Original option integer→two gauge normalized values→Volume frame.
UI navigation disabled; layout Volume is parsed separately from original data.
"""
import json,struct,itertools,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STUB
from ui_sarc import read_files
from ui_lyt import parse_bflyt,parse_bflan
B=0x7100000000;u=UC();mu=u.mu;H=u.alloc(0x58);O=u.alloc(0x80);W=[u.alloc(0x220) for _ in range(5)];A=[u.alloc(0x30) for _ in range(2)];P=[u.alloc(0x60) for _ in range(2)]
def ptr(a,v):mu.mem_write(a,struct.pack('<Q',v))
for k,w in enumerate(W):ptr(H+0x28+k*8,w)
for k in range(2):ptr(W[k]+0x160,A[k]);ptr(W[k]+0x180,P[k]);ptr(A[k]+8,O)
def hook(mu,pc,n,_):
 if pc==B+0x341f050:mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif pc==B+0x0851c78:mu.reg_write(UC_ARM64_REG_X0,100);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
mu.hook_add(UC_HOOK_CODE,hook);cases=0
for stick,gyro in itertools.product(range(-2,23),repeat=2):
 mu.mem_write(O+0x70,struct.pack('<iiBBB',stick,gyro,1,0,1));u.call(B+0x341ef14,H,O)
 got=[u.ru32(W[k]+0x1f0) for k in range(2)]+[u.ru32(A[k]+0x14) for k in range(2)]
 vals=[np.float32(min(max(np.float32(np.float32(np.float32(v-10)/np.float32(10))+np.float32(1))*np.float32(.5),np.float32(0)),np.float32(1))) for v in [gyro,stick]]
 ref=[struct.unpack('<I',struct.pack('<f',v))[0] for v in vals]+[struct.unpack('<I',struct.pack('<f',np.float32(v*np.float32(100))))[0] for v in vals]
 if got!=ref:raise AssertionError((stick,gyro,got,ref))
 cases+=1
fs=read_files('extracted/romfs/Layout/GuageScrollOption_00.Nin_NX_NVN.blarc.zs');lyt=parse_bflyt(fs['blyt/GuageScrollOption_00.bflyt']);anim=parse_bflan(fs['anim/GuageScrollOption_00_Volume.bflan']);labels=[]
def walk(x):
 if isinstance(x,dict):
  if x.get('type')=='txt1' and x.get('name','').startswith('T_Num'):labels.append({k:x[k] for k in ['name','text','translate']})
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(lyt)
data={'layout':'GuageScrollOption_00','labels':labels,'controls':lyt['controls'],'layout_check':lyt['_check'],'volume_frameSize':anim['frameSize'],'volume_entries':[e for e in anim['entries'] if e['name'].startswith(('T_Num','P_Arrow'))]}
Path('analysis/completion/r8/sensitivity_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out={'pass':cases,'mismatch':0,'boundaries':['original341ef14→314b05c wholefunctions; isolated GUI flags/positions','0851c78 animationframecount returns100 matching originalVolume data; GUI navigation341f050stubbed','input options are synthetic integers; controller buttons/profile save writer not executed'],'data':'sensitivity_data.json'}
Path('analysis/completion/r8/sensitivity_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
