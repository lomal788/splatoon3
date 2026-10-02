"""vtable 주소 → 슬롯 중 'adrp x0; add x0; ret' 형태로 문자열을 반환하는 함수(getName 등) 찾기.
사용: PY web/tools/combat_vtname.py <vtable...> [--slots N] [--dump]
"""
import struct, sys
B = 0x7100000000
img = open('C:/dev/splatoon3/extracted/exefs/main.reloc.img', 'rb').read()
raw = open('C:/dev/splatoon3/extracted/exefs/main.img', 'rb').read()
def q(a): return struct.unpack_from('<Q', img, a - B)[0]
def u32(a): return struct.unpack_from('<I', raw, a - B)[0]
def strret(fn):
    try:
        i0, i1, i2 = u32(fn), u32(fn + 4), u32(fn + 8)
    except struct.error:
        return None
    if (i0 & 0x9f00001f) == 0x90000000 and (i1 & 0xffc003ff) == 0x91000000 and i2 == 0xd65f03c0:
        immlo = (i0 >> 29) & 3; immhi = (i0 >> 5) & 0x7ffff
        imm = ((immhi << 2) | immlo) << 12
        if imm & (1 << 32): imm -= 1 << 33
        a = (fn & ~0xfff) + imm + ((i1 >> 10) & 0xfff)
        return raw[a - B:a - B + 100].split(b'\0')[0].decode('latin1')
    return None
args = [a for a in sys.argv[1:] if a.startswith('0x')]
n = int(sys.argv[sys.argv.index('--slots') + 1]) if '--slots' in sys.argv else 64
for vt in map(lambda x: int(x, 16), args):
    print(hex(vt))
    for s in range(n):
        f = q(vt + s * 8)
        if not (B <= f < B + 0x3e9e000):
            break
        nm = strret(f)
        if '--dump' in sys.argv or nm:
            print(f'  slot {s:3d} +{s*8:#05x} {f:#x} {nm or ""}')
