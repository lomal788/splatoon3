import bisect
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capstone
from capstone import arm64_const as A
from xref import BASE, load_img

ROOT = Path(__file__).resolve().parents[2]
m = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
md.detail = True
md.skipdata = True

starts, sizes = [], []
for line in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8").splitlines()[1:]:
    p = line.split("\t")
    starts.append(int(p[0], 16) | 0x7100000000 if not p[0].startswith("71") else int(p[0], 16))
    sizes.append(int(p[1]))


def func_of(a):
    i = bisect.bisect_right(starts, a) - 1
    return starts[i], sizes[i]


GOT = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x7105790FC0
out = subprocess.run([sys.executable, str(ROOT / "web/tools/xref.py"), "addr", hex(GOT)], capture_output=True, text=True).stdout
refs = [int(t.rstrip("L"), 16) for t in out.split(":", 1)[1].split()]
def span(r):
    fs, sz = func_of(r)
    if fs <= r < fs + sz:
        return fs, sz
    return r - 0x10, 0x1000


funcs = sorted({span(r) for r in refs})

CALLER_SAVED = {f"x{i}" for i in range(19)} | {"x30"}


def rn(r):
    n = md.reg_name(r)
    if n.startswith("w"):
        n = "x" + n[1:]
    return n


getters = {}


def scan(fs, fsz, report):
    t = {}
    events = []
    code = bytes(m[fs - BASE: fs - BASE + fsz])
    for x in md.disasm(code, fs):
        ops = x.operands
        mn = x.mnemonic
        if mn in ("ldr", "ldur") and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM:
            d = rn(ops[0].reg)
            b = rn(ops[1].mem.base) if ops[1].mem.base else None
            off = ops[1].mem.disp
            v = None
            if b and b in t:
                bt = t[b]
                if bt == "GOT" and off == 0:
                    v = "G"
                elif bt == "G" and off in (0xC8, 0xD0):
                    v = "C8" if off == 0xC8 else "D0"
                elif bt in ("C8", "D0") and off != 0:
                    v = f"{bt}[{off:#x}]"
                    events.append((x.address, f"load {v}"))
            if x.address in refs or (b is None and False):
                v = "GOT"
            if v:
                t[d] = v
            else:
                t.pop(d, None)
            continue
        if mn == "ldp" and len(ops) == 3 and ops[2].type == A.ARM64_OP_MEM:
            b = rn(ops[2].mem.base)
            d1, d2 = rn(ops[0].reg), rn(ops[1].reg)
            off = ops[2].mem.disp
            t.pop(d1, None); t.pop(d2, None)
            if b in t and t[b] == "G" and off == 0xC8:
                t[d1], t[d2] = "C8", "D0"
                events.append((x.address, "ldp C8,D0"))
            continue
        if mn in ("str", "stur", "stp", "strb", "strh") and ops and ops[-1].type == A.ARM64_OP_MEM:
            b = rn(ops[-1].mem.base)
            if b in t and (t[b] in ("C8", "D0", "G") or t[b].endswith("[0x6548]")):
                src = [rn(o.reg) for o in ops[:-1] if o.type == A.ARM64_OP_REG]
                events.append((x.address, f"STORE {t[b]}+{ops[-1].mem.disp:#x} <- {[t.get(s, s) for s in src]}"))
            continue
        if mn == "mov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_REG:
            d, s = rn(ops[0].reg), rn(ops[1].reg)
            if s in t:
                t[d] = t[s]
            else:
                t.pop(d, None)
            continue
        if mn == "add" and len(ops) == 3 and ops[1].type == A.ARM64_OP_REG and ops[2].type == A.ARM64_OP_IMM:
            d, s = rn(ops[0].reg), rn(ops[1].reg)
            if s in t and t[s] in ("C8", "D0"):
                t[d] = f"&{t[s]}+{ops[2].imm:#x}"
                continue
        if mn in ("bl", "blr", "b", "br"):
            args = {r: t[r] for r in ("x0", "x1", "x2", "x3") if r in t}
            if args and mn != "b" or (mn == "b" and args and ops[0].type == A.ARM64_OP_IMM and not (fs <= ops[0].imm < fs + fsz)):
                tgt = hex(ops[0].imm) if ops[0].type == A.ARM64_OP_IMM else md.reg_name(ops[0].reg)
                events.append((x.address, f"{mn} {tgt} args={args}"))
            if mn in ("bl", "blr"):
                for r in list(t):
                    if r in CALLER_SAVED:
                        del t[r]
                if mn == "bl" and ops[0].imm in getters:
                    t["x0"] = getters[ops[0].imm]
            continue
        if mn == "ret":
            if "x0" in t and t["x0"] in ("C8", "D0", "G"):
                getters[fs] = t["x0"]
            continue
        if ops and ops[0].type == A.ARM64_OP_REG and mn not in ("cmp", "cmn", "tst", "cbz", "cbnz", "tbz", "tbnz"):
            t.pop(rn(ops[0].reg), None)
    if report and events:
        print(f"## func {fs:#x} size {fsz}")
        for a, e in events:
            print(f"   {a:#x} {e}")


for fs, fsz in funcs:
    scan(fs, fsz, False)
print("getters:", {hex(k): v for k, v in getters.items()})
for fs, fsz in funcs:
    scan(fs, fsz, True)
