"""명령 문자열 정규식 전수 검색 (구간 지정, 함수별 묶음).

사용:
  PY web/tools/combat4_iscan.py <정규식> [--lo 0x...] [--hi 0x...] [--all 정규식2 ...] [--max N]
  예) tbz/tbnz #0xc 와 ldr [..,#0x14] 가 모두 있는 함수:
      PY web/tools/combat4_iscan.py "tb[n]?z w\\d+, #0xc," --all "ldr w\\d+, \\[x\\d+, #0x14\\]" --lo 0x7103a00000 --hi 0x7103d00000

명령 단위(4바이트)로 capstone 디코드하므로 데이터 워드에서 멈추지 않는다.
--all 을 주면 첫 정규식이 걸린 함수 중 --all 정규식들이 모두 같은 함수 안에 있는 것만 출력한다.
함수 경계는 analysis/functions/main.nso.tsv(Ghidra 전체 분석).
"""
import argparse
import re
import sys
from pathlib import Path

import capstone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img  # noqa: E402
import func_lookup  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--lo", default="0x7100000000")
    ap.add_argument("--hi", default=hex(BASE + TEXT_END))
    ap.add_argument("--all", nargs="*", default=[])
    ap.add_argument("--max", type=int, default=200)
    a = ap.parse_args()
    pat = re.compile(a.pattern)
    others = [re.compile(p) for p in a.all]
    m = load_img()
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    lo, hi = int(a.lo, 16), int(a.hi, 16)
    starts, rows = func_lookup.load()
    hits = {}
    text = {}
    for addr in range(lo, hi, 4):
        off = addr - BASE
        ins = next(md.disasm(bytes(m[off:off + 4]), addr), None)
        if ins is None:
            continue
        s = f"{ins.mnemonic} {ins.op_str}"
        f = func_lookup.lookup(starts, rows, addr)
        fs = f[0] if f else 0
        if pat.search(s):
            hits.setdefault(fs, []).append((addr, s))
        if others:
            for i, o in enumerate(others):
                if o.search(s):
                    text.setdefault(fs, set()).add(i)
    n = 0
    for fs, lst in sorted(hits.items()):
        if others and len(text.get(fs, ())) != len(others):
            continue
        print(f"func {fs:#x}: " + "; ".join(f"{x:#x} {s}" for x, s in lst[:6]))
        n += 1
        if n >= a.max:
            break


if __name__ == "__main__":
    main()
