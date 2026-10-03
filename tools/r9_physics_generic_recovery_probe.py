"""r9 generic overlap recovery whole-function trace. Original allocator/TLS environment initialized; independent EPA formula comparison not yet claimed."""
import json,struct,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import init_native
u,init=init_native();Q=u.alloc(0x80);O=u.alloc(0x40);P=u.alloc(0x40);VA=u.alloc(0x100);VB=u.alloc(0x100);records=[];counts={hex(p):0 for p in (0x7100ae7b34,0x7100ae9b14,0x7100ae7fd0,0x7100ae892c,0x7100ae926c,0x7100ae9840,0x7100ae9498,0x7100ae8e80,0x7100ae8af8)}
def hook(mu,pc,size,data):
 counts[hex(pc)]+=1
 if pc in (0x7100ae7b34,0x7100ae9b14,0x7100ae7fd0):
  a=mu.reg_read(UC_ARM64_REG_X0);sz=0xe0 if pc==0x7100ae7b34 else 0x100
  records.append(dict(pc=hex(pc),x=[mu.reg_read(globals()[f'UC_ARM64_REG_X{i}']) for i in range(8)],descriptor=bytes(mu.mem_read(a,sz)).hex()))
for pc in counts:u.mu.hook_add(UC_HOOK_CODE,hook,begin=int(pc,16),end=int(pc,16))
cube=list(itertools.product((-1.,1.),repeat=3));point=[(0.,0.,0.)];tri=[(-1.,0.,-1.),(1.,0.,-1.),(0.,0.,1.)];res=[]
for name,av,bv,org,delt in [('cube-cube',cube,cube,(.5,.3,.1),(1.,0.,0.)),('cube-point',cube,point,(.5,.3,.1),(1.,0.,0.)),('point-point',point,point,(0.,0.,0.),(1.,0.,0.)),('tri-point',tri,point,(0.,0.,0.),(0.,1.,0.)),('cube-touch',cube,cube,(2.,0.,0.),(-1.,0.,0.))]:
 for pp,vv in ((VA,av),(VB,bv)):u.mu.mem_write(pp,struct.pack('<'+'f'*len(vv)*3,*sum((list(v) for v in vv),[])))
 u.mu.mem_write(Q,struct.pack('<4f',*delt,0.))
 for j,v in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(*org,0.))):u.mu.mem_write(Q+0x10+j*16,struct.pack('<4f',*v))
 u.mu.mem_write(Q+0x50,struct.pack('<6f',.001,.001,0.,0.,.5,.5));u.w32(Q+0x68,256);u.w32(Q+0x6c,0)
 for initial in (False,True):
  u.mu.mem_write(O,bytes(64));u.wf(O,1.);u.mu.mem_write(P,bytes(64));records.clear();before=dict(counts);e=u.call(0x7100aec920,VA,len(av),VB,len(bv),Q,O,P if initial else 0,0,count=10000000)
  r=dict(name=name,initial=initial,error=e,ret=u.x(0),out=bytes(u.mu.mem_read(O,64)).hex(),init=bytes(u.mu.mem_read(P,64)).hex(),calls={k:v-before[k] for k,v in counts.items()},records=records.copy());res.append(r);print({k:v for k,v in r.items() if k not in ('records','out','init')})
r=dict(scope=__doc__,init_errors=init,results=res,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_recovery_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('runtime',u.null_calls,u.auto_pages,u.faults)

