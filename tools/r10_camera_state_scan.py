"""Bounded ARM64 field-alias candidates. Candidates are not type proofs."""
from pathlib import Path
import json, struct, sys
import numpy as np
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_REG, ARM64_OP_IMM, ARM64_OP_MEM
sys.path.insert(0,str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img

OUT=Path('analysis/camera_100_r10/state');OUT.mkdir(parents=True,exist_ok=True)
m=load_img(); words=np.frombuffer(m[:TEXT_END],dtype='<u4')
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);md.detail=True
targets={0x9314,0x9315,0x9318,0x9330,0x9304,0x930c,0x9210,0x9212,0x9213,0x1918}
# ADD/SUB imm64 with one of the large field page bases.
starts=np.flatnonzero(((words&0x7f000000)==0x11000000)|((words&0x7f800000)==0x52800000))
rows=[]
def reg(i,r):
 s=i.reg_name(r)
 return 'x'+s[1:] if s.startswith('w') and s not in ['wzr','wsp'] else s
for j in starts:
 w=int(words[j]);is_mov=(w&0x7f800000)==0x52800000
 imm=((w>>5)&65535)<<(((w>>21)&3)*16) if is_mov else ((w>>10)&4095)<<(12 if w&(1<<22) else 0)
 if not (0x9200<=imm<=0x9320 or imm in [0x9000,0x1918,0x12e5,0x12f9,0x13e9,0x13e7]):continue
 # Roots are unknown object addresses; linear offsets are tracked only.
 state={};text=[]
 for i in md.disasm(m[j*4:j*4+256],BASE+int(j)*4):
  ops=i.operands;text.append(f'{i.address:#x} {i.mnemonic} {i.op_str}')
  for o in ops:
   if o.type==ARM64_OP_MEM:
    base=reg(i,o.mem.base)
    idx=state.get(reg(i,o.mem.index),0) if o.mem.index else 0
    off=state.get(base,0)+o.mem.disp+idx
    if off in targets:
     rows.append(dict(pc=hex(i.address),field=hex(off),seed=hex(BASE+int(j)*4),instruction=text[-1],access='store' if i.mnemonic.startswith('st') else 'load',trace=text.copy()))
  if i.mnemonic in ['add','sub'] and len(ops)==3 and ops[0].type==ARM64_OP_REG and ops[1].type==ARM64_OP_REG and ops[2].type==ARM64_OP_IMM:
   a=reg(i,ops[0].reg);b=reg(i,ops[1].reg);v=ops[2].imm<<ops[2].shift.value
   state[a]=state.get(b,0)+(v if i.mnemonic=='add' else -v)
  elif i.mnemonic in ['add','sub'] and len(ops)==3 and ops[0].type==ARM64_OP_REG and ops[1].type==ARM64_OP_REG and ops[2].type==ARM64_OP_REG:
   a=reg(i,ops[0].reg);b=reg(i,ops[1].reg);c=reg(i,ops[2].reg)
   v=state.get(c,0)<<ops[2].shift.value
   state[a]=state.get(b,0)+(v if i.mnemonic=='add' else -v)
  elif i.mnemonic in ['mov','movz'] and len(ops)==2 and ops[0].type==ARM64_OP_REG:
   if ops[1].type==ARM64_OP_REG:state[reg(i,ops[0].reg)]=state.get(reg(i,ops[1].reg),0)
   elif ops[1].type==ARM64_OP_IMM:state[reg(i,ops[0].reg)]=ops[1].imm<<ops[1].shift.value
  else:
   _,writes=i.regs_access()
   for r in writes:state.pop(reg(i,r),None)
  if i.mnemonic in ['ret','b','br']:break
dedup={(r['pc'],r['field']):r for r in rows}
out=dict(scope='linear 256B ADD/SUB field alias candidates, unknown roots, not exhaustive field or runtime proof',rows=list(dedup.values()))
(OUT/'alias_candidates.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
for r in out['rows']:print(r['pc'],r['field'],r['access'],r['instruction'])
