"""r8 enum parser executes original metadata functions. Only SDK string/guard/lock routines stubbed.
The output is original name-array index metadata, corroborated with branches in combat functions.
"""
import json,struct,sys
from pathlib import Path
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
import respawn_emu as R
class Meta(R.Emu):
 def _block(self,mu,addr,size,user):
  if self._allowed(addr):return
  if R.PLT_LO<=addr<R.PLT_HI:
   name=self._plt_name(addr);x=[mu.reg_read(r) for r in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2]];ret=0
   if name=='__cxa_guard_acquire':ret=1
   elif name=='__cxa_guard_release':mu.mem_write(x[0],b'\1')
   elif name in ('memcpy','memmove'):mu.mem_write(x[0],bytes(mu.mem_read(x[1],x[2])));ret=x[0]
   elif name=='strncpy':
    out=bytearray();end=False
    for i in range(x[2]):
     c=0 if end else mu.mem_read(x[1]+i,1)[0];out.append(c);end=end or c==0
    mu.mem_write(x[0],bytes(out));ret=x[0]
   elif name=='memset':mu.mem_write(x[0],bytes([x[1]&255])*x[2]);ret=x[0]
   self.calls.append((addr,name,x));mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  super()._block(mu,addr,size,user)
 def cstr(self,p):
  b=bytearray()
  for i in range(500):
   x=self.mu.mem_read(p+i,1)[0]
   if not x:return b.decode()
   b.append(x)
  raise ValueError('unterminated')
e=Meta([0x71027b8258,0x710349a028]);out={}
for label,fn,n in [('DamageResultType',0x71027b8258,8),('DamageReasonOtherId',0x710349a028,11)]:
 e.call(fn,[]);p=e.mu.reg_read(UC_ARM64_REG_X0);vals=[]
 for i in range(n):vals.append(e.cstr(struct.unpack('<Q',e.mu.mem_read(p+8*i,8))[0]))
 out[label]={'function':hex(fn),'entries':[{'value':i,'name':v} for i,v in enumerate(vals)],'stub_calls':[{'address':hex(a),'name':b} for a,b,x in e.calls]}
assert [v['name'] for v in out['DamageResultType']['entries']]==['Through','Constant','Aggregated','NetPriorityFailure','Invincible','Armored','Damaged','Cure']
assert out['DamageReasonOtherId']['entries'][1]['name']=='Blood'
p=Path(__file__).resolve().parents[2]/'analysis/completion/r8/combat_enum_emu.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
