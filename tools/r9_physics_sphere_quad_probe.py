"""Original full sphere→quad specialized sweep exploratory fixture. Collector capture is output boundary; no shape/query arithmetic stub."""
import struct,json
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import init_native
u,errors=init_native();mu=u.mu
Center=u.alloc(0x10);Out=u.alloc(8);mu.reg_write(UC_ARM64_REG_X8,Out);errors.append(['originalSphere',u.call(0x710092efbc,Center,0,fargs=(.5,))]);SA=u.rq(Out)
SB=u.alloc(0xc0);u.w8(SB+0x18,4);mu.mem_write(SB+0x1a,struct.pack('<H',1));u.w32(SB+0x40,0x40);V=SB+0x80
verts=[(-1,0,-1),(-1,0,1),(1,0,1),(1,0,-1)];mu.mem_write(V,struct.pack('<12f',*sum((list(v) for v in verts),[])))
IA=u.alloc(0x60);IB=u.alloc(0x60);M=u.alloc(0x40);mu.mem_write(M,struct.pack('<16f',1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1));W=u.alloc(0x40);mu.mem_write(W,struct.pack('<16f',1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1));u.wq(IA+0x20,W);u.wq(IB+0x20,W)
for I in (IA,IB):mu.mem_write(I+0x40,struct.pack('<4f',1,1,1,1))
Q=u.alloc(0xb0);Ctx=u.alloc(0x40);Tag=u.alloc(0x10);u.wq(Q+0x38,SA);u.wf(Q+0x78,.001);Meta=u.alloc(0x30);VT=u.alloc(0x40);CB=u.alloc(0x10);mu.mem_write(CB,bytes.fromhex('c0035fd6'));u.wq(VT+0x28,CB);u.wq(Meta,VT);mu.mem_write(Meta+0x10,struct.pack('<2f',1,1));records=[]
def capture(mu,p,size,data):
 addr=mu.reg_read(UC_ARM64_REG_X1);raw=bytes(mu.mem_read(addr,0x80));records.append(raw.hex())
mu.hook_add(UC_HOOK_CODE,capture,begin=CB,end=CB)
rows=[]
for name,o,d in [('face',(0,2,0),(0,-4,0)),('edge',(1.3,2,0),(0,-4,0)),('corner',(1.3,2,1.3),(0,-4,0)),('miss',(3,2,0),(0,-4,0)),('away',(0,2,0),(0,4,0)),('overlap',(0,.3,0),(0,-4,0)),('below',(0,-2,0),(0,4,0))]:
 for initial in (False,True):
  mu.mem_write(Q+0x50,struct.pack('<4f',*d,0));mu.mem_write(M+0x30,struct.pack('<4f',*o,0));u.wf(Ctx+0x18,0);records.clear();e=u.call(0x710094ae10,Ctx,Q,IA,SB,Tag,IB,M,0,stack_args=(Meta,Meta if initial else 0),count=2000000);rows.append(dict(name=name,origin=o,delta=d,initial=initial,error=e,records=records[:],decoded=[dict(fraction=struct.unpack_from('<f',bytes.fromhex(r),0x20)[0],point=list(struct.unpack_from('<4f',bytes.fromhex(r),0)),normal=list(struct.unpack_from('<4f',bytes.fromhex(r),0x10))) for r in records]));print(rows[-1])
out=dict(scope=__doc__,sphere=hex(SA),sphere_type=u.r8(SA+0x18),rows=rows,init=errors,runtime=dict(null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed));Path('analysis/completion/r9/physics_sphere_quad_probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(out['init'],out['runtime'])
