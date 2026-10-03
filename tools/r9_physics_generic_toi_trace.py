"""r9 general TOI whole-function trace at feature/support/advance boundaries. Observation only."""
import json, struct, itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC(); Q=u.alloc(0x80); O=u.alloc(0x40); P=u.alloc(0x40); VA=u.alloc(0x100);VB=u.alloc(0x100)
pcs=(0x7100aecda4,0x7100aee80c,0x7100aeeadc,0x7100aef0bc,0x7100aef19c,0x7100aef1c0,0x7100aefb60,0x7100aefbc8)
records=[]
def hook(mu,a,s,d):
 sp=mu.reg_read(UC_ARM64_REG_SP)
 records.append(dict(pc=hex(a),x=[mu.reg_read(globals()[f'UC_ARM64_REG_X{i}']) for i in range(31)],q=[mu.reg_read(globals()[f'UC_ARM64_REG_Q{i}']).to_bytes(16,'little').hex() for i in range(32)],sp=hex(sp),stack=bytes(mu.mem_read(sp,0x340)).hex()))
for pc in pcs:u.mu.hook_add(UC_HOOK_CODE,hook,begin=pc,end=pc)
cube=list(itertools.product((-1.,1.),repeat=3));tri=[(-1.,0.,-1.),(1.,0.,-1.),(0.,0.,1.)]
results=[]
for name,av,bv,org,delt in [('cube-point',cube,[(0.,0.,0.)],(4.,0.,0.),(-8.,0.,0.)),('cube-cube',cube,cube,(4.,0.,0.),(-8.,0.,0.)),('tri-point',tri,[(0.,0.,0.)],(0.,4.,0.),(0.,-8.,0.)),('oblique',cube,cube,(4.,4.,.5),(-8.,-8.,0.))]:
 for pp,vv in [(VA,av),(VB,bv)]:u.mu.mem_write(pp,struct.pack('<'+'f'*len(vv)*3,*sum((list(v) for v in vv),[])))
 u.mu.mem_write(Q,struct.pack('<4f',*delt,0.))
 for j,v in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(*org,0.))):u.mu.mem_write(Q+0x10+j*16,struct.pack('<4f',*v))
 u.mu.mem_write(Q+0x50,struct.pack('<6f',.001,.001,0.,0.,.5,.5));u.w32(Q+0x68,256);u.w32(Q+0x6c,0)
 for initial in (False,True):
  u.mu.mem_write(O,bytes(64));u.wf(O,1.);u.mu.mem_write(P,bytes(64));records.clear();e=u.call(0x7100aec920,VA,len(av),VB,len(bv),Q,O,P if initial else 0,0,count=3000000)
  results.append(dict(name=name,initial=initial,error=e,ret=u.x(0),out=bytes(u.mu.mem_read(O,64)).hex(),init=bytes(u.mu.mem_read(P,64)).hex(),records=records.copy()))
  print(name,initial,e,u.x(0),u.rf(O),len(records))
r=dict(scope=__doc__,results=results,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_toi_trace.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
