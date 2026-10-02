"""r6 camweapon: r6_camweapon_seedstore_scan.py 결과(후보 주소 목록)를 걸러 +0xa4..+0xb0 에 0 이 아닌 레지스터 4칸을 저장하는 곳만 남긴다."""
import bisect, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capstone
from capstone import arm64_const as A
from xref import BASE, load_img
ROOT = Path(__file__).resolve().parents[2]
m = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM); md.detail = True; md.skipdata = True
starts = []
for line in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8").splitlines()[1:]:
    starts.append(int(line.split("\t")[0], 16))
hits = [int(l, 16) for l in Path(sys.argv[1]).read_text().split() if l.startswith("0x")]
res = {}
for h in hits:
    ins = list(md.disasm(bytes(m[h - 48 - BASE:h + 52 - BASE]), h - 48))
    base = None
    for x in ins:
        if x.address == h:
            base = md.reg_name(x.operands[-1].mem.base)
    cov = {}
    for x in ins:
        if x.mnemonic in ("str", "stur", "stp") and x.operands[-1].type == A.ARM64_OP_MEM and md.reg_name(x.operands[-1].mem.base) == base:
            regs = [o.reg for o in x.operands[:-1]]
            w = 4 if md.reg_name(regs[0]).startswith("w") else 8
            for i, r in enumerate(regs):
                nm = md.reg_name(r)
                for k in range(0, w, 4):
                    cov[x.operands[-1].mem.disp + i * w + k] = nm
    if all(o in cov and cov[o] not in ("wzr", "xzr") for o in (0xA4, 0xA8, 0xAC, 0xB0)):
        fs = starts[bisect.bisect_right(starts, h) - 1]
        res.setdefault(fs, []).append(h)
for fs, hs in sorted(res.items()):
    print(f"func {fs:#x}: {' '.join(hex(h) for h in hs)}")
print("funcs", len(res))
