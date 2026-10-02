"""r6 player: 큰 오프셋(>0xfff) 필드 쓰기 검색. mov wN,#off (또는 add xR, xB, #off 형태) 뒤 12명령 안의
str/strb/strh/stp ..., [xK, xN] / [xR, #imm] 를 찾는다. 기준 레지스터의 정체는 판단하지 않는다.
사용: PY web/tools/r6_player_regoffscan.py <오프셋hex> [--lo] [--hi] [--load]"""
import argparse, re, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import load_img, BASE, TEXT_END
import numpy as np
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
ap = argparse.ArgumentParser(); ap.add_argument('off'); ap.add_argument('--lo', default='0x7100000000'); ap.add_argument('--hi', default=None); ap.add_argument('--load', action='store_true')
a = ap.parse_args(); off = int(a.off, 16)
m = load_img(); lo = int(a.lo, 16) - BASE; hi = (int(a.hi, 16) - BASE) if a.hi else TEXT_END
w = np.frombuffer(bytes(m[lo:hi - (hi - lo) % 4]), dtype='<u4')
# movz w/x, #imm16 (shift 0): sf x 10100101 00 imm16 Rd -> mask 0x7fe00000==0x52800000
cand = np.nonzero(((w & 0x7FFFFFE0) == (0x52800000 | ((off & 0xFFFF) << 5))))[0]
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
ops = ('ldr', 'ldrb', 'ldrh', 'ldrsw', 'ldp', 'ldur') if a.load else ('str', 'strb', 'strh', 'stp', 'stur')
for i in cand:
    pc = BASE + lo + 4 * int(i)
    rd = int(w[i] & 0x1F)
    regs = {f'x{rd}', f'w{rd}'}
    addr_regs = set()
    for j in range(1, 14):
        if i + j >= len(w):
            break
        p2 = pc + 4 * j
        ins = next(md.disasm(struct.pack('<I', int(w[i + j])), p2), None)
        if ins is None:
            continue
        s = ins.op_str
        mm = re.search(r'\[(\w+), (\w+)\]', s)
        if mm and mm.group(2) in regs and ins.mnemonic in ops:
            print(f'{p2:#x}  {ins.mnemonic} {s}   (mov@{pc:#x})')
        ma = re.match(r'(x\d+), (x\d+), (x\d+)$', s)
        if ins.mnemonic == 'add' and ma and (ma.group(3) in regs or ma.group(2) in regs):
            addr_regs.add(ma.group(1))
        mb = re.search(r'\[(x\d+)(?:, #(-?0x[0-9a-f]+|\d+))?\]', s)
        if mb and mb.group(1) in addr_regs and ins.mnemonic in ops:
            print(f'{p2:#x}  {ins.mnemonic} {s}   (add base, mov@{pc:#x})')
