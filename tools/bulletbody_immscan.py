import argparse
import struct

IMG = 'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
BASE = 0x7100000000


def main():
    ap = argparse.ArgumentParser(description='movz/orr 즉시값(가상 멤버 포인터 = vt오프셋+1 등) 전수 검색')
    ap.add_argument('imms', nargs='+')
    ap.add_argument('--lo', default='0x7100000000')
    ap.add_argument('--hi', default='0x7104000000')
    a = ap.parse_args()
    want = {int(x, 16) for x in a.imms}
    d = open(IMG, 'rb').read()
    lo = int(a.lo, 16) - BASE
    hi = min(int(a.hi, 16) - BASE, len(d))
    words = struct.unpack_from('<%dI' % ((hi - lo) // 4), d, lo)
    for i, w in enumerate(words):
        if (w & 0x7f800000) == 0x52800000 and ((w >> 21) & 3) == 0:
            imm = (w >> 5) & 0xffff
            if imm in want:
                print(hex(BASE + lo + i * 4), hex(imm), 'x%d' % (w & 31))


if __name__ == '__main__':
    main()
