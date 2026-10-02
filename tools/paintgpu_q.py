"""paintgpu 보조: 이미지에서 qword/dword/float 읽기.  사용: paintgpu_q.py q <주소> [개수] | f <주소> [개수] | d <주소> [개수]"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img

def main():
    m = load_img()
    kind, a = sys.argv[1], int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    o = a - BASE
    for i in range(n):
        if kind == "q":
            print(hex(a + i * 8), hex(struct.unpack_from("<Q", m, o + i * 8)[0]))
        elif kind == "f":
            v = struct.unpack_from("<f", m, o + i * 4)[0]
            print(hex(a + i * 4), v, hex(struct.unpack_from("<I", m, o + i * 4)[0]))
        else:
            print(hex(a + i * 4), struct.unpack_from("<i", m, o + i * 4)[0])

if __name__ == "__main__":
    main()
