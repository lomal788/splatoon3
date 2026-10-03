"""r9 independent float32 check of native generic cast advance block aef0bc..aef1c0. Synthetic finite block inputs; not a whole GJK claim."""
import json,struct,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();S=u.alloc(0x600);Q=u.alloc(0x80);O=u.alloc(0x40)
f=np.float32
bits=lambda v:struct.unpack('<I',struct.pack('<f',float(v)))[0]
pack=lambda vs:struct.pack('<'+'f'*len(vs),*map(float,vs))
def qr(n,vs):u.mu.reg_write(globals()[f'UC_ARM64_REG_Q{n}'],int.from_bytes(pack(vs),'little'))
def xr(n,v):u.mu.reg_write(globals()[f'UC_ARM64_REG_X{n}'],int(v))
stop={0x7100aef1bc:'within-threshold',0x7100aef19c:'reject',0x7100aef1c0:'iterate',0x7100aefb60:'budget-valid'}
seen=[]
def hook(mu,a,s,d):seen.append(stop[a]);mu.emu_stop()
for p in stop:u.mu.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
rng=random.Random(0xAEC920);bad=[];branches={};fields=0;samples=[]
for i in range(4097):
 sep=f(rng.randint(-32,256)/16);rad=f(rng.randint(0,32)/16);threshold=f(rng.randint(0,16)/64);t=f(rng.randint(0,16)/32);cap=f(rng.randint(16,64)/32)
 normal=[f(rng.randint(-16,16)/16) for _ in range(3)]+[f(0.)];delta=[f(rng.randint(-128,128)/16) for _ in range(3)]+[f(0.)]
 if i<4:sep=f(3);rad=f(.5);threshold=f(.001);t=f(0);cap=f(1);normal=[f(1),f(0),f(0),f(0)];delta=[f((-4,4,0,-8)[i]),f(0),f(0),f(0)]
 pts=[[f(rng.randint(-128,128)/16) for _ in range(3)]+[f(.5+j*2**-24)] for j in range(4)]
 iteration=rng.randrange(256);limit=256 if i%3 else iteration+1;flag=(i>>1)&1;oldA=1+i%3;newA=oldA+((i>>2)&1);oldB=1+(i>>3)%3;newB=oldB+((i>>4)&1)
 u.mu.mem_write(S,bytes(0x600));u.mu.mem_write(Q,bytes(0x80));u.mu.mem_write(O,bytes(0x40));u.wf(O,cap);u.w32(Q+0x68,limit)
 u.mu.mem_write(S+0x110,pack(delta));u.mu.mem_write(S+0x120,pack([threshold]*2));u.mu.mem_write(S+0xe8,pack([t]*2));u.wq(S+0xe0,O);u.w32(S+0xf4,flag);u.mu.mem_write(S+0xb8,struct.pack('<II',0x3727c5ac,0x3727c5ac))
 for j,p in enumerate(pts):u.mu.mem_write(S+0x1d0+j*16,pack(p))
 qr(15,[sep,sep,0.,0.]);qr(18,[rad,rad,0.,0.]);qr(0,normal);xr(9,newB);xr(10,newA);xr(11,oldB);xr(15,oldA);xr(20,iteration);xr(21,Q);xr(29,S+0x400);u.mu.reg_write(UC_ARM64_REG_SP,S);seen.clear();error=None
 gap=f(sep-rad);closing=f(f(f(delta[0]*normal[0])+f(delta[1]*normal[1]))+f(delta[2]*normal[2]));changed=False;dt=None;nt=t
 if not gap>threshold:want='within-threshold'
 elif not closing<f(0.):want='reject'
 else:
  dt=f(-f(gap-threshold)/closing);nt=f(t+dt)
  if not nt<cap:want='reject'
  else:changed=True;want='iterate' if (flag and (newA>oldA or newB>oldB)) or iteration+1<limit else 'budget-valid'
 try:u.mu.emu_start(0x7100aef0bc,0x7100aefb70,count=256)
 except Exception as e:error=str(e)
 actual=seen[0] if seen else 'no-exit';bv=[]
 if actual!=want:bv.append(['branch',actual,want])
 if changed:
  check=[('time0',u.r32(S+0xe8),bits(nt)),('time1',u.r32(S+0xec),bits(nt)),('iteration',u.x(20),iteration+1),('tolerance0',u.r32(S+0x3a8),0x3727c5ac),('tolerance1',u.r32(S+0x3ac),0x3727c5ac)]
  for j,p in enumerate(pts):
   for k in range(4):check.append((f'point{j}.{k}',u.r32(S+0x1d0+j*16+k*4),bits(f(p[k]-f(delta[k]*dt)))))
  for k in range(4):check.append((f'offset.{k}',u.r32(S+0x130+k*4),bits(f(delta[k]*nt))))
  for nm,got,expected in check:
   fields+=1
   if got!=expected:bv.append([nm,got,expected])
 if error:bv.append(['error',error])
 if bv:bad.append(dict(i=i,bad=bv))
 branches[actual]=branches.get(actual,0)+1
 if i<4 or bv and len(samples)<10:samples.append(dict(i=i,sep=float(sep),rad=float(rad),threshold=float(threshold),t=float(t),cap=float(cap),delta=list(map(float,delta)),normal=list(map(float,normal)),gap=float(gap),closing=float(closing),dt=None if dt is None else float(dt),nexttime=float(nt),branch=actual,reference=want,bad=bv))
r=dict(scope=__doc__,cases=4097,f32_and_integer_fields=fields,branches=branches,bad_count=len(bad),bad=bad[:30],samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_toi_advance_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k not in ('scope','bad','samples')},ensure_ascii=False))
