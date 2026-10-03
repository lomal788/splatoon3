"""New Havok query dispatcher initializer, no geometry contact/TOI kernel execution."""
import json
from pathlib import Path
from r6_player_uc import PUC
u=PUC();Q=u.alloc(0x3e40);err=u.call(0x7100947508,Q,0);assert err is None,err
T=(0,1,2,4,8);ex=[[0x949570]*4+[0x936ee8],[0x949570,0x948f30,0x948f30,0x94ae10,0x936ee8],[0x949570,0x948f30,0x948f30,0x948f30,0x936ee8],[0x949570]*4+[0x936ee8],[0x945350]*4+[0x936ee8]]
rows=[];bad=[]
for i,a in enumerate(T):
 for j,b in enumerate(T):
  got=u.rq(Q+0x1eb0+a*0xf8+b*8);want=0x7100000000+ex[i][j];rows.append({'A':a,'B':b,'fn':hex(got)})
  if got!=want:bad.append([a,b,hex(got),hex(want)])
o={'scope':__doc__,'cases':25,'matrix':rows,'mismatch':bad,'null':u.null_calls,'auto':u.auto_pages,'plt':u.plt_stubbed}
Path('analysis/completion/r8/physics_query_dispatch_emu.json').write_text(json.dumps(o,indent=2),encoding='utf-8');print(json.dumps(o))
