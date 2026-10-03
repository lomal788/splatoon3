"""r8 original native capsule-to-capsule contact probe; original multi-thread graph executed serially in dependency order."""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import HEAP,STACK,STACK_SZ
u,errors=init_native();W,D,A,e=make_world(u,mode=1);errors+=e
Mat=u.alloc(0x50);errors.append(['materialCtor',u.call(0x7100a507cc,Mat)])
for off in (0x1a,0x1c,0x1e):u.mu.mem_write(Mat+off,b'\0\0')
errors.append(['materialLibrary',u.call(0x7100a4f76c,u.rq(W+0x8a8),Mat)]);MatID=u.x(0)&0xffff
hits={hex(p):0 for p in (0x7100a181fc,0x7100a29f20,0x7100a4b8c8,0x71009d5b68)}
def hit(mu,addr,size,data):
 hits[hex(addr)]+=1
 if addr==0x7100a181fc and hits[hex(addr)]==1:
  regs={"x"+str(i):mu.reg_read(globals()["UC_ARM64_REG_X"+str(i)]) for i in range(31)}
  regs.update({"q"+str(i):mu.reg_read(globals()["UC_ARM64_REG_Q"+str(i)]) for i in range(32)})
  regs.update({name:mu.reg_read(globals()["UC_ARM64_REG_"+name.upper()]) for name in ("sp","fpcr","fpsr")})
  Path('analysis/completion/r8/physics_finalize_kernel_fixture.json').write_text(json.dumps(dict(regs=regs,heap_base=HEAP,heap_length=u.heap_next-HEAP,stack_base=STACK,stack_length=STACK_SZ,native_body=N,native_motion=M,world=W,bss_base=0x7103e9e000,bss_length=0x5a00000-0x3e9e000),indent=2),encoding='utf8')
  Path('analysis/completion/r8/physics_finalize_kernel_heap.bin').write_bytes(bytes(mu.mem_read(HEAP,u.heap_next-HEAP)))
  Path('analysis/completion/r8/physics_finalize_kernel_stack.bin').write_bytes(bytes(mu.mem_read(STACK,STACK_SZ)))
  Path('analysis/completion/r8/physics_finalize_kernel_bss.bin').write_bytes(bytes(mu.mem_read(0x7103e9e000,0x5a00000-0x3e9e000)))
for p in hits:u.mu.hook_add(UC_HOOK_CODE,hit,begin=int(p,16),end=int(p,16))
def cap(a,b,r):
 V=u.alloc(0x20);P=u.alloc(8)
 for j,v in enumerate(a):u.wf(V+j*4,v)
 for j,v in enumerate(b):u.wf(V+0x10+j*4,v)
 errors.append(['capsule',u.call(0x7100930b40,V,V+0x10,0,0,0,0,0,0,P,fargs=(r,))]);return u.rq(P)
def body(shape,pos,vel=(0,0,0),kind=2):
 B=u.alloc(0xc0);errors.append(['bodyCinfo',u.call(0x71009e64f8,B)]);u.wq(B,shape);u.w8(B+0x28,kind);u.wf(B+0x70,100);u.mu.mem_write(B+0xc,struct.pack('<H',MatID))
 for j,v in enumerate(pos):u.wf(B+0x30+j*4,v)
 for j,v in enumerate(vel):u.wf(B+0x50+j*4,v)
 errors.append(['createBody',u.call(0x71009c78f0,W,B,0xffffffffffffffff)]);H=u.x(0)
 if kind==2:
  MD=u.alloc(0x30);errors.append(['massDistribution',u.call(0x7100abf6e0,MD,shape,0x7104a81450)])
  for j in range(3):u.wf(MD+0x20+j*4,0)
  errors.append(['setDistribution',u.call(0x71009db37c,W,H,MD,0)])
  errors.append(['setMass',u.call(0x71009d7338,W,H,0,fargs=(100.,))])
 P=u.alloc(8);u.wq(P,H);errors.append(['addBody',u.call(0x71009c6a70,W,P,1,0,0)]);return H
F=body(cap((-10,-.1,0),(10,-.1,0),.1),(0,0,0),kind=0)
H=body(cap((0,0,0),(0,.7,0),.6),(0,.45,0),(0,-3,0))
TG=u.alloc(0x500);errors.append(['taskgraph',u.call(0x7100902bb0,TG)]);TI=u.alloc(0x20);u.wf(TI,1/60);u.wf(TI+4,0);u.w32(TI+8,1)
N=u.rq(W+0x38)+int(H&0xffffff)*0xc0;M=u.rq(W+0x150)+u.r32(N+0x80)*0x80
CTX=u.alloc(0xc0);u.w32(CTX+0x98,1);graphs=[];done=set()
for off in (0x4c8,0x4d0,0x4d8):u.wq(TG+off,0xffffffffffffffff)
def run_graph():
 count=u.r32(TG+0x20);ptr=u.rq(TG+0x18);ep=u.rq(TG+0x328);ec=u.r32(TG+0x330)
 edges=[struct.unpack('<HH',u.mu.mem_read(ep+4*i,4)) for i in range(ec)];log=[]
 for guard in range(count+1):
  ready=[i for i in range(count) if i not in done and all(a in done for a,b in edges if b==i and a<count)]
  if not ready:break
  for i in ready:
   node=ptr+i*0x18;task=u.rq(node);times=struct.unpack('<H',u.mu.mem_read(node+8,2))[0]
   if task:
    try:fn=u.rq(u.rq(task)+0x18)
    except Exception as ex:
     log.append(dict(index=i,task=hex(task),times=times,error=str(ex)));graphs.append(dict(count=count,edges=edges,log=log));return 'invalid task header'
    for k in range(times):
     error=u.call(fn,task,CTX,count=30000000);log.append(dict(index=i,task=hex(task),fn=hex(fn),times=times,iteration=k,error=error))
     if error:graphs.append(dict(count=count,edges=edges,log=log));return error
   done.add(i)
 graphs.append(dict(count=count,edges=edges,log=log,done=len(done)))
 return None if len(done)==count else 'task graph cycle/unhandled dependency'

final_trace=[]
def final_hook(mu,addr,size,data):
 def fq(r):return struct.unpack('<4f',int(mu.reg_read(globals()['UC_ARM64_REG_Q'+str(r)])).to_bytes(16,'little'))
 sp=mu.reg_read(UC_ARM64_REG_SP)
 if addr==0x7100a4b8c8:
  regs={'x'+str(i):mu.reg_read(globals()['UC_ARM64_REG_X'+str(i)]) for i in range(31)}
  regs.update({'q'+str(i):mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]) for i in range(32)})
  regs.update({name:mu.reg_read(globals()['UC_ARM64_REG_'+name.upper()]) for name in ('sp','fpcr','fpsr')})
  state=regs['x1'];info=u.rq(state+0x10);current=u.rq(state+0x68);base=u.rq(state+0x90)
  meta=dict(regs=regs,heap_base=HEAP,heap_length=u.heap_next-HEAP,stack_base=STACK,stack_length=STACK_SZ,native_body=N,native_motion=M,world=W,bss_base=0x7103e9e000,bss_length=0x5a00000-0x3e9e000,state=state,info=info,current=current,baseline=base)
  Path('analysis/completion/r8/physics_finalize_fixture.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
  for suffix,base_addr,n in [('heap',HEAP,u.heap_next-HEAP),('stack',STACK,STACK_SZ),('bss',0x7103e9e000,0x5a00000-0x3e9e000)]:Path('analysis/completion/r8/physics_finalize_'+suffix+'.bin').write_bytes(bytes(mu.mem_read(base_addr,n)))
  final_trace.append(dict(pc=hex(addr),state=hex(state),current=bytes(mu.mem_read(current,0x40)).hex(),baseline=bytes(mu.mem_read(base,0x40)).hex(),info=bytes(mu.mem_read(info,0x100)).hex(),native=bytes(mu.mem_read(M,0x80)).hex()))
 elif addr==0x7100a4be1c:
  info=mu.reg_read(UC_ARM64_REG_X24)
  final_trace.append(dict(pc=hex(addr),q4=fq(4),q5=fq(5),baseline150=struct.unpack('<4f',mu.mem_read(sp+0x150,16)),baseline160=struct.unpack('<4f',mu.mem_read(sp+0x160,16)),coefficients={hex(k):u.rf(info+k) for k in (0x10,0x74,0xb0,0xb4,0xb8,0xbc,0xc0)}))
 elif addr==0x7100a4c12c:
  final_trace.append(dict(pc=hex(addr),effective=fq(0),dt=struct.unpack('<4f',mu.mem_read(sp+0x160,16)),native=bytes(mu.mem_read(M,0x80)).hex()))
for pc in (0x7100a4b8c8,0x7100a4be1c,0x7100a4c12c):u.mu.hook_add(UC_HOOK_CODE,final_hook,begin=pc,end=pc)

trace=[]
for i in range(1):
 c=u.call(0x71009ce484,W,TI,TG,count=50000000)
 if c is None:c=run_graph()
 if c is None:errors.append(['collideGraphReset',u.call(0x71009d275c,TG)]);done.clear()
 s=u.call(0x71009cee34,W,TG,count=50000000) if c is None else 'collide failed'
 if s is None:s=run_graph()
 trace.append(dict(frame=i,errors=[c,s],position=[u.rf(N+0x30+j*4) for j in range(3)],com=struct.unpack('<ddd',u.mu.mem_read(M+0x10,24)),vel=[u.rf(M+0x60+j*4) for j in range(3)],hits=dict(hits)))
 if c or s:break
 errors.append(["graphReset",u.call(0x71009d275c,TG)]);done.clear()
r=dict(final_trace=final_trace,graphs=graphs,native_motion=bytes(u.mu.mem_read(M,0x80)).hex(),material=bytes(u.mu.mem_read(Mat,0x50)).hex(),scope=__doc__,errors=errors,trace=trace,hits=hits,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,os=u.os_calls)
Path('analysis/completion/r8/physics_finalize_capture_probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(frames=len(trace),hits=hits,null=r['null'],auto=r['auto'],faults=r['faults']),ensure_ascii=False))
