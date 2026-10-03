"""r9 native generic aligned equal-shape TOI vs independent axis plane fraction, limited geometry path."""
import json,struct,itertools,random
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();Q=u.alloc(0x80);O=u.alloc(0x40);VA=u.alloc(0x100);f=np.float32;rng=random.Random(0xaec920);cases=[];bad=[];errors=[]
shapes=[[(0.,0.,0.)],[(-1.,-1.,-1.),(1.,1.,1.)],[(-1.,-1.,-1.),(1.,1.,1.),(-1.,1.,-1.)],[(-1.,-1.,-1.),(1.,1.,1.),(-1.,1.,-1.),(1.,-1.,1.)],list(itertools.product((-1.,1.),repeat=3))]
for i in range(100):
 av=shapes[i%5];axis=(i//5)%3;sgn=f(1 if i%2 else -1);extent=f(0 if len(av)==1 else 1);D=f(rng.uniform(3.,20.));speed=f(rng.uniform(.25,50.));radius=f(.5);p=[f(0)]*4;dv=[f(0)]*4;p[axis]=f(sgn*D);dv[axis]=f(-sgn*speed)
 u.mu.mem_write(VA,bytes(0x100));u.mu.mem_write(VA,struct.pack('<'+'f'*3*len(av),*sum((list(v) for v in av),[])));u.mu.mem_write(Q,struct.pack('<4f',*dv))
 for j,v in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),p)):u.mu.mem_write(Q+0x10+16*j,struct.pack('<4f',*v))
 u.mu.mem_write(Q+0x50,struct.pack('<2f',.001,.001));u.mu.mem_write(Q+0x58,bytes(8));u.mu.mem_write(Q+0x60,struct.pack('<2f',radius,radius));u.w32(Q+0x68,256);u.w32(Q+0x6c,0);u.mu.mem_write(O,bytes(64));u.wf(O,1.)
 e=u.call(0x7100aec920,VA,len(av),VA,len(av),Q,O,0,0,count=2000000);raw=bytes(u.mu.mem_read(O,64));frac=struct.unpack('<f',raw[:4])[0];expect=f(f(f(D-f(extent+extent))-radius)/speed);expectedvalid=bool(expect<1)
 errors.append([i,e]) if e else None
 if u.r32(O+0x30)!=int(expectedvalid) or (expectedvalid and raw[:4]!=struct.pack('<f',expect)):bad.append(dict(i=i,n=len(av),axis=axis,sgn=float(sgn),D=float(D),speed=float(speed),expected=float(expect),actual=frac,raw=raw.hex(),error=e))
 cases.append(dict(i=i,n=len(av),axis=axis,sgn=float(sgn),D=float(D),speed=float(speed),expected=float(expect),raw=raw.hex()))
r=dict(scope=__doc__,cases=100,mismatch=bad,errors=errors,samples=cases,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_toi_aligned_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('mismatch',len(bad),bad[:4]);print('runtime',errors,u.null_calls,u.auto_pages,u.faults,u.plt_stubbed)
