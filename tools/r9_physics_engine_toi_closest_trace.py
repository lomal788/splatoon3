"""r9 four TOI whole handlers with dynamic-like game previous/current origins and original backend local COM getter. Native capsule is fixture static; geometry/filter binding is explicitly separate. Probe records every query and staged contact; independent formula is not yet assumed."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
F=make_engine_toi_fixture();u=F['u'];GB=F['GB'];GBB=F['GBB'];Args=F['Args'];P0=F['P0'];P1=F['P1'];Stage=F['Stage'];CL=F['CL'];Points=F['Points'];Entries=F['Entries']
u.wq(GBB,0x7105756338);u.wq(GB+0x88,4)
cur=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,1.75];prev=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,1.]
u.mu.mem_write(GB+0xd8,struct.pack('<12f',*cur));u.mu.mem_write(GB+0x108,struct.pack('<12f',*prev));u.mu.mem_write(P0,struct.pack('<3f',0,0,11.25));u.mu.mem_write(P1,struct.pack('<3f',0,0,-2.25));records=[]
def capture(mu,p,size,data):
 if p==0x71009af088:
  qs=mu.reg_read(UC_ARM64_REG_X1);A=mu.reg_read(UC_ARM64_REG_X2);B=mu.reg_read(UC_ARM64_REG_X5);records.append(dict(pc=hex(p),Q=bytes(mu.mem_read(qs,0xb0)).hex(),shapeA=bytes(mu.mem_read(A,0xa0)).hex(),shapeB=bytes(mu.mem_read(B,0xa0)).hex()))
 elif p==0x7100949210:
  SP=mu.reg_read(UC_ARM64_REG_SP);P=mu.reg_read(UC_ARM64_REG_X4);capture.closest=P;records.append(dict(pc=hex(p),fn=hex(mu.reg_read(UC_ARM64_REG_X8)),gA=bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X0),0x28)).hex(),gB=bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X1),0x28)).hex(),ctx=bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X2),0x40)).hex()))
 elif p==0x7100949214:
  records.append(dict(pc=hex(p),output=bytes(mu.mem_read(capture.closest,0x28)).hex()))
 else:
  P=mu.reg_read(UC_ARM64_REG_X1);records.append(dict(pc=hex(p),point=bytes(mu.mem_read(P,0x80)).hex()))
for p in (0x71009af088,0x7103c563dc,0x7100949210,0x7100949214):u.mu.hook_add(UC_HOOK_CODE,capture,begin=p,end=p)
r=[]
for fn in (0x7103c52d30,0x7103c5368c,0x7103c54140,0x7103c54de4):
 u.w32(Stage+0x24,0);u.w32(CL+8,0);u.mu.mem_write(Points,bytes(0x400));u.mu.mem_write(Entries,bytes(0x80));b=len(records);e=u.call(fn,0,Args,count=5000000)
 r.append(dict(fn=hex(fn),error=e,records=records[b:],staged=bytes(u.mu.mem_read(Points,0x80)).hex(),count=u.r32(CL+8)));print(r[-1])
out=dict(scope=__doc__,results=r,errors=F['errors'],null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_engine_toi_closest_trace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('runtime',u.null_calls,u.auto_pages,u.faults)
