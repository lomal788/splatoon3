"""r8 native contact-kernel fixture replay for independent equation investigation only.
Reuses collision agent's live original first-kernel fixture; no new wholePhysics proof.
"""
import json,struct
from pathlib import Path
from collections import Counter
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import UC_HOOK_CODE,UC_HOOK_BLOCK,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC,init_native,make_world
from r6_player_uc import BASE
J=Path('analysis/completion/r8/physics_kernel_fixture.json');f=json.loads(J.read_text(encoding='utf8'));u=PhysicsUC();init_errors=[];mu=u.mu
mu.mem_write(f['heap_base'],Path('analysis/completion/r8/physics_kernel_heap.bin').read_bytes());mu.mem_write(f['stack_base'],Path('analysis/completion/r8/physics_kernel_stack.bin').read_bytes())
mu.mem_write(f['bss_base'],Path('analysis/completion/r8/physics_kernel_bss.bin').read_bytes())
for name,v in f['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+name.upper()],v)
blocks=[];writes=[];samples=[]
def sample(mu,a,sz,z):
 regs={"x"+str(i):mu.reg_read(globals()["UC_ARM64_REG_X"+str(i)]) for i in range(29)};qs={"q"+str(i):struct.unpack("<4f",mu.reg_read(globals()["UC_ARM64_REG_Q"+str(i)]).to_bytes(16,"little")) for i in range(32)}
 row=regs["x12"];lam=regs["x13"];samples.append(dict(pc=hex(a),regs=regs,qs=qs,row=bytes(mu.mem_read(row,32)).hex() if a==BASE+0xa1a98c else None,lambda_value=u.rf(lam) if a in [BASE+0xa1a98c,BASE+0xa1a940] else None))
for p in [0xa1a98c,0xa1a940,0xa1a960,0xa1abd0,0xa1b46c]:mu.hook_add(UC_HOOK_CODE,sample,begin=BASE+p,end=BASE+p)
def block(mu,a,s,z):blocks.append((a,s))
def write(mu,access,a,s,v,z):writes.append([mu.reg_read(UC_ARM64_REG_PC),a,s,v])
mu.hook_add(UC_HOOK_BLOCK,block)
mu.hook_add(UC_HOOK_MEM_WRITE,write,begin=f['heap_base'],end=f['heap_base']+f['heap_length']-1)
M=f['native_motion'];before=bytes(mu.mem_read(M,0x80));error=None
try:mu.emu_start(BASE+0xa181fc,f['regs']['x30'],count=10000000)
except Exception as ex:error=str(ex)
counts=Counter(blocks);cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM);uniq=[]
for (a,size),n in counts.items():
 uniq.append({'pc':hex(a),'count':n,'asm':[[hex(i.address),i.mnemonic,i.op_str] for i in cs.disasm(bytes(mu.mem_read(a,size)),a)]})
after=bytes(mu.mem_read(M,0x80));out={'scope':__doc__,'input_regs':f['regs'],'native_init_errors':init_errors,'error':error,'stopped_pc':hex(mu.reg_read(UC_ARM64_REG_PC)),'return_pc':hex(f['regs']['x30']),'native_motion_before':before.hex(),'native_motion_after':after.hex(),'native_vel_before':struct.unpack('<fff',before[0x60:0x6c]),'native_vel_after':struct.unpack('<fff',after[0x60:0x6c]),'samples':samples,'blocks':uniq,'heapwrites':[[hex(p),hex(a),s,hex(v&((1<<(8*s))-1))] for p,a,s,v in writes],'null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed}
Path('analysis/completion/r8/contact_kernel_replay.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['blocks','heapwrites','input_regs','scope','samples']},indent=2));print('blocks',len(uniq),'heapwrites',len(writes))
