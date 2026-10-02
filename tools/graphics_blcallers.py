"""BL/B 호출자 찾기: main.reloc.img text 구간에서 대상 주소로 가는 BL(및 B) 명령 주소를 출력.
usage: graphics_blcallers.py <target...>"""
import sys, numpy as np
B = 0x7100000000
TEXT_END = 0x3e9df50
img = np.fromfile('C:/dev/splatoon3/extracted/exefs/main.reloc.img', dtype='<u4', count=TEXT_END // 4)
pc = np.arange(len(img), dtype=np.int64) * 4
op = img >> 26
imm = (img & 0x3ffffff).astype(np.int64)
imm = np.where(imm & 0x2000000, imm - 0x4000000, imm)
tgt = pc + imm * 4
for t in sys.argv[1:]:
    t = int(t, 16) - B
    bl = np.nonzero((op == 0x25) & (tgt == t))[0]
    b = np.nonzero((op == 0x05) & (tgt == t))[0]
    print(hex(t + B), 'BL:', ' '.join(hex(B + i * 4) for i in bl), '| B:', ' '.join(hex(B + i * 4) for i in b))
