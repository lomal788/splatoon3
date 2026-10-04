"""Clobber-aware audit of literal ADRP/GOT NVN API references.

This is a bounded static audit, not proof about runtime pointer arithmetic,
private command encoding, NVN driver defaults, or hardware framebuffer state.
"""
import json
import sys
import numpy as np
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import xref
B=xref.BASE;m=xref.load_img();idx=xref.load_idx();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);md.detail=True
def alias(n):return 'x'+n[1:] if n.startswith('w') else n
def validate(pc,target):
    ins=list(md.disasm(m[max(0,pc-32):pc+4],B+max(0,pc-32)))
    last=ins[-1]
    good=[]
    for i,a in enumerate(ins[:-1]):
        if a.mnemonic!='adrp':continue
        rd=alias(a.reg_name(a.operands[0].reg));page=a.operands[1].imm
        mem=[p for p in last.operands if p.type==3]
        if not mem or alias(last.reg_name(mem[0].mem.base))!=rd or page+mem[0].mem.disp!=B+target:continue
        clobber=[]
        for z in ins[i+1:-1]:
            if rd in [alias(z.reg_name(r)) for r in z.regs_access()[1]]:clobber.append(hex(z.address))
        good.append({'adrp':hex(a.address),'base':rd,'clobbers':clobber})
    return good
rows=[]
for name,got,cell in [('SetViewportSwizzles',0x577a048,0x57d6088),('SetViewport',0x577a040,0x57d6078),('SetScissor',0x5779440,0x57d6090),('QueuePresentTexture',0x5779670,0x57d5538),('WindowSetCrop',0x5779710,0x57d55d8)]:
    refs=[]
    for pc,kind in sorted(set(xref.refs_to(got,idx))):
        v=validate(pc,got);ins=next(md.disasm(m[pc:pc+4],B+pc))
        refs.append({'pc':hex(B+pc),'insn':ins.mnemonic+' '+ins.op_str,'candidates':v,'accepted_literal':any(not z['clobbers'] for z in v)})
    rows.append({'api':name,'got':hex(B+got),'function_pointer_cell':hex(B+cell),'refs':refs})
out={'scope':'main xref ADPR plus unsigned memory reference within eight instructions with register clobber audit','limitation':'bounded literal reference audit; no runtime arithmetic, STP/aliases, inline NVN private command encodings or driver/default swizzle proof','rows':rows}
# Independent longer scan for swizzle: every ADRP to its GOT page, walk to
# same-register clobber / branch / max128 instructions, rather than xref's 8.
w=np.frombuffer(m[:xref.TEXT_END & ~3],dtype='<u4')
ii=np.nonzero((w&0x9f000000)==0x90000000)[0]
aa=w[ii].astype(np.int64);imm=(((aa>>5)&0x7ffff)<<2)|((aa>>29)&3)
imm=np.where(imm&(1<<20),imm-(1<<21),imm)
page=((ii.astype(np.int64)*4)&~0xfff)+(imm<<12)
ad=ii[page==0x577a000]*4
longrefs=[]
for pc in ad:
    seq=list(md.disasm(m[int(pc):int(pc)+512],B+int(pc)))
    first=seq[0];rd=alias(first.reg_name(first.operands[0].reg))
    for n,z in enumerate(seq[1:],1):
        for op in z.operands:
            if op.type==3 and alias(z.reg_name(op.mem.base))==rd and op.mem.disp==0x48:
                longrefs.append({'adrp':hex(first.address),'pc':hex(z.address),'distance_instructions':n,'insn':z.mnemonic+' '+z.op_str})
        if rd in [alias(z.reg_name(r)) for r in z.regs_access()[1]] or z.mnemonic in ['b','bl','br','blr','ret']:break
out['swizzle_long_literal_scan']={'matching_page_adrps':len(ad),'memory_refs':longrefs,'scope':'all main ADRPs to577a000, direct base+48 until base clobber/branch or128 instructions','limitation':'no aliases/arithmetic or path-sensitive flow; does not establish native NVN swizzle defaults or private command packet contents'}
(ROOT/'analysis/camera_100_r10/posture/nvn_literal_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'api_counts':[{'api':r['api'],'accepted_count':sum(v['accepted_literal'] for v in r['refs']),'rejected_count':sum(not v['accepted_literal'] for v in r['refs'])} for r in rows], 'swizzle_long_literal_scan':out['swizzle_long_literal_scan']}))
