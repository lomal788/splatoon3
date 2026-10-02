"""text 영역에서 32비트 상수(movz lo16 + movk hi16, 같은 레지스터, 근접 8명령)를 만드는 위치 찾기.
사용: PY web/tools/network_constscan.py 0xbc4e7627 [...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
from disasm import func_start


def find_const32(w, v):
    lo, hi = v & 0xFFFF, v >> 16
    out = []
    for sf in (0, 1):
        movz = (0x52800000 | (sf << 31)) | (lo << 5)
        movk = (0x72A00000 | (sf << 31)) | (hi << 5)
        cand = np.nonzero((w & 0xFFFFFFE0) == movz)[0]
        for i in cand:
            rd = int(w[i]) & 0x1F
            for k in range(1, 9):
                if i + k < len(w) and int(w[i + k]) == (movk | rd):
                    out.append(int(i) * 4)
                    break
    return out


def main():
    m = load_img()
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    for a in sys.argv[1:]:
        v = int(a, 16)
        hits = find_const32(w, v)
        print(f"{v:#010x}: " + " ".join(f"{BASE + h:#x}(f {BASE + (func_start(m, h, 0x20000) or 0):#x})" for h in hits))


if __name__ == "__main__":
    main()
