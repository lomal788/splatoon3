import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img


def main():
    ap = argparse.ArgumentParser(description="ldr/str 64·32비트 unsigned-offset 명령을 오프셋으로 전수 검색")
    ap.add_argument("offset", help="바이트 오프셋(16진)")
    ap.add_argument("--kind", default="str64", choices=["str64", "ldr64", "str32", "ldr32", "strs", "ldrs", "stps", "ldps", "ldurs", "sturs"])
    ap.add_argument("--lo", default="0x7100000000")
    ap.add_argument("--hi", default=hex(BASE + TEXT_END))
    a = ap.parse_args()
    off = int(a.offset, 16)
    spec = {
        "str64": (0xF9000000, 8), "ldr64": (0xF9400000, 8),
        "str32": (0xB9000000, 4), "ldr32": (0xB9400000, 4),
        "strs": (0xBD000000, 4), "ldrs": (0xBD400000, 4),
        "stps": (0x2D000000, 4), "ldps": (0x2D400000, 4),
        "sturs": (0xBC000000, 1), "ldurs": (0xBC400000, 1),
    }[a.kind]
    op, sc = spec
    if off % sc:
        sys.exit("정렬 안 맞음")
    m = load_img()
    lo, hi = int(a.lo, 16) - BASE, int(a.hi, 16) - BASE
    words = memoryview(m)[lo:hi].cast("I")
    imm = off // sc
    for i, w in enumerate(words):
        if a.kind in ("stps", "ldps"):
            ok = (w & 0xFFC00000) == op and ((w >> 15) & 0x7F) == (imm & 0x7F)
        elif a.kind in ("sturs", "ldurs"):
            ok = (w & 0xFFE00C00) == op and ((w >> 12) & 0x1FF) == (off & 0x1FF)
        else:
            ok = (w & 0xFFC00000) == op and ((w >> 10) & 0xFFF) == imm
        if ok:
            print(hex(BASE + lo + i * 4), f"Rt=x{w & 31} Rn=x{(w >> 5) & 31}")


if __name__ == "__main__":
    main()
