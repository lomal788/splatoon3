"""r9 whole original aefd00->aefdc0 point-convex TOI axis-aligned one-vertex sphere path. Independent finite f32 fraction/normal/miss reference. Does not cover generic simplex or rotating casts."""
import json,struct,random
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();V=u.alloc(16);Q=u.alloc(0x80);O=u.alloc(0x40);rng=random.Random(0xaefdc0);f=np.float32;bad=[];samples=[];errors=[];valids=0;misses=0
for j,vs in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.))):u.mu.mem_write(Q+0x10+16*j,struct.pack('<4f',*vs))
for i in range(2048):
 axis=i%3;sgn=1. if i%2 else -1.;r=f(rng.uniform(.01,3));D=f(f(r)+f(rng.uniform(.01,100)));speed=f(rng.uniform(.1,200));away=i%5==0
 p=[f(0)]*4;dv=[f(0)]*4;p[axis]=f(sgn*D);dv[axis]=f(sgn*speed if away else -sgn*speed)
 u.mu.mem_write(Q,struct.pack('<4f',*dv));u.mu.mem_write(Q+0x40,struct.pack('<4f',*p));u.mu.mem_write(Q+0x50,struct.pack('<2f',.001,.001));u.mu.mem_write(Q+0x58,struct.pack('<2f',0.,0.));u.mu.mem_write(Q+0x60,struct.pack('<2f',r,r));u.mu.mem_write(Q+0x68,bytes(16));u.mu.mem_write(O,bytes(0x40));u.wf(O,1.)
 with np.errstate(all='ignore'):
  t=f(f(D-r)/speed);threshold=f(f(1)-f(f(f(1)/f(np.sqrt(f(speed*speed))))*f(2**-23)))
 valid=bool(not away and t<threshold)
 err=u.call(0x7100aefd00,V,1,V,1,Q,O,count=2000000);got=u.r32(O+0x30);errors.append([i,err]) if err else None
 normal=[f(np.copysign(f(0),f(sgn)))]*4;normal[axis]=f(sgn)
 if valid:
  valids+=1;expect=struct.pack('<2f',t,t)+bytes(24)+struct.pack('<4f',*normal)+struct.pack('<I',1)+bytes(12)
 else:misses+=1;expect=struct.pack('<f',1.)+bytes(60)
 actual=bytes(u.mu.mem_read(O,0x40))
 if err or actual!=expect:bad.append(dict(i=i,axis=axis,away=away,r=float(r),D=float(D),speed=float(speed),t=float(t),valid=valid,actual=actual.hex(),expected=expect.hex(),error=err))
 if i<8:samples.append(dict(i=i,valid=valid,r=float(r),D=float(D),speed=float(speed),fraction=struct.unpack('<2f',actual[:8]),normal=struct.unpack('<4f',actual[32:48]),raw=actual.hex()))
r=dict(scope=__doc__,cases=2048,valid_cases=valids,miss_cases=misses,f32_fields=12*2048,raw_bytes_compared=64*2048,mismatch=bad,errors=errors,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_point_toi_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k not in ('mismatch','samples')},ensure_ascii=False));print('mismatch',len(bad),bad[:3])

