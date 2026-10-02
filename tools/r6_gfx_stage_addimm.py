"""add xD, xN, #imm (64비트, shift 0) 명령 전수 검색 → 함수별 집합. 여러 imm 이 모두 나오는 함수를 출력.
사용: PY web/tools/r6_gfx_stage_addimm.py <imm16진> [<imm16진> ...] [--lo --hi]
"""
import sys, argparse
import numpy as np
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import func_lookup
ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(); ap.add_argument("imms", nargs="+"); ap.add_argument("--lo", default="0x7100000000"); ap.add_argument("--hi", default="0x7103e9df50")
a = ap.parse_args()
B = 0x7100000000
m = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
lo, hi = int(a.lo, 16) - B, int(a.hi, 16) - B
w = np.frombuffer(m[lo:hi - ((hi - lo) & 3)], dtype=np.uint32)
st, rows = func_lookup.load()
sets = []
for s in a.imms:
    imm = int(s, 16)
    sel = ((w & 0xFFC00000) == 0x91000000) & (((w >> 10) & 0xFFF) == imm)
    fs = {}
    for i in np.nonzero(sel)[0]:
        ad = B + lo + int(i) * 4
        r = func_lookup.lookup(st, rows, ad)
        if r: fs.setdefault(r[0], []).append(ad)
    sets.append(fs)
common = set(sets[0])
for s in sets[1:]: common &= set(s)
for f in sorted(common):
    print(hex(f), " ".join(",".join(hex(x) for x in s[f][:3]) for s in sets))
