import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img


def main():
    ap = argparse.ArgumentParser(description="ldrb/strb/ldrh/strh unsigned-offset 명령을 오프셋으로 전수 검색")
    ap.add_argument("offset", nargs="+", help="바이트 오프셋(16진), 여러 개 가능")
    ap.add_argument("--kind", default="ldrb", choices=["ldrb", "strb", "ldrh", "strh", "ldrsb"])
    ap.add_argument("--lo", default="0x7100000000")
    ap.add_argument("--hi", default=hex(BASE + TEXT_END))
    ap.add_argument("--rn", type=int, default=None, help="기준 레지스터 번호 제한")
    a = ap.parse_args()
    op, sc = {"ldrb": (0x39400000, 1), "strb": (0x39000000, 1), "ldrh": (0x79400000, 2),
              "strh": (0x79000000, 2), "ldrsb": (0x39800000, 1)}[a.kind]
    m = load_img()
    lo, hi = int(a.lo, 16) - BASE, int(a.hi, 16) - BASE
    words = memoryview(m)[lo:hi].cast("I")
    offs = {int(o, 16) // sc: int(o, 16) for o in a.offset}
    for i, w in enumerate(words):
        if (w & 0xFFC00000) != op:
            continue
        imm = (w >> 10) & 0xFFF
        if imm not in offs:
            continue
        rn = (w >> 5) & 31
        if a.rn is not None and rn != a.rn:
            continue
        print(f"{BASE + lo + i * 4:#x} {a.kind} w{w & 31}, [x{rn}, #{offs[imm]:#x}]")


if __name__ == "__main__":
    main()
