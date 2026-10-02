"""main 텍스트에서 BL/B 대상이 주어진 주소인 명령 위치를 찾는다.
사용: PY web/tools/effect_blcallers.py 0x71018b2cc0 [...]
"""
import sys
import numpy as np
img = np.fromfile('C:/dev/splatoon3/extracted/exefs/main.img', dtype='<u4', count=0x3e9df50 // 4)
base = 0x7100000000
idx = np.arange(img.size, dtype=np.int64)
for a in sys.argv[1:]:
    t = int(a, 16) - base
    for op, name in ((0x94000000, 'bl'), (0x14000000, 'b')):
        m = (img & 0xFC000000) == op
        imm = (img & 0x03FFFFFF).astype(np.int64)
        imm = np.where(imm & 0x02000000, imm - 0x04000000, imm)
        hit = np.nonzero(m & ((idx * 4 + imm * 4) == t))[0]
        print(a, name, ' '.join(hex(base + int(h) * 4) for h in hit[:40]), '(%d)' % hit.size)
