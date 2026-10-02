"""[respawn] ADD Xd, Xn, #imm (64비트, 시프트 없음) 명령 전수 검색.

사용: PY web/tools/respawn_addscan.py <imm16진> [--range lo hi]
  출력: 명령 주소, Rd, Rn, 함수 시작(func_lookup 기준 analysis/functions/main.nso.tsv)
구조체 내부 하위 객체 포인터(예: 본체+0xd58 쓰러짐 구조체 T)를 인자로 넘기는 곳을 찾는 데 쓴다.
"""
import argparse
import bisect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img

ROOT = Path(__file__).resolve().parents[2]


def func_table():
    starts, sizes = [], []
    for ln in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8", errors="replace").splitlines():
        p = ln.split("\t")
        try:
            a = int(p[0], 16)
            n = int(p[1])
        except (ValueError, IndexError):
            continue
        starts.append(a)
        sizes.append(n)
    o = sorted(range(len(starts)), key=lambda i: starts[i])
    return [starts[i] for i in o], [sizes[i] for i in o]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imm")
    ap.add_argument("--range", nargs=2, default=["0x7100000000", hex(BASE + TEXT_END)])
    a = ap.parse_args()
    imm = int(a.imm, 16)
    lo, hi = (int(x, 16) - BASE for x in a.range)
    m = load_img()
    words = memoryview(m)[lo:hi].cast("I")
    st, sz = func_table()
    for i, w in enumerate(words):
        if (w & 0xFFC00000) == 0x91000000 and ((w >> 10) & 0xFFF) == imm:
            addr = BASE + lo + i * 4
            rd, rn = w & 31, (w >> 5) & 31
            k = bisect.bisect_right(st, addr) - 1
            f = st[k] if k >= 0 and addr < st[k] + sz[k] else None
            print(f"{addr:#x} add x{rd}, x{rn}, #{imm:#x}  func {f:#x}" if f else f"{addr:#x} add x{rd}, x{rn}, #{imm:#x}  func ?")


if __name__ == "__main__":
    main()
