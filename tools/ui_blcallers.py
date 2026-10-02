"""main text 에서 BL/B 직접 호출자 찾기 (ui 분석용 보조 도구).
사용: ui_blcallers.py <주소...>   → 각 주소를 BL(또는 B) 대상으로 하는 명령 주소 목록
"""
import sys
import numpy as np

B = 0x7100000000
TEXT_END = 0x3e9df50
img = open(r"C:/dev/splatoon3/extracted/exefs/main.img", "rb").read()[:TEXT_END]
w = np.frombuffer(img[:len(img) // 4 * 4], dtype="<u4")
op = w >> 26
imm = (w & 0x3FFFFFF).astype(np.int64)
imm = np.where(imm & 0x2000000, imm - 0x4000000, imm)
pc = np.arange(len(w), dtype=np.int64) * 4
tgt = pc + imm * 4
for a in sys.argv[1:]:
    t = int(a, 16) - B
    bl = np.nonzero((op == 0x25) & (tgt == t))[0]
    b = np.nonzero((op == 0x05) & (tgt == t))[0]
    print(a, "BL:", " ".join(hex(B + i * 4) for i in bl), "| B:", " ".join(hex(B + i * 4) for i in b))
