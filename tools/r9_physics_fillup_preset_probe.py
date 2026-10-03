"""Whole original PhiveConfig loader with raw original BYML; probes FillUpPlayer mask registration, not scene instantiation."""
import struct,json,hashlib
from pathlib import Path
from r8_physics_native_uc import PhysicsUC
from spl_data import unzs,byml
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
u=PhysicsUC();u.wq(0x71059975c0,0);raw=unzs(Path('extracted/romfs/Phive/Config/PhiveConfig.byml.zs').read_bytes());data=byml(raw);P=u.alloc(len(raw));u.mu.mem_write(P,raw);CF=u.alloc(0x8000);trace=[];allocs=[];Heap=u.alloc(0x100);HeapVT=u.alloc(0x100);Alloc=u.alloc(16);u.mu.mem_write(Alloc,bytes.fromhex("c0035fd6"));u.wq(Heap,HeapVT);u.wq(HeapVT+0x30,Alloc);HeapState=u.alloc(16);u.mu.mem_write(HeapState,bytes.fromhex("c0035fd6"));u.wq(HeapVT+0xb0,HeapState);Parent=u.alloc(0x100);u.wq(Parent,HeapVT);u.wq(Heap+0x38,Parent)
def boundary(mu,a,size,arg):
 if a==0x7103513f3c:ret=Heap;allocs.append(dict(kind="configHeapCreate",size=mu.reg_read(UC_ARM64_REG_X0)))
 elif a==HeapState:ret=0;allocs.append(dict(kind="heapStateQuery",object=hex(mu.reg_read(UC_ARM64_REG_X0))))
 else:
  n=mu.reg_read(UC_ARM64_REG_X1);al=mu.reg_read(UC_ARM64_REG_X2);ret=u.alloc(n,max(16,abs(al if al<1<<31 else al-(1<<32))));allocs.append(dict(kind="heapAllocate",size=n,alignment=al))
 mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
u.mu.hook_add(UC_HOOK_CODE,boundary,begin=0x7103513f3c,end=0x7103513f3c);u.mu.hook_add(UC_HOOK_CODE,boundary,begin=Alloc,end=Alloc);u.mu.hook_add(UC_HOOK_CODE,boundary,begin=HeapState,end=HeapState)
def capture(mu,a,size,arg):
 if a==0x7103b13cb0:
  trace.append(dict(writer=hex(a),descriptor=hex(mu.reg_read(UC_ARM64_REG_X28)),registers=[hex(mu.reg_read(r)) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X20,UC_ARM64_REG_X21,UC_ARM64_REG_X22,UC_ARM64_REG_X23,UC_ARM64_REG_X24,UC_ARM64_REG_X25)],mask=hex(mu.reg_read(UC_ARM64_REG_X23))))
u.mu.hook_add(UC_HOOK_CODE,capture,begin=0x7103b13cb0,end=0x7103b13cb0);e=u.call(0x7103b0f3d8,CF,P,0,count=30000000)
out=dict(scope=__doc__,error=e,config_sha256=hashlib.sha256(raw).hexdigest(),CF=hex(CF),config_memory=bytes(u.mu.mem_read(CF,0x400)).hex(),tag_count=u.r32(CF+0x80),tag_values=[hex(u.rq(u.rq(CF+0x88)+8*i)) for i in range(min(u.r32(CF+0x80),100))],allocator_boundary=allocs,preset_memory=bytes(u.mu.mem_read(u.rq(CF+0x2b8),min(len(data['MaterialPresetCollection'])*128,0x5000))).hex() if u.rq(CF+0x2b8) else None,trace=trace,runtime=dict(null={str(k):v for k,v in u.null_calls.items()},nullwrite={str(k):v for k,v in u.null_writes.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used));Path('analysis/completion/r9/physics_fillup_preset_probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ('config_memory','preset_memory','trace','allocator_boundary','tag_values')},indent=2));print('trace_count',len(trace),trace[:1])
if e or u.null_calls or u.auto_pages or u.faults:raise SystemExit(1)
