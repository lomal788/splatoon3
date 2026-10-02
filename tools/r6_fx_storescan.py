"""r6 fx: 이미지 전체에서 [Rn,#off] 저장(str/strb/strh/stp/stur, 64·32비트) 명령을 비트 디코드로 빠르게 찾는다.
사용: PY web/tools/r6_fx_storescan.py <off> [--lo 0x7100000000 --hi 0x7104000000] [--near <off2> --win 0x100]
--near: 같은 Rn 으로 off2 에 저장하는 명령이 ±win 바이트 안에 있는 것만 출력
"""
import sys, argparse
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
B = 0x7100000000
raw = np.fromfile('C:/dev/splatoon3/extracted/exefs/main.reloc.img', dtype=np.uint8)
w = raw[:raw.size // 4 * 4].view('<u4').astype(np.uint64)

def stores(off):
    hits = {}
    rn = (w >> 5) & 31
    # STR 64 unsigned
    for base, sz, name in ((0xF9000000, 8, 'str x'), (0xB9000000, 4, 'str w'), (0x79000000, 2, 'strh'), (0x39000000, 1, 'strb'),
                           (0xFD000000, 8, 'str d'), (0xBD000000, 4, 'str s'), (0x3D800000, 16, 'str q')):
        if off % sz:
            continue
        m = ((w & 0xFFC00000) == base) & (((w >> 10) & 0xFFF) == off // sz)
        for i in np.nonzero(m)[0]:
            hits[int(i)] = (name, int(rn[i]))
    # STP 64/32 signed offset (also pre-index)
    for base, sz, name in ((0xA9000000, 8, 'stp x'), (0x29000000, 4, 'stp w'), (0xA9800000, 8, 'stp x!'), (0x6D000000, 8, 'stp d'), (0x2D000000, 4, 'stp s'), (0xAD000000, 16, 'stp q')):
        imm7 = ((w >> 15) & 0x7F).astype(np.int64)
        imm7 = np.where(imm7 >= 64, imm7 - 128, imm7)
        m0 = (w & 0xFFC00000) == base
        for k in (0, 1):
            m = m0 & ((imm7 * sz + k * sz) == off)
            for i in np.nonzero(m)[0]:
                hits[int(i)] = (name + ('[2nd]' if k else ''), int(rn[i]))
    # STUR 64/32/8
    for base, name in ((0xF8000000, 'stur x'), (0xB8000000, 'stur w'), (0x38000000, 'sturb'), (0xFC000000, 'stur d'), (0xBC000000, 'stur s')):
        imm9 = ((w >> 12) & 0x1FF).astype(np.int64)
        imm9 = np.where(imm9 >= 256, imm9 - 512, imm9)
        m = ((w & 0xFFE00C00) == base) & (imm9 == off)
        for i in np.nonzero(m)[0]:
            hits[int(i)] = (name, int(rn[i]))
    return hits

ap = argparse.ArgumentParser()
ap.add_argument('off', type=lambda s: int(s, 0))
ap.add_argument('--lo', type=lambda s: int(s, 0), default=0x7100000000)
ap.add_argument('--hi', type=lambda s: int(s, 0), default=0x7104000000)
ap.add_argument('--near', type=lambda s: int(s, 0), action='append', default=[])
ap.add_argument('--win', type=lambda s: int(s, 0), default=0x100)
ap.add_argument('--rn', type=int, default=None)
a = ap.parse_args()
H = stores(a.off)
N = [stores(o) for o in a.near]
for i in sorted(H):
    addr = B + i * 4
    if not (a.lo <= addr < a.hi):
        continue
    name, rn = H[i]
    if a.rn is not None and rn != a.rn:
        continue
    ok = True
    for nh in N:
        if not any(j in nh and nh[j][1] == rn for j in range(i - a.win // 4, i + a.win // 4)):
            ok = False
            break
    if ok:
        print(hex(addr), name, 'x%d' % rn)
