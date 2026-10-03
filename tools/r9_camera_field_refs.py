from pathlib import Path
import numpy as np,json
from capstone import *
from capstone.arm64 import *
B=0x7100000000;b=Path('extracted/exefs/main.reloc.img').read_bytes();w=np.frombuffer(b[:0x3e99000],dtype='<u4');m=Cs(CS_ARCH_ARM64,CS_MODE_ARM);m.detail=True
fields={0x9210,0x9211,0x9212,0x9314,0x9315,0x143d0,0x1918};refs=[]
# ADD xD,xN,immediate; keep true effective immediate with LSL12.
ix=np.nonzero((w&0xff000000)==0x91000000)[0]
def R(r):
 s=m.reg_name(r)
 if s in ('fp','lr'):return 29 if s=='fp' else 30
 return int(s[1:]) if len(s)>1 and s[0] in 'xw' and s[1:].isdigit() else -1
for q in ix:
 pc=int(q)*4;k=int(w[q]);delta=((k>>10)&4095)*(4096 if k&(1<<22) else 1)
 if delta not in {0x9000,0x14000,0x1000,0x143d0,0x9210,0x9212,0x9314,0x1918}:continue
 aliases={k&31:delta};seed=next(m.disasm(b[pc:pc+4],B+pc));
 for i in m.disasm(b[pc+4:pc+4+0x400],B+pc+4):
  for op in i.operands:
   if op.type==ARM64_OP_MEM and R(op.mem.base) in aliases and aliases[R(op.mem.base)]+op.mem.disp in fields:
    if i.mnemonic.startswith(('str','stur','stp','st1')):refs.append(dict(seed=hex(B+pc),seed_op=seed.op_str,pc=hex(i.address),field=hex(aliases[R(op.mem.base)]+op.mem.disp),text=i.mnemonic+' '+i.op_str))
  old=dict(aliases)
  if i.mnemonic in ('bl','blr'):
   for r in range(19):aliases.pop(r,None)
  else:
   _,wr=i.regs_access()
   for r in wr:aliases.pop(R(r),None)
   if i.mnemonic=='add' and len(i.operands)==3 and i.operands[1].type==ARM64_OP_REG and R(i.operands[1].reg) in old and i.operands[2].type==ARM64_OP_IMM:aliases[R(i.operands[0].reg)]=old[R(i.operands[1].reg)]+i.operands[2].imm*(1<<i.operands[2].shift.value)
   if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[1].type==ARM64_OP_REG and R(i.operands[1].reg) in old:aliases[R(i.operands[0].reg)]=old[R(i.operands[1].reg)]
  if not aliases or i.mnemonic=='ret':break
uniq={z['pc']:z for z in refs};out=list(uniq.values());Path('analysis/completion/r9/camera_field_writers.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))