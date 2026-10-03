"""Replay whole original09d5b68 native body transform in live snapshot; independent no-angular identity COM64 minus local COM offset and f32 position/residual equations. Synthetic COM varied; shape AABB functions remain original."""
import json,struct,random,sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();d=json.loads(Path('analysis/completion/r8/physics_pose_fixture.json').read_text());h=Path('analysis/completion/r8/physics_pose_heap.bin').read_bytes();stack=Path('analysis/completion/r8/physics_pose_stack.bin').read_bytes()
u.mu.mem_write(d['bss_base'],Path('analysis/completion/r8/physics_pose_bss.bin').read_bytes());u.heap_next=d['heap_base']+len(h)
M=d['native_motion'];N=d['native_body'];rng=random.Random(0x9d5b68);bad=[];samples=[];errors=[]
def restore():
 u.mu.mem_write(d['heap_base'],h);u.mu.mem_write(d['stack_base'],stack)
 for k,v in d['regs'].items():u.mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
for i in range(1024):
 restore();center=[u.rf(N+0xc+j*0x10) for j in range(3)]
 if i==0:com=list(struct.unpack('<3d',u.mu.mem_read(M+0x10,24)))
 else:
  scale=rng.choice([1.,1e4,1e10]);com=[rng.uniform(-scale,scale) for j in range(3)];u.mu.mem_write(M+0x10,struct.pack('<3d',*com))
 origin=[com[j]-float(np.float32(center[j])) for j in range(3)];of=[np.float32(x) for x in origin];res=[np.float32(origin[j]-float(of[j])) for j in range(3)]
 try:u.mu.emu_start(0x71009d5b68,d['regs']['x30'],count=2000000)
 except Exception as e:errors.append(dict(i=i,error=str(e)));break
 got_pos=bytes(u.mu.mem_read(N+0x30,12));got_res=bytes(u.mu.mem_read(N+0x40,12));want_pos=struct.pack('<3f',*of);want_res=struct.pack('<3f',*res)
 if got_pos!=want_pos or got_res!=want_res:bad.append(dict(i=i,got_pos=got_pos.hex(),want_pos=want_pos.hex(),got_res=got_res.hex(),want_res=want_res.hex()))
 if i<4:samples.append(dict(i=i,com=com,center=center,origin=struct.unpack('<3f',got_pos),residual=struct.unpack('<3f',got_res)))

r=dict(cases=i+1,f32_fields=6*(i+1),mismatch=bad,errors=errors,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/physics_pose_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k not in ('samples','mismatch')},ensure_ascii=False));print('mismatch',len(bad),bad[:2])
