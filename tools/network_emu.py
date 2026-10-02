import struct
import sys
from pathlib import Path

import capstone
from capstone import arm64_const as A

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
from disasm import cstr_at, func_start

_md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
_md.detail = True


def bl_callers(m, target):
    import numpy as np
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    idx = np.nonzero((w & 0xFC000000) == 0x94000000)[0]
    imm = (w[idx] & 0x3FFFFFF).astype(np.int64)
    imm = np.where(imm & (1 << 25), imm - (1 << 26), imm)
    t = idx.astype(np.int64) * 4 + imm * 4
    tgt = target - BASE if target >= BASE else target
    return [int(i) * 4 for i in idx[t == tgt]]


def regname(r):
    n = _md.reg_name(r)
    if n in ("sp", "wsp"):
        return "sp"
    if n in ("x29", "fp"):
        return "x29"
    if n in ("x30", "lr"):
        return "x30"
    if n[0] in "wx" and n[1:].isdigit():
        return "x" + n[1:]
    return n


class Emu:
    def __init__(self, m):
        self.m = m
        self.r = {"sp": ("sp", 0)}
        self.stk = {}

    def get(self, name):
        if name in ("xzr", "wzr"):
            return 0
        return self.r.get(name)

    def addr(self, mem):
        b = regname(mem.base)
        v = self.get(b)
        if isinstance(v, tuple):
            return (v[0], v[1] + mem.disp)
        return None

    def step(self, ins):
        ops = ins.operands
        mn = ins.mnemonic
        wide = ins.op_str.startswith("x") or ins.op_str.startswith("sp")
        mask = 0xFFFFFFFFFFFFFFFF if wide else 0xFFFFFFFF
        if mn in ("mov", "movz", "movn") and len(ops) == 2:
            d = regname(ops[0].reg)
            if ops[1].type == A.ARM64_OP_IMM:
                self.r[d] = ops[1].imm & mask
            elif ops[1].type == A.ARM64_OP_REG:
                v = self.get(regname(ops[1].reg))
                self.r[d] = v & mask if isinstance(v, int) else v
            return
        if mn == "movk":
            d = regname(ops[0].reg)
            v = self.get(d)
            sh = ops[1].shift.value if ops[1].shift.type else 0
            if isinstance(v, int):
                self.r[d] = (v & ~(0xFFFF << sh) | (ops[1].imm << sh)) & mask
            return
        if mn == "adrp":
            self.r[regname(ops[0].reg)] = ops[1].imm
            return
        if mn in ("add", "sub") and len(ops) == 3 and ops[2].type == A.ARM64_OP_IMM:
            d = regname(ops[0].reg)
            v = self.get(regname(ops[1].reg))
            imm = ops[2].imm << (ops[2].shift.value if ops[2].shift.type else 0)
            if mn == "sub":
                imm = -imm
            if isinstance(v, int):
                self.r[d] = (v + imm) & mask
            elif isinstance(v, tuple):
                self.r[d] = (v[0], v[1] + imm)
            else:
                self.r[d] = None
            return
        if mn in ("str", "stur", "stp", "strb", "strh", "sturb", "sturh"):
            memop = ops[-1]
            a = self.addr(memop.mem)
            regs = [o for o in ops[:-1] if o.type == A.ARM64_OP_REG]
            size = 8 if ins.op_str.startswith("x") else 4
            if mn in ("strb", "sturb"):
                size = 1
            if mn in ("strh", "sturh"):
                size = 2
            post = ins.writeback and len(ops) > len(regs) + 1
            pre = ins.writeback and not post
            base = regname(memop.mem.base)
            if a is not None:
                ea = a if not post else (a[0], a[1] - memop.mem.disp)
                for k, o in enumerate(regs):
                    self.stk[(ea[0], ea[1] + k * size)] = self.get(regname(o.reg))
            if pre and isinstance(self.get(base), tuple):
                v = self.get(base)
                self.r[base] = (v[0], v[1] + memop.mem.disp)
            if post:
                v = self.get(base)
                if isinstance(v, tuple):
                    self.r[base] = (v[0], v[1] + ops[-1].imm if ops[-1].type == A.ARM64_OP_IMM else v[1])
            return
        if mn in ("ldr", "ldur", "ldp") and ops[-1].type == A.ARM64_OP_MEM:
            a = self.addr(ops[-1].mem)
            base = regname(ops[-1].mem.base)
            bv = self.get(base)
            regs = [o for o in ops if o.type == A.ARM64_OP_REG]
            size = 8 if ins.op_str.startswith("x") else 4
            for k, o in enumerate(regs):
                d = regname(o.reg)
                val = None
                if a is not None:
                    val = self.stk.get((a[0], a[1] + k * size))
                elif isinstance(bv, int) and len(regs) == 1 and 0 <= bv - BASE + ops[-1].mem.disp < len(self.m):
                    off = bv - BASE + ops[-1].mem.disp
                    val = struct.unpack_from("<Q" if size == 8 else "<I", self.m, off)[0]
                self.r[d] = val
            return
        if mn in ("bl", "blr"):
            for i in range(19):
                self.r.pop(f"x{i}", None)
            self.r.pop("x30", None)
            return
        if ops and ops[0].type == A.ARM64_OP_REG and not mn.startswith(("st", "cmp", "tst", "cb", "tb", "b", "ret", "cmn", "fcmp", "prfm")):
            self.r[regname(ops[0].reg)] = None


def run_to(m, start, stop, on_call=None):
    """start~stop 직선 실행. on_call(emu, call_off, target)"""
    e = Emu(m)
    p = start
    while p < stop:
        ins = next(_md.disasm(m[p:p + 4], BASE + p), None)
        if ins is None:
            p += 4
            continue
        if ins.mnemonic == "bl" and on_call:
            on_call(e, p, ins.operands[0].imm)
        e.step(ins)
        p += 4
    return e


def s(m, v):
    if isinstance(v, int) and BASE <= v < BASE + len(m):
        return cstr_at(m, v - BASE, 200)
    return None
