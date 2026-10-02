import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from class_info import class_info, vtable_len
from xref import BASE, load_idx, load_img


def slot_owners(m, vals):
    data = m[0x3E9E000:0x59AD000]
    cnt = {}
    for v in set(vals):
        needle = struct.pack("<Q", v)
        n = 0
        p = data.find(needle)
        while p >= 0:
            if p % 8 == 0:
                n += 1
            p = data.find(needle, p + 1)
        cnt[v] = n
    return cnt


def main():
    ap = argparse.ArgumentParser(description="클래스 vtable 슬롯 전체 출력(슬롯 함수가 몇 개 테이블에 나오는지 함께)")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--vt", action="store_true", help="names를 vtable 주소(16진)로 해석")
    ap.add_argument("--unique", action="store_true", help="다른 테이블과 공유하지 않는 슬롯만")
    a = ap.parse_args()
    m = load_img()
    idx = None if a.vt else load_idx()
    for n in a.names:
        if a.vt:
            vt = int(n, 16) - BASE
            label = n
        else:
            info = class_info(m, idx, n)
            if "vtable" not in info:
                print(f"# {n}: vtable 못 찾음")
                continue
            vt = int(info["vtable"], 16) - BASE
            label = f"{n} {info['vtable']}"
        k = vtable_len(m, vt)
        vals = [struct.unpack_from("<Q", m, vt + i * 8)[0] for i in range(k)]
        cnt = slot_owners(m, vals)
        print(f"# {label} slots={k}")
        for i, v in enumerate(vals):
            if a.unique and cnt[v] > 1:
                continue
            print(f"{i:3d} {hex(v)} refs={cnt[v]}")


if __name__ == "__main__":
    main()
