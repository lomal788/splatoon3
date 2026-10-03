"""Original 094e6e4 advance/refinement blocks + real game handlers. Partial math proof; generic support/quat/full TOI not claimed."""
import json,math,struct,random,warnings
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
warnings.filterwarnings('ignore',category=RuntimeWarning)
f=np.float32

def bits(v):return struct.unpack('<I',struct.pack('<f',float(v)))[0]
def pack2(v):return int.from_bytes(struct.pack('<2f',*v),'little')
def get2(mu,r):return list(struct.unpack('<2f',int(mu.reg_read(r)).to_bytes(16,'little')[:8]))
def amin(a,b,numeric=False):
 a,b=f(a),f(b)
 if np.isnan(a) or np.isnan(b):
  if numeric and not(np.isnan(a) and np.isnan(b)):return b if np.isnan(a) else a
  return f(float('nan'))
 if a==b==0:return f(-0.) if bits(a)&0x80000000 or bits(b)&0x80000000 else f(0.)
 return a if a<b else b

def amax(a,b):
 a,b=f(a),f(b)
 if np.isnan(a) or np.isnan(b):return f(float('nan'))
 if a==b==0:return f(-0.) if bits(a)&bits(b)&0x80000000 else f(0.)
 return a if a>b else b

def advance(t,remain,gap,offset,bound,mint,cap):
 return [amin(f(f(t[i])+amax(f(f(f(remain[i])*f(f(gap[i])-f(offset[i])))/f(bound[i])),mint[i])),cap[i]) for i in range(2)]

def refine(ut,lt,ug,lg,target,mint):
 return [amax(f(f(f(f(ut[i])-f(lt[i]))*amax(amin(f(f(f(target[i])-f(lg[i]))/f(f(ug[i])-f(lg[i]))),f(.9),True),f(.1)))+f(lt[i])),mint[i]) for i in range(2)]

F=make_engine_toi_fixture();u=F['u'];mu=u.mu
GB,GBB,Args,Ang,Stage,CL,Points,Entries=(F[k] for k in ('GB','GBB','Args','Ang','Stage','CL','Points','Entries'))
u.wq(GBB,0x7105756338);u.wq(GB+0x88,4)
traces=[];pending={};core=[];whole=[];bad=[];fields=0

def chk(label,actual,expected):
 global fields
 for i,(a,b) in enumerate(zip(actual,expected)):
  fields+=1
  if bits(a)!=bits(b):bad.append(dict(label=label,lane=i,actual=hex(bits(a)),expected=hex(bits(b))))

def capture(mu,p,size,data):
 sp=mu.reg_read(UC_ARM64_REG_SP)
 if p==0x710094e6e4:
  Q=mu.reg_read(UC_ARM64_REG_X1);core.append(dict(Q=bytes(mu.mem_read(Q,0x132)).hex()))
 elif p==0x710094ea28:
  t=get2(mu,UC_ARM64_REG_Q0);remain=get2(mu,UC_ARM64_REG_Q1);gap=get2(mu,UC_ARM64_REG_Q2);offset=get2(mu,UC_ARM64_REG_Q9);bound=get2(mu,UC_ARM64_REG_Q12);cap=get2(mu,UC_ARM64_REG_Q7);mint=list(struct.unpack('<2f',mu.mem_read(sp+0x150,8)))
  pending['advance']=dict(t=t,remain=remain,gap=gap,offset=offset,bound=bound,mint=mint,cap=cap)
 elif p==0x710094ea6c:
  d=pending.pop('advance');out=get2(mu,UC_ARM64_REG_Q1);chk('whole advance',out,advance(**d));traces.append(dict(kind='advance',inputs=d,out=out))
 elif p==0x710094f170:
  d={k:list(struct.unpack('<2f',int(mu.reg_read(r)).to_bytes(8,'little'))) for k,r in (('ut',UC_ARM64_REG_X28),('lt',UC_ARM64_REG_X27),('ug',UC_ARM64_REG_X24),('lg',UC_ARM64_REG_X23))};d['target']=get2(mu,UC_ARM64_REG_Q8);d['mint']=list(struct.unpack('<2f',mu.mem_read(sp+0x150,8)));pending['refine']=d
 elif p==0x710094f1e4:
  d=pending.pop('refine');out=list(struct.unpack('<2f',int(mu.reg_read(UC_ARM64_REG_X20)).to_bytes(8,'little')));chk('whole refine',out,refine(**d));traces.append(dict(kind='refine',inputs=d,out=out))
for p in (0x710094e6e4,0x710094ea28,0x710094ea6c,0x710094f170,0x710094f1e4):mu.hook_add(UC_HOOK_CODE,capture,begin=p,end=p)
rng=random.Random(0x094e6e4)
for case in range(192):
 theta=f(rng.uniform(.01,2.9)) if case>=6 else f([.1,1.,math.pi/2,-.1,-1.,2.][case]);c=math.cos(float(theta));s=math.sin(float(theta));mu.mem_write(GB+0xd8,struct.pack('<12f',c,0,s,0,0,1,0,0,-s,0,c,0));mu.mem_write(Ang,struct.pack('<3f',0,theta,0))
 x=f(rng.uniform(1.3,7.));endx=f(rng.uniform(-7.,-.2));y=f(rng.uniform(-1.,1.));z=f(rng.uniform(-.8,.8));mu.mem_write(F['P0'],struct.pack('<3f',x,y,z));mu.mem_write(F['P1'],struct.pack('<3f',endx,y,z))
 for fn in (0x7103c54140,0x7103c54de4):
  u.w32(Stage+0x24,0);u.w32(CL+8,0);mu.mem_write(Points,bytes(0x400));mu.mem_write(Entries,bytes(0x80));before=len(traces);bc=len(core);e=u.call(fn,0,Args,count=20000000);whole.append(dict(case=case,fn=hex(fn),theta=float(theta),error=e,core_calls=len(core)-bc,trace_count=len(traces)-before,count=u.r32(CL+8),fraction=u.rf(Points+0x60)))
print('whole',len(whole),'traces',len(traces),'fields',fields,'bad',len(bad),'errors',sum(r['error'] is not None for r in whole))
# Isolated straight line blocks reuse original bytes. Explicit live registers/stack, no native branch replacement.
from r8_physics_native_uc import PhysicsUC
b=PhysicsUC();bm=b.mu;Q=b.alloc(0x200);SP=b.alloc(0x1000)+0x800;FP=SP+0x200;b.wq(FP-0xe0,Q+0x50);b.wq(FP-0xf0,Q+0x60);b.wf(Q+0x114,1)
block_fields=0;block_bad=[]
def setq(r,v):bm.reg_write(r,pack2(v))
def checkblock(label,a,e):
 global block_fields
 for i,(x,y) in enumerate(zip(a,e)):
  block_fields+=1
  if bits(x)!=bits(y):block_bad.append(dict(case=case,label=label,lane=i,actual=hex(bits(x)),expected=hex(bits(y))))
for case in range(8192):
 t=[f(rng.uniform(0,1)) for _ in range(2)];cap=[f(rng.uniform(float(x),1.5)) for x in t];remain=[f(cap[i]-t[i]) for i in range(2)];gap=[f(rng.uniform(-2,20)) for _ in range(2)];off=[f(rng.uniform(-1,3)) for _ in range(2)];bound=[f(rng.uniform(.00001,25)) for _ in range(2)];mint=[f(rng.choice([0.,.0001,.01,.1])) for _ in range(2)]
 if case<4:bound=[f(0.),f(float('inf'))];gap=[f(case-1),f(0.)];off=[f(0),f(0)];mint=[f(0),f(0)]
 bm.reg_write(UC_ARM64_REG_SP,SP);bm.reg_write(UC_ARM64_REG_X29,FP);bm.reg_write(UC_ARM64_REG_X21,Q)
 for r,v in ((UC_ARM64_REG_Q0,t),(UC_ARM64_REG_Q1,remain),(UC_ARM64_REG_Q2,gap),(UC_ARM64_REG_Q9,off),(UC_ARM64_REG_Q12,bound),(UC_ARM64_REG_Q7,cap)):setq(r,v)
 bm.mem_write(SP+0x150,struct.pack('<2f',*mint));bm.emu_start(0x710094ea28,0x710094ea6c,count=40);checkblock('advance',get2(bm,UC_ARM64_REG_Q1),advance(t,remain,gap,off,bound,mint,cap))
 lt=t;ut=cap;lg=[f(rng.uniform(.01,20)) for _ in range(2)];ug=[f(rng.uniform(-2,0)) for _ in range(2)];target=[f(rng.uniform(-3,3)) for _ in range(2)]
 if case<4:ug=lg[:];target=lg[:] if case%2==0 else [f(lg[i]+1) for i in range(2)]
 for r,v in ((UC_ARM64_REG_X24,ug),(UC_ARM64_REG_X23,lg),(UC_ARM64_REG_X28,ut),(UC_ARM64_REG_X27,lt)):bm.reg_write(r,pack2(v))
 setq(UC_ARM64_REG_Q8,target);bm.emu_start(0x710094f170,0x710094f1e4,count=40);actual=list(struct.unpack('<2f',int(bm.reg_read(UC_ARM64_REG_X20)).to_bytes(8,'little')));checkblock('refine',actual,refine(ut,lt,ug,lg,target,mint))
out=dict(scope=__doc__,whole_cases=len(whole),whole=whole,whole_trace_count=len(traces),whole_fields=fields,whole_bad=bad,core=core,traces=traces,block_cases_each=8192,block_fields=block_fields,block_bad=block_bad,init_errors=F['errors'],runtime=dict(null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed),block_runtime=dict(null=b.null_calls,auto=b.auto_pages,faults=b.faults,plt=b.plt_stubbed))
Path('analysis/completion/r9/physics_rotation_advance_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=True),encoding='utf-8');print('blockfields',block_fields,'bad',len(block_bad),'runtime',out['runtime'],'blockruntime',out['block_runtime']);print('firstbad',bad[:2],block_bad[:2]);assert not bad and not block_bad and not any(r['error'] for r in whole)
