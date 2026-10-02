import argparse
import struct
import sys
from pathlib import Path

import capstone
from capstone import arm64_const as A

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img

_md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
_md.detail = True


def cstr_at(m, off, maxlen=80):
    if not (0 <= off < len(m)):
        return None
    end = m.find(b"\0", off, off + maxlen)
    if end <= off:
        return None
    s = m[off:end]
    if all(0x20 <= c < 0x7F for c in s) and (off == 0 or m[off - 1] == 0):
        return s.decode()
    return None


def is_prologue(w):
    return (w & 0xFFC003FF) == 0xD10003FF or (w & 0xFFC07FFF) == 0xA9807BFD or (w & 0xFFC003E0) == 0xA98003E0


def func_start(m, off, limit=0x8000):
    p = off & ~3
    while p > off - limit:
        w = struct.unpack_from("<I", m, p)[0]
        prev = struct.unpack_from("<I", m, p - 4)[0]
        ends = prev == 0xD65F03C0 or (prev & 0xFC000000) == 0x14000000 or prev == 0 or (prev & 0xFFE0001F) == 0xD4200000
        if ends and is_prologue(w):
            return p
        p -= 4
    return None


def disasm(m, start, count=None, end=None, annotate=True):
    pages = {}
    out = []
    p = start
    while (count is None or len(out) < count) and (end is None or p < end):
        code = m[p:p + 4]
        ins = next(_md.disasm(code, BASE + p), None)
        if ins is None:
            out.append((p, f".word {struct.unpack('<I', code)[0]:#010x}", ""))
            p += 4
            continue
        note = ""
        if annotate:
            ops = ins.operands
            if ins.mnemonic == "adrp":
                pages[ops[0].reg] = ops[1].imm - BASE
            elif ins.mnemonic == "add" and len(ops) == 3 and ops[1].reg in pages and ops[2].type == A.ARM64_OP_IMM:
                t = pages[ops[1].reg] + ops[2].imm
                s = cstr_at(m, t)
                note = f'"{s}"' if s else f"-> {BASE + t:#x}"
            elif ins.mnemonic.startswith("ldr") and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM and ops[1].mem.base in pages:
                t = pages[ops[1].mem.base] + ops[1].mem.disp
                if 0 <= t + 8 <= len(m):
                    if ins.op_str.startswith("s"):
                        note = f"[{BASE + t:#x}] = f32 {struct.unpack_from('<f', m, t)[0]!r}"
                    elif ins.op_str.startswith("d"):
                        note = f"[{BASE + t:#x}] = f64 {struct.unpack_from('<d', m, t)[0]!r}"
                    elif ins.op_str.startswith("w"):
                        note = f"[{BASE + t:#x}] = u32 {struct.unpack_from('<I', m, t)[0]:#x}"
                    else:
                        note = f"[{BASE + t:#x}] = u64 {struct.unpack_from('<Q', m, t)[0]:#x}"
            elif ins.mnemonic == "fmov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_FP:
                note = f"{ops[1].fp!r}"
            elif ins.mnemonic in ("mov", "movz", "movk") and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM and ins.op_str.startswith("w"):
                v = ops[1].imm & 0xFFFFFFFF
                if ins.mnemonic == "movk":
                    note = ""
                elif v > 0xFFFF:
                    note = f"f32 {struct.unpack('<f', struct.pack('<I', v))[0]!r}"
        if annotate and ins.mnemonic != "adrp" and ins.operands and ins.operands[0].type == A.ARM64_OP_REG and not ins.mnemonic.startswith(("st", "cmp", "tst", "cb", "tb")):
            pages.pop(ins.operands[0].reg, None)
        out.append((p, f"{ins.mnemonic} {ins.op_str}", note))
        p += 4
        if end is None and count is None and ins.mnemonic == "ret":
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addr")
    ap.add_argument("-n", type=int)
    ap.add_argument("--end")
    ap.add_argument("--func", action="store_true", help="함수 시작으로 되돌아가 ret까지")
    a = ap.parse_args()
    m = load_img()
    off = int(a.addr, 16)
    off = off - BASE if off >= BASE else off
    if a.func:
        off = func_start(m, off)
    end = None
    if a.end:
        end = int(a.end, 16)
        end = end - BASE if end >= BASE else end
    sys.stdout.reconfigure(encoding="utf-8")
    for p, text, note in disasm(m, off, a.n, end):
        print(f"{BASE + p:#x}  {text:<48} {'; ' + note if note else ''}")


if __name__ == "__main__":
    main()
