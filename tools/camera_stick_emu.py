"""[camrest] 오른쪽 스틱 기록 함수 0x71024a73b8(본체+0xa9c 구조체 채움)를 unicorn 으로 원본 실행해
세이브 IsReverseUD(+0x4001)/IsReverseLR(+0x4002)가 스틱 값에 적용되는 방식을 확인한다.

원본 실행: 0x71024a73b8(x0 = 본체+0xa9c 흉내 버퍼, x1 = 본체+0xa890 흉내 객체(+0x68 = 0 → 컨트롤러 경로), x2 = int*)
스텁: 0x7103d55638(컨트롤러 조회) → 가짜 컨트롤러(+0x128 오른쪽 스틱 x, +0x12c y, +0x114 플래그),
      0x71024c99f0(조작 불가 판정) → 0 반환. 세이브 객체 포인터(전역 0x71058ab398, GOT 0x710579df10 가 가리킴)는 가짜 세이브로 바꿈.
기대(판독): out+0 = (LR? -x : x), out+4 = (UD? -y : y), out+8/+0xc = 원시(반전 전) x,y - 이전 out+0/+4(반전 후 값).

사용: camera_stick_emu.py
"""
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
FUNC = 0x71024a73b8
CTRL_GET = 0x7103d55638
NOCTRL = 0x71024c99f0
SAVE_PTR = 0x71058ab398
STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000


def f(v):
    return struct.pack("<f", v)


def run(x, y, rev_ud, rev_lr, prev=(0.0, 0.0)):
    img = IMG.read_bytes()
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
    mu.mem_write(BASE, img)
    for a in (STACK, HEAP, STUB):
        mu.mem_map(a, 0x100000)
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
    mu.mem_write(STUB, struct.pack("<I", 0xD65F03C0) * 0x400)
    ctrl, save, obj, out, i464, mgr = HEAP + 0x1000, HEAP + 0x10000, HEAP + 0x20000, HEAP + 0x30000, HEAP + 0x31000, HEAP + 0x32000
    mu.mem_write(ctrl + 0x128, f(x) + f(y))
    mu.mem_write(ctrl + 0x114, struct.pack("<I", 0))
    mu.mem_write(save + 0x4001, bytes([1 if rev_ud else 0, 1 if rev_lr else 0]))
    mu.mem_write(SAVE_PTR, struct.pack("<Q", save))
    mu.mem_write(obj + 0x68, struct.pack("<Q", 0))
    mu.mem_write(out, f(prev[0]) + f(prev[1]))
    mu.mem_write(i464, struct.pack("<i", 7))
    # 컨트롤러 관리자 전역(*0x7105790f50 = 0x71059a57d0)의 객체: +0x110 인덱스만 읽힘
    mu.mem_write(0x71059a57d0, struct.pack("<Q", mgr))

    def hook(uc, addr, size, _):
        if addr == CTRL_GET:
            uc.reg_write(UC_ARM64_REG_X0, ctrl)
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
        elif addr == NOCTRL:
            uc.reg_write(UC_ARM64_REG_X0, 0)
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
    mu.hook_add(UC_HOOK_CODE, hook, begin=CTRL_GET, end=CTRL_GET)
    mu.hook_add(UC_HOOK_CODE, hook, begin=NOCTRL, end=NOCTRL)
    mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
    mu.reg_write(UC_ARM64_REG_X0, out)
    mu.reg_write(UC_ARM64_REG_X1, obj)
    mu.reg_write(UC_ARM64_REG_X2, i464)
    mu.reg_write(UC_ARM64_REG_X30, STUB + 0xF00)
    mu.emu_start(FUNC, STUB + 0xF00, count=5000)
    return struct.unpack("<4f", mu.mem_read(out, 16))


def main():
    ok = True
    cases = [(0.5, -0.25, False, False), (0.5, -0.25, True, False), (0.5, -0.25, False, True), (0.5, -0.25, True, True)]
    for x, y, ud, lr in cases:
        prev = (0.1, 0.2)
        r = run(x, y, ud, lr, prev)
        ex = (-x if lr else x, -y if ud else y, x - prev[0], y - prev[1])
        good = all(abs(a - b) < 1e-6 for a, b in zip(r, ex))
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} raw=({x},{y}) UD={ud} LR={lr} prev={prev} -> out={tuple(round(v, 6) for v in r)} 기대={ex}")
    print("ALL PASS" if ok else "SOME FAIL")


if __name__ == "__main__":
    main()
