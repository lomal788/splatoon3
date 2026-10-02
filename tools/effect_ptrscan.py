"""재배치 적용 이미지(main.reloc.img)에서 8바이트 포인터 값이 주어진 주소인 위치를 찾는다(vtable 역추적용).
사용: PY web/tools/effect_ptrscan.py 0x71018b4bac [...]
"""
import sys
import numpy as np
raw = np.fromfile('C:/dev/splatoon3/extracted/exefs/main.reloc.img', dtype=np.uint8)
q = raw[:raw.size // 8 * 8].view('<u8')
for a in sys.argv[1:]:
    v = int(a, 16)
    hit = np.nonzero(q == v)[0]
    print(a, ' '.join(hex(0x7100000000 + int(h) * 8) for h in hit[:20]), '(%d)' % hit.size)
