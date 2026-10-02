"""ADRP page + (add|ldr) imm 로 특정 주소를 만드는 명령 전수 검색(창 넓게). xref.py 보다 느리지만 창이 넓다.
사용: PY web/tools/r6_gfx_stage_adrpscan.py <주소> [창=64]
"""
import sys
import numpy as np
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
m = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
BASE = 0x7100000000; TEXT_END = 0x3E9DF50
tgt = int(sys.argv[1], 16); W = int(sys.argv[2]) if len(sys.argv) > 2 else 64
w = np.frombuffer(m[:TEXT_END - (TEXT_END & 3)], dtype=np.uint32)
isadrp = (w & 0x9F000000) == 0x90000000
idx = np.nonzero(isadrp)[0]
page = tgt & ~0xFFF; lo12 = tgt & 0xFFF
for i in idx:
    ww = int(w[i]); pc = BASE + int(i) * 4
    imm = ((ww >> 29) & 3) | (((ww >> 5) & 0x7FFFF) << 2)
    if imm & (1 << 20): imm -= 1 << 21
    if (pc & ~0xFFF) + (imm << 12) != page: continue
    rd = ww & 31
    for j in range(i + 1, min(i + W, len(w))):
        x = int(w[j])
        if (x & 0xFF800000) == 0x91000000 and ((x >> 5) & 31) == rd and ((x >> 10) & 0xFFF) == lo12 and not (x >> 22) & 1:
            print(hex(BASE + j * 4), "add"); break
        if (x & 0xFFC00000) == 0xF9400000 and ((x >> 5) & 31) == rd and ((x >> 10) & 0xFFF) * 8 == lo12:
            print(hex(BASE + j * 4), "ldr"); break
