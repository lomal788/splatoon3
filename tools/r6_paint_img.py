"""r6 paint 공용: main.reloc.img 읽기(가상 주소 0x7100000000 기준)."""
import struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
IMG = (ROOT / "extracted" / "exefs" / "main.reloc.img").read_bytes()
BASE = 0x7100000000

def rd(a, n): return IMG[a - BASE:a - BASE + n]
def u64(a): return struct.unpack_from("<Q", IMG, a - BASE)[0]
def u32(a): return struct.unpack_from("<I", IMG, a - BASE)[0]
def f32(a): return struct.unpack_from("<f", IMG, a - BASE)[0]
def cstr(a):
    e = IMG.index(b"\0", a - BASE); return IMG[a - BASE:e].decode("utf-8", "replace")
def is_code(p): return 0x7100004000 <= p < 0x7104400000

def vtable(a, n=64):
    out = []
    for i in range(n):
        p = u64(a + i * 8)
        if not (BASE <= p < BASE + len(IMG)): break
        out.append(p)
    return out

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "vt":
        a = int(sys.argv[2], 16); n = int(sys.argv[3]) if len(sys.argv) > 3 else 64
        for i, p in enumerate(vtable(a, n)): print(f"+0x{i*8:03x} {hex(p)}")
    elif cmd == "q":
        for s in sys.argv[2:]:
            a = int(s, 16); print(hex(a), hex(u64(a)))

def class_of_slot(slot_addr, back=0x600):
    """vtable 칸 주소 → (vtable 시작, 슬롯 번호, 클래스 이름) — 슬롯2 getName(adrp+add x0;ret) 기준."""
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for k in range(0, back, 8):
        vt = slot_addr - k
        try:
            g = u64(vt + 0x10)
        except Exception:
            continue
        if not is_code(g): continue
        ins = list(md.disasm(rd(g, 12), g))
        if len(ins) == 3 and ins[0].mnemonic == "adrp" and ins[1].mnemonic == "add" and ins[2].mnemonic == "ret":
            page = int(ins[0].op_str.split("#")[1], 16); off = int(ins[1].op_str.split("#")[1], 16)
            s = cstr(page + off)
            if "::" in s:
                return vt, k // 8, s
    return None
