"""r9 whole FillUp parent24f8f58→actual fallback24f9384+actual12d8dcc. Explicit nativequery output supplier; independent classification/requery/rotation/bisection/tie reference. Not geometriccast verification."""
import json,struct,random,collections
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
f=np.float32;bits=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0];fh=lambda i:struct.unpack('<f',struct.pack('<I',i))[0];pack=lambda vv:struct.pack('<'+'f'*len(vv),*map(float,vv))
u=PhysicsUC();D=u.alloc(0x3000);POS=u.alloc(16);OFF=u.alloc(16);OUT=u.alloc(16);LIST=u.alloc(0x100);ENT=u.alloc(0x400);CC=[u.alloc(0x80) for i in range(32)];NODE=[u.alloc(0x50) for i in range(32)];table=bytes(u.mu.mem_read(0x7104aa5b5c,4096));state={};rng=random.Random(0x24f8f58);bad=[];samples=[];counts=collections.Counter();fields=0
source=Path('web/tools/r9_physics_fillup_fallback_emu.py').read_text(encoding='utf-8-sig');exec(source[source.index('def rayref'):source.index('\ndef supply')],globals())
u.wq(D+0x28b8,LIST);u.w32(0x71058bc7a0,0);u.mu.emu_start(0x71024f0c84,0x71024f0c94,count=5);threshold=f(u.rf(0x71058bc7a0))
def supply(mu,pc,size,data):
 q=mu.reg_read(UC_ARM64_REG_X0);j=state['query_count'];state['query_count']+=1;state['rays'].append(bytes(mu.mem_read(q+0x10,24)).hex())
 for i,rr in enumerate(state['rows']):
  tag=rr['tag'] if j==0 else 0;u.wq(CC[i]+0x40,tag);u.wq(CC[i]+0x50,tag)
 mu.reg_write(UC_ARM64_REG_X0,int(state['visibility'][j]));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
u.mu.hook_add(UC_HOOK_CODE,supply,begin=0x7103a5f36c,end=0x7103a5f36c)
for case in range(2048):
 mode=case%4;adj=case%2;n=rng.randrange(0,16);pos=[f(rng.uniform(-8,8)) for k in range(3)];off=[f(rng.uniform(-4,4)) for k in range(3)] if case%5 else [f(0)]*3;dist=f(rng.uniform(.1,20));vis=[rng.randrange(5)!=0 for j in range(12)];rows=[];eligible=[]
 for i in range(n):
  side=rng.randrange(2);height=f(rng.randrange(-8,8)/4);norm=f(rng.choice((-1,0,1,.5,.8)));sep=f(rng.uniform(-2,2));eflag=side|(2 if rng.randrange(7)==0 else 0);cf=(4 if rng.randrange(7)==0 else 0)|(0x100 if rng.randrange(5)!=0 else 0);tag=rng.choice((0,0x10000000,4,0x100000,0x2000000,0x8000000,0x8200000))
  u.wf(CC[i]+4,height);u.wf(CC[i]+0x10,norm);u.wf(CC[i]+0x30,sep);u.w32(CC[i]+0x68,cf);u.wq(ENT+i*16,CC[i]);u.w8(ENT+i*16+8,eflag);u.wq(NODE[i],CC[i]);u.w8(NODE[i]+8,eflag)
  rows.append(dict(side=side,height=float(height),norm=float(norm),sep=float(sep),eflag=eflag,cf=cf,tag=tag))
  if not(cf&4 or eflag&2) and(mode!=3 or cf&0x100):eligible.append(i)
 u.w32(LIST+0xa0,2 if mode>=2 else mode);u.w8(LIST+0xa4,int(mode==3));u.w32(LIST+8,n);u.w32(LIST+0xc,n);u.wq(LIST+0x30,ENT);u.wq(LIST+0x40,ENT)
 if mode==3:
  sentinel=LIST+0x68;u.w32(LIST+0x7c,0x20);u.wq(LIST+0x70,NODE[0]+0x20 if n else sentinel)
  for i in range(n):u.wq(NODE[i]+0x28,NODE[i+1]+0x20 if i+1<n else sentinel)
 u.mu.mem_write(POS,pack(pos));u.mu.mem_write(OFF,pack(off));u.mu.mem_write(OUT,pack([11,12,13]));u.w32(D+0x2868,0xa0);state.update(query_count=0,rays=[],visibility=vis,rows=rows);e=u.call(0x71024f8f58,D,POS,OFF,OUT,adj,fargs=[float(dist)],count=1000000)
 refq=[0];wantrays=[];wantout=list(map(f,(11,12,13)));base=pos.copy();length=dist;branches=[]
 def query(theta=None):
  j=refq[0];refq[0]+=1
  if theta is None:
   st=[f(base[k]+off[k]) for k in range(3)];nz=f(length*f(-0.));ray=st+[f(nz+st[0]),f(st[1]-length),f(nz+st[2])]
  else:ray=rayref(theta,base,off,length)
  wantrays.append(pack(ray).hex());return j,vis[j],ray
 def best_height():
  h=f(-3.4028234663852886e38);result=None
  for i in eligible:
   rr=rows[i];hh=f(rr['height']) if rr['side'] else f(f(rr['height'])+f(f(rr['sep'])*f(rr['norm'])))
   if h<hh:h=hh;result=h
  return result
 def fallback(theta):
  angle=theta;out=[f(0)]*3;lo=f(0);hi=f(abs(theta));initial=True
  for j in range(4):
   ix,yes,ray=query(angle)
   if j==0 and not yes:return False,angle,out
   if yes:
    h=best_height()
    if h is not None:out=[ray[0],h,ray[2]]
    theta=angle
    if j:hi=f(abs(angle))
   elif j:lo=f(abs(angle))
   if j<3:angle=f(f(lo+hi)*f(.5 if angle>=0 else -.5))
  return True,theta,out
 while True:
  ix,yes,ray=query();found=0;special=0;retry=0;highest=f(-3.4028234663852886e38)
  if yes:
   for i in eligible:
    rr=rows[i];ny=f(rr['norm']) if rr['side'] else f(-f(rr['norm']))
    if ny<threshold:continue
    h=f(rr['height']) if rr['side'] else f(f(rr['height'])+f(f(rr['sep'])*f(rr['norm'])))
    if highest>=h:continue
    highest=h;found=1;tag=rr['tag'] if ix==0 else 0;retry=int(bool(tag&0x8200000));special=1 if tag&0x100004 else ((tag>>28)&1)
    if adj:wantout[1]=h
  invalid=special|retry|(found^1)
  if retry and invalid:
   branches.append('retry');newY=f(highest+f(-.35));length=f(length-max(f(base[1]-newY),f(0)));base[1]=newY;continue
  if not invalid:wantret=1;branches.append('normal');break
  if all(x==f(0) for x in off):wantret=0;branches.append('zerooffset');break
  branches.append('fallback');ap=f(fh(0x3fb2b8c2));am=f(-ap);sp,tp,op=fallback(ap);sm,tm,om=fallback(am);wantret=int(sp or sm)
  if sp and sm:wantout=om if f(-tm)<=tp else op
  elif sp:wantout=op
  elif sm:wantout=om
  break
 actual=[u.x(0)&1,bytes(u.mu.mem_read(OUT,12)).hex(),state['query_count'],state['rays'],u.r32(D+0x2868)&0xffff,u.r32(D+0x2884),u.r32(D+0x286c)];expected=[wantret,pack(wantout).hex(),refq[0],wantrays,0xac,8,1];fields+=8+6*refq[0];counts.update(branches)
 if e or actual!=expected:bad.append(dict(case=case,error=e,mode=mode,adj=adj,rows=rows,pos=list(map(float,pos)),off=list(map(float,off)),dist=float(dist),visibility=vis,branches=branches,actual=actual,reference=expected))
 if case<2:samples.append(dict(case=case,actual=actual,reference=expected))
r=dict(scope=__doc__,cases=2048,fields=fields,bad_count=len(bad),bad=bad[:20],branches=dict(counts),samples=samples,query_supplier_stub=True,threshold_bits=hex(u.r32(0x71058bc7a0)),null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_fillup_parent_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scope','bad','samples')});print('first',bad[:1])
