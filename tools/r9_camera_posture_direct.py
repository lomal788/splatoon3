from pathlib import Path
import numpy as np,json
from capstone import *
from capstone.arm64 import *
B=0x7100000000; T=B+0x5997898;b=Path('extracted/exefs/main.reloc.img').read_bytes();w=np.frombuffer(b[:0x3e99000],dtype='<u4');m=Cs(CS_ARCH_ARM64,CS_MODE_ARM);m.detail=True
ix=np.nonzero((w&0x9f000000)==0x90000000)[0]; refs=[];pages=0
def R(r):
 s=m.reg_name(r)
 if s in ('fp','lr'):return 29 if s=='fp' else 30
 return int(s[1:]) if len(s)>1 and s[0] in 'xw' and s[1:].isdigit() else -1
for q in ix:
 pc=int(q)*4;k=int(w[q]);im=(((k>>5)&0x7ffff)<<2)|((k>>29)&3);im=im-(1<<21) if im&(1<<20) else im
 pg=((B+pc)&~4095)+im*4096
 if pg!=(T&~4095):continue
 pages+=1;aliases={k&31:pg}
 for i in m.disasm(b[pc+4:pc+4+0x300],B+pc+4):
  for op in i.operands:
   if op.type==ARM64_OP_MEM and R(op.mem.base) in aliases and aliases[R(op.mem.base)]+op.mem.disp==T:refs.append(dict(adrp=hex(B+pc),pc=hex(i.address),text=i.mnemonic+' '+i.op_str,kind='memory'))
  old=dict(aliases)
  if i.mnemonic in ('bl','blr'):
   for r,v in old.items():
    if r<8 and v==T:refs.append(dict(adrp=hex(B+pc),pc=hex(i.address),text=i.mnemonic+' '+i.op_str,kind='call',arg=r))
   for r in range(19):aliases.pop(r,None)
  else:
   _,wr=i.regs_access()
   for r in wr:aliases.pop(R(r),None)
   if i.mnemonic=='add' and len(i.operands)==3 and i.operands[1].type==ARM64_OP_REG and R(i.operands[1].reg) in old and i.operands[2].type==ARM64_OP_IMM:aliases[R(i.operands[0].reg)]=old[R(i.operands[1].reg)]+i.operands[2].imm
   if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[1].type==ARM64_OP_REG and R(i.operands[1].reg) in old:aliases[R(i.operands[0].reg)]=old[R(i.operands[1].reg)]
  if not aliases or i.mnemonic=='ret':break
Path('analysis/completion/r9/camera_posture_direct_refs.json').write_text(json.dumps(dict(pages=pages,refs=refs),indent=2)+'\n',encoding='utf8');print(json.dumps(dict(pages=pages,refs=refs)))