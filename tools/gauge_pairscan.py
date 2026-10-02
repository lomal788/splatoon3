"""LDR X 포인터 로드 후 근처에서 그 레지스터 기준 필드 접근 찾기.
사용: PY web/tools/gauge_pairscan.py <포인터오프셋> <필드오프셋> [--win 12] [--store]
예: 0x450 0x140  → ldr xN,[xM,#0x450] ... str/ldr ?, [xN,#0x140]
"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_fstart import fstart, starts
from xref import BASE, TEXT_END, load_img
from gauge_fieldscan import UOFF

ap = argparse.ArgumentParser()
ap.add_argument("ptr"); ap.add_argument("field")
ap.add_argument("--win", type=int, default=12); ap.add_argument("--store", action="store_true")
a = ap.parse_args()
m = load_img(); w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4"); s = starts(m)
po = int(a.ptr, 16) // 8; fo = int(a.field, 16)
idx = np.nonzero((w & 0xFFFFFC00) == (0xF9400000 | (po << 10)))[0]
for i in idx:
    rd = int(w[i]) & 31
    for k in range(1, a.win):
        j = i + k
        if j >= len(w): break
        x = int(w[j])
        hit = None
        for msk, v, sc, st in UOFF:
            if fo % sc or fo // sc >= 4096: continue
            if (x & (msk | (0xFFF << 10))) == (v | ((fo // sc) << 10)) and ((x >> 5) & 31) == rd:
                hit = st
        if hit is not None and (hit or not a.store):
            print(f"{BASE+int(i)*4:#x} -> {BASE+j*4:#x} {'W' if hit else 'R'} func {BASE+fstart(s,int(j)*4):#x}")
            break
        if (x & 31) == rd and (x & 0xFF000000) not in (0xB9000000, 0xBD000000, 0xF9000000, 0x39000000): break
