"""r6 camweapon: 대전 설정 RandomSeed0..3(+0xa4..+0xb0) 저장 후보 전수 스캔.

같은 베이스 레지스터로 +0xa4 와 +0xac(또는 +0xb0)에 저장하는 명령이 12명령 안에 함께 있는 곳을 찾는다.
(str w / str x / stp w,w / stp x,x / stur 모두 포함)
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capstone
from capstone import arm64_const as A
from xref import BASE, TEXT_END, load_img

m = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
md.detail = True
md.skipdata = True
lo, hi = 0x7100800000, BASE + TEXT_END


def stores(x):
    if x.mnemonic not in ("str", "stur", "stp", "stnp"):
        return None
    op = x.operands[-1]
    if op.type != A.ARM64_OP_MEM or x.operands[0].type != A.ARM64_OP_REG:
        return None
    n = 2 if x.mnemonic in ("stp", "stnp") else 1
    w = 4 if md.reg_name(x.operands[0].reg).startswith("w") else 8
    offs = [op.mem.disp + i * w for i in range(n)]
    cover = set()
    for o in offs:
        cover.update(range(o, o + w, 4))
    return md.reg_name(op.mem.base), cover


hits = []
win = []
CH = 0x400000
for s in range(lo, hi, CH):
    for x in md.disasm(bytes(m[s - BASE: min(s + CH, hi) - BASE]), s):
        st = stores(x)
        win.append((x, st))
        if len(win) > 24:
            win.pop(0)
        if len(win) == 24:
            cx, cst = win[12]
            if cst and 0xA4 in cst[1]:
                base = cst[0]
                cov = set()
                for y, yst in win:
                    if yst and yst[0] == base:
                        cov |= yst[1]
                if {0xA4, 0xA8, 0xAC, 0xB0} <= cov:
                    hits.append(cx.address)
for h in hits:
    print(hex(h))
print("total", len(hits))
