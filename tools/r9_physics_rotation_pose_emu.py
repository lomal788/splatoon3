"""r9 whole original quaternion interpolation08a8764 and matrix08a5ed0, plus original asin/sin SIMD polynomials. Independent f32 order; finite/unit quaternion duplicated time fixture only."""
import json,struct,random,math
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
from unicorn.arm64_const import UC_ARM64_REG_Q0
f=np.float32
fh=lambda h:struct.unpack('<f',struct.pack('<I',h))[0]
bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0]
pack=lambda vv:struct.pack('<'+'f'*len(vv),*map(float,vv))
def xor(x,mask):return f(fh(bits(x)^mask))
def asin_ref(v):
 a=f(min(abs(float(v)),1.));z=f(a*a);reduced=a>f(.5)
 if reduced:z=f(f(1-a)*f(.5));base=f(np.sqrt(z))
 else:base=a
 p=f(f(z*f(fh(0x3d2cb352)))+f(fh(0x3cc617e3)))
 for c in (0x3d3a3ec7,0x3d9980f6,0x3e2aaae4):p=f(f(z*p)+f(fh(c)))
 p=f(z*p);r=f(base+f(base*p))
 if reduced:r=f(f(fh(0x3fc90fdb))-f(r+r))
 if a<f(fh(0x38d1b717)):r=a
 return xor(r,0x80000000 if v<f(0) else 0)
def sin_ref(v):
 a=f(abs(float(v)));j=(int(f(a*f(fh(0x3fa2f983))))+1)&~1;y=f(j);r=a
 for c in (0xbf490000,0xb97da000,0xb3222169):r=f(r+f(y*f(fh(c))))
 z=f(r*r);c=f(f(z*f(fh(0x37ccf5ce)))+f(fh(0xbab6061a)));c=f(f(z*c)+f(fh(0x3d2aaaa5)));c=f(z*c);c=f(z*c);c=f(c-f(f(.5)*z));c=f(f(1)+c)
 p=f(f(z*f(fh(0xb94ca1f9)))+f(fh(0x3c08839e)));p=f(f(z*p)+f(fh(0xbe2aaaa3)));p=f(z*p);s=f(r+f(r*p));val=s if not j&2 else c;val=f(min(float(val),1.));return xor(val,(bits(v)&0x80000000)^((j&4)<<29))
def dot4(v):return f(f(v[0]+v[1])+f(v[2]+v[3]))
def quat_ref(a,b,t):
 d=dot4([f(a[k]*b[k]) for k in range(4)]);sg=0x80000000 if d<f(0) else 0;ad=xor(d,sg)
 if ad>=f(fh(0x3f7fbe77)):wa=f(1-t);wb=t
 else:
  theta=f(f(fh(0x3fc90fdb))-asin_ref(ad));angleA=f(theta-f(t*theta));angleB=f(t*theta)
  # original FRINTM range reduction; finite t0..1 angles already0..pi/2, floor is0.
  inv=f(f(1)/f(np.sqrt(f(f(1)-f(ad*ad)))))
  wa=f(inv*sin_ref(angleA));wb=f(inv*sin_ref(angleB))
 wb=xor(wb,sg);q=[f(f(a[k]*wa)+f(b[k]*wb)) for k in range(4)];d2=dot4([f(x*x) for x in q])
 return [f(0)]*4 if d2==f(0) else [f(x/f(np.sqrt(d2))) for x in q]
def matrix_ref(q):
 x,y,z,w=q;dx=f(x+x);dy=f(y+y);dz=f(z+z);xx=f(dx*x);yy=f(dy*y);zz=f(dz*z);xy=f(dy*x);xz=f(dz*x);yz=f(dz*y);wx=f(dx*w);wy=f(dy*w);wz=f(dz*w);h=f(1-zz)
 return [f(h-yy),f(xy+wz),f(xz-wy),f(yz-wx),f(xy-wz),f(h-xx),f(yz+wx),f(xz+wy),f(xz+wy),f(yz-wx),f(f(1-xx)-yy),f(0)]
u=PhysicsUC();A=u.alloc(16);B=u.alloc(16);T=u.alloc(16);O=u.alloc(48);rng=random.Random(0x8A8764);bad=[];fields={};samples=[];modes={'linear':0,'trig':0}
for i in range(4097):
 values=[f(rng.uniform(-100,100)) for k in range(4)]
 if i<3:values=[f(-0.),f(0),f(-1),f(1)]
 for name,fn,ref,vals in [('asin',0x71008a69e0,asin_ref,[f(x/100) for x in values]),('sin',0x71008a6770,sin_ref,values)]:
  u.mu.mem_write(A,pack(vals));e=u.call(fn,A);out=u.mu.reg_read(UC_ARM64_REG_Q0).to_bytes(16,'little');want=pack([ref(v) for v in vals]);fields[name]=fields.get(name,0)+4
  if e or out!=want:bad.append(dict(i=i,scope=name,error=e,input=list(map(float,vals)),actual=out.hex(),reference=want.hex()))
 av=[f(rng.uniform(-1,1)) for k in range(4)];bv=[f(rng.uniform(-1,1)) for k in range(4)]
 av=[f(v/f(np.sqrt(dot4([f(z*z) for z in av])))) for v in av];bv=[f(v/f(np.sqrt(dot4([f(z*z) for z in bv])))) for v in bv]
 if i%4==0:bv=[f(v*(-1 if i%8 else 1)) for v in av]
 t=f(rng.randrange(1025)/1024);modes['linear' if abs(float(dot4([f(av[k]*bv[k]) for k in range(4)])))>=f(fh(0x3f7fbe77)) else 'trig']+=1
 u.mu.mem_write(A,pack(av));u.mu.mem_write(B,pack(bv));u.mu.mem_write(T,pack([t,t,0,0]));e=u.call(0x71008a8764,O,A,B,T);out=bytes(u.mu.mem_read(O,16));want=pack(quat_ref(av,bv,t));fields['quat']=fields.get('quat',0)+4
 if e or out!=want:bad.append(dict(i=i,scope='quat',error=e,a=list(map(float,av)),b=list(map(float,bv)),t=float(t),actual=out.hex(),reference=want.hex()))
 u.mu.mem_write(A,want);e=u.call(0x71008a5ed0,O,A);outm=bytes(u.mu.mem_read(O,48));wm=pack(matrix_ref(quat_ref(av,bv,t)));fields['matrix']=fields.get('matrix',0)+12
 if e or outm!=wm:bad.append(dict(i=i,scope='matrix',error=e,actual=outm.hex(),reference=wm.hex()))
 if i<2:samples.append(dict(i=i,t=float(t),a=list(map(float,av)),b=list(map(float,bv)),out=out.hex(),ref=want.hex(),matrix=outm.hex()))
r=dict(scope=__doc__,cases=4097,fields=fields,modes=modes,bad_count=len(bad),bad=bad[:60],samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_rotation_pose_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k not in ('scope','bad','samples')},ensure_ascii=False));print('badfirst',bad[:2])
