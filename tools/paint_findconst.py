import struct
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
m = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
TEXT = 0x3E9DF50
w = np.frombuffer(m[:TEXT], dtype="<u4")


def find_f32(val):
    bits = struct.unpack("<I", struct.pack("<f", val))[0]
    lo, hi = bits & 0xFFFF, bits >> 16
    hits = []
    movk = (w & 0xFFE00000) == 0x72A00000
    movk_hi = ((w >> 5) & 0xFFFF) == hi
    for i in np.nonzero(movk & movk_hi)[0]:
        rd = w[i] & 31
        for j in range(max(0, i - 6), i):
            x = int(w[j])
            if (x & 0xFFE00000) == 0x52800000 and (x & 31) == rd and ((x >> 5) & 0xFFFF) == lo:
                hits.append(0x7100000000 + i * 4)
                break
        else:
            if lo == 0:
                pass
    if lo == 0:
        movz_hi = ((w & 0xFFE00000) == 0x52A00000) & (((w >> 5) & 0xFFFF) == hi)
        hits += [0x7100000000 + int(i) * 4 for i in np.nonzero(movz_hi)[0]]
    return hits


for v in sys.argv[1:]:
    h = find_f32(float(v))
    print(v, len(h), " ".join(hex(x) for x in h[:40]))
