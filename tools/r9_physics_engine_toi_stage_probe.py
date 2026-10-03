"""r9 whole engine four-handler capsule TOI with actual native math and game staging/list writes. Explicit identity/static fixture; filter/codec null. Independent axis fraction and staging p0+f*(p1-p0) check only; not generic/rotation closure."""
import json,struct
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
F=make_engine_toi_fixture();u=F['u'];Stage=F['Stage'];CL=F['CL'];Points=F['Points'];Entries=F['Entries'];Args=F['Args'];f=np.float32
hits={hex(p):0 for p in (0x71009af088,0x7100947aec,0x7100949570,0x7100948f30,0x7100aec920,0x7100aefd00,0x7103c5606c,0x7103c563dc,0x7103c5621c,0x7103c56588,0x7103c5677c,0x7103c5698c,0x7103a60c74)};record=[]
def pc(mu,p,size,d):
 hits[hex(p)]+=1
 if p in (0x7103c5621c,0x7103c56588,0x7103c5677c,0x7103c5698c):
  qp=mu.reg_read(UC_ARM64_REG_X1);cx=mu.reg_read(UC_ARM64_REG_X0);record.append(dict(pc=hex(p),point=bytes(mu.mem_read(qp,0x80)).hex(),context=bytes(mu.mem_read(cx,0x20)).hex()))
for p in hits:u.mu.hook_add(UC_HOOK_CODE,pc,begin=int(p,16),end=int(p,16))
results=[];bad=[]
for fn in (0x7103c52d30,0x7103c5368c,0x7103c54140,0x7103c54de4):
 u.w32(Stage+0x24,0);u.w32(CL+8,0);u.w32(CL+0x98,0);u.w32(CL+0x9c,0);u.mu.mem_write(Points,bytes(0x400));u.mu.mem_write(Entries,bytes(0x80));before=dict(hits);e=u.call(fn,0,Args,count=5000000)
 raw=bytes(u.mu.mem_read(Points,0x80));frac=f(f(f(2)-f(f(.6)+f(.6)))/f(4));pos=f(f(2)+f(frac*f(f(-2)-f(2))));expect=struct.pack('<f',frac)+struct.pack('<3f',pos,0,0);actual=raw[0x60:0x64]+raw[0x24:0x30]
 if expect!=actual or u.rq(Entries)!=Points or u.r32(CL+8)!=1:bad.append(dict(fn=hex(fn),expected=expect.hex(),actual=actual.hex(),listptr=hex(u.rq(Entries)),count=u.r32(CL+8)))
 results.append(dict(fn=hex(fn),error=e,hits={k:v-before[k] for k,v in hits.items()},pc=hex(u.mu.reg_read(UC_ARM64_REG_PC)),raw=raw.hex(),stage_count=u.r32(Stage+0x24),list_count=u.r32(CL+8),listptr=hex(u.rq(Entries)),counters=[u.r32(CL+0x98),u.r32(CL+0x9c)]));print(results[-1])
r=dict(scope=__doc__,results=results,bit_mismatch=bad,postrecords=record,init_errors=F['errors'],null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_engine_toi_stage_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('bad',bad,'runtime',u.null_calls,u.auto_pages,u.faults)
