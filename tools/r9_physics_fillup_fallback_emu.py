"""r9 whole FillUp angular fallback24f9384 with original12d8dcc array/linked iterator. Native query results are explicit synthetic supplier, not geometric hit emulation. Independent f32 lookup rotation/bisection/contactheight."""
import json,struct,random,collections
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
f=np.float32;bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0];fh=lambda i:struct.unpack('<f',struct.pack('<I',i))[0];pack=lambda vv:struct.pack('<'+'f'*len(vv),*map(float,vv))
u=PhysicsUC();D=u.alloc(0x3000);CTX=u.alloc(0x20);POS=u.alloc(16);OFF=u.alloc(16);DIST=u.alloc(4);ANGLE=u.alloc(4);OUT=u.alloc(16);LIST=u.alloc(0x100);ENT=u.alloc(0x400);CC=[u.alloc(0x80) for i in range(32)];NODE=[u.alloc(0x50) for i in range(32)];ITER=u.alloc(0x50);table=bytes(u.mu.mem_read(0x7104aa5b5c,4096));state={};rng=random.Random(0x24f9384);bad=[];samples=[];counts=collections.Counter();fields=0
for i,p in enumerate((D,POS,OFF,DIST)):u.wq(CTX+i*8,p)
u.wq(D+0x28b8,LIST)
def rayref(theta,pos,off,dist):
 v=int(f(theta*f(fh(0x4e22f983))));idx=(v>>24)&255;frac=f(f(v&0xffffff)*f(2**-24));sv,ds,cv,dc=struct.unpack_from('<4f',table,idx*16);s=f(f(sv)+f(frac*f(ds)));c=f(f(cv)+f(frac*f(dc)));x,y,z=off;zero=f(0);x0=f(x*zero);z0=f(z*zero);ys=f(f(x0+y)+z0);term=f(x0-z0);yz=f(ys*zero);yo=f(f(s*term)+f(ys+f(c*f(y-ys))));xo=f(f(s*f(z-f(y*zero)))+f(yz+f(c*f(x-yz))));zo=f(f(s*f(f(y*zero)-x))+f(yz+f(c*f(z-yz))));start=[f(pos[0]+xo),f(pos[1]+yo),f(pos[2]+zo)];negzero=f(dist*f(-0.));end=[f(negzero+start[0]),f(start[1]-dist),f(negzero+start[2])];return start+end

def supply(mu,pc,size,data):
 q=mu.reg_read(UC_ARM64_REG_X0);j=state['query_count'];state['query_count']+=1;state['rays'].append(bytes(mu.mem_read(q+0x10,24)).hex());visible=state['visibility'][j]
 mu.reg_write(UC_ARM64_REG_X0,int(visible));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
u.mu.hook_add(UC_HOOK_CODE,supply,begin=0x7103a5f36c,end=0x7103a5f36c)
for case in range(4096):
 mode=case%4;n=rng.randrange(0,20);pos=[f(rng.uniform(-8,8)) for k in range(3)];off=[f(rng.uniform(-4,4)) for k in range(3)];dist=f(rng.uniform(.1,20));theta=f(rng.choice((1,-1))*float(f(fh(0x3fb2b8c2))))
 vis=[bool(case&(1<<j)) for j in range(4)] if case<16 else [rng.randrange(5)!=0 for j in range(4)];rows=[];elig=[]
 for i in range(n):
  side=rng.randrange(2);height=f(rng.randrange(-8,8)/4);norm=f(rng.choice((-1,0,1,.5)));sep=f(rng.uniform(-2,2));eflag=side|(2 if rng.randrange(7)==0 else 0);cf=(4 if rng.randrange(7)==0 else 0)|(0x100 if rng.randrange(5)!=0 else 0)
  u.wf(CC[i]+4,height);u.wf(CC[i]+0x10,norm);u.wf(CC[i]+0x30,sep);u.w32(CC[i]+0x68,cf);u.wq(ENT+i*16,CC[i]);u.w8(ENT+i*16+8,eflag);u.wq(NODE[i],CC[i]);u.w8(NODE[i]+8,eflag)
  rows.append(dict(side=side,height=float(height),norm=float(norm),sep=float(sep),eflag=eflag,cf=cf));
  if not(cf&4 or eflag&2) and(mode!=3 or cf&0x100):elig.append(i)
 u.w32(LIST+0xa0,2 if mode>=2 else mode);u.w8(LIST+0xa4,int(mode==3));u.w32(LIST+8,n);u.w32(LIST+0xc,n);u.wq(LIST+0x30,ENT);u.wq(LIST+0x40,ENT)
 if mode==3:
  # node embedding displacement0x20, original relative-next chain; sentinel list+68.
  sentinel=LIST+0x68;u.w32(LIST+0x7c,0x20);u.wq(LIST+0x70,NODE[0]+0x20 if n else sentinel)
  for i in range(n):u.wq(NODE[i]+0x28,NODE[i+1]+0x20 if i+1<n else sentinel)
 u.mu.mem_write(POS,pack(pos));u.mu.mem_write(OFF,pack(off));u.wf(DIST,dist);u.w32(ANGLE,0x42f60000);u.mu.mem_write(OUT,pack([11,12,13]));u.w32(D+0x2868,0xa0);state.update(query_count=0,rays=[],visibility=vis);e=u.call(0x71024f9384,CTX,ANGLE,OUT,fargs=[float(theta)],count=1000000)
 wantangle=f(123);wantout=list(map(f,(11,12,13)));wantrays=[];qtheta=theta;lo=f(0);hi=f(abs(theta));queries=1 if not vis[0] else 4
 def out_at(angle):
  ray=rayref(angle,pos,off,dist);highest=f(-3.4028234663852886e38);result=None
  for i in elig:
   rr=rows[i];hh=f(rr['height']) if rr['side'] else f(f(rr['height'])+f(f(rr['sep'])*f(rr['norm'])))
   if highest<hh:highest=hh;result=[ray[0],hh,ray[2]]
  return ray,result
 for j in range(queries):
  ray,out=out_at(qtheta);wantrays.append(pack(ray).hex())
  if vis[j]:
   wantangle=qtheta
   if out is not None:wantout=out
   if j:hi=f(abs(qtheta))
  elif j:lo=f(abs(qtheta))
  if j<queries-1:qtheta=f(f(lo+hi)*f(.5 if theta>=0 else -.5))
 actual=[u.x(0)&1,u.r32(ANGLE),bytes(u.mu.mem_read(OUT,12)).hex(),state['query_count'],state['rays'],u.r32(D+0x2868)&0xffff];expected=[int(vis[0]),bits(wantangle),pack(wantout).hex(),queries,wantrays,0xac];fields+=7+6*queries
 if e or actual!=expected:bad.append(dict(case=case,error=e,mode=mode,visibility=vis,rows=rows,pos=list(map(float,pos)),off=list(map(float,off)),dist=float(dist),theta=float(theta),actual=actual,reference=expected))
 counts[str(mode)]+=1
 if case<2:samples.append(dict(case=case,actual=actual,expected=expected))
r=dict(scope=__doc__,cases=4096,fields=fields,bad_count=len(bad),bad=bad[:30],modes=dict(counts),samples=samples,query_supplier_stub=True,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_fillup_fallback_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scope','bad','samples')});print('first',bad[:1])
