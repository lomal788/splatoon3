"""[life] HP 홀더 원본 함수를 unicorn 으로 실행해 재구현(life_hp.py)과 비교한다.

원본 실행 대상(수정 없음):
  0x7101a88ce0 HP 홀더 초기화(H, &init)
  0x7101a88e1c 리셋(H)
  0x7101a89524 데미지 누적(H, info, accumulate)
  0x7101a89790 회복(H, info)
  0x7101a8905c 프레임 갱신(s0=dt, H)
외부(PLT) 호출은 memcpy/memset/strlen 만 파이썬으로 처리하고 나머지는 0 반환 스텁.
사용: PY web/tools/life_emu.py   (시나리오 전부 실행, 불일치 시 종료코드 1)
"""
import random
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from life_hp import HpHolder, F  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK = 0x10000000
HEAP = 0x20000000
RETADDR = 0x30000000
PLT_LO, PLT_HI = 0x7103e99000, 0x7103e9e000


def imports():
    out = subprocess.run([sys.executable, str(Path(__file__).parent / "player_imports.py")],
                         capture_output=True, text=True).stdout
    d = {}
    for ln in out.splitlines():
        a, n = ln.split()
        d[int(a, 16)] = n
    return d


class Emu:
    def __init__(self):
        img = IMG.read_bytes()
        self.img = img
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x200000)
        mu.mem_map(RETADDR, 0x1000)
        mu.mem_write(RETADDR, struct.pack("<I", 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.mu = mu
        self.got = imports()
        self.calls = []
        mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)
        self.heap = HEAP

    def alloc(self, n):
        a = self.heap
        self.heap += (n + 0xFF) & ~0xFF
        self.mu.mem_write(a, b"\0" * n)
        return a

    def _plt(self, mu, addr, size, user):
        # PLT 스텁: adrp x16 ; ldr x17,[x16,#off] ; add ; br x17
        w0 = struct.unpack_from("<I", self.img, addr - BASE)[0]
        w1 = struct.unpack_from("<I", self.img, addr + 4 - BASE)[0]
        immlo = (w0 >> 29) & 3
        immhi = (w0 >> 5) & 0x7FFFF
        page = ((immhi << 2) | immlo) << 12
        if page & (1 << 32):
            page -= 1 << 33
        got = (addr & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
        name = self.got.get(got, f"?{got:#x}")
        x0, x1, x2 = (mu.reg_read(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2))
        ret = 0
        if name == "memcpy" or name == "memmove":
            if x2:
                mu.mem_write(x0, bytes(mu.mem_read(x1, x2)))
            ret = x0
        elif name == "memset":
            if x2:
                mu.mem_write(x0, bytes([x1 & 0xFF]) * x2)
            ret = x0
        elif name == "strlen":
            n = 0
            while mu.mem_read(x0 + n, 1)[0]:
                n += 1
            ret = n
        self.calls.append(name)
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def call(self, fn, *args, s0=None):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3]
        for r, v in zip(regs, args):
            mu.reg_write(r, v)
        if s0 is not None:
            mu.reg_write(UC_ARM64_REG_S0, struct.unpack("<I", struct.pack("<f", s0))[0])
        mu.reg_write(UC_ARM64_REG_LR, RETADDR)
        mu.emu_start(fn, RETADDR, count=2_000_000)

    def r32(self, a):
        return struct.unpack("<i", self.mu.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack("<i", v))

    def wf(self, a, v):
        self.mu.mem_write(a, struct.pack("<f", v))

    def rf(self, a):
        return struct.unpack("<f", self.mu.mem_read(a, 4))[0]


H_SIZE = 0xF00


def make_info(e, H, dmg, team, attacker):
    """DamageInfo(0xc8 B) = 홀더 내부 기록 H+0x50..+0x118 과 같은 배치. 초기화 직후 기록을 복사하고 문자열 버퍼 포인터를 고친다."""
    info = e.alloc(0x100)
    raw = bytes(e.mu.mem_read(H + 0x50, 0xC8))
    e.mu.mem_write(info, raw)
    e.mu.mem_write(info + 0x58, struct.pack("<Q", info + 0x64))
    e.w32(info, dmg)
    e.w32(info + 4, team)
    e.w32(info + 8, attacker)
    return info


def read_state(e, H):
    return dict(hp=e.r32(H + 0x4c), pending=e.r32(H + 0x50), wait=e.r32(H + 0x130),
                last=e.r32(H + 0x138), last_att=e.r32(H + 0x140), max=e.r32(H + 0x48))


def scenario(seed, steps=240):
    rnd = random.Random(seed)
    e = Emu()
    H = e.alloc(H_SIZE)
    initv = e.alloc(8)
    e.call(0x7101a88ce0, H, initv)
    e.w32(0x71058bbb78 + 0x1c0, 60)  # bss 상수(정적 초기화 0x7102455db0 결과, player_initemu)
    flags = rnd.choice([6, 2, 4, 0, 7, 3])
    mx = rnd.choice([1000, 1200, 200, 8000])
    drain = rnd.choice([0.0, 0.0, 30.0, 7.5, 123.4])
    regen = rnd.choice([0.0, 60.0, 100.0, 33.3, 250.0])
    e.w32(H, flags)
    e.w32(H + 0x48, mx)
    e.call(0x7101a88e1c, H)
    e.wf(H + 0x120, drain)
    e.wf(H + 0x124, regen)
    m = HpHolder()
    m.flags, m.max = flags, mx
    m.reset()
    m.drain, m.regen = F(drain), F(regen)
    dt = float(F(1) / F(60))
    bad = 0
    for t in range(steps):
        k = rnd.random()
        if k < 0.25:
            for _ in range(rnd.choice([1, 1, 2, 3])):
                d = rnd.choice([0, 1, 3, 50, 120, 180, 360, 999, 1000, 99999, -5])
                team, att = rnd.randrange(4), rnd.randrange(-1, 8)
                info = make_info(e, H, d, team, att)
                e.call(0x7101a89524, H, info, 1)
                m.add_damage(d, team, att)
        elif k < 0.32:
            c = rnd.choice([10, 100, 500])
            info = make_info(e, H, c, 0, 0)
            e.call(0x7101a89790, H, info)
            m.cure(c)
        e.call(0x7101a8905c, H, s0=dt)
        m.update(dt, wait_frames=60)
        s = read_state(e, H)
        mine = dict(hp=m.hp, pending=m.pending, wait=m.wait, last=m.last_dmg, last_att=m.last_attacker, max=m.max)
        if s != mine:
            bad += 1
            if bad <= 3:
                print(f"  seed {seed} t {t}: 원본 {s} / 재구현 {mine}")
    return bad, (flags, mx, drain, regen)


def main():
    total = 0
    for seed in range(40):
        bad, cfg = scenario(seed)
        total += bad
        print(f"seed {seed:2d} flags={cfg[0]} max={cfg[1]} drain={cfg[2]} regen={cfg[3]} : 불일치 {bad}/240")
    print("합계 불일치", total)
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
