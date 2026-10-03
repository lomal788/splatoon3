"""r9 whole original point-convex cast aefd00/aefdc0 initial probe.
Explicit one-point vertex shape and linear cast, no generic GJK closure claim.
"""
import json,struct
from pathlib import Path
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();V=u.alloc(16);Q=u.alloc(0x80);O=u.alloc(0x40)
u.mu.mem_write(Q,struct.pack('<4f',-4.,0.,0.,0.))
for j,vs in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(2.,0.,0.,0.))):u.mu.mem_write(Q+0x10+16*j,struct.pack('<4f',*vs))
u.mu.mem_write(Q+0x50,struct.pack('<2f',.001,.001));u.mu.mem_write(Q+0x58,struct.pack('<2f',0.,0.));u.mu.mem_write(Q+0x60,struct.pack('<2f',.5,.5));u.wf(O,1.)
e=u.call(0x7100aefd00,V,1,V,1,Q,O,count=2000000)
r=dict(error=e,returnvalue=u.x(0),query=bytes(u.mu.mem_read(Q,0x80)).hex(),out=bytes(u.mu.mem_read(O,0x40)).hex(),fraction=struct.unpack('<2f',u.mu.mem_read(O,8)),normal=struct.unpack('<4f',u.mu.mem_read(O+0x20,16)),valid=u.r32(O+0x30),null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r9/physics_point_toi_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
