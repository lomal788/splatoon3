"""[life] 즉시 오프셋 메모리 접근 스캔.

사용:
  PY web/tools/life_scan.py mem <오프셋> [--kind ldr64|ldr32|str64|str32|ldrb|strb|ldrs32|strs32|movz|any] [--range lo hi]
      text 전체에서 [Xn, #오프셋] 형태의 LDR/STR(부호 없는 즉시값) 명령을 찾아 (주소, 함수 시작, +거리)를 출력
  PY web/tools/life_scan.py funcs <오프셋> [--kind ...]
      위 결과를 함수 시작별로 묶어 개수와 함께 출력
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
from network_fstart import starts, fstart

# (opcode 마스크 값, 스케일)  부호 없는 12비트 즉시값 형식
KINDS = {
    "ldr64": (0xF9400000, 8),
    "str64": (0xF9000000, 8),
    "ldr32": (0xB9400000, 4),
    "str32": (0xB9000000, 4),
    "ldrs32": (0xBD400000, 4),  # LDR St (f32)
    "strs32": (0xBD000000, 4),  # STR St (f32)
    "ldrb": (0x39400000, 1),
    "strb": (0x39000000, 1),
    "ldrh": (0x79400000, 2),
    "strh": (0x79000000, 2),
}


def scan(m, off, kinds, lo=None, hi=None):
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    out = []
    if "movz" in kinds:
        # MOVZ Wd/Xd, #imm16 (hw=0): 큰 오프셋을 레지스터로 만들어 [Xn, Xm] 로 접근하는 패턴
        kinds = [k for k in kinds if k != "movz"]
        if off <= 0xFFFF:
            idx = np.nonzero(((w & 0x7FE00000) == 0x52800000) & (((w >> 5) & 0xFFFF) == off))[0]
            for i in idx:
                a = BASE + int(i) * 4
                if lo is None or lo <= a < hi:
                    out.append((a, "movz", int(w[i])))
    for k in kinds:
        opc, sc = KINDS[k]
        if off % sc:
            continue
        imm = off // sc
        if imm > 0xFFF:
            continue
        idx = np.nonzero(((w & 0xFFC00000) == opc) & (((w >> 10) & 0xFFF) == imm))[0]
        for i in idx:
            a = BASE + int(i) * 4
            if lo is not None and not (lo <= a < hi):
                continue
            out.append((a, k, int(w[i])))
    out.sort()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["mem", "funcs"])
    ap.add_argument("off")
    ap.add_argument("--kind", default="any")
    ap.add_argument("--range", nargs=2)
    a = ap.parse_args()
    m = load_img()
    s = starts(m)
    kinds = list(KINDS) + ["movz"] if a.kind == "any" else a.kind.split(",")
    lo = hi = None
    if a.range:
        lo, hi = int(a.range[0], 16), int(a.range[1], 16)
    res = scan(m, int(a.off, 16), kinds, lo, hi)
    if a.cmd == "mem":
        for addr, k, w in res:
            f = fstart(s, addr - BASE)
            rn = (w >> 5) & 31
            rt = w & 31
            print(f"{addr:#x} {k:6s} r{rt}<-[x{rn}] func {BASE + f:#x} +{addr - BASE - f:#x}")
    else:
        c = Counter()
        kk = {}
        for addr, k, w in res:
            f = BASE + fstart(s, addr - BASE)
            c[f] += 1
            kk.setdefault(f, set()).add(k)
        for f, n in sorted(c.items()):
            print(f"{f:#x} {n} {','.join(sorted(kk[f]))}")


if __name__ == "__main__":
    main()
