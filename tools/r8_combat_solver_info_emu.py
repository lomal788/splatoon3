"""Original solver-info tau/damping->substep bias coefficients. Analysis only, isolated fixture; no contact/solver completion claim."""
import json,struct,random
from pathlib import Path
import numpy as np
from r6_player_uc import PUC
u=PUC();p=u.alloc(0x100);g=u.alloc(0x20);f=np.float32
for i in range(4):u.wf(g+4*i,0.)
rng=random.Random(0x8a452fc);bad=[];samples=[];cases=0
for i in range(1024):
 tau=f(.6 if i==0 else rng.uniform(.1,.9));damp=f(1. if i==0 else rng.uniform(.5,1.5));dt=f(1/60 if i==0 else rng.uniform(1/240,1/15));sub=8 if i==0 else rng.randrange(1,17);micro=1 if i==0 else rng.randrange(1,5)
 u.mu.mem_write(p,bytes(0x100));u.wf(p+0x20,dt);u.wf(p+0x24,dt);u.wf(p+0x84,float.fromhex('0x1.ffffe0p+63'))
 e1=u.call(0x7100a452fc,p,fargs=(float(tau),float(damp)))
 e2=u.call(0x7100a4536c,p,g,sub,micro,fargs=(float(dt),float(dt)))
 ratio=f(tau/damp);half=f(f(tau*f(.5))/damp);inv=f(f(1)/dt);invsub=f(inv*f(sub));subdt=f(f(f(1)/f(sub))*dt)
 want={0x10:dt,0x14:dt,0x18:inv,0x1c:inv,0x38:subdt,0x3c:subdt,0x40:invsub,0x44:invsub,0xd0:f(ratio*invsub),0xd4:f(ratio*invsub),0xd8:f(f(-half)*invsub),0xdc:f(f(-half)*invsub),0xe0:f(damp/tau),0xe4:ratio,0xe8:f(damp/f(tau*f(.5))),0xec:half}
 for off,val in want.items():
  got=bytes(u.mu.mem_read(p+off,4));expected=struct.pack('<f',val)
  if got!=expected:bad.append(dict(i=i,offset=hex(off),got=got.hex(),expected=expected.hex()))
 if e1 or e2:bad.append(dict(i=i,errors=[e1,e2]))
 if i<4:samples.append(dict(i=i,tau=float(tau),damp=float(damp),dt=float(dt),sub=sub,micro=micro,d0=u.rf(p+0xd0),d8=u.rf(p+0xd8)))
 cases+=1
out=dict(cases=cases,f32_fields=cases*16,mismatch=bad,samples=samples,null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/solver_info_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({**out,'mismatch':bad[:4]},ensure_ascii=False));assert not bad
