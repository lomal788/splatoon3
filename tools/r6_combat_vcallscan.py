"""vt+<off> 가상 호출(ldr xA,[xB,#off]; ... blr xA) 중 직전 N개 명령에서 지정 레지스터들이 설정되는 곳 찾기.
사용: PY web/tools/r6_combat_vcallscan.py <off> <lo> <hi> [--regs w1,w2] [--back 10]
"""
import argparse, re, sys
from pathlib import Path
import capstone
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img  # noqa
sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("off"); ap.add_argument("lo"); ap.add_argument("hi")
ap.add_argument("--regs", default="w1,w2"); ap.add_argument("--back", type=int, default=10)
a = ap.parse_args()
img = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
lo, hi = int(a.lo, 16), int(a.hi, 16)
off = int(a.off, 16)
regs = a.regs.split(",")
ins = []
for addr in range(lo, hi, 4):
    w = img[addr - BASE: addr - BASE + 4]
    d = next(md.disasm(w, addr), None)
    ins.append((addr, (d.mnemonic + " " + d.op_str) if d else "?"))
pat = re.compile(r"ldr (x\d+), \[x\d+, #%s\]$" % hex(off))
for i, (ad, t) in enumerate(ins):
    m = pat.match(t)
    if not m:
        continue
    r = m.group(1)
    for j in range(i + 1, min(i + 5, len(ins))):
        if ins[j][1] == "blr " + r:
            prev = [x[1] for x in ins[max(0, i - a.back): j]]
            ok = all(any(re.match(r"\w+ %s, " % g, p) for p in prev) for g in regs)
            if ok:
                print(hex(ad), "|", " ; ".join(prev[-a.back:]))
            break
