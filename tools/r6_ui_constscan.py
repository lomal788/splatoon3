"""f32 상수(movz/movk w 로 만든 것)를 쓰는 명령 위치. 사용: r6_ui_constscan.py 1920.0 1080.0 ..."""
import struct, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from r6_ui_lib import *
import numpy as np

w = words()
for s in sys.argv[1:]:
    v = struct.unpack("<I", struct.pack("<f", float(s)))[0]
    hi, lo = v >> 16, v & 0xFFFF
    res = []
    if lo == 0:
        sel = ((w & 0xFFE00000) == 0x52A00000) & (((w >> 5) & 0xFFFF) == hi)   # movz w, #hi, lsl16
        res = [BASE + int(i) * 4 for i in np.nonzero(sel)[0]]
    else:
        sel = ((w & 0xFFE00000) == 0x52800000) & (((w >> 5) & 0xFFFF) == lo)
        for i in np.nonzero(sel)[0]:
            for j in range(i + 1, i + 4):
                x = int(w[j])
                if (x & 0xFFE00000) == 0x72A00000 and ((x >> 5) & 0xFFFF) == hi:
                    res.append(BASE + int(i) * 4)
    fs = {}
    for a in res:
        f, _ = func_of(a)
        fs.setdefault(f, []).append(a)
    out(s, hex(v), len(res), "funcs", len(fs))
    for f, l in sorted(fs.items()):
        out("  ", hex(f), " ".join(hex(x) for x in l[:6]))
