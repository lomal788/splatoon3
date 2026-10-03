"""r9 exploratory whole native generic cast. Outputs/coverage only, no independent formula claim."""
import json,struct,itertools
from pathlib import Path
from r8_physics_native_uc import PhysicsUC
from unicorn import UC_HOOK_CODE
u=PhysicsUC();Q=u.alloc(0x80);O=u.alloc(0x40);VA=u.alloc(0x100);VB=u.alloc(0x100);cases=[];vis=set()
def pc(mu,a,s,d):vis.add(a)
h=u.mu.hook_add(UC_HOOK_CODE,pc,begin=0x7100aec920,end=0x7100aefc00)
cube=list(itertools.product((-1.,1.),repeat=3)); tri=[(-1.,0.,-1.),(1.,0.,-1.),(0.,0.,1.)]
for name,av,bv,orig,delta,r in [('pointpoint',[(0.,0.,0.)],[(0.,0.,0.)],(2.,0.,0.),(-4.,0.,0.),.5),('cube-point',cube,[(0.,0.,0.)],(4.,0.,0.),(-8.,0.,0.),.5),('point-cube',[(0.,0.,0.)],cube,(4.,0.,0.),(-8.,0.,0.),.5),('triangle-point',tri,[(0.,0.,0.)],(0.,4.,0.),(0.,-8.,0.),.5),('cube-cube',cube,cube,(4.,0.,0.),(-8.,0.,0.),.5),('cube-cube-oblique',cube,cube,(4.,4.,.5),(-8.,-8.,0.),.5),('cube-cube-away',cube,cube,(4.,4.,.5),(8.,8.,0.),.5)]:
 u.mu.mem_write(VA,struct.pack('<'+'f'*3*len(av),*sum((list(v) for v in av),[])));u.mu.mem_write(VB,struct.pack('<'+'f'*3*len(bv),*sum((list(v) for v in bv),[])));u.mu.mem_write(Q,struct.pack('<4f',*delta,0.))
 for j,v in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(*orig,0.))):u.mu.mem_write(Q+0x10+16*j,struct.pack('<4f',*v))
 u.mu.mem_write(Q+0x50,struct.pack('<2f',.001,.001));u.mu.mem_write(Q+0x58,struct.pack('<2f',0.,0.));u.mu.mem_write(Q+0x60,struct.pack('<2f',r,r));u.mu.mem_write(Q+0x68,bytes(16));u.w32(Q+0x68,256);u.mu.mem_write(O,bytes(64));u.wf(O,1.);vis.clear();e=u.call(0x7100aec920,VA,len(av),VB,len(bv),Q,O,0,0,count=2000000)
 cases.append(dict(name=name,error=e,returnvalue=u.x(0),valid=u.r32(O+0x30),fraction=struct.unpack('<2f',u.mu.mem_read(O,8)),normal=struct.unpack('<4f',u.mu.mem_read(O+0x20,16)),point=struct.unpack('<4f',u.mu.mem_read(O+0x10,16)),out=bytes(u.mu.mem_read(O,64)).hex(),pcs=[hex(x) for x in sorted(vis)]));print(name,e,u.x(0),u.r32(O+0x30),struct.unpack('<2f',u.mu.mem_read(O,8)))
r=dict(scope=__doc__,cases=cases,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_generic_toi_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
