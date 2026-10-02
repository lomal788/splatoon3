"""함수 시작 추정: BL 대상 + 데이터 영역의 text 포인터(vtable 등) 집합에서 주소 이하 최대값.
사용: PY web/tools/network_fstart.py <주소...>   (처음 실행 시 analysis/network/fstarts.npy 생성)
"""
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "analysis/network/fstarts.npy"


def build(m):
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    idx = np.nonzero((w & 0xFC000000) == 0x94000000)[0]
    imm = (w[idx] & 0x3FFFFFF).astype(np.int64)
    imm = np.where(imm & (1 << 25), imm - (1 << 26), imm)
    t = idx.astype(np.int64) * 4 + imm * 4
    d = np.frombuffer(m[0x3E9E000:len(m) & ~7], dtype="<u8").astype(np.int64) - BASE
    d = d[(d >= 0) & (d < TEXT_END) & ((d & 3) == 0)]
    s = np.unique(np.concatenate([t[(t >= 0) & (t < TEXT_END)], d]))
    np.save(CACHE, s)
    return s


def starts(m=None):
    if CACHE.exists():
        return np.load(CACHE)
    return build(m or load_img())


def fstart(s, off):
    i = np.searchsorted(s, off, "right") - 1
    return int(s[i]) if i >= 0 else None


if __name__ == "__main__":
    s = starts()
    for a in sys.argv[1:]:
        v = int(a, 16)
        o = v - BASE if v >= BASE else v
        f = fstart(s, o)
        print(f"{BASE + o:#x} {BASE + f:#x} +{o - f:#x}")
