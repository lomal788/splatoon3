"""함수 시작 후보 색인: BL 대상 + data 영역 포인터(vtable 등) 중 text를 가리키는 값.
사용: camera_funcs.py build | range <시작> <끝> | at <주소>(포함하는 함수 시작 후보)
"""
import sys, os, numpy as np
R = r"C:/dev/splatoon3"
BASE = 0x7100000000; TEXT_END = 0x3e9df50
OUT = R + "/analysis/camera/func_starts.npy"
def build():
    d = np.fromfile(R + "/extracted/exefs/main.img", dtype='<u4', count=TEXT_END // 4)
    idx = np.nonzero((d & 0xFC000000) == 0x94000000)[0]
    imm = (d[idx] & 0x03FFFFFF).astype(np.int64)
    imm = np.where(imm & 0x02000000, imm - 0x04000000, imm)
    tgt = idx.astype(np.int64) * 4 + imm * 4
    q = np.fromfile(R + "/extracted/exefs/main.reloc.img", dtype='<u8')
    q = q[0x5388000 // 8:]
    p = q[(q >= BASE) & (q < BASE + TEXT_END)].astype(np.int64) - BASE
    s = np.unique(np.concatenate([tgt[(tgt >= 0) & (tgt < TEXT_END)], p[p % 4 == 0]]))
    np.save(OUT, s); print(len(s))
def load(): return np.load(OUT)
if __name__ == "__main__":
    c = sys.argv[1]
    if c == "build": build()
    elif c == "range":
        s = load(); a = int(sys.argv[2], 0) - BASE; b = int(sys.argv[3], 0) - BASE
        print(' '.join(hex(BASE + x) for x in s[(s >= a) & (s < b)]))
    elif c == "at":
        s = load()
        for v in sys.argv[2:]:
            a = int(v, 0) - BASE; i = np.searchsorted(s, a, 'right') - 1
            print(v, hex(BASE + s[i]), hex(BASE + s[i + 1]) if i + 1 < len(s) else '')
