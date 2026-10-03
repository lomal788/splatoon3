"""r9 whole original EPA facet barycentric/edgeweighted signed coords ae9590, exact mixed precision reference. Synthetic finite nondegenerate facets."""
import json,struct,random
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
f=np.float32
bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0]
fh=lambda i:struct.unpack('<f',struct.pack('<I',i))[0]
p4=lambda a:struct.pack('<4f',*map(float,a))
def dotf(v):return f(f(v[0]+v[1])+v[2])
def dotd(a,b):return float(a[2])*float(b[2])+(float(a[0])*float(b[0])+float(a[1])*float(b[1]))
def ref(a,b,c,p):
 edges=[[f(c[k]-b[k]) for k in range(4)],[f(a[k]-c[k]) for k in range(4)],[f(b[k]-a[k]) for k in range(4)]]
 ll=[]
 for i,e in enumerate(edges):
  sq=[f(z*z) for z in e];ll.append(f(sq[2]+f(sq[1]+sq[0])) if i<2 else dotf(sq))
 mn=min(ll);mask=sum((1<<i) if l<=mn else 0 for i,l in enumerate(ll));j=[0,0,1,0,2,0,1,0][mask];i=((0x36>>(j*2))&3)^j;k=((0x2d>>(j*2))&3)^j
 ej=edges[j];ei=edges[i];invd=1./dotd(ei,ei);proj=dotd(ej,ei)*invd;perp=[f(float(ej[x])-proj*float(ei[x])) for x in range(4)];delta=[f(p[x]-[a,b,c][k][x]) for x in range(4)]
 weighti=f(dotf([f(delta[x]*perp[x]) for x in range(3)])*f(f(1)/dotf([f(perp[x]*perp[x]) for x in range(3)])))
 d2=[f(delta[x]-f(ej[x]*weighti)) for x in range(4)];w=[f(0)]*4;w[i]=weighti;w[j]=f(f(invd)*f(-dotf([f(ei[x]*d2[x]) for x in range(3)])));w[k]=f(f(1-w[j])-w[i])
 signed=[]
 for x,l in enumerate(ll+[ll[2]]):
  inv=f(fh((0x5f2fed52-(bits(l)>>1))&0xffffffff));z=f(l*f(fh(0xbf0e425b)));z=f(z*inv);z=f(z*inv);z=f(z+f(fh(0x3fc6fa83)));z=f(z*inv);signed.append(f(w[x]*z))
 return w,signed,mask,j
u=PhysicsUC();D=u.alloc(0x4e40);P=u.alloc(16);W=u.alloc(16);S=u.alloc(16);rng=random.Random(0xAE9590);bad=[];samples=[];masks={};ties=0
for n in range(4097):
 a=[f(rng.uniform(-4,4)) for x in range(4)];b=[f(rng.uniform(-4,4)) for x in range(4)];c=[f(rng.uniform(-4,4)) for x in range(4)];p=[f(rng.uniform(-4,4)) for x in range(4)]
 if n%16==0:a=list(map(f,(0,0,0,0)));b=list(map(f,(1,1,0,0)));c=list(map(f,(0,1,1,0)))
 j=n%5
 for x,v in enumerate((a,b,c)):u.mu.mem_write(D+0x8d0+x*16,p4(v));u.w8(D+0xd60+j*16+x*4+2,x)
 u.mu.mem_write(P,p4(p));e=u.call(0x7100ae9590,D,j,P,W,S);w,s,mask,chosen=ref(a,b,c,p);masks[str(mask)]=masks.get(str(mask),0)+1;ties+=mask not in (1,2,4)
 out=bytes(u.mu.mem_read(W,16))+bytes(u.mu.mem_read(S,16));want=p4(w)+p4(s)
 if e or out!=want:bad.append(dict(n=n,error=e,a=list(map(float,a)),b=list(map(float,b)),c=list(map(float,c)),p=list(map(float,p)),mask=mask,chosen=chosen,actual=out.hex(),reference=want.hex()))
 if n<2:samples.append(dict(n=n,actual=out.hex(),reference=want.hex()))
r=dict(scope=__doc__,cases=4097,fields=4097*8,bad_count=len(bad),bad=bad[:40],masks=masks,ties=ties,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_penetration_barycentric_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scope','bad','samples')});print('first',bad[:1])

