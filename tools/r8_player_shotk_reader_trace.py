"""New reader experiment: PlayerParam+10c under actual original frame slots.
Reuses r6 synthetic World construction; this does not emulate Havok or real weapon state.
Absence of reads in these scenarios does not prove no consumer.
"""
import json
from pathlib import Path
from collections import Counter
from r6_player_world import World
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import UC_ARM64_REG_PC
out={'scope':__doc__,'scenarios':[]}
for state,hold in ((0x56,0),(0x60,32),(0x85,4),(0x87,4)):
 w=World(state=state);u=w.u;B=w.body;P=u.rq(B+0xa658);seen=Counter()
 def rd(mu,access,addr,size,value,ud):
  seen[(mu.reg_read(UC_ARM64_REG_PC),addr-P,size)]+=1
 u.mu.hook_add(UC_HOOK_MEM_READ,rd,begin=P+0x100,end=P+0x118)
 st=w.start();w.set_contact(ground=True);w.set_paint(kind=2,own=0,enemy=1);w.set_ray(True)
 for off,v in ((0xb0,.096),(0xb4,.088),(0xb8,.104),(0xbc,1),(0xc0,.192),(0x100,.08),(0x104,.024),(0x108,.012),(0x10c,.5),(0x110,.003),(0x114,.4),(0x118,0)):u.wf(P+off,v)
 errs=[]
 for i in range(10):
  w.set_pad(hold=hold,trig=hold if i==0 else 0,stick=(0,1));r=w.step(slots=(16,18,19))
  if any(v is not None for v in r.values()):errs.append([i,r])
 row={'state':hex(state),'hold':hold,'start':st,'errors':errs,'reads':[{'pc':hex(k[0]),'offset':hex(k[1]),'size':k[2],'n':n} for k,n in sorted(seen.items())]}
 out['scenarios'].append(row);print(json.dumps(row),flush=True)
Path('analysis/completion/r8/player_shotk_reader_trace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
