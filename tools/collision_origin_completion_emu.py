"""Original PlayerCollision reset transform; capture side effects behind explicit stubs."""
import json,random,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_LR,UC_ARM64_REG_PC
from network_uc import UC,BASE,END,STUB
ROOT=Path(__file__).resolve().parents[2]
def run():
 h=UC();mu=h.mu
 pc=h.alloc(0xe500);actor=h.alloc(0x1000);sched=h.alloc(0x600);jobs=h.alloc(0x1000);beh=h.alloc(0x200);body=h.alloc(0xac90);coll=h.alloc(0x100);shapes=h.alloc(0x100);cap=h.alloc(0x120);capvt=h.alloc(0x20);ctrlwrap=h.alloc(0x30);ctrl=h.alloc(0x80);ctrlvt=h.alloc(0x280);result=h.alloc(0x1800);component=h.alloc(0x80);under=h.alloc(0x200)
 def q(a,v):mu.mem_write(a,struct.pack('<Q',v))
 def u(a,v):mu.mem_write(a,struct.pack('<I',v))
 q(pc+0x28,actor);q(actor+0x510,sched);q(sched+0x20,jobs)
 q(pc+0xe3a8,beh);q(beh+0x108,body)
 q(pc+0x38,coll);u(coll+0xb8,1);q(coll+0xc0,shapes);q(shapes,cap);q(cap,capvt);q(capvt,STUB+0x380)
 q(pc+0xe3b8,ctrlwrap);q(ctrlwrap+8,ctrl);q(ctrl,ctrlvt);q(ctrlvt+0xb8,STUB+0x388)
 q(pc+0xe378,result);q(pc+0xe3b0,component);q(component+0x18,under)
 for off in [0x48,0x50,0x58]:q(pc+off,h.alloc(0x300))
 mu.mem_write(BASE+0x5851db0,b'\1')
 seen=[];stubs=set();captured=[]
 def hook(m,a,s,d):
  if a==STUB+0x388:
   captured.append(bytes(m.mem_read(m.reg_read(UC_ARM64_REG_X1),48)))
  elif a==STUB+0x380:m.reg_write(UC_ARM64_REG_X0,1)
  elif a>=BASE and not BASE+0x24f4440<=a<BASE+0x24f489c:
   stubs.add(hex(a));m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
 mu.hook_add(UC_HOOK_CODE,hook)
 rng=random.Random(20261003); mismatches=[]; samples=[]
 f=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 def bits(v):return struct.pack('<f',v).hex()
 cases=[(-0.0,-0.0,-0.0,0.6),(0.,0.,0.,0.6),(1.,2.,3.,0.6),(0.,-0.6,0.,0.6)]
 cases+=[tuple(f(rng.uniform(-200,200)) for _ in range(3))+(f(rng.choice([0.6,1.0,0.4,0.35])),) for _ in range(1020)]
 for i,(x,y,z,r) in enumerate(cases):
  for off,v in zip([0x10,0x14,0x18],[x,y,z]):h.f32(body+off,v)
  for off,v in zip(range(0x1c,0x40,4),[1,0,0,0,1,0,0,0,1]):h.f32(body+off,v)
  h.f32(cap+0xf0,r);captured.clear();h.call(BASE+0x24f4440,pc,0)
  got=[struct.unpack_from('<f',captured[0],off)[0] for off in [0xc,0x1c,0x2c]]
  exp=[f(x+0.0),f(y+r),f(z+0.0)]
  ok=[bits(v) for v in got]==[bits(v) for v in exp]
  row={'case':i,'game_position':[x,y,z],'radius':r,'expected_bits':[bits(v) for v in exp],'original_bits':[bits(v) for v in got]}
  if i<4:samples.append(row)
  if not ok:mismatches.append(row)
 out={'function':'0x71024f4440','cases':len(cases),'passed':len(cases)-len(mismatches),'mismatches':mismatches,'samples':samples,'stubs':sorted(stubs)+['capsule type query returns true','ctrl vt+0xb8 captures transform and returns'],'unverified':['side effects of stubbed helpers','normal frame synchronization after Havok','shape radius writer not executed; radii supplied explicitly']}
 p=ROOT/'analysis/completion/collision_origin_emu.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'original reset transform: {out["passed"]}/{len(cases)} bit matches; mismatches={len(mismatches)}; {p}')
 if mismatches:raise SystemExit(1)
if __name__=='__main__':run()
