"""`add xD, xN, #imm` (64bit, shift 0) 전역 스캔 → 함수별. 구조체 하위 블록 포인터를 넘기는 곳 찾기.
사용: PY web/tools/gauge_addscan.py 0xbd4 [0xbe4 ...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_fstart import fstart, starts
from xref import BASE, TEXT_END, load_img

m = load_img()
w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
s = starts(m)
for q in sys.argv[1:]:
    imm = int(q, 16)
    idx = np.nonzero((w & 0xFFFFFC00) == (0x91000000 | (imm << 10)))[0]
    print(f"== add #{q}: {len(idx)}")
    for i in idx:
        a = int(i) * 4
        ins = int(w[i])
        print(f"  {BASE + a:#x} x{ins & 31} = x{(ins >> 5) & 31} + {q}  func {BASE + fstart(s, a):#x}")
