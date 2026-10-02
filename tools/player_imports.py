"""main의 JUMP_SLOT(외부 함수) GOT 주소와 이름을 출력. 사용: player_imports.py [이름정규식]"""
import re, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import RAW, BASE
m = RAW.read_bytes()
mod0 = struct.unpack_from("<I", m, 4)[0]
dyn = mod0 + struct.unpack_from("<i", m, mod0 + 4)[0]
tags = {}
while True:
    t, v = struct.unpack_from("<qQ", m, dyn); dyn += 16
    if t == 0: break
    tags.setdefault(t, v)
symtab, strtab = tags[6], tags[5]
pat = re.compile(sys.argv[1]) if len(sys.argv) > 1 else None
for r in range(tags[23], tags[23] + tags[2], 24):
    roff, info, addend = struct.unpack_from("<QQq", m, r)
    rsym = info >> 32
    name_off = struct.unpack_from("<I", m, symtab + rsym * 24)[0]
    e = m.index(b"\0", strtab + name_off)
    name = m[strtab + name_off:e].decode()
    if pat is None or pat.search(name):
        print(hex(BASE + roff), name)
