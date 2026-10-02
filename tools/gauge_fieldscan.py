"""오프셋 접근(LDR/STR 32/64bit·f32, unsigned imm 및 LDUR/STUR) 전역 스캔 → 함수별 묶음.
사용: PY web/tools/gauge_fieldscan.py <대상오프셋> [--with 0xa658,0xbd4 ...] [--store] [--range 0x7102300000-0x7102700000]
  --with: 같은 함수 안에서 함께 접근해야 하는 오프셋(전부 있어야 출력)
  --store: 대상 오프셋을 '쓰는' 함수만
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_fstart import fstart, starts
from xref import BASE, TEXT_END, load_img

# (마스크, 값, 스케일, 쓰기?) — unsigned offset 형식
UOFF = [
    (0xFFC00000, 0xB9000000, 4, True), (0xFFC00000, 0xB9400000, 4, False),  # STR/LDR W
    (0xFFC00000, 0xBD000000, 4, True), (0xFFC00000, 0xBD400000, 4, False),  # STR/LDR S
    (0xFFC00000, 0xF9000000, 8, True), (0xFFC00000, 0xF9400000, 8, False),  # STR/LDR X
    (0xFFC00000, 0x39000000, 1, True), (0xFFC00000, 0x39400000, 1, False),  # STRB/LDRB
    (0xFFC00000, 0x79000000, 2, True), (0xFFC00000, 0x79400000, 2, False),  # STRH/LDRH
]
# LDUR/STUR (imm9 signed)
UNSC = [(0xFFE00C00, 0xB8000000, True), (0xFFE00C00, 0xB8400000, False),
        (0xFFE00C00, 0xBC000000, True), (0xFFE00C00, 0xBC400000, False)]


def scan(w, off):
    hits = {}
    for m, v, sc, st in UOFF:
        if off % sc:
            continue
        imm = off // sc
        if imm >= 4096:
            continue
        idx = np.nonzero((w & (m | (0xFFF << 10))) == (v | (imm << 10)))[0]
        for i in idx:
            hits[int(i) * 4] = st
    if off < 256:
        for m, v, st in UNSC:
            idx = np.nonzero((w & (m | (0x1FF << 12))) == (v | (off << 12)))[0]
            for i in idx:
                hits[int(i) * 4] = st
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("off")
    ap.add_argument("--with", dest="w", default="")
    ap.add_argument("--store", action="store_true")
    ap.add_argument("--range", default="")
    a = ap.parse_args()
    m = load_img()
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    s = starts(m)
    tgt = scan(w, int(a.off, 16))
    funcs = {}
    for addr, st in tgt.items():
        f = fstart(s, addr)
        funcs.setdefault(f, []).append((addr, st))
    lo, hi = 0, 1 << 40
    if a.range:
        lo, hi = (int(x, 16) - BASE for x in a.range.split("-"))
    withs = [int(x, 16) for x in a.w.split(",") if x]
    others = {o: scan(w, o) for o in withs}
    sarr = np.asarray(s)
    for f in sorted(funcs):
        if not (lo <= f < hi):
            continue
        lst = funcs[f]
        if a.store and not any(st for _, st in lst):
            continue
        i = np.searchsorted(sarr, f, "right")
        end = int(sarr[i]) if i < len(sarr) else f + 0x4000
        ok = True
        info = []
        for o, h in others.items():
            n = [x for x in h if f <= x < end]
            if not n:
                ok = False
                break
            info.append(f"{o:#x}x{len(n)}")
        if not ok:
            continue
        acc = " ".join(f"{BASE + x:#x}{'W' if st else 'R'}" for x, st in sorted(lst))
        print(f"{BASE + f:#x} (len {end - f:#x}) {acc} {' '.join(info)}")


if __name__ == "__main__":
    main()
