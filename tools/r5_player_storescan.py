"""r5 player: 오프셋 범위를 덮는 store 명령 전수 검색(capstone, 명령 단위).
사용: PY web/tools/r5_player_storescan.py <오프셋hex> [--lo 0x71..] [--hi 0x71..] [--load]
[Rn, #imm] 형식(부호 없는/부호 있는 즉치, 사전·사후 인덱스 제외)의 저장 폭이 오프셋을 덮으면 출력한다.
기준 레지스터가 무엇인지는 판단하지 않는다(호출부에서 판독 필요)."""
import argparse, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import load_img, BASE, TEXT_END
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
W = {'strb': 1, 'sturb': 1, 'strh': 2, 'sturh': 2}
ap = argparse.ArgumentParser()
ap.add_argument('off'); ap.add_argument('--lo', default='0x7100000000'); ap.add_argument('--hi', default=None)
ap.add_argument('--load', action='store_true', help='store 대신 load 검색')
a = ap.parse_args()
off = int(a.off, 16)
m = load_img()
lo = int(a.lo, 16); hi = int(a.hi, 16) if a.hi else BASE + TEXT_END
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
pat = re.compile(r'\[(\w+), #(-?0x[0-9a-f]+|-?\d+)\]$')
pre = ('ldr', 'ldur', 'ldp') if a.load else ('str', 'stur', 'stp')
mv = memoryview(m)
for addr in range(lo, hi, 4):
    w = int.from_bytes(mv[addr - BASE:addr - BASE + 4], 'little')
    # 빠른 거름: load/store 계열(op0 x1x0)
    if (w >> 25) & 0b0101 != 0b0100:
        continue
    for i in md.disasm(bytes(mv[addr - BASE:addr - BASE + 4]), addr):
        mn = i.mnemonic
        if not mn.startswith(pre):
            continue
        mm = pat.search(i.op_str)
        if not mm:
            continue
        imm = int(mm.group(2), 0)
        regs = i.op_str.split(',')
        r0 = regs[0].strip()
        if mn in W:
            width = W[mn]
        else:
            width = {'w': 4, 'x': 8, 's': 4, 'd': 8, 'q': 16, 'h': 2, 'b': 1}.get(r0[0], 4)
        n = 2 if mn.startswith(('stp', 'ldp')) else 1
        if imm <= off < imm + width * n:
            print(hex(addr), mn, i.op_str)
