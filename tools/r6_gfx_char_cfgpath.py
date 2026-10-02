"""r6 gfx_char: 함수 안 제어 흐름 경로 검사(capstone, bl 은 따라가지 않고 다음 명령으로).

  PY web/tools/r6_gfx_char_cfgpath.py <함수시작> <크기> <출발> <경유> [--write-off 0xf0 --base x19]
출발 주소에서 ret 까지 가는 경로 중 '경유' 주소를 지나지 않는 경로가 있는지, 그리고 출발~경유 사이에서
[base, #off] 에 쓰는 명령이 있는지 출력한다. 간접 분기(br)는 끝으로 본다(목록 출력).
"""
import argparse
import sys
from pathlib import Path

import capstone
from capstone import arm64_const as A

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    for k in ("start", "size", "src", "via"):
        ap.add_argument(k, type=lambda s: int(s, 0))
    ap.add_argument("--write-off", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--base", default="x19")
    a = ap.parse_args()
    img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.detail = True
    md.skipdata = True
    ins = {i.address: i for i in md.disasm(img[a.start - BASE:a.start - BASE + a.size], a.start)}
    end = a.start + a.size

    def succ(i):
        m = i.mnemonic
        if m == "ret":
            return []
        if m in ("br", "brk"):
            return None
        tgt = None
        for o in i.operands:
            if o.type == A.ARM64_OP_IMM:
                tgt = o.imm
        if m == "b":
            return [tgt]
        if m.startswith("b.") or m in ("cbz", "cbnz", "tbz", "tbnz"):
            return [i.address + 4, tgt]
        return [i.address + 4]

    seen, stack, rets, indirect, writes = set(), [a.src], [], [], []
    while stack:
        x = stack.pop()
        if x in seen or x == a.via:
            continue
        if not (a.start <= x < end) or x not in ins:
            rets.append(("out", hex(x)))
            continue
        seen.add(x)
        i = ins[x]
        if a.write_off is not None and i.mnemonic.startswith("st") and i.operands and \
                i.operands[-1].type == A.ARM64_OP_MEM and i.operands[-1].mem.disp == a.write_off and \
                i.reg_name(i.operands[-1].mem.base) == a.base:
            writes.append(f"{hex(x)} {i.mnemonic} {i.op_str}")
        s = succ(i)
        if s is None:
            indirect.append(hex(x))
            continue
        if not s:
            rets.append(("ret", hex(x)))
        stack.extend(t for t in s if t is not None)
    print("경유 없이 닿는 끝:", rets)
    print("간접 분기:", indirect)
    print("출발→경유 사이 쓰기:", writes)
    print("방문 명령 수:", len(seen))


if __name__ == "__main__":
    main()
