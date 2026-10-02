import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "extracted" / "exefs" / "main.img"
BASE = 0x7100000000


def got_names():
    m = RAW.read_bytes()
    mod0 = struct.unpack_from("<I", m, 4)[0]
    dyn = mod0 + struct.unpack_from("<i", m, mod0 + 4)[0]
    tags = {}
    while True:
        t, v = struct.unpack_from("<qQ", m, dyn)
        dyn += 16
        if t == 0:
            break
        tags.setdefault(t, v)
    symtab, strtab = tags[6], tags[5]
    out = {}
    for tab, size in ((tags.get(7, 0), tags.get(8, 0)), (tags.get(23, 0), tags.get(2, 0))):
        for r in range(tab, tab + size, 24):
            roff, info, addend = struct.unpack_from("<QQq", m, r)
            rtype, rsym = info & 0xFFFFFFFF, info >> 32
            if rtype in (0x402, 0x401) and rsym:
                name_off = struct.unpack_from("<I", m, symtab + rsym * 24)[0]
                e = m.index(b"\0", strtab + name_off)
                out[BASE + roff] = m[strtab + name_off:e].decode()
    return m, out


def plt_target(m, addr):
    off = addr - BASE
    w0, w1 = struct.unpack_from("<II", m, off)
    if (w0 & 0x9F000000) != 0x90000000:
        return None
    immlo = (w0 >> 29) & 3
    immhi = (w0 >> 5) & 0x7FFFF
    imm = ((immhi << 2) | immlo) << 12
    if imm & (1 << 32):
        imm -= 1 << 33
    page = (addr & ~0xFFF) + imm
    imm12 = ((w1 >> 10) & 0xFFF) << 3
    return page + imm12


if __name__ == "__main__":
    m, names = got_names()
    for a in sys.argv[1:]:
        a = int(a, 16)
        g = plt_target(m, a)
        print(hex(a), hex(g) if g else None, names.get(g, "?"))
