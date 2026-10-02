"""[life] 32비트 상수(예: 플레이어 메시지 ID 0x6c2b6a05) 구성 위치 찾기.
사용: PY web/tools/life_msgscan.py <u32값...>
MOVZ lo16 + MOVK hi16(lsl16) 가 같은 레지스터에 6명령 안에 오는 곳과, 함수 시작을 출력.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
from network_fstart import starts, fstart

m = load_img()
s = starts(m)
w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
for a in sys.argv[1:]:
    v = int(a, 16)
    lo, hi = v & 0xFFFF, v >> 16
    mz = np.nonzero(((w & 0x7FE00000) == 0x52800000) & (((w >> 5) & 0xFFFF) == lo))[0]
    mk = set(np.nonzero(((w & 0x7FE00000) == 0x72A00000) & (((w >> 5) & 0xFFFF) == hi))[0].tolist())
    for i in mz:
        rd = int(w[i]) & 31
        for j in range(i + 1, i + 7):
            if j in mk and (int(w[j]) & 31) == rd:
                ad = BASE + int(i) * 4
                f = fstart(s, int(i) * 4)
                print(f"{v:#x} @ {ad:#x} func {BASE + f:#x} +{int(i) * 4 - f:#x}")
                break
