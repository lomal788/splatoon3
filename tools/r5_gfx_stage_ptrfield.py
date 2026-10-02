"""ldr xN,[xM,#A] 뒤 창 안에서 str ?, [xN,#B] (A 객체 포인터의 B 필드 쓰기) 를 찾는다.
사용: PY web/tools/r5_gfx_stage_ptrfield.py <A16진> <B16진> <시작> <끝> [창=8]
"""
import sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM, ARM64_OP_REG
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
B = 0x7100000000
A = int(sys.argv[1], 16); F = int(sys.argv[2], 16); s = int(sys.argv[3], 16); e = int(sys.argv[4], 16)
W = int(sys.argv[5]) if len(sys.argv) > 5 else 8
img = open(IMG, 'rb').read()
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM); md.detail = True; md.skipdata = True
pend = []
for ins in md.disasm(img[s - B:e - B], s):
    if ins.id == 0:
        pend = []; continue
    ops = ins.operands
    pend = [(a, r, n - 1) for a, r, n in pend if n > 0]
    if ins.mnemonic.startswith('st') and ops and ops[-1].type == ARM64_OP_MEM and ops[-1].mem.disp == F:
        for a, r, n in pend:
            if ops[-1].mem.base == r:
                print(hex(a), '->', hex(ins.address), ins.mnemonic, ins.op_str)
    if ins.mnemonic == 'ldr' and len(ops) == 2 and ops[1].type == ARM64_OP_MEM and ops[1].mem.disp == A and ops[0].type == ARM64_OP_REG:
        pend.append((ins.address, ops[0].reg, W))
    elif ops and ops[0].type == ARM64_OP_REG and not ins.mnemonic.startswith(('st', 'cmp', 'tst', 'cb', 'b')):
        pend = [(a, r, n) for a, r, n in pend if r != ops[0].reg]
