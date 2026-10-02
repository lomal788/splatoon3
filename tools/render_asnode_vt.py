import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img

KIND_VT = {
    1: 0x7105742750, 2: 0x71057435f8, 3: 0x7105743410, 4: 0x7105743508, 5: 0x7105742570,
    6: 0x7105742860, 7: 0x7105743138, 8: 0x7105743028, 9: 0x7105743320, 10: 0x7105742660,
    11: 0x7105742b30, 12: 0x7105742950, 13: 0x7105742478, 14: 0x7105742e28, 15: 0x7105742570,
    16: 0x7105742c28, 17: 0x7105742150, 18: 0x7105741f50, 19: 0x7105742a40, 20: 0x7105742060,
    21: 0x7105742278, 22: 0x7105741e60, 23: 0x7105743708, 24: 0x7105743228, 25: 0x7105742d38,
}


def main():
    ap = argparse.ArgumentParser(description="엔진 AS 노드 종류별 vtable 슬롯 표(종류 = ASB 노드 u16 종류)")
    ap.add_argument("kinds", nargs="*", type=int)
    ap.add_argument("-n", type=int, default=24, help="슬롯 수")
    a = ap.parse_args()
    m = load_img()
    kinds = a.kinds or sorted(KIND_VT)
    print("slot  " + "  ".join(f"k{k:<11d}" for k in kinds))
    for s in range(a.n):
        row = []
        for k in kinds:
            off = KIND_VT[k] - BASE + s * 8
            v = struct.unpack_from("<Q", m, off)[0]
            row.append(f"{v:#x}")
        print(f"+{s*8:#04x} " + "  ".join(row))


if __name__ == "__main__":
    main()
