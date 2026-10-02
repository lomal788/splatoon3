"""함수 시작 후보 목록: BL 대상 + 데이터 영역의 text 포인터(vtable 등) + ADRP+ADD로 만든 text 주소(상태 콜백 등).

사용:
  PY web/tools/gimmick_funcs.py range 0x7102178000 0x710218c000   # 구간의 함수 시작 후보
  PY web/tools/gimmick_funcs.py callers 0x710217e1cc              # BL로 부르는 곳
"""
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, ROOT, TEXT_END, load_img

CACHE = ROOT / "analysis" / "gimmick" / "func_starts.npz"


def build(m):
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    pc = np.arange(len(w), dtype=np.int64) * 4
    isbl = (w & 0xFC000000) == 0x94000000
    imm = (w[isbl] & 0x3FFFFFF).astype(np.int64)
    imm = np.where(imm & (1 << 25), imm - (1 << 26), imm)
    bl_from = pc[isbl]
    bl_to = bl_from + imm * 4
    d = np.frombuffer(m[0x3E9E000:(len(m) & ~7)], dtype="<u8").astype(np.int64)
    ptr = d[(d > BASE) & (d < BASE + TEXT_END)] - BASE
    z = np.load(ROOT / "analysis" / "xref_adrp.npz")
    adr = z["tgt"][(z["kind"] == 0) & (z["tgt"] < TEXT_END) & (z["tgt"] % 4 == 0)]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE, bl_from=bl_from, bl_to=bl_to, ptr=np.unique(np.concatenate([ptr, adr])))


def load():
    if not CACHE.exists():
        build(load_img())
    z = np.load(CACHE)
    return z["bl_from"], z["bl_to"], z["ptr"]


def main():
    cmd = sys.argv[1]
    bl_from, bl_to, ptr = load()
    if cmd == "range":
        lo, hi = (int(x, 16) - BASE for x in sys.argv[2:4])
        s = set(bl_to[(bl_to >= lo) & (bl_to < hi)].tolist()) | set(ptr[(ptr >= lo) & (ptr < hi)].tolist())
        for a in sorted(s):
            print(hex(a + BASE))
    elif cmd == "callers":
        for x in sys.argv[2:]:
            t = int(x, 16) - BASE
            print(x, " ".join(hex(a + BASE) for a in bl_from[bl_to == t]))


if __name__ == "__main__":
    main()
