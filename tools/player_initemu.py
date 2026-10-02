"""정적 초기화 함수(.init_array)를 unicorn으로 실행해 bss 전역 상수 값을 뽑는다.

플레이어 코드의 상수(fRam00000071058bbXXX 등)는 bss에 있고 TU별 정적 초기화 함수가 채운다.
이 도구는 main.reloc.img를 0x7100000000에 올리고 지정 함수를 실행한 뒤, 지정 구간에서
바뀐 4바이트 단위 값을 f32/s32로 출력한다. PLT(외부 함수) 호출은 x0=0으로 즉시 반환하고,
지정 구간 밖 쓰기도 허용한다(같은 이미지 안이면 기록됨).

사용:
  player_initemu.py <구간시작> <구간끝> <함수...> [--json 출력.json]
  player_initemu.py 0x71058bb000 0x71058c1000 --all-init   # init_array 전체 중 구간에 쓰는 함수만
"""
import argparse
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_LR, UC_ARM64_REG_SP, UC_ARM64_REG_X0

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, RAW, load_img

PLT_LO, PLT_HI = 0x7103E99000, 0x7103E9E000
STACK = 0x7FF0000000
RET_MAGIC = 0x7FFF000000


def init_array_funcs():
    raw = RAW.read_bytes()
    m = load_img()
    mod0 = struct.unpack_from("<I", raw, 4)[0]
    dyn = mod0 + struct.unpack_from("<i", raw, mod0 + 4)[0]
    tags = {}
    while True:
        t, v = struct.unpack_from("<qQ", raw, dyn)
        dyn += 16
        if t == 0:
            break
        tags.setdefault(t, v)
    ia, isz = tags[25], tags[27]
    return [struct.unpack_from("<Q", m, ia + i * 8)[0] for i in range(isz // 8)]


class Emu:
    def __init__(self):
        img = load_img()
        size = (len(img) + 0xFFFF) & ~0xFFFF
        size = max(size, 0x5A00000)
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        self.uc.mem_map(BASE, size)
        self.uc.mem_write(BASE, bytes(img))
        self.uc.mem_map(STACK - 0x100000, 0x200000)
        self.uc.mem_map(RET_MAGIC, 0x1000)
        self.uc.hook_add(UC_HOOK_CODE, self._code, begin=PLT_LO, end=PLT_HI)
        self.uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)
        self.faults = []

    def _code(self, uc, addr, size, ud):
        uc.reg_write(UC_ARM64_REG_X0, 0)
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def _unmapped(self, uc, access, addr, size, value, ud):
        self.faults.append(addr)
        return False

    def run(self, func, count=2_000_000):
        uc = self.uc
        uc.reg_write(UC_ARM64_REG_SP, STACK)
        uc.reg_write(UC_ARM64_REG_LR, RET_MAGIC)
        try:
            uc.emu_start(func, RET_MAGIC, count=count)
            return True
        except Exception as e:  # noqa
            return f"{e} pc={hex(uc.reg_read(UC_ARM64_REG_PC))}"

    def read(self, lo, hi):
        return self.uc.mem_read(lo, hi - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lo")
    ap.add_argument("hi")
    ap.add_argument("funcs", nargs="*")
    ap.add_argument("--all-init", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    lo, hi = int(a.lo, 16), int(a.hi, 16)
    emu = Emu()
    before = bytes(emu.read(lo, hi))
    funcs = [int(f, 16) for f in a.funcs]
    if a.all_init:
        funcs += init_array_funcs()
    writer = {}
    for f in funcs:
        cur = bytes(emu.read(lo, hi))
        r = emu.run(f)
        after = bytes(emu.read(lo, hi))
        if after != cur:
            for i in range(0, hi - lo, 4):
                if after[i:i + 4] != cur[i:i + 4]:
                    writer[lo + i] = f
            if r is not True:
                print(f"# {hex(f)}: {r}", file=sys.stderr)
    after = bytes(emu.read(lo, hi))
    out = {}
    for i in range(0, hi - lo, 4):
        if after[i:i + 4] != before[i:i + 4]:
            u = struct.unpack_from("<I", after, i)[0]
            fl = struct.unpack_from("<f", after, i)[0]
            out[hex(lo + i)] = {"u32": u, "f32": fl, "writer": hex(writer.get(lo + i, 0))}
    for k, v in out.items():
        print(f"{k} {v['u32']:#010x} f32={v['f32']:.9g} s32={struct.unpack('<i', struct.pack('<I', v['u32']))[0]} by {v['writer']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
