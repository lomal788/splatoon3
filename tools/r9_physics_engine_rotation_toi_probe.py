"""r9 engine rotation TOI exploratory whole4 handler fixture. Vertical capsules under pure Y rotation have invariant geometry. Native query/filter math actual; filter/codec null, OS/TLS fixtures. No generic rotation reference closure claimed."""
import json,struct,math
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
F=make_engine_toi_fixture();u=F['u'];GB=F['GB'];GBB=F['GBB'];Args=F['Args'];Ang=F['Ang'];Stage=F['Stage'];CL=F['CL'];Points=F['Points'];Entries=F['Entries']
u.wq(GBB,0x7105756338);u.wq(GB+0x88,4)
hits={hex(p):0 for p in (0x7100948360,0x710094e6e4,0x7100af7b70,0x7100929530,0x7103c563dc,0x7100aec920)};records=[]
def capture(mu,p,size,data):
 hits[hex(p)]+=1
 if p==0x7100948360:
  Q=mu.reg_read(UC_ARM64_REG_X1);records.append(dict(pc=hex(p),Q=bytes(mu.mem_read(Q,0xb0)).hex()))
for p in hits:u.mu.hook_add(UC_HOOK_CODE,capture,begin=int(p,16),end=int(p,16))
r=[]
for theta in (0.,.1,1.,math.pi/2):
 # actual game rotation uses explicit orthogonal pure-Y matrix fixture.
 c=math.cos(theta);s=math.sin(theta);mx=[c,0,s,0,0,1,0,0,-s,0,c,0];u.mu.mem_write(GB+0xd8,struct.pack('<12f',*mx));u.mu.mem_write(Ang,struct.pack('<3f',0,theta,0))
 for fn in (0x7103c54140,0x7103c54de4):
  u.w32(Stage+0x24,0);u.w32(CL+8,0);u.mu.mem_write(Points,bytes(0x400));u.mu.mem_write(Entries,bytes(0x80));before=dict(hits);b=len(records);e=u.call(fn,0,Args,count=20000000)
  raw=bytes(u.mu.mem_read(Points,0x80));r.append(dict(theta=theta,fn=hex(fn),error=e,hits={k:v-before[k] for k,v in hits.items()},records=records[b:],staged=raw.hex(),fraction=struct.unpack_from('<f',raw,0x60)[0],count=u.r32(CL+8)));print({k:v for k,v in r[-1].items() if k!='records' and k!='staged'})
out=dict(scope=__doc__,results=r,init_errors=F['errors'],null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_engine_rotation_toi_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('runtime',u.null_calls,u.auto_pages,u.faults,u.plt_stubbed)
