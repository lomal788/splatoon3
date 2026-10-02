"""데이터 주소(vtable 칸) → vtable 시작·슬롯 번호·클래스 이름 후보(getName 슬롯 문자열, typeinfo 이름).
사용: PY web/tools/r6_gfx_stage_vtof.py <칸주소...>
"""
import sys, struct
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img
from class_info import vtable_start, vtable_len
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
m = load_img()
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
def cstr(va):
    o = va - BASE
    if not (0 <= o < len(m)): return None
    e = m.find(b"\0", o, o + 200)
    if e < 0: return None
    try: return m[o:e].decode("utf-8")
    except Exception: return None
def getname(fn):
    # adrp x0; add x0 ; ret
    o = fn - BASE
    ins = list(md.disasm(m[o:o + 12], fn))
    if len(ins) == 3 and ins[0].mnemonic == "adrp" and ins[1].mnemonic == "add" and ins[2].mnemonic == "ret":
        pg = int(ins[0].op_str.split("#")[1], 16); off = int(ins[1].op_str.split("#")[1], 16)
        s = cstr(pg + off)
        if s and len(s) > 2: return s
    return None
for q in sys.argv[1:]:
    a = int(q, 16)
    st = vtable_start(m, a - BASE)
    slot = (a - BASE - st) // 8
    ti = struct.unpack_from("<Q", m, st - 8)[0]
    tname = None
    if BASE < ti < BASE + len(m):
        nm = struct.unpack_from("<Q", m, ti - BASE + 8)[0]
        tname = cstr(nm)
    n = vtable_len(m, st)
    names = []
    for i in range(min(n, 12)):
        fn = struct.unpack_from("<Q", m, st + i * 8)[0]
        g = getname(fn)
        if g: names.append((i, g))
    print(f"{a:#x}: vtable {BASE+st:#x} slot {slot} (+{slot*8:#x}) len {n} typeinfo {tname} names {names}")
