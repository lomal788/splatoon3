"""r6 gfx_char: main .text 전체에서 명령 패턴을 찾아 함수별로 묶는다(capstone 없이 원시 부호 비교).

패턴(인자, 여러 개 가능):
  movz:<imm>        mov w/x, #imm (movz, shift 0)
  ldr64:<off> / ldr32:<off> / str64:<off> / str32:<off> / ldrs:<off> / strs:<off>   unsigned offset 적재·저장
  add:<imm>         add x, x, #imm (shift 0)
--all 이면 모든 패턴이 들어 있는 함수만 출력한다. 함수 경계는 analysis/functions/main.nso.tsv.
사용: PY web/tools/r6_gfx_char_opscan.py movz:0x2710 ldr64:0x360 --all [--lo 0x71000000 --hi ...]
"""
import argparse
import bisect
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000
TEXT_END = 0x7103E99000


def funcs():
    starts, sizes = [], []
    for ln in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        p = ln.split("\t")
        starts.append(int(p[0], 16))
        sizes.append(int(p[1]))
    order = sorted(range(len(starts)), key=lambda i: starts[i])
    return [starts[i] for i in order], [sizes[i] for i in order]


def match(w, kind, v):
    if kind == "movz":
        return (w & 0x7FE00000) == 0x52800000 and ((w >> 5) & 0xFFFF) == v
    if kind == "add":
        return (w & 0xFFC00000) == 0x91000000 and ((w >> 10) & 0xFFF) == v
    scale = {"ldr64": 8, "str64": 8, "ldr32": 4, "str32": 4, "ldrs": 4, "strs": 4}[kind]
    op = {"ldr64": 0xF9400000, "str64": 0xF9000000, "ldr32": 0xB9400000, "str32": 0xB9000000,
          "ldrs": 0xBD400000, "strs": 0xBD000000}[kind]
    return (w & 0xFFC00000) == op and v % scale == 0 and ((w >> 10) & 0xFFF) == v // scale


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("pats", nargs="+")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--lo", type=lambda s: int(s, 16), default=BASE)
    ap.add_argument("--hi", type=lambda s: int(s, 16), default=TEXT_END)
    a = ap.parse_args()
    pats = [(p.split(":")[0], int(p.split(":")[1], 16)) for p in a.pats]
    img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
    starts, sizes = funcs()
    hits = {}
    for off in range(a.lo - BASE, min(a.hi, TEXT_END) - BASE, 4):
        w = struct.unpack_from("<I", img, off)[0]
        for i, (k, v) in enumerate(pats):
            if match(w, k, v):
                addr = BASE + off
                j = bisect.bisect_right(starts, addr) - 1
                f = starts[j] if j >= 0 and addr < starts[j] + max(sizes[j], 4) else None
                hits.setdefault(f, {}).setdefault(i, []).append(addr)
    for f, d in sorted(hits.items(), key=lambda x: (x[0] or 0)):
        if a.all and len(d) < len(pats):
            continue
        desc = " ".join(f"{a.pats[i]}@" + ",".join(hex(x) for x in d[i]) for i in sorted(d))
        print(f"{hex(f) if f else 'nofunc'}\t{desc}")


if __name__ == "__main__":
    main()
