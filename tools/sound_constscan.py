"""32비트 상수(movz/movn + movk) 위치 찾기. 사용: PY web/tools/sound_constscan.py <값|'ABCD'(LE 매직)> ..."""
import struct
import sys

import numpy as np

B = 0x7100000000
TEXT_END = 0x3E9DF50
d = open('C:/dev/splatoon3/extracted/exefs/main.reloc.img', 'rb').read()
w = np.frombuffer(d[:TEXT_END & ~3], dtype='<u4')


def scan(val):
    lo, hi = val & 0xFFFF, val >> 16
    # movz w/x, #lo  : 0x52800000 | imm16<<5 | rd   (sf 0) / 0xD2800000 (sf 1)
    movz = np.nonzero(((w & 0x7FE00000) == 0x52800000) & (((w >> 5) & 0xFFFF) == lo))[0]
    out = []
    for i in movz:
        rd = w[i] & 31
        for j in range(i + 1, min(i + 8, len(w))):
            x = int(w[j])
            if (x & 0x7FE00000) == 0x72A00000 and (x & 31) == rd and ((x >> 5) & 0xFFFF) == hi:
                out.append(B + 4 * int(i))
                break
    return out


for a in sys.argv[1:]:
    v = struct.unpack('<I', a.encode('latin1'))[0] if len(a) == 4 and not a.startswith('0x') else int(a, 0)
    print(a, hex(v), [hex(x) for x in scan(v)][:40])
