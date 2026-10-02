import argparse
import json
import struct
import sys
from pathlib import Path

import capstone
from capstone import arm64_const as A

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, ROOT, find_cstr, load_idx, load_img, refs_to
from disasm import func_start

_md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
_md.detail = True

TYPE_NAMES_PATH = ROOT / "analysis" / "param_type_desc.json"


def ins_at(m, p):
    return next(_md.disasm(m[p:p + 4], BASE + p), None)


def reg_name(r):
    return _md.reg_name(r)


def xnum(name):
    if name in ("xzr", "wzr"):
        return "zr"
    if name[0] in "xw" and name[1:].isdigit():
        return "r" + name[1:]
    return name


def func_end(m, start, limit=0x3000):
    p = start
    seen_ret = False
    while p < start + limit:
        w = struct.unpack_from("<I", m, p)[0]
        if w == 0xD65F03C0:
            seen_ret = True
        elif seen_ret and p > start:
            prev = struct.unpack_from("<I", m, p - 4)[0]
            is_tail = prev == 0xD65F03C0 or (prev & 0xFC000000) == 0x14000000
            if is_tail and ((w & 0xFFC003E0) == 0xD10003E0 or (w & 0xFFC07FFF) == 0xA9807BFD):
                return p
        p += 4
    return p


def parse_visitor(m, start):
    end = func_end(m, start)
    this = "x0"
    pages = {}
    got = {}
    offs = []
    last_type = None
    fields = []
    p = start
    while p < end:
        ins = ins_at(m, p)
        p += 4
        if ins is None:
            continue
        ops = ins.operands
        mn = ins.mnemonic
        if mn == "mov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_REG and reg_name(ops[1].reg) == "x0" and this == "x0":
            this = reg_name(ops[0].reg)
        elif mn == "adrp":
            pages[reg_name(ops[0].reg)] = ops[1].imm - BASE
        elif mn == "ldr" and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM and reg_name(ops[1].mem.base) in pages and ins.op_str.startswith("x"):
            t = pages[reg_name(ops[1].mem.base)] + ops[1].mem.disp
            got[reg_name(ops[0].reg)] = struct.unpack_from("<Q", m, t)[0]
        elif mn == "add" and len(ops) == 3 and ops[2].type == A.ARM64_OP_IMM:
            src = reg_name(ops[1].reg)
            if src == this:
                offs.append(ops[2].imm)
            elif src in got and ops[2].imm == 0x10:
                last_type = got[src]
            elif src in pages:
                t = pages[src] + ops[2].imm
                end_s = m.find(b"\0", t, t + 100)
                s = m[t:end_s]
                if end_s > t + 1 and m[t - 1] == 0 and s.replace(b"_", b"").isalnum() and offs:
                    fields.append({"name": s.decode(), "offset": offs[0] if offs else None,
                                   "flag_offset": offs[1] if len(offs) > 1 else None,
                                   "type_desc": hex(last_type) if last_type else None, "at": hex(BASE + p - 4)})
                    offs = []
    return fields, end


def find_vtables(m, fn):
    out = []
    needle = struct.pack("<Q", BASE + fn)
    p = m.find(needle)
    while p >= 0:
        if p % 8 == 0:
            q = p
            while struct.unpack_from("<Q", m, q - 8)[0] > BASE:
                q -= 8
            out.append(q)
        p = m.find(needle, p + 1)
    return sorted(set(out))


class ConstEval:
    def __init__(self, m):
        self.m = m
        self.regs = {}
        self.pages = {}

    def get(self, name):
        if name in ("xzr", "wzr"):
            return 0
        return self.regs.get(xnum(name))

    def set(self, name, v):
        if v is None:
            self.regs.pop(xnum(name), None)
        else:
            self.regs[xnum(name)] = v

    def step(self, ins):
        ops = ins.operands
        mn = ins.mnemonic
        if not ops:
            return
        dst = reg_name(ops[0].reg) if ops[0].type == A.ARM64_OP_REG else None
        if mn == "adrp":
            self.pages[dst] = ops[1].imm - BASE
            self.set(dst, None)
        elif mn in ("mov", "movz") and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM:
            sh = ops[1].shift.value if ops[1].shift.type else 0
            v = (ops[1].imm << sh) & ((1 << 64) - 1)
            self.set(dst, v & 0xFFFFFFFF if dst[0] == "w" else v)
        elif mn == "movn" and len(ops) == 2:
            sh = ops[1].shift.value if ops[1].shift.type else 0
            v = ~(ops[1].imm << sh)
            self.set(dst, v & (0xFFFFFFFF if dst[0] == "w" else (1 << 64) - 1))
        elif mn == "movk":
            cur = self.get(dst) or 0
            sh = ops[1].shift.value if ops[1].shift.type else 0
            v = (cur & ~(0xFFFF << sh)) | (ops[1].imm << sh)
            self.set(dst, v)
        elif mn == "mov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_REG:
            self.set(dst, self.get(reg_name(ops[1].reg)))
            if reg_name(ops[1].reg) in self.pages:
                self.pages[dst] = self.pages[reg_name(ops[1].reg)]
        elif mn == "fmov" and len(ops) == 2:
            if ops[1].type == A.ARM64_OP_FP:
                if dst[0] == "s":
                    self.set(dst, struct.unpack("<I", struct.pack("<f", ops[1].fp))[0])
                elif dst[0] == "d":
                    self.set(dst, struct.unpack("<Q", struct.pack("<d", ops[1].fp))[0])
            elif ops[1].type == A.ARM64_OP_REG:
                self.set(dst, self.get(reg_name(ops[1].reg)))
        elif mn == "movi" and dst and dst[0] == "d":
            self.set(dst, ops[1].imm if len(ops) > 1 else 0)
        elif mn == "add" and len(ops) == 3 and ops[2].type == A.ARM64_OP_IMM and reg_name(ops[1].reg) in self.pages:
            self.set(dst, BASE + self.pages[reg_name(ops[1].reg)] + ops[2].imm)
        elif mn.startswith("ldr") and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM and reg_name(ops[1].mem.base) in self.pages:
            t = self.pages[reg_name(ops[1].mem.base)] + ops[1].mem.disp
            sz = {"w": 4, "s": 4, "x": 8, "d": 8, "q": 16}.get(dst[0], 0)
            if sz == 16:
                self.set(dst, int.from_bytes(self.m[t:t + 16], "little"))
            elif sz:
                self.set(dst, int.from_bytes(self.m[t:t + sz], "little"))
        elif mn in ("bl", "blr"):
            for r in list(self.regs):
                if r[0] == "r" and int(r[1:]) <= 18:
                    del self.regs[r]
        elif dst and mn not in ("str", "stur", "stp", "strh", "strb", "sturh", "sturb", "stnp", "cmp", "tst", "cbz", "cbnz", "tbz", "tbnz", "b"):
            self.set(dst, None)


def reg_size(name):
    return {"w": 4, "s": 4, "x": 8, "d": 8, "q": 16, "h": 2, "b": 1}.get(name[0], 8) if name not in ("xzr", "wzr") else (8 if name == "xzr" else 4)


def eval_ctor(m, vtable, ref_at):
    start = func_start(m, ref_at)
    ev = ConstEval(m)
    stores = {}
    obj = None
    p = start
    end = func_end(m, start)
    vt_addr = BASE + vtable
    while p < end:
        ins = ins_at(m, p)
        p += 4
        if ins is None:
            continue
        ops = ins.operands
        mn = ins.mnemonic
        if mn in ("str", "stur", "strh", "strb", "sturh", "sturb", "stp") and ops[-1].type == A.ARM64_OP_MEM:
            base = reg_name(ops[-1].mem.base)
            disp = ops[-1].mem.disp
            srcs = [reg_name(o.reg) for o in ops[:-1]]
            size = {"strh": 2, "sturh": 2, "strb": 1, "sturb": 1}.get(mn, reg_size(srcs[0]))
            mem = stores.setdefault(base, {})
            for i, src in enumerate(srcs):
                v = ev.get(src)
                for k in range(size):
                    mem[disp + i * size + k] = None if v is None else (v >> (8 * k)) & 0xFF
            if mn in ("str", "stp") and ev.get(srcs[0]) == vt_addr and obj is None:
                obj = (base, disp)
        ev.step(ins)
        if mn == "ret" and obj:
            break
    if obj is None:
        return start, {}
    base, disp = obj
    return start, {k - disp: v for k, v in stores[base].items()}


def read_field(mem, off, kind):
    size = {"f32": 4, "s32": 4, "u32": 4, "bool": 1, "u8": 1, "f64": 8, "s64": 8, "vec3f": 12, "vec2f": 8}.get(kind, 4)
    bs = [mem.get(off + i, "?") for i in range(size)]
    if any(b == "?" for b in bs):
        return {"unwritten": True} if all(b == "?" for b in bs) else {"partial": True}
    if any(b is None for b in bs):
        return {"unknown": True}
    raw = bytes(bs)
    if kind == "f32":
        return struct.unpack("<f", raw)[0]
    if kind == "s32":
        return struct.unpack("<i", raw)[0]
    if kind == "bool":
        return bool(raw[0])
    if kind == "vec3f":
        return list(struct.unpack("<3f", raw))
    return raw.hex()


def analyze(m, idx, names, type_names):
    cands = {}
    for nm in names:
        for off in find_cstr(m, nm):
            for src, k in refs_to(off, idx):
                fs = func_start(m, src)
                if fs is not None:
                    cands.setdefault(fs, set()).add(nm)
    if not cands:
        return None
    best = max(cands, key=lambda f: len(cands[f]))
    fields, _ = parse_visitor(m, best)
    for f in fields:
        f["kind"] = type_names.get(f["type_desc"], f["type_desc"])
    result = {"visitor": hex(BASE + best), "fields": fields, "classes": []}
    for vt in find_vtables(m, best):
        for q in (vt, vt - 16):
            for src, k in refs_to(q, idx):
                if k:
                    continue
                cstart, mem = eval_ctor(m, q if q == vt else vt, src)
                defaults = {f["name"]: read_field(mem, f["offset"], f["kind"]) for f in fields if f["offset"] is not None}
                result["classes"].append({"vtable": hex(BASE + vt), "ctor": hex(BASE + cstart), "ref": hex(BASE + src), "defaults": defaults})
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+", help="같은 파라미터 구조체의 필드 이름 몇 개")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    m = load_img()
    idx = load_idx()
    type_names = json.loads(TYPE_NAMES_PATH.read_text()) if TYPE_NAMES_PATH.exists() else {}
    r = analyze(m, idx, a.names, type_names)
    sys.stdout.reconfigure(encoding="utf-8")
    if a.json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return
    print("visitor", r["visitor"])
    for c in r["classes"]:
        print(f" class vtable={c['vtable']} ctor={c['ctor']} (ref {c['ref']})")
    for f in r["fields"]:
        ds = [c["defaults"].get(f["name"]) for c in r["classes"]]
        print(f"  +{f['offset']:#05x} {str(f['kind']):>14} {f['name']:<36} {ds}")


if __name__ == "__main__":
    main()
