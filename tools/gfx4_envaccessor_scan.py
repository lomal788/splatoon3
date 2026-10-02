"""env 파라미터 접근자 클래스(getId: mov w0,#ID; ret / getGroupName: adrp x0; add x0 "<그룹>"; ret) 쌍을 전수 검색.
사용: PY web/tools/gfx4_envaccessor_scan.py [시작 끝]
출력: ID  그룹이름  getId주소  (같은 클래스 vtable 근처의 get/set 함수는 따로 확인)
"""
import struct, sys
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
B = 0x7100000000
m = open(IMG, 'rb').read()
lo = int(sys.argv[1], 16) if len(sys.argv) > 2 else 0x7101040000
hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x7101070000
def w(a): return struct.unpack_from('<I', m, a - B)[0]
def cstr(a):
    o = a - B; e = m.index(b'\0', o); return m[o:e].decode('utf8', 'replace')
RET = 0xd65f03c0
res = []
for a in range(lo, hi, 4):
    i0, i1 = w(a), w(a + 4)
    if (i0 & 0xffe0001f) == 0x52800000 and i1 == RET:  # movz w0,#imm
        imm = (i0 >> 5) & 0xffff
        i2, i3, i4 = w(a + 8), w(a + 12), w(a + 16)
        if (i2 & 0x9f00001f) == 0x90000000 and (i3 & 0xffc003ff) == 0x91000000 and i4 == RET:
            immlo = (i2 >> 29) & 3; immhi = (i2 >> 5) & 0x7ffff
            page = ((a + 8) & ~0xfff) + (((immhi << 2) | immlo) << 12)
            if page & (1 << 32 + 0): pass
            off = (i3 >> 10) & 0xfff
            s = page + off
            try:
                res.append((imm, cstr(s), a))
            except Exception:
                pass
for imm, s, a in sorted(res):
    print('0x%02x\t%s\t0x%x' % (imm, s, a))
