import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000
TEXT = 0x3E9DF50
m = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
w = np.frombuffer(m[:TEXT], dtype="<u4").astype(np.int64)


def ldrb_imm(off):
    return ((w & 0xFFC00000) == 0x39400000) & (((w >> 10) & 0xFFF) == off)


def ldr_s_imm(off):
    return ((w & 0xFFC00000) == 0xBD400000) & (((w >> 10) & 0xFFF) == off // 4)


def scan(pairs, window=40):
    hits = None
    for flag, field in pairs:
        a = np.nonzero(ldrb_imm(flag))[0]
        b = np.nonzero(ldr_s_imm(field))[0]
        bi = np.searchsorted(b, a)
        ok = set()
        for i, j in zip(a, bi):
            if j < len(b) and b[j] - i < window:
                ok.add(int(i) // 2048)
        hits = ok if hits is None else hits & ok
    return sorted(hits)


if __name__ == "__main__":
    pairs = []
    for s in sys.argv[1:]:
        f, d = s.split(":")
        pairs.append((int(f, 16), int(d, 16)))
    for blk in scan(pairs):
        print(hex(BASE + blk * 2048 * 4))
