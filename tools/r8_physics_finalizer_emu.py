"""Replay whole original finalizer0a4b8c8 in actual native snapshot; independent ordinary-player no-angular COM and physical velocity equations. Synthetic solver arrays varied; full contacts not replaced."""
import json,struct,random,sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();d=json.loads(Path('analysis/completion/r8/physics_finalize_fixture.json').read_text());h=Path('analysis/completion/r8/physics_finalize_heap.bin').read_bytes();stack=Path('analysis/completion/r8/physics_finalize_stack.bin').read_bytes()
u.mu.mem_write(d['bss_base'],Path('analysis/completion/r8/physics_finalize_bss.bin').read_bytes());u.heap_next=d['heap_base']+len(h)
M=d['native_motion'];cur=d['current']+0x20;bas=d['baseline']+0x20;info=d['info'];rng=random.Random(0xa4b8c8);bad=[];samples=[];errors=[]
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
 dt=np.float32(u.rf(info+0x10));tau=np.float32(u.rf(info+0xb0));invsub=np.float32(u.rf(info+0x74));invtau=np.float32(u.rf(info+0xc0));factor=np.float32(invsub*invtau)
 delta=[np.float32(np.float32(v[j])-np.float32(b[j])) for j in range(3)]
 effective=[np.float32(np.float32(np.float32(b[j])+np.float32(delta[j]*tau))*factor) for j in range(3)]
 expected_com=[old[j]+float(np.float32(effective[j]*dt)) for j in range(3)]
 try:u.mu.emu_start(0x7100a4b8c8,d['regs']['x30'],count=2000000)
 except Exception as e:errors.append(dict(i=i,error=str(e)));break
 got_vel=bytes(u.mu.mem_read(M+0x60,12));got_com=bytes(u.mu.mem_read(M+0x10,24));expected_vel=struct.pack('<3f',*delta);expected_com_b=struct.pack('<3d',*expected_com)
 if got_vel!=expected_vel or got_com!=expected_com_b:bad.append(dict(i=i,got_vel=got_vel.hex(),want_vel=expected_vel.hex(),got_com=got_com.hex(),want_com=expected_com_b.hex()))
 if i<4:samples.append(dict(i=i,current=[float(x) for x in v],baseline=[float(x) for x in b],physical_delta=[float(x) for x in delta],effective=[float(x) for x in effective],com=struct.unpack('<3d',got_com)))
r=dict(cases=i+1,f32_fields=3*(i+1),f64_fields=3*(i+1),mismatch=bad,errors=errors,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/physics_finalizer_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k not in ('samples','mismatch')},ensure_ascii=False));print('mismatch',len(bad),bad[:2])
