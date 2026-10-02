"""명령 순서 패턴 검색: 정규식 A 다음 N개 명령 안에 정규식 B 가 나오는 위치.

사용: PY web/tools/combat4_seqscan.py <정규식A> <정규식B> [--win 4] --lo 0x.. --hi 0x..
예) 탄 바디 래퍼(+0x138) 가상 호출 슬롯 0x20:
    PY web/tools/combat4_seqscan.py "ldr x\\d+, \\[x\\d+, #0x138\\]" "ldr x\\d+, \\[x\\d+, #0x20\\]" --lo 0x7101640000 --hi 0x7101900000
"""
import argparse
import re
import sys
from pathlib import Path

import capstone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img  # noqa: E402
import func_lookup  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--win", type=int, default=4)
    ap.add_argument("--lo", required=True)
    ap.add_argument("--hi", required=True)
    x = ap.parse_args()
    ra, rb = re.compile(x.a), re.compile(x.b)
    m = load_img()
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    lo, hi = int(x.lo, 16), int(x.hi, 16)
    starts, rows = func_lookup.load()
    texts = []
    for addr in range(lo, hi, 4):
        ins = next(md.disasm(bytes(m[addr - BASE: addr - BASE + 4]), addr), None)
        texts.append((addr, f"{ins.mnemonic} {ins.op_str}" if ins else ""))
    for i, (addr, s) in enumerate(texts):
        if ra.search(s):
            for j in range(i + 1, min(i + 1 + x.win, len(texts))):
                if rb.search(texts[j][1]):
                    f = func_lookup.lookup(starts, rows, addr)
                    print(f"{addr:#x} [{f[0]:#x}]  {s}  ...  {texts[j][0]:#x} {texts[j][1]}")
                    break


if __name__ == "__main__":
    main()
