"""r6 ui: MSBT 숫자 태그 [2:0:p0 p1 p2 p3] 처리 함수를 unicorn 으로 원본 실행해 결과 문자열을 얻는다.

원본
  태그 분기 0x7101360478 (게임 TagProcessor vtable 0x710557cce0 슬롯 22): 그룹(+2) 2 → 0x7101360544
  0x7101360544: 종류(+4) 0 = 정수 삽입. p0=인자 번호(<16 이면 args+8+4*p0 의 s32), p1→w2=max(p1,1), p2→w3,
               숫자 문자열 = 0x71013616b0(버퍼, 값, w2, w3, 0); p3 == 0 이면 ASCII 0x21..0x7e → +0xFEE0(전각), 공백 → U+3000
  결과를 출력 버퍼(x2)[*x3] 에 붙이고 *x3, *x4 += 글자 수
스텁: libc PLT(memcpy 0x7103e99f20 등)만 파이썬 구현으로 대체, 그 밖 원본 그대로. 문자열 버퍼·인자 구조는 판독대로 구성.
사용: r6_ui_msbt_num_emu.py → analysis/r6_ui/msbt_num_emu.json
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_ui_lib import *

OUT = ROOT / "analysis" / "r6_ui" / "msbt_num_emu.json"
FN = 0x7101360544


_E = None


def run(params, values, kind=0):
    global _E
    if _E is None:
        _E = Emu()
        hook_libc(_E)
    e = _E
    e.heap_next = e.HEAP + 0x1000
    tag = e.alloc(0x20)
    e.mu.mem_write(tag, struct.pack("<HHHH", 0x0E, 2, kind, len(params)) + bytes(params))
    outbuf = e.alloc(0x200)
    plen = e.alloc(8)
    pcnt = e.alloc(8)
    args = e.alloc(0x60)
    for i, v in enumerate(values):
        e.mu.mem_write(args + 8 + 4 * i, struct.pack("<i", v))
    # 스택 인자: 진입 sp 위치 = args 포인터
    sp = e.STACK + 0x1F0000
    e.mu.mem_write(sp, struct.pack("<Q", args))
    mu = e.mu
    for r, v in zip(XREGS, (0, tag, outbuf, plen, pcnt, 0x100, 0, 0)):
        mu.reg_write(r, v)
    mu.reg_write(UC_ARM64_REG_SP, sp)
    mu.reg_write(UC_ARM64_REG_X30, e.STUB + 0xFFF0)
    mu.emu_start(FN, e.STUB + 0xFFF0, count=200000)
    n = struct.unpack("<I", mu.mem_read(plen, 4))[0]
    s = bytes(mu.mem_read(outbuf, 2 * n)).decode("utf-16-le")
    return s, n, struct.unpack("<I", mu.mem_read(pcnt, 4))[0]


def main():
    cases = []
    tags = {
        "Shr_Points_00 정수부 00 03 00 00": [0, 3, 0, 0],
        "Shr_Points_00 소수부 01 01 00 00": [1, 1, 0, 0],
        "VSTimer 분 00 02 00 00": [0, 2, 0, 0],
        "VSTimer 초 01 02 01 00": [1, 2, 1, 0],
        "MsnTimer 분 00 02 02 00": [0, 2, 2, 0],
        "MinSec_1Digit 분 00 01 00 00": [0, 1, 0, 0],
        "1/100초 02 02 01 00": [2, 2, 1, 0],
        "비교: p3=1 (00 03 00 01)": [0, 3, 0, 1],
        "비교: p2=1 (00 03 01 00)": [0, 3, 1, 0],
        "비교: p2=2 (00 03 02 00)": [0, 3, 2, 0],
    }
    vals = [0, 3, 9, 36, 120, 999, 1234, 12345, -5]
    for name, p in tags.items():
        row = {"tag": name, "params": p, "out": {}}
        for v in vals:
            args = [0, 0, 0]
            args[p[0]] = v
            s, n, c = run(p, args)
            row["out"][str(v)] = s
        cases.append(row)
        out(name, " | ".join(f"{v}→'{row['out'][str(v)]}'" for v in vals))
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
