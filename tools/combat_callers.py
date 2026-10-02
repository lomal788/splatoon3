"""BL/B 직접 호출자 찾기. 사용: PY web/tools/combat_callers.py <함수주소...>"""
import sys
import numpy as np
B = 0x7100000000
TEXT_END = 0x3e9df50
d = np.fromfile('C:/dev/splatoon3/extracted/exefs/main.img', dtype='<u4', count=TEXT_END // 4)
pc = np.arange(len(d), dtype=np.int64) * 4
op = d & 0xFC000000
isbl = op == 0x94000000
isb = op == 0x14000000
imm = (d & 0x03FFFFFF).astype(np.int64)
imm = np.where(imm & 0x02000000, imm - 0x04000000, imm)
tgt = pc + imm * 4
for a in sys.argv[1:]:
    t = int(a, 16) - B
    bl = pc[isbl & (tgt == t)] + B
    bb = pc[isb & (tgt == t)] + B
    print(a, 'BL:', ' '.join(hex(x) for x in bl), '| B:', ' '.join(hex(x) for x in bb))
