"""r6 gfx_char: LOD 레코드(모델 +0x38 배열, 0x50 B, [Start, 2Start−End, 1/(End−Start)]) reader 후보 찾기.

조건(같은 함수 안, capstone):
  1) ldr xA, [xB, #0x38]
  2) add xD, xA, xI, lsl #4 (xI = 5·i 꼴) 또는 xK = 0x50 (mov) 이고 madd/umaddl/smaddl xD, xI, xK, xA  또는  add xD, xA, xI, lsl/uxtw 와 이전 mul 0x50
  3) xD 기준 ldr s?, [xD, #0|#4|#8] (또는 ldp s, s, [xD])
rd == rn 쓰기, sp 기준은 제외한다. 함수 경계는 analysis/functions/main.nso.tsv.
사용: PY web/tools/r6_gfx_char_lodscan.py [--lo 0x7100000000 --hi 0x7103e99000]
"""
import argparse
import bisect
import struct
import sys
from pathlib import Path

import capstone
from capstone import arm64_const as A

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=lambda s: int(s, 16), default=BASE)
    ap.add_argument("--hi", type=lambda s: int(s, 16), default=0x7103E99000)
    a = ap.parse_args()
    img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
    rows = []
    for ln in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        p = ln.split("\t")
        s = int(p[0], 16)
        if a.lo <= s < a.hi:
            rows.append((s, int(p[1])))
    rows.sort()
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.detail = True
    md.skipdata = True
    hits = []
    for s, n in rows:
        code = img[s - BASE:s - BASE + n]
        if b"\x00\x0a\x80\x52" not in code and b"\x00\x0a\x80\xd2" not in code and b"\x0a\x80" not in code:
            pass
        ins = list(md.disasm(code, s))
        base38 = {}
        k50 = set()
        rec = {}
        found = []
        for i in ins:
            ops = i.operands if i.id != 0 else []
            m = i.mnemonic
            if m == "ldr" and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM and ops[1].mem.disp == 0x38 \
                    and ops[1].mem.base != A.ARM64_REG_SP and ops[0].reg != ops[1].mem.base and i.reg_name(ops[0].reg).startswith("x"):
                base38[ops[0].reg] = i.address
                continue
            if m in ("mov", "movz") and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM and ops[1].imm == 0x50:
                k50.add(ops[0].reg)
                continue
            if m in ("madd", "umaddl", "smaddl") and len(ops) == 4:
                regs = [o.reg for o in ops]
                if (regs[2] in k50 or regs[1] in k50) and regs[3] in base38:
                    rec[regs[0]] = (base38[regs[3]], i.address)
                    continue
            if m == "add" and len(ops) == 3 and ops[1].type == A.ARM64_OP_REG and ops[1].reg in base38                     and ops[2].type == A.ARM64_OP_REG and ops[2].shift.type == A.ARM64_SFT_LSL and ops[2].shift.value == 4:
                rec[ops[0].reg] = (base38[ops[1].reg], i.address)
                continue
            if m in ("ldr", "ldp", "ldur") and ops and ops[-1].type == A.ARM64_OP_MEM and ops[-1].mem.base in rec \
                    and ops[-1].mem.disp in (0, 4, 8) and i.reg_name(ops[0].reg).startswith("s"):
                found.append((rec[ops[-1].mem.base], i.address, i.mnemonic + " " + i.op_str))
        if found:
            hits.append((s, found))
    for s, f in hits:
        print(hex(s), "; ".join(f"ldr38@{hex(b)} madd@{hex(c)} -> {hex(d)} {t}" for (b, c), d, t in f[:4]))


if __name__ == "__main__":
    main()
