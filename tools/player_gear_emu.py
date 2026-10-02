"""원본 PlayerParam 기어 계산 함수를 unicorn으로 직접 실행해 player_gear.py 재구현과 비교한다.

대상: 0x710265df40 (HumanMoveUp → PlayerParam+0xb0/+0xb4/+0xb8/+0xbc)
      0x710265fd48 (SquidMoveUp → +0xc0/+0xc4/+0xc8)
      0x7102665ee4 (OpInkEffectReduction → +0x100..+0x118)

합성 상태:
- PlayerParam 객체(0x260 B)를 빈 메모리에 만들고 AP(+0x3c+id*4 메인, +0x74+id*4 서브)를 넣는다.
- 기어 파라미터 객체는 생성자 기본값(param_reflect 판독값)을 필드 오프셋에 쓰고, "설정됨" 플래그 바이트를
  모두 1로 둬 $parent 탐색을 건너뛴다(데이터 파일에 값이 없을 때 생성자 기본값을 쓰는 것과 같은 결과).
- +0x148(MainWeaponSetting) = 0, +0xac(특수 능력 비트) = 인자.
- 기어 열거 표(0x71058c0458 개수, 0x71058c0460 포인터, 가드 0x71058c0468)는 0..13 항등 표로,
  특수 능력 표(0x71058bc378/0x71058bc380/가드 0x71058bc388)는 값 100..111로 채운다.
- logf/expf/powf/sqrtf PLT는 numpy float32로 계산해 돌려준다(그 밖의 PLT는 x0=0 반환).
검증 범위: 위 세 함수 단독 실행. 실제 게임에서 AP 값이 어떻게 채워지는지(0x710265ca78)는 포함하지 않는다.
"""
import argparse
import math
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_S0, UC_ARM64_REG_S1,
                                 UC_ARM64_REG_X0)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from player_initemu import Emu
from player_gear import ap_to_rate, gear_lerp, HUMAN, SQUID, OPINK

f32 = np.float32
HEAP = 0x7F00000000
PLT = {0x7103E9C2A0: "logf", 0x7103E9BE20: "expf", 0x7103E9BB60: "powf", 0x7103E9BB50: "sqrtf"}


def fbits(x):
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def bitsf(u):
    return struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0]


class GearEmu(Emu):
    def __init__(self):
        super().__init__()
        self.uc.mem_map(HEAP, 0x10000)
        self.uc.hook_add(UC_HOOK_CODE, self._math, begin=0x7103E9B000, end=0x7103E9D000)
        # 기어 열거 표: 개수 14, 포인터 → HEAP+0x8000, 항등 0..13, 가드 바이트 1
        tbl = HEAP + 0x8000
        self.uc.mem_write(tbl, b"".join(struct.pack("<i", i) for i in range(14)))
        self.uc.mem_write(0x71058C0458, struct.pack("<I", 14))
        self.uc.mem_write(0x71058C0460, struct.pack("<Q", tbl))
        self.uc.mem_write(0x71058C0468, b"\x01")
        # 특수 능력 열거 표(0x71058bc378 개수, 0x71058bc380 포인터, 가드 0x71058bc388): 값 100..111
        tbl2 = HEAP + 0x8100
        self.uc.mem_write(tbl2, b"".join(struct.pack("<i", 100 + i) for i in range(12)))
        self.uc.mem_write(0x71058BC378, struct.pack("<I", 12))
        self.uc.mem_write(0x71058BC380, struct.pack("<Q", tbl2))
        self.uc.mem_write(0x71058BC388, b"\x01")
        # 정적 초기화 0x710265c230이 채우는 상수 구조체(0x71058c0340)를 원본 함수로 실행해 채운다(0x34c = 0.8 등)
        r = self.run(0x710265C230)
        if r is not True:
            raise RuntimeError(f"init 0x710265c230: {r}")

    def _math(self, uc, addr, size, ud):
        name = PLT.get(addr)
        if name is None:
            return
        s0 = bitsf(uc.reg_read(UC_ARM64_REG_S0))
        s1 = bitsf(uc.reg_read(UC_ARM64_REG_S1))
        if name == "logf":
            r = f32(math.log(s0)) if s0 > 0 else f32(-math.inf)
        elif name == "expf":
            r = f32(math.exp(s0))
        elif name == "powf":
            r = f32(math.pow(s0, s1))
        else:
            r = f32(math.sqrt(s0))
        uc.reg_write(UC_ARM64_REG_S0, fbits(r))
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def make_param(self, base, fields, flag_lo, flag_hi):
        self.uc.mem_write(base, b"\0" * 0x100)
        for off, val in fields.items():
            self.uc.mem_write(base + off, struct.pack("<f", val))
        self.uc.mem_write(base + flag_lo, b"\x01" * (flag_hi - flag_lo))

    def run_gear(self, func, skill_id, ap_main, ap_sub, ptr_off, pobj, special_bits=0):
        pp = HEAP
        self.uc.mem_write(pp, b"\0" * 0x260)
        self.uc.mem_write(pp + 0x3C + skill_id * 4, struct.pack("<i", ap_main))
        self.uc.mem_write(pp + 0x74 + skill_id * 4, struct.pack("<i", ap_sub))
        self.uc.mem_write(pp + 0xAC, struct.pack("<I", special_bits))
        self.uc.mem_write(pp + ptr_off, struct.pack("<Q", pobj))
        self.uc.reg_write(UC_ARM64_REG_X0, pp)
        r = self.run(func)
        if r is not True:
            raise RuntimeError(r)
        return pp

    def rd(self, a):
        return struct.unpack("<f", self.uc.mem_read(a, 4))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aps", default="0,3,6,9,10,13,16,19,20,22,26,29,30,32,35,39,41,45,48,51,54,57")
    a = ap.parse_args()
    e = GearEmu()
    human = HEAP + 0x1000
    e.make_param(human, {0x40: 0.096, 0x44: 0.12, 0x3C: 0.144, 0x4C: 0.088, 0x50: 0.116, 0x48: 0.144,
                         0x34: 0.104, 0x38: 0.124, 0x30: 0.144, 0x58: 1.0, 0x5C: 1.125, 0x54: 1.25}, 0x60, 0x6C)
    squid = HEAP + 0x2000
    e.make_param(squid, {0x40: 0.192, 0x44: 0.216, 0x3C: 0.24, 0x4C: 0.1728, 0x50: 0.216, 0x48: 0.24,
                         0x34: 0.2016, 0x38: 0.2208, 0x30: 0.24}, 0x54, 0x5D)
    opink = HEAP + 0x3000
    e.make_param(opink, {0x58: 0.08, 0x5C: 0.098, 0x54: 0.11, 0x64: 0.024, 0x68: 0.05568, 0x60: 0.0768,
                         0x70: 0.012, 0x74: 0.033, 0x6C: 0.042, 0x7C: 0.5, 0x80: 0.75, 0x78: 1.0,
                         0x4C: 0.003, 0x50: 0.00225, 0x48: 0.0015, 0x40: 0.4, 0x44: 0.3, 0x3C: 0.2,
                         0x34: 0.0, 0x38: 26.0, 0x30: 39.0}, 0x84, 0x9B)
    cases = [
        ("Human", 0x710265DF40, 3, 0x198, human, 0, {0xB0: HUMAN["Mid"], 0xB4: HUMAN["Slow"], 0xB8: HUMAN["Fast"], 0xBC: HUMAN["Shot"]}, False),
        ("Squid", 0x710265FD48, 4, 0x1A0, squid, 0, {0xC0: SQUID["Mid"], 0xC4: SQUID["Slow"], 0xC8: SQUID["Fast"]}, False),
        ("SquidNinjaBit4", 0x710265FD48, 4, 0x1A0, squid, 1 << 4, {0xC0: SQUID["Mid"], 0xC4: SQUID["Slow"], 0xC8: SQUID["Fast"]}, True),
        ("OpInk", 0x7102665EE4, 11, 0x1F0, opink, 0, {0x100: OPINK["JumpVel"], 0x104: OPINK["MoveVel"], 0x108: OPINK["MoveVel_Shot"],
                                                         0x10C: OPINK["MoveVel_ShotK"], 0x110: OPINK["DamagePerFrame"],
                                                         0x114: OPINK["DamageLmt"], 0x118: OPINK["ArmorHP"]}, False),
    ]
    worst = 0.0
    n = 0
    for name, func, sid, poff, pobj, bits, outs, ninja in cases:
        for x in [int(v) for v in a.aps.split(",")]:
            for main_ap, sub_ap in ((x, 0), (0, x)) if x else ((0, 0),):
                pp = e.run_gear(func, sid, main_ap, sub_ap, poff, pobj, bits)
                rate = ap_to_rate(main_ap + sub_ap, ninja)
                row = []
                for off, lmh in outs.items():
                    got = e.rd(pp + off)
                    exp = float(gear_lerp(*lmh, rate))
                    d = abs(got - exp)
                    worst = max(worst, d)
                    n += 1
                    row.append(f"+{off:#x}={got:.7g}" + ("" if d == 0 else f"(재구현 {exp:.7g}, 차 {d:.2e})"))
                print(f"{name:15s} AP main={main_ap:2d} sub={sub_ap:2d}  " + " ".join(row))
    print(f"# 비교 {n}건, 최대 절대 차 {worst:.3e}")


if __name__ == "__main__":
    main()
