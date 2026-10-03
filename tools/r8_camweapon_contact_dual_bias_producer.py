"""Trace original native Jacobian row producer before first kernel; no solver bypass.
Reuse collision native scene constructor/graph fixture as supplied in r8.
"""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
s=Path('web/tools/r8_physics_contact_kinematic_probe.py').read_text(encoding='utf8').split('\ntrace=[]')[0]
a=s.index('def hit(');b=s.index('\ndef cap(',a);s=s[:a]+s[b:]
ns={'__name__':'r8_bias_native','__file__':str(Path('web/tools/r8_physics_contact_kinematic_probe.py').resolve())};exec(compile(s,'r8_bias_native','exec'),ns)
u=ns['u'];mu=u.mu
fixture=json.loads(Path('analysis/completion/r8/contact_dual_kernel_replay.json').read_text(encoding='utf8'));row=int(fixture['samples'][0]['regs']['x12'])-0x10;writes=[];samples=[]
def sample(mu,addr,size,user):
 regs={"x"+str(i):mu.reg_read(globals()["UC_ARM64_REG_X"+str(i)]) for i in range(31)};qs={"q"+str(i):hex(mu.reg_read(globals()["UC_ARM64_REG_Q"+str(i)])) for i in range(32)}
 mem={hex(v):bytes(mu.mem_read(v,0xe0)).hex() for k,v in regs.items() if k in ["x19","x20","x21","x24","x26"]}
 samples.append(dict(pc=hex(addr),regs=regs,qs=qs,mem=mem))
for pc in [0xa165a0,0xa165ec,0xa16670,0xa16684,0xa166ac,0xa174f0,0xa1752c]:mu.hook_add(UC_HOOK_CODE,sample,begin=0x7100000000+pc,end=0x7100000000+pc)
def write(mu,access,addr,size,value,user):
 regs={"x"+str(i):mu.reg_read(globals()["UC_ARM64_REG_X"+str(i)]) for i in range(31)};qs={"q"+str(i):hex(mu.reg_read(globals()["UC_ARM64_REG_Q"+str(i)])) for i in range(32)}
 writes.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),addr=hex(addr),offset=addr-row,size=size,value=hex(value&((1<<(size*8))-1)),regs=regs,qs=qs))
class FirstKernel(Exception):pass
def stop(mu,addr,size,user):raise FirstKernel()
mu.hook_add(UC_HOOK_MEM_WRITE,write,begin=row-0x40,end=row+0x1f)
mu.hook_add(UC_HOOK_CODE,stop,begin=0x7100a181fc,end=0x7100a181fc)
reason=None
try:
 c=u.call(0x71009ce484,ns['W'],ns['TI'],ns['TG'],count=50000000)
 if c is None:c=ns['run_graph']()
 if c is None:u.call(0x71009d275c,ns['TG']);ns['done'].clear()
 if c is None:c=u.call(0x71009cee34,ns['W'],ns['TG'],count=50000000)
 if c is None:c=ns['run_graph']()
 reason=c
except FirstKernel:reason='explicit stop at first original0a181fc entry after all Jacobian generation'
out={'row':hex(row),'row_bytes':bytes(mu.mem_read(row,0x20)).hex(),'row_f32':struct.unpack('<8f',mu.mem_read(row,0x20)),'reason':reason,'writes':writes,'samples':samples,'null':u.null_calls,'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed,'boundary':'capsulefloor and human(.7,.6),mass100/inertia0/friction0 original r8 scene;original scene/graph constructors reused,stopfirstkernel, no normal equation calculated here'}
Path('analysis/completion/r8/contact_dual_bias_producer.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['writes','plt','samples']},indent=2));print('writes',[(w['pc'],w['offset'],w['size'],w['value']) for w in writes])
