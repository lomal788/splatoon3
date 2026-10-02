"""Original AArch64 roll/wall-kick count write and damping instruction blocks.
No gameplay frame or trigger execution is asserted. Finite local f32 inputs only.
"""
import json, random, struct
from pathlib import Path
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_X19, UC_ARM64_REG_X25, UC_ARM64_REG_X29, UC_ARM64_REG_S8
from network_uc import UC, STACK
ROOT=Path(__file__).resolve().parents[2]
e=UC(); launch=e.alloc(0x100); pp=e.alloc(0x260); singleton=e.alloc(0x200); gptr=e.alloc(8)
def ptr(a,v): e.mu.mem_write(a,struct.pack('<Q',v))
ptr(gptr,singleton)
rng=random.Random(20261004); writes=[]; damp=[]
for n in [0,1,9,10,0x7fffffff,0xffffffff]+[rng.getrandbits(32) for _ in range(256)]:
 for frame in [0,1,90,0x7fffffff,0x80000000,0xffffffff]:
  e.u32(launch+0x24,n); e.u32(singleton+0x148,frame)
  e.mu.reg_write(UC_ARM64_REG_X19,launch); e.mu.reg_write(UC_ARM64_REG_X25,gptr)
  e.mu.emu_start(0x7102459eec,0x7102459f08,count=64)
  got=[e.ru32(launch+0x24),e.ru32(launch+0x28)]
  expected=[(n+1)&0xffffffff,frame if frame<0x80000000 else 0]
  assert got==expected,(n,frame,got,expected)
  writes.append(dict(n=n,frame=frame,got=got))
for n in [-0x80000000,-1,0,1,2,3,4,5,6,7,8,9,10,11,0x7fffffff]:
 for ratio in [.85,.9,.925,1.0]+[rng.uniform(.85,1) for _ in range(64)]:
  e.u32(launch+0x24,n); e.f32(pp+0x140,ratio)
  bp=STACK+0x80000; ptr(bp-0x28,pp)
  e.mu.reg_write(UC_ARM64_REG_X19,launch); e.mu.reg_write(UC_ARM64_REG_X29,bp)
  e.mu.reg_write(UC_ARM64_REG_S8,0x3f800000) # preceding original prologue initializes factor=1
  e.mu.emu_start(0x7102459b44,0x7102459bb8,count=100)
  got=e.mu.reg_read(UC_ARM64_REG_S8)
  expected=np.float32(1)
  for _ in range(max(0,min(n,10))): expected=np.float32(np.float32(ratio)*expected)
  bits=struct.unpack('<I',struct.pack('<f',expected))[0]
  assert got==bits,(n,ratio,got,bits)
  damp.append(dict(n=n,ratio=float(np.float32(ratio)),got=hex(got),expected=hex(bits)))
result=dict(writes_count=len(writes),damping_count=len(damp),mismatches=0,writes=writes,damping=damp,
 limitations=['instruction blocks, not whole 0x7102459630','reset/trigger conditions instruction reading only'])
(ROOT/'analysis/completion/roll_counter_emu.json').write_text(json.dumps(result,indent=1),encoding='utf-8')
print('counter write '+str(len(writes))+' / damping '+str(len(damp))+' exact, mismatches=0')
