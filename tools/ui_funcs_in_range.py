"""주소 구간 안의 함수 시작 후보(BL 대상 + 재배치 이미지의 포인터 값) 목록. ui 분석 보조.
사용: ui_funcs_in_range.py <시작> <끝>
"""
import sys
import numpy as np

B = 0x7100000000
TEXT_END = 0x3e9df50
lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
img = open(r"C:/dev/splatoon3/extracted/exefs/main.img", "rb").read()[:TEXT_END]
w = np.frombuffer(img[:len(img) // 4 * 4], dtype="<u4")
imm = (w & 0x3FFFFFF).astype(np.int64)
imm = np.where(imm & 0x2000000, imm - 0x4000000, imm)
tgt = np.arange(len(w), dtype=np.int64) * 4 + imm * 4 + B
s = set(int(x) for x in tgt[((w >> 26) == 0x25) & (tgt >= lo) & (tgt < hi)])
r = open(r"C:/dev/splatoon3/extracted/exefs/main.reloc.img", "rb").read()
q = np.frombuffer(r[:len(r) // 8 * 8], dtype="<u8")
s |= set(int(x) for x in q[(q >= lo) & (q < hi)])
print(" ".join(hex(x) for x in sorted(s)))
