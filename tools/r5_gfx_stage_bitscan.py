"""오프셋 X 의 32/8비트 필드에 비트를 넣는(orr/bfi/and 후 str) 명령 근접 패턴 스캔.
사용: PY web/tools/r5_gfx_stage_bitscan.py <오프셋16진> <시작> <끝> [창=4]
출력: str 주소, 앞 창 안의 orr/and/bfi/bfxil 명령 텍스트
"""
import sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
B = 0x7100000000
off = int(sys.argv[1], 16); s = int(sys.argv[2], 16); e = int(sys.argv[3], 16)
W = int(sys.argv[4]) if len(sys.argv) > 4 else 4
img = open(IMG, 'rb').read()
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM); md.detail = True; md.skipdata = True
prev = []
for ins in md.disasm(img[s - B:e - B], s):
    if ins.mnemonic in ('str', 'strb', 'sturb', 'stur') and ins.operands and ins.operands[-1].type == ARM64_OP_MEM and ins.operands[-1].mem.disp == off:
        bits = [p for p in prev[-W:] if p[1].split()[0] in ('orr', 'and', 'bfi', 'bfxil', 'eor', 'bic')]
        if bits:
            print(hex(ins.address), ins.mnemonic, ins.op_str, '|', ' ; '.join('%s %s' % (hex(a), t) for a, t in bits))
    prev.append((ins.address, ins.mnemonic + ' ' + ins.op_str))
    if len(prev) > 16: prev.pop(0)
