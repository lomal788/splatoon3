"""r6 player: 외부 함수 이름(정규식) -> PLT 스텁 주소. 사용: r6_player_pltaddr.py <정규식>"""
import re, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_player_uc import _imports, IMG, BASE, PLT_LO, PLT_HI
img = IMG.read_bytes()
got, _ = _imports()
pat = re.compile(sys.argv[1])
want = {g: n for g, n in got.items() if pat.search(n)}
for a in range(PLT_LO, PLT_HI, 4):
    w0 = struct.unpack_from('<I', img, a - BASE)[0]
    if (w0 & 0x9F000000) != 0x90000000:
        continue
    w1 = struct.unpack_from('<I', img, a + 4 - BASE)[0]
    immlo = (w0 >> 29) & 3; immhi = (w0 >> 5) & 0x7FFFF
    page = ((immhi << 2) | immlo) << 12
    if page & (1 << 32): page -= 1 << 33
    g = (a & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
    if g in want:
        print(hex(a), want[g])
