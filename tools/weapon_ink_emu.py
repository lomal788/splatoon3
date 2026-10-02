"""슈터 메인 사격의 잉크 소비·회복 정지·연사 타이머 원본 함수를 unicorn으로 실행해 파이썬 재구현과 비교한다.

대상(main NSO, 0x7100000000 기준):
  0x7102492120  잉크 소비/부족 판정 (안에서 0x7102491f88 회복량 함수 호출)
  0x7102491f88  프레임당 잉크 회복량
  0x7102551530  연사 타이머 (PlayerInkActionShooter+0x68)
  0x7102353718  잉크 회복 정지 프레임 설정

가짜 본체(0xb000 B)를 힙에 만들고 필요한 필드만 채운다. 전역은 오프라인(로컬 조작) 경로가 되도록
  [0x7105825fd0] -> 0 으로 채운 객체(+0x180 = 0)
  [0x7105801cc0] -> 관리자(+0xc70 -> 객체 +0x18 = -1)
을 넣고, 정적 초기화 상수 [0x71058bbf24] = 0.33(player_initemu 결과)을 쓴다. PLT 호출은 x0=0 반환.

사용: weapon_ink_emu.py [--n 2000] [--seed 1]
"""
import argparse
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import (UC_ARM64_REG_PC, UC_ARM64_REG_LR, UC_ARM64_REG_SP, UC_ARM64_REG_X0,
                                 UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_X4,
                                 UC_ARM64_REG_S0,
                                 UC_ARM64_REG_CPACR_EL1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img

PLT_LO, PLT_HI = 0x7103E99000, 0x7103E9E000
STACK = 0x7FF0000000
RET_MAGIC = 0x7FFF000000
HEAP = 0x7E00000000
F = np.float32

FN_CONSUME = 0x7102492120
FN_RATE = 0x7102491F88
FN_TIMER = 0x7102551530
FN_STOP = 0x7102353718


def f2u(x):
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def u2f(u):
    return F(struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0])


class Emu:
    def __init__(self):
        img = load_img()
        size = max((len(img) + 0xFFFF) & ~0xFFFF, 0x5A00000)
        uc = self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        uc.mem_map(BASE, size)
        uc.mem_write(BASE, bytes(img))
        uc.mem_map(STACK - 0x100000, 0x200000)
        uc.mem_map(RET_MAGIC, 0x1000)
        uc.mem_map(HEAP, 0x100000)
        uc.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        uc.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)
        self.calls = []
        self.faults = []
        self.next = HEAP
        self.w32(0x71058BBF24, f2u(0.33))
        net = self.alloc(0x200)
        self.w64(0x7105825FD0, net)
        mgr = self.alloc(0x1000)
        idx = self.alloc(0x40)
        self.w32(idx + 0x18, 0xFFFFFFFF)
        self.w64(mgr + 0xC70, idx)
        self.w64(0x7105801CC0, mgr)
        self.body = self.alloc(0xB000)
        self.pp = self.alloc(0x260)
        self.winfo_holder = self.alloc(0x300)
        self.winfo = self.alloc(0x40)
        self.owner = self.alloc(0x200)
        self.timer = self.alloc(0x40)

    def alloc(self, n):
        a = self.next
        self.next += (n + 0xFF) & ~0xFF
        return a

    def _plt(self, uc, addr, size, ud):
        self.calls.append(addr)
        uc.reg_write(UC_ARM64_REG_X0, 0)
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def _unmapped(self, uc, access, addr, size, value, ud):
        self.faults.append(addr)
        return False

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def w64(self, a, v):
        self.uc.mem_write(a, struct.pack("<Q", v))

    def wf(self, a, v):
        self.w32(a, f2u(v))

    def r32(self, a):
        return struct.unpack("<I", self.uc.mem_read(a, 4))[0]

    def rs32(self, a):
        return struct.unpack("<i", self.uc.mem_read(a, 4))[0]

    def rf(self, a):
        return u2f(self.r32(a))

    def run(self, fn, x=(), s0=None):
        uc = self.uc
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3]
        for r, v in zip(regs, x):
            uc.reg_write(r, v)
        if s0 is not None:
            uc.reg_write(UC_ARM64_REG_S0, f2u(s0))
        uc.reg_write(UC_ARM64_REG_SP, STACK)
        uc.reg_write(UC_ARM64_REG_LR, RET_MAGIC)
        uc.emu_start(fn, RET_MAGIC, count=200000)
        if self.faults:
            raise RuntimeError(f"unmapped {[hex(a) for a in self.faults]}")
        return uc.reg_read(UC_ARM64_REG_X0), u2f(uc.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF)

    def setup_body(self, ink, flag6d8, stealth, std_frm, stl_frm, weapon_id):
        b = self.body
        self.uc.mem_write(b, bytes(0xB000))
        self.wf(b + 0x698, ink)
        self.wf(b + 0x6A0, ink)
        self.uc.mem_write(b + 0x6D8, bytes([flag6d8]))
        self.wf(b + 0x6BC, stealth)
        self.w64(b + 0xA658, self.pp)
        self.wf(self.pp + 0xCC, std_frm)
        self.wf(self.pp + 0xD0, stl_frm)
        self.wf(self.pp + 0xD4, 1.0)
        self.w64(self.pp + 0x168, 0)
        self.w64(b + 0xA8D0, self.winfo_holder)
        self.w64(self.winfo_holder + 0x138, self.winfo)
        self.w64(self.winfo_holder + 0x2B8, 0)
        self.w32(self.winfo + 0x14, weapon_id)
        self.w32(b + 0x1058, 1)


def py_rate(stealth, std_frm, stl_frm, weapon_id, flag6d8):
    if flag6d8:
        return F(0)
    frm = F(stl_frm) if F(stealth) > 0 else F(std_frm)
    k = F(0.9090909) if (weapon_id % 10000) // 10 == 1 else F(1.0)
    return F(F(1.0) / frm) * k


def py_consume(cost, ink, partial_off, query, flag6d8, std_frm, stl_frm, weapon_id):
    cost, r = F(cost), F(ink)
    partial = bool(r < cost and r > 0 and not partial_off and flag6d8)
    if r < cost:
        d = F(r - cost)
        near = d >= u2f(0xB727C5AC) and d <= u2f(0x3727C5AC)
    else:
        near = False
    ok = bool(r >= cost) or partial or near
    out = dict(ok=ok, ink=r, s6b8=None)
    if query or not ok:
        return out
    new = F(0) if partial else F(r - cost)
    thr = py_rate(0.0, std_frm, stl_frm, weapon_id, flag6d8)
    if new < thr:
        new = F(0)
    out.update(ink=new, s6b8=(0, 0))
    return out


def py_timer(t, repeat):
    t = list(t)
    a = max(t[3], 1) - 1
    b = max(t[4], 1) - 1
    c = max(t[5], 1) - 1
    t[3], t[4], t[5] = a, b, c
    ph, rem = F(t[0]), F(t[1])
    if a > 0 or t[2] >= t[6]:
        return 0, t
    if b == 0 or (t[7] and ph < 1):
        step = F(F(1.0) / F(repeat))
        ph = F(step + ph)
        rem = F(F(F(1.0) - ph) / step)
        rem = rem if rem > 0 else F(0)
        t[0], t[1] = ph, rem
    if ph < 1:
        d = F(ph - F(1.0))
        if d < u2f(0xB727C5AC) or d > u2f(0x3727C5AC):
            return 0, t
        ph = F(1.0)
        t[0] = ph
    if b != 0 and t[7]:
        return 0, t
    t[0] = F(ph - F(1.0))
    return 1, t


def py_stop(cur, frames, set_flag, squid):
    v = cur if cur >= frames else frames
    s6b4 = int(F(0.33) * F(v)) if set_flag else None
    return v, s6b4


def check_consume(emu, rnd, n):
    bad = 0
    cases = []
    cost = F(0.0092)
    for v in [0, 1e-6, 0.0091899, 0.00919, 0.0091901, 0.0092, 0.0092001, 0.0093, 0.0108, 0.0109, 0.01086, 1.0]:
        cases.append((cost, F(v), 0, 0, 0, 0.0, 600.0, 180.0, 40))
    for _ in range(n):
        c = F(rnd.choice([0.0092, rnd.uniform(0, 0.05)]))
        ink = F(rnd.choice([rnd.uniform(-0.01, 1.0), c + F(rnd.uniform(-2e-5, 2e-5)), rnd.uniform(0, 0.02)]))
        cases.append((c, ink, rnd.randint(0, 1), rnd.randint(0, 1), rnd.randint(0, 1), rnd.choice([0.0, 0.5]),
                      rnd.choice([600.0, 410.0, 220.0]), rnd.choice([180.0, 117.0]), rnd.choice([40, 10, 11, 1000])))
    for (c, ink, poff, q, fl, stl, sf, tf, wid) in cases:
        emu.setup_body(ink, fl, stl, sf, tf, wid)
        emu.wf(emu.body + 0x6B8, 3.0)
        ret, _ = emu.run(FN_CONSUME, x=(emu.body + 0x698, emu.winfo_holder, poff, q), s0=c)
        e_ok = bool(ret & 1)
        e_ink = emu.rf(emu.body + 0x698)
        e6b8 = (emu.r32(emu.body + 0x6B8), emu.r32(emu.body + 0x6BC))
        p = py_consume(c, ink, poff, q, fl, sf, tf, wid)
        good = e_ok == p["ok"] and f2u(e_ink) == f2u(p["ink"])
        if p["s6b8"] is not None:
            good = good and e6b8 == (0, 0)
        if not good:
            bad += 1
            if bad <= 10:
                print("consume 불일치", c, ink, poff, q, fl, e_ok, e_ink, p)
    print(f"0x7102492120 소비: {len(cases)}건, 불일치 {bad}")
    return bad


def check_rate(emu, rnd, n):
    bad = 0
    for _ in range(n):
        stl = rnd.choice([0.0, -0.1, 0.3, 1.0])
        sf, tf = rnd.choice([600.0, 410.0, 220.0, rnd.uniform(100, 700)]), rnd.choice([180.0, 148.5, 117.0])
        wid, fl = rnd.choice([40, 10, 11, 21, 1010, -1]), rnd.randint(0, 1)
        emu.setup_body(0.5, fl, stl, sf, tf, wid)
        emu.uc.reg_write(UC_ARM64_REG_X4, emu.body + 0xA5D8)
        _, s0 = emu.run(FN_RATE, x=(emu.body + 0x698, emu.pp, emu.body + 0x9218, emu.body + 0xBD4))
        p = py_rate(stl, sf, tf, wid, fl)
        if f2u(s0) != f2u(p):
            bad += 1
            if bad <= 10:
                print("rate 불일치", stl, sf, tf, wid, fl, s0, p)
    print(f"0x7102491f88 회복량: {n}건, 불일치 {bad}")
    return bad


def check_timer(emu, rnd, n):
    bad = 0
    total = 0
    for _ in range(n):
        repeat = rnd.choice([6, 1, 2, 3, 4, 5, 7, 8, 12, 30])
        t = [F(rnd.choice([0.0, rnd.uniform(-0.2, 1.3), 1.0, 0.99999, 1 - 1 / repeat])), F(0),
             rnd.choice([0, 0, 1, 5]), rnd.choice([0, 0, 1, 2, 3]), rnd.choice([0, 0, 1, 10]), rnd.choice([0, 1, 3]),
             rnd.choice([999, 999, 1, 0]), rnd.randint(0, 1)]
        a = emu.timer
        for step in range(rnd.randint(1, 20)):
            emu.wf(a, t[0]); emu.wf(a + 4, t[1])
            for i, off in enumerate([8, 0xC, 0x10, 0x14, 0x18]):
                emu.w32(a + off, t[2 + i])
            emu.uc.mem_write(a + 0x1C, bytes([t[7]]))
            ret, _ = emu.run(FN_TIMER, x=(a, repeat))
            et = [emu.rf(a), emu.rf(a + 4)] + [emu.rs32(a + o) for o in (8, 0xC, 0x10, 0x14, 0x18)] + [t[7]]
            pr, pt = py_timer(t, repeat)
            total += 1
            same = (ret & 1) == pr and all(f2u(x) == f2u(y) for x, y in zip(et[:2], pt[:2])) and et[2:7] == pt[2:7]
            if not same:
                bad += 1
                if bad <= 10:
                    print("timer 불일치", repeat, t, ret, et, pr, pt)
            t = pt
    print(f"0x7102551530 연사 타이머: {total}스텝, 불일치 {bad}")
    return bad


def check_stop(emu, rnd, n):
    bad = 0
    for _ in range(n):
        cur, frames = rnd.randint(-50, 40), rnd.choice([20, 15, 30, 40, 50, 60, rnd.randint(0, 90)])
        sf, sq = rnd.randint(0, 1), rnd.randint(0, 1)
        emu.setup_body(1.0, 0, 0, 600, 180, 40)
        off = 0x6B0 if sq else 0x6A8
        emu.w32(emu.body + off, cur)
        emu.w32(emu.body + 0x6B4, 0x12345)
        emu.w64(emu.owner + 0x108, emu.body)
        emu.run(FN_STOP, x=(emu.owner, frames, sf, sq))
        v, s6b4 = py_stop(cur, frames, sf, sq)
        e6b4 = emu.rs32(emu.body + 0x6B4)
        good = emu.rs32(emu.body + off) == v and (e6b4 == (s6b4 if s6b4 is not None else 0x12345))
        if not good:
            bad += 1
            if bad <= 10:
                print("stop 불일치", cur, frames, sf, sq, emu.rs32(emu.body + off), e6b4, v, s6b4)
    print(f"0x7102353718 회복 정지: {n}건, 불일치 {bad}")
    return bad


def splattershot_table():
    cost = F(F(F(0.0092) * F(F(1.0) * F(1.0))))
    print("\n[스플래시슈터, 기어 0]")
    print(f"  소비량 = {cost!r} (0x{f2u(cost):08x})")
    print(f"  회복량 Std  = {py_rate(0, 600, 180, 40, 0)!r} (0x{f2u(py_rate(0, 600, 180, 40, 0)):08x})/프레임")
    print(f"  회복량 잠복 = {py_rate(1, 600, 180, 40, 0)!r} (0x{f2u(py_rate(1, 600, 180, 40, 0)):08x})/프레임")
    print(f"  회복 정지 +0x6b4 = {py_stop(0, 20, 1, 0)[1]}")
    ink, shots = F(1.0), 0
    while True:
        p = py_consume(cost, ink, 0, 0, 0, 600, 180, 40)
        if not p["ok"]:
            break
        ink, shots = p["ink"], shots + 1
    print(f"  가득 찬 탱크에서 회복 없이 쏠 수 있는 발 수 = {shots}, 남은 잉크 {ink!r}")
    t = [F(1) - F(F(1) / F(6)), F(0), 0, 0, 0, 0, 999, 0]
    fires = []
    for fr in range(1, 26):
        r, t = py_timer(t, 6)
        if r:
            fires.append(fr)
    print(f"  리셋 직후 phase=1-1/6에서 매 프레임 타이머를 돌릴 때 발사 프레임 = {fires}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    emu = Emu()
    bad = check_consume(emu, rnd, a.n)
    bad += check_rate(emu, rnd, a.n // 4)
    bad += check_timer(emu, rnd, a.n // 4)
    bad += check_stop(emu, rnd, a.n // 4)
    print(f"PLT 호출 {len(emu.calls)}회")
    splattershot_table()
    print(f"\n총 불일치 {bad}")


if __name__ == "__main__":
    main()
