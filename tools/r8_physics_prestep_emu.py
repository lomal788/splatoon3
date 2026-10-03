"""Replay whole original prestep0a4b514 in actual native snapshot; independent baseline/physical delta and substep gravity equations; no-angular uncapped finite player fixture."""
import json,struct,random,sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();d=json.loads(Path('analysis/completion/r8/physics_prestep_fixture.json').read_text());h=Path('analysis/completion/r8/physics_prestep_heap.bin').read_bytes();stack=Path('analysis/completion/r8/physics_prestep_stack.bin').read_bytes()
u.mu.mem_write(d['bss_base'],Path('analysis/completion/r8/physics_prestep_bss.bin').read_bytes());u.heap_next=d['heap_base']+len(h)
M=d['native_motion'];cur=d['current'];bas=d['baseline'];info=d['info'];rng=random.Random(0xa4b514);bad=[];samples=[];errors=[]
def vec(a):return [u.rf(a+j*4) for j in range(3)]
def restore():
 u.mu.mem_write(d['heap_base'],h);u.mu.mem_write(d['stack_base'],stack)
 for k,v in d['regs'].items():u.mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
def write_linear(p,v):
 u.wf(p+0x10,v[0]);u.wf(p+0x14,v[1]);u.wf(p+0xc,v[2])
for i in range(1024):
 restore()
 if i==0:
  b=[u.rf(bas+0x10),u.rf(bas+0x14),u.rf(bas+0xc)];v=[u.rf(cur+0x10),u.rf(cur+0x14),u.rf(cur+0xc)];old=list(struct.unpack('<3d',u.mu.mem_read(M+0x10,24)))
 else:
  b=[np.float32(rng.uniform(-20,20)) for j in range(3)];delta=[np.float32(rng.uniform(-20,20)) for j in range(3)];v=[np.float32(b[j]+delta[j]) for j in range(3)];scale=rng.choice([1.,1e4,1e10]);old=[rng.uniform(-scale,scale) for j in range(3)]
  write_linear(bas,b);write_linear(cur,v);u.mu.mem_write(M+0x10,struct.pack('<3d',*old))
 delta=[np.float32(np.float32(v[j])-np.float32(b[j])) for j in range(3)]
 tau=np.float32(u.rf(info+0xb0));g=[np.float32(u.rf(info+0x90+j*4)) for j in range(3)];expected_base=[np.float32(np.float32(b[j])+np.float32(delta[j]*tau)) for j in range(3)]
 expected_current=[np.float32(np.float32(delta[j]+expected_base[j])+g[j]) for j in range(3)]
 try:u.mu.emu_start(0x7100a4b514,d['regs']['x30'],count=2000000)
 except Exception as e:errors.append(dict(i=i,error=str(e)));break
 def read_linear(p):return struct.pack('<3f',u.rf(p+0x10),u.rf(p+0x14),u.rf(p+0xc))
 got_current=read_linear(cur);got_base=read_linear(bas);want_current=struct.pack('<3f',*expected_current);want_base=struct.pack('<3f',*expected_base)
 if got_current!=want_current or got_base!=want_base:bad.append(dict(i=i,current=got_current.hex(),want_current=want_current.hex(),baseline=got_base.hex(),want_base=want_base.hex()))
 if i<4:samples.append(dict(i=i,current=[float(x) for x in v],baseline=[float(x) for x in b],delta=[float(x) for x in delta],next_current=struct.unpack('<3f',got_current),next_baseline=struct.unpack('<3f',got_base)))

r=dict(cases=i+1,f32_fields=6*(i+1),mismatch=bad,errors=errors,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/physics_prestep_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k not in ('samples','mismatch')},ensure_ascii=False));print('mismatch',len(bad),bad[:2])
