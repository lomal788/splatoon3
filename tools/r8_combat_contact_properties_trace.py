"""Trace original pair-cache c0/c8 writer using already-built r8 native scene fixture; no independent equation or solver completion claim."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
s=Path('web/tools/r8_camweapon_contact_bias_producer.py').read_text(encoding='utf-8').split('fixture=json.loads')[0]
ns={'__file__':str(Path('web/tools/r8_camweapon_contact_bias_producer.py').resolve()),'__name__':'r8_properties_fixture'};exec(compile(s,'fixture','exec'),ns)
ns=ns['ns'];u=ns['u'];mu=u.mu
j=json.loads(Path('analysis/completion/r8/contact_bias_producer.json').read_text(encoding='utf-8'));ss=next(x for x in j['samples'] if int(x['pc'],16)==0x7100a16d14);p=ss['regs']['x21'];writes=[]
def write(mu,access,addr,size,value,user):
 writes.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),addr=hex(addr),offset=addr-p,size=size,value=hex(value&((1<<(size*8))-1)),regs={"x"+str(i):mu.reg_read(globals()["UC_ARM64_REG_X"+str(i)]) for i in range(31)},q={"q"+str(i):hex(mu.reg_read(globals()["UC_ARM64_REG_Q"+str(i)])) for i in range(32)}))
class Stop(Exception):pass
def stop(mu,addr,size,user):raise Stop()
mu.hook_add(UC_HOOK_MEM_WRITE,write,begin=p+0xc0,end=p+0xdf);mu.hook_add(UC_HOOK_CODE,stop,begin=0x7100a181fc,end=0x7100a181fc)
reason=None
try:
 c=u.call(0x71009ce484,ns['W'],ns['TI'],ns['TG'],count=50000000)
 if c is None:c=ns['run_graph']()
 if c is None:u.call(0x71009d275c,ns['TG']);ns['done'].clear()
 if c is None:c=u.call(0x71009cee34,ns['W'],ns['TG'],count=50000000)
 if c is None:c=ns['run_graph']()
 reason=c
except Stop:reason='stop first original kernel entry'
out=dict(pointer=hex(p),writes=writes,reason=reason,final=bytes(mu.mem_read(p+0xc0,32)).hex(),null=u.null_calls,auto=u.auto_pages,faults=u.faults,scope=__doc__)
Path('analysis/completion/r8/contact_properties_trace.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='writes'}));print([(x['pc'],x['offset'],x['size'],x['value']) for x in writes])
