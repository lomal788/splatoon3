"""오프셋 접근 명령 전수 스캔 (unsigned-offset ldr/str 계열, 바이트·하프·워드·더블·s·d·q).
사용: PY web/tools/r6_gfx_stage_offscan.py <오프셋16진> <kind[,kind...]> [--lo 0x..] [--hi 0x..] [--func]
kind: strb ldrb strh ldrh str32 ldr32 str64 ldr64 strs ldrs strd ldrd strq ldrq stp32 stp64 ldp32 ldp64
--func 이면 함수 시작(전체 분석 목록)을 함께 출력
"""
import sys
import argparse
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
TEXT_END = 0x3E9DF50
SPEC = {
    "strb": (0x39000000, 1), "ldrb": (0x39400000, 1),
    "strh": (0x79000000, 2), "ldrh": (0x79400000, 2),
    "str32": (0xB9000000, 4), "ldr32": (0xB9400000, 4),
    "str64": (0xF9000000, 8), "ldr64": (0xF9400000, 8),
    "strs": (0xBD000000, 4), "ldrs": (0xBD400000, 4),
    "strd": (0xFD000000, 8), "ldrd": (0xFD400000, 8),
    "strq": (0x3D800000, 16), "ldrq": (0x3DC00000, 16),
}
PAIR = {"stp32": (0x29000000, 4), "ldp32": (0x29400000, 4), "stp64": (0xA9000000, 8), "ldp64": (0xA9400000, 8),
        "stps": (0x2D000000, 4), "ldps": (0x2D400000, 4), "stpq": (0xAD000000, 16), "ldpq": (0xAD400000, 16)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("offset")
    ap.add_argument("kinds")
    ap.add_argument("--lo", default=hex(BASE))
    ap.add_argument("--hi", default=hex(BASE + TEXT_END))
    ap.add_argument("--func", action="store_true")
    ap.add_argument("--rn", type=int, default=-1)
    a = ap.parse_args()
    off = int(a.offset, 16)
    m = IMG.read_bytes()
    lo, hi = int(a.lo, 16) - BASE, int(a.hi, 16) - BASE
    lo &= ~3
    w = np.frombuffer(m[lo:hi - ((hi - lo) & 3)], dtype=np.uint32)
    hits = []
    for k in a.kinds.split(","):
        if k in SPEC:
            op, sc = SPEC[k]
            if off % sc:
                continue
            sel = ((w & 0xFFC00000) == op) & (((w >> 10) & 0xFFF) == off // sc)
        else:
            op, sc = PAIR[k]
            if off % sc or off // sc > 63:
                continue
            sel = ((w & 0xFFC00000) == op) & (((w >> 15) & 0x7F) == off // sc)
        if a.rn >= 0:
            sel &= ((w >> 5) & 31) == a.rn
        for i in np.nonzero(sel)[0]:
            ww = int(w[i])
            hits.append((BASE + lo + int(i) * 4, k, ww & 31, (ww >> 5) & 31))
    hits.sort()
    look = None
    if a.func:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import func_lookup
        st, rows = func_lookup.load()
        look = lambda x: func_lookup.lookup(st, rows, x)
    for ad, k, rt, rn in hits:
        s = f"{ad:#x} {k} Rt={rt} Rn=x{rn}"
        if look:
            r = look(ad)
            s += f"  func {r[0]:#x}" if r else ""
        print(s)
    print(f"# {len(hits)}건", file=sys.stderr)


if __name__ == "__main__":
    main()
