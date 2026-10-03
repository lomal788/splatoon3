"""Strict GOT reference scan: nearest GPR writer before LDR64 must be ADRP exact page.
Unlike xref8window, arbitrary register clobbers are rejected and long straight-line gaps retained.
"""
import json,struct
from pathlib import Path
import numpy as np
from capstone import *
from capstone.arm64 import *
BASE=0x7100000000;b=Path('extracted/exefs/main.reloc.img').read_bytes();w=np.frombuffer(b[:0x3e99000],dtype='<u4');md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);md.detail=True
GOT=0x57917d0;target=BASE+GOT;offset=GOT&4095
ix=np.nonzero(((w&0xffc00000)==0xf9400000)&(((w>>10)&4095)*8==offset))[0];out=[]
def regn(r):
 n=md.reg_name(r)
 if n in ('fp','lr'):return 29 if n=='fp' else 30
 return int(n[1:]) if len(n)>1 and n[0] in ('x','w') and n[1:].isdigit() else -1
for q in ix:
 pc=int(q)*4;rn=(int(w[q])>>5)&31;lo=max(pc-0x800,0);prev=None
 for a in range(pc-4,lo-1,-4):
  ins=next(md.disasm(b[a:a+4],BASE+a),None)
  if ins is None:continue
  _,wr=ins.regs_access()
  if rn in [regn(r) for r in wr]:prev=ins;break
 if prev is None or prev.mnemonic!='adrp' or prev.operands[1].imm+(offset)!=target:continue
 ins=next(md.disasm(b[pc:pc+4],BASE+pc));n=dict(pc=hex(BASE+pc),adrp=hex(prev.address),text=ins.mnemonic+' '+ins.op_str,following=[])
 for a in md.disasm(b[pc+4:pc+4+0x180],BASE+pc+4):
  n['following'].append(dict(pc=hex(a.address),text=a.mnemonic+' '+a.op_str))
  if a.mnemonic=='ret':break
 out.append(n)
Path('analysis/completion/r9/camera_posture_refs.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');
writers=[]
for row in out:
 pc=int(row['pc'],16);first=next(md.disasm(b[pc-BASE:pc-BASE+4],pc));aliases={regn(first.operands[0].reg):0}
 for i in md.disasm(b[pc-BASE+4:pc-BASE+4+0x180],pc+4):
  for op in i.operands:
   if op.type==ARM64_OP_MEM and regn(op.mem.base) in aliases and op.mem.disp+aliases[regn(op.mem.base)]==0 and i.mnemonic.startswith(('str','stur','stp')):writers.append(dict(got=row['pc'],pc=hex(i.address),text=i.mnemonic+' '+i.op_str))
  r,wri=i.regs_access();old=dict(aliases)
  for rr in wri:aliases.pop(regn(rr),None)
  if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[1].type==ARM64_OP_REG and regn(i.operands[1].reg) in old:aliases[regn(i.operands[0].reg)]=old[regn(i.operands[1].reg)]
  if i.mnemonic=='add' and len(i.operands)==3 and i.operands[1].type==ARM64_OP_REG and regn(i.operands[1].reg) in old and i.operands[2].type==ARM64_OP_IMM:aliases[regn(i.operands[0].reg)]=old[regn(i.operands[1].reg)]+i.operands[2].imm
  if not aliases:break
Path('analysis/completion/r9/camera_posture_writers.json').write_text(json.dumps(writers,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(references=len(out),writers=writers),indent=2))
