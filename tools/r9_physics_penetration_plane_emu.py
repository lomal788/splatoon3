"""r9 original whole EPA double facet preparation ae926c vs independent mixed f32/f64 formula. Nondegenerate synthetic facet inputs, four origin/bias lanes."""
import json,struct,random,math
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
f=np.float32
p4=lambda a:struct.pack('<4f',*map(float,a))
def ref(a,b,c,origin,bias,error):
 ab=[f(b[k]-a[k]) for k in range(3)];ac=[f(c[k]-a[k]) for k in range(3)]
 nx=float(ab[1])*float(ac[2])-float(ab[2])*float(ac[1]);ny=float(ab[2])*float(ac[0])-float(ab[0])*float(ac[2]);nz=float(ab[0])*float(ac[1])-float(ab[1])*float(ac[0]);exact=[nx,ny,nz,0.]
 rounded=list(map(f,exact));high=[float(f(f(bias[k]+rounded[k])-bias[k])) for k in range(4)];low=[exact[k]-high[k] for k in range(4)]
 norm2=f(f(f(rounded[0]*rounded[0])+f(rounded[1]*rounded[1]))+f(rounded[2]*rounded[2]));inv=f(f(1)/f(np.sqrt(norm2)))
 d=[float(f(origin[k]-a[k])) for k in range(3)];hd=(high[2]*d[2])+(high[0]*d[0]+high[1]*d[1]);ld=(low[2]*d[2])+(low[0]*d[0]+low[1]*d[1]);dot=hd+ld
 uncertainty=f(f(f(error*inv)*error)*error);margin=error if error>uncertainty else uncertainty;distance=f(margin+f(f(dot)*inv));normal=[f(high[k]+low[k]) for k in range(4)]
 return high,low,inv,margin,distance,normal
u=PhysicsUC();D=u.alloc(0x4e40);rng=random.Random(0xAE926C);bad=[];samples=[]
for i in range(4097):
 a=[f(rng.uniform(-4,4)) for k in range(4)];b=[f(rng.uniform(-4,4)) for k in range(4)];c=[f(rng.uniform(-4,4)) for k in range(4)];o=[f(rng.uniform(-4,4)) for k in range(4)];bias=[f(2**rng.randrange(-3,20)) for k in range(4)];err=f(2**rng.randrange(-20,-2));j=i%5
 for k,v in enumerate((a,b,c)):u.mu.mem_write(D+0x8d0+k*16,p4(v))
 for k,v in enumerate((0,1,2)):u.w8(D+0xd60+j*16+k*4+2,v)
 u.mu.mem_write(D+0x90,p4(o));u.mu.mem_write(D+0xa0,p4(bias));u.wf(D+0xb0,err);e=u.call(0x7100ae926c,D,j)
 hi,lo,inv,margin,distance,n=ref(a,b,c,o,bias,err)
 actual=bytes(u.mu.mem_read(D+0x2be0+j*32,32))+bytes(u.mu.mem_read(D+0x3be0+j*32,32))+bytes(u.mu.mem_read(D+0x2560+j*4,4))+bytes(u.mu.mem_read(D+0x2960+j*4,4))+bytes(u.mu.mem_read(D+0x2760+j*4,4))+bytes(u.mu.mem_read(D+0x1d60+j*16,16))+bytes(u.mu.mem_read(D+0x2b60+j,1))
 want=struct.pack('<8d3f4fB',*(hi+lo),float(inv),float(margin),float(distance),*map(float,n),1)
 if e or actual!=want:bad.append(dict(i=i,error=e,a=list(map(float,a)),b=list(map(float,b)),c=list(map(float,c)),origin=list(map(float,o)),bias=list(map(float,bias)),err=float(err),actual=actual.hex(),reference=want.hex()))
 if i<2:samples.append(dict(i=i,actual=actual.hex(),reference=want.hex()))
r=dict(scope=__doc__,cases=4097,fields=4097*16,bad_count=len(bad),bad=bad[:40],samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_penetration_plane_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scope','bad','samples')});print('first',bad[:1])
