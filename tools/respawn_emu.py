"""[respawn] 사망→리스폰 타이머를 원본 함수로 실행(unicorn)해 확인한다.

원본 실행 대상(수정 없음, 그대로 실행):
  0x71024a2c98  플레이어 프레임 갱신 중 쓰러짐/리스폰 타이머 구간(인자 37개)
  0x710249e2bc  리스폰 실행(Revival 송신 + 리셋 호출)
  0x710249cb60  리스폰 리셋(재시작 종류 param_40)
그 밖의 게임 함수 호출은 전부 스텁(x0=0 즉시 반환)으로 바꾸고 호출 주소·인자를 기록한다.
  - 0x710245fd38(ToHumanRespawn 요청), 0x710249e2bc(리스폰 실행) 등은 '호출 시점'만 확인 대상.
  - PLT memcpy/memmove/memset/strlen 은 파이썬으로 처리.
메모리: main.reloc.img(bss 포함) + 플레이어 정적 초기화 상수(analysis/player/bss_consts_58bb000.json, player_initemu 결과)
        + 널 페이지(0~0x400000 0 채움; 0 포인터 역참조를 0으로 읽게 함) + 가짜 본체(0xac80)·컴포넌트 버퍼.
사용: PY web/tools/respawn_emu.py            (시나리오 전부 실행, 기대값 불일치 시 종료코드 1)
결과: analysis/respawn/emu_respawn.txt 에 같은 내용을 저장
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_BLOCK, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BSS_JSON = ROOT / "analysis" / "player" / "bss_consts_58bb000.json"
OUT = ROOT / "analysis" / "respawn" / "emu_respawn.txt"
BASE = 0x7100000000
NULLPG = 0x400000
STACK = 0x10000000
HEAP = 0x20000000
HEAP_SZ = 0x4000000
RETADDR = 0x30000000
PLT_LO, PLT_HI = 0x7103E99000, 0x7103E9E000

F_FRAME = 0x71024A2C98
F_REVIVE = 0x710249E2BC
F_RESET = 0x710249CB60
F_TOHUMAN = 0x710245FD38
F_HOLDER_RESET = 0x7101A88E1C  # HP 홀더 리셋(원본 실행)
F_HOLDER_INIT = 0x7101A88CE0  # HP 홀더 초기화(원본 실행, 준비용)

LOG = []


def log(s=""):
    print(s)
    LOG.append(s)


def func_ranges(addrs):
    tsv = (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf-8", errors="replace").splitlines()
    want = set(addrs)
    out = []
    for ln in tsv[1:]:
        p = ln.split("\t")
        a = int(p[0], 16)
        if a in want:
            out.append((a, a + int(p[1])))
    assert len(out) == len(want), "함수 크기 조회 실패"
    return out


def imports():
    o = subprocess.run([sys.executable, str(Path(__file__).parent / "player_imports.py")],
                       capture_output=True, text=True).stdout
    d = {}
    for ln in o.splitlines():
        a, n = ln.split()
        d[int(a, 16)] = n
    return d


class Emu:
    def __init__(self, allowed):
        img = IMG.read_bytes()
        self.img = img
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(0, NULLPG)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        for k, v in json.loads(BSS_JSON.read_text()).items():
            mu.mem_write(int(k, 16), struct.pack("<I", v["u32"]))
        mu.mem_map(STACK, 0x200000)
        mu.mem_map(HEAP, HEAP_SZ)
        mu.mem_map(RETADDR, 0x1000)
        mu.mem_write(RETADDR, struct.pack("<I", 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.mu = mu
        self.heap = HEAP
        self.allowed = func_ranges(allowed)
        self.got = imports()
        self.calls = []
        mu.hook_add(UC_HOOK_BLOCK, self._block)
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)

    def _unmapped(self, mu, access, addr, size, value, user):
        raise RuntimeError(f"unmapped access {addr:#x} pc={mu.reg_read(UC_ARM64_REG_PC):#x}")

    def clear_null(self):
        self.mu.mem_write(0, b"\0" * NULLPG)

    def alloc(self, n):
        a = self.heap
        self.heap += (n + 0xFFF) & ~0xFFF
        assert self.heap < HEAP + HEAP_SZ
        return a

    def _allowed(self, a):
        return a == RETADDR or any(lo <= a < hi for lo, hi in self.allowed)

    def _plt_name(self, addr):
        w0 = struct.unpack_from("<I", self.img, addr - BASE)[0]
        w1 = struct.unpack_from("<I", self.img, addr + 4 - BASE)[0]
        page = (((w0 >> 5) & 0x7FFFF) << 2 | ((w0 >> 29) & 3)) << 12
        if page & (1 << 32):
            page -= 1 << 33
        got = (addr & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
        return self.got.get(got, f"?{got:#x}")

    def _block(self, mu, addr, size, user):
        if self._allowed(addr):
            return
        rd = mu.reg_read
        x = [rd(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
                             UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7)]
        ret = 0
        name = None
        if PLT_LO <= addr < PLT_HI:
            name = self._plt_name(addr)
            if name in ("memcpy", "memmove") and x[2]:
                mu.mem_write(x[0], bytes(mu.mem_read(x[1], x[2])))
                ret = x[0]
            elif name == "memset" and x[2]:
                mu.mem_write(x[0], bytes([x[1] & 0xFF]) * x[2])
                ret = x[0]
            elif name == "strlen":
                n = 0
                while mu.mem_read(x[0] + n, 1)[0]:
                    n += 1
                ret = n
        self.calls.append((addr, name, x))
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, rd(UC_ARM64_REG_LR))

    def call(self, fn, regs, stack_args=(), s0=None):
        mu = self.mu
        sp = STACK + 0x180000
        for i, v in enumerate(stack_args):
            mu.mem_write(sp + 8 * i, struct.pack("<Q", v))
        mu.reg_write(UC_ARM64_REG_SP, sp)
        rr = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
              UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7]
        for r, v in zip(rr, regs):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_LR, RETADDR)
        self.calls = []
        mu.emu_start(fn, RETADDR, count=5_000_000)
        return self.calls

    def r32(self, a):
        return struct.unpack("<i", self.mu.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack("<i", v))

    def w8(self, a, v):
        self.mu.mem_write(a, bytes([v]))

    def w64(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v))

    def wf(self, a, v):
        self.mu.mem_write(a, struct.pack("<f", v))

    def rf(self, a):
        return struct.unpack("<f", self.mu.mem_read(a, 4))[0]


SPAWN_MGR_VAR = 0x7105863D00  # GOT 0x71057999c8 가 가리키는 bss 변수(스폰 지점 관리자 포인터)


class World:
    """가짜 본체(PlayerBehavior+0x108) 하나와 컴포넌트 버퍼."""

    def __init__(self, e, versus_spawn):
        self.e = e
        self.body = e.alloc(0x10000)
        self.T = self.body + 0xD58
        self.actor = e.alloc(0x2000)
        e.w64(self.body + 8, self.actor)
        # 본체 컴포넌트 포인터 표(+0xa600~+0xa910)를 서로 다른 0 버퍼로 채운다
        self.comp = {}
        for off in range(0xA600, 0xA910, 8):
            b = e.alloc(0x10000)
            e.w64(self.body + off, b)
            self.comp[off] = b
        self.pd = self.comp[0xA8A0]
        # 넷 레플리카(본체+0xa8e0): +0x2c 활성, +0x48 = 3 → 이 기기가 조작 기기(0x71024a2c98 switch case 3)
        self.net = self.comp[0xA8E0]
        e.w8(self.net + 0x2C, 1)
        e.w32(self.net + 0x48, 3)
        self.mgr = 0
        if versus_spawn:
            self.mgr = e.alloc(0x4000)
            e.w8(self.mgr + 0x3680, 1)
            e.w8(self.mgr + 0x3681, 1)
        e.w64(SPAWN_MGR_VAR, self.mgr)
        # T+0xf8 = -1 (지점 인덱스 없음: 0x71024a2c98 의 T+0xf8 분기 생략)
        e.w32(self.T + 0xF8, -1)
        # HP 홀더 3개를 원본 초기화 0x7101a88ce0(H, &max)로 만든다(PD+0x30, Armor+0x38, CoopZombie+0x30)
        initv = e.alloc(8)
        e.w32(initv, 1000)
        for comp_off, h_off in ((0xA8A0, 0x30), (0xA8C0, 0x38), (0xA7C0, 0x30)):
            e.call(F_HOLDER_INIT, [self.comp[comp_off] + h_off, initv])
        # PlayerDamage HP 를 쓰러진 상태(0)로
        e.w32(self.pd + 0x30, 6)
        e.w32(self.pd + 0x78, 1000)
        e.w32(self.pd + 0x7C, 0)
        # 리스폰 지점 포즈(T+0x148, 0x30 B): 위치 + 방향(데이터 확인 예: Yagara Alpha Spawner)
        for i, v in enumerate([7.5, 33.5, 106.5, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]):
            e.wf(self.T + 0x148 + 4 * i, v)

    def T32(self, off):
        return self.e.r32(self.T + off)

    def frame(self):
        """0x71024a2c98 한 번. 호출부(0x7102476fd0, move_full_main.c 2003줄)의 본체 기준 주소 인자는 그대로,
        포인터 값 인자(*plVarNN)는 0 버퍼로 준다."""
        e = self.e
        e.clear_null()
        b = self.body
        args = [self.comp[0xA600 + 8 * (i % 0x60)] for i in range(37)]
        fixed = {1: b + 0xA5F9, 2: self.net, 4: b + 0x9208, 7: self.T, 9: b + 0xA90, 16: b + 0x784,
                 18: b + 0xC0, 20: b + 0xC18, 21: b + 0x9228, 22: b + 0xAF0, 23: b + 0x750, 25: b + 0x92AC,
                 26: b + 0x350, 32: b + 0x4F8, 33: b + 0xD10, 34: b + 0xB40, 37: b + 0xAB4}
        for k, v in fixed.items():
            args[k - 1] = v
        return e.call(F_FRAME, args[:8], args[8:])

    def revive(self, kind=1, use_alt=0):
        """0x710249e2bc(본체+0xa5f9, T, T+0x148, T-0xa08, 넷, use_alt, kind) — 0x71024a2c98 의 호출 그대로."""
        e = self.e
        e.clear_null()
        return e.call(F_REVIVE, [self.body + 0xA5F9, self.T, self.T + 0x148, self.T - 0xA08,
                                 self.net, use_alt, kind])


def hit(calls, addr):
    return [c for c in calls if c[0] == addr]


def scenario_frame_timer(versus):
    """사망 대기 T+8 → 리스폰 실행 → T+4 → ToHumanRespawn 요청, T+0xf4 무적, T+0 끝을 프레임별로."""
    e = Emu([F_FRAME, F_REVIVE, F_RESET, F_HOLDER_RESET, F_HOLDER_INIT])
    w = World(e, versus)
    death = 390  # 0x710245ff9c 가 기어 0에서 넣는 값(Around 90 + Chase 270 + 30, 판독식)
    e.w32(w.T + 8, death)
    events = []
    revived_at = None
    for f in range(1, 700):
        calls = w.frame()
        for c in calls:
            if c[0] == F_TOHUMAN:
                events.append((f, "0x710245fd38 ToHumanRespawn 요청"))
        # 0x710249e2bc 는 허용 범위라 실제로 실행된다. 리셋이 T+0 을 넣었는지로 판정
        if revived_at is None and w.T32(0) > 0:
            revived_at = f
            events.append((f, f"리스폰 실행: T+8={w.T32(8)} T+0={w.T32(0)} T+4={w.T32(4)} T+0xf4={w.T32(0xf4)} "
                              f"HP={e.r32(w.pd + 0x7c)} 위치=({e.rf(w.body+0x10):.1f},{e.rf(w.body+0x14):.1f},{e.rf(w.body+0x18):.1f})"))
        if revived_at is not None and f > revived_at + 130:
            break
        if revived_at is not None:
            for off, nm in ((0, "T+0"), (0xF4, "T+0xf4")):
                if w.T32(off) == 0 and not any(ev[1] == f"{nm}=0" for ev in events):
                    events.append((f, f"{nm}=0"))
    return events, revived_at


def scenario_remote():
    """이 기기가 조작 기기가 아니면(넷 레플리카 +0x48=0, +0x44=5 ≠ 로컬 0) T+8 은 1에서 멈추고 리스폰을 부르지 않는다."""
    e = Emu([F_FRAME, F_REVIVE, F_RESET, F_HOLDER_RESET, F_HOLDER_INIT])
    w = World(e, True)
    e.w32(w.net + 0x48, 0)
    e.w32(w.net + 0x44, 5)
    e.w32(w.T + 8, 5)
    seq = []
    for _ in range(8):
        w.frame()
        seq.append(w.T32(8))
    return seq, w.T32(0)


INV_CASES = [
    ("모두 0", {}),
    ("T+0xf4=1 (리스폰 무적)", {"T": {0xF4: 1}}),
    ("T+0=1", {"T": {0: 1}}),
    ("T+8=1 (사망 대기)", {"T": {8: 1}}),
    ("T+0x88=1", {"T": {0x88: 1}}),
    ("T+0x98=1", {"T": {0x98: 1}}),
    ("T+0xb4=1", {"T": {0xB4: 1}}),
    ("T+0x101=1", {"T8": {0x101: 1}}),
    ("본체+0xf34=1 (리스폰 착지 단계 1)", {"B": {0xF34: 1}}),
    ("본체+0xf34=3", {"B": {0xF34: 3}}),
    ("본체+0x9211=1", {"B8": {0x9211: 1}}),
    ("DokanWarp(+0xa880)+0x30=3", {"C": {(0xA880, 0x30): 3}}),
    ("DashPanel(+0xa698)+0x68=1", {"C": {(0xA698, 0x68): 1}}),
    ("MissionTicketGate(+0xa6c8)+0x38=1, +0x3c=0.0", {"C": {(0xA6C8, 0x38): 1}}),
    ("상태기계(+0xa8c8) 상태 0xf1 WorldAppear", {"C": {(0xA8C8, 0xC8): 0xF1}}),
    ("PlayerDemo(+0xa650)+0x30=1", {"C8": {(0xA650, 0x30): 1}}),
]


def scenario_invincible():
    """무적 판정 0x71024c7624 를 원본 실행. 인자는 호출부 0x7102484224(0x7102483134 안)와 같은 본체 기준."""
    out = []
    for name, setv in INV_CASES:
        e = Emu([0x71024C7624])
        w = World(e, True)
        b, c = w.body, w.comp
        for k, v in setv.get("T", {}).items():
            e.w32(w.T + k, v)
        for k, v in setv.get("T8", {}).items():
            e.w8(w.T + k, v)
        for k, v in setv.get("B", {}).items():
            e.w32(b + k, v)
        for k, v in setv.get("B8", {}).items():
            e.w8(b + k, v)
        for (co, k), v in setv.get("C", {}).items():
            e.w32(c[co] + k, v)
        for (co, k), v in setv.get("C8", {}).items():
            e.w8(c[co] + k, v)
        e.clear_null()
        regs = [b + 0xA5F9, w.T, c[0xA880], b + 0x925C, c[0xA698], b + 0x9208, c[0xA6C8], b + 0x588]
        stack = [c[0xA7E8], c[0xA7F0], c[0xA8C8], c[0xA650], 0]
        e.call(0x71024C7624, regs, stack)
        out.append((name, e.mu.reg_read(UC_ARM64_REG_X0) & 1))
    return out


def scenario_reset(versus):
    """0x710249cb60 을 0x710249e2bc 경유로 실행한 직후 값(재시작 종류는 e2bc가 0 고정이므로 cRespawn)."""
    e = Emu([F_REVIVE, F_RESET, F_HOLDER_RESET, F_HOLDER_INIT])
    w = World(e, versus)
    e.w32(w.T + 8, 0)
    calls = w.revive(kind=1)
    return dict(T0=w.T32(0), T4=w.T32(4), Tf4=w.T32(0xF4), hp=e.r32(w.pd + 0x7C), mx=e.r32(w.pd + 0x78),
                remoteHp=e.r32(w.pd + 0xEE0), predHp=e.r32(w.pd + 0xEE4),
                pos=(e.rf(w.body + 0x10), e.rf(w.body + 0x14), e.rf(w.body + 0x18)),
                tohuman=bool(hit(calls, F_TOHUMAN)))


def main():
    bad = 0
    log("== A. 리스폰 리셋 직후 값 (0x710249e2bc → 0x710249cb60 원본 실행, 재시작 종류 cRespawn) ==")
    expect = {True: (60, 15, 59), False: (120, 75, 119)}
    for versus in (True, False):
        r = scenario_reset(versus)
        ok = (r["T0"], r["T4"], r["Tf4"]) == expect[versus] and r["hp"] == 1000 and r["mx"] == 1000 \
            and r["pos"] == (7.5, 33.5, 106.5)
        bad += not ok
        log(f"스폰관리자 팀별 플래그={int(versus)}: T+0={r['T0']} T+4={r['T4']} T+0xf4={r['Tf4']} "
            f"HP={r['hp']}/{r['mx']} PD+0xee0={r['remoteHp']} PD+0xee4={r['predHp']} 위치={r['pos']} "
            f"ToHuman즉시={r['tohuman']}  기대 {expect[versus]} → {'일치' if ok else '불일치'}")
    log()
    log("== B. 프레임 타이머 (0x71024a2c98 를 매 프레임 원본 실행, 조작 기기, Scene_Mission 꺼짐) ==")
    for versus in (True, False):
        ev, rv = scenario_frame_timer(versus)
        log(f"-- 스폰관리자 팀별 플래그={int(versus)}, 시작 T+8=390")
        for f, s in ev:
            log(f"  프레임 {f:4d}: {s}")
        t0, t4, tf4 = expect[versus]
        # 리셋(T+0/T+4/T+0xf4 대입)은 같은 0x71024a2c98 호출 안에서 T+0/T+4/T+0xf4 감소 블록보다 먼저 실행되므로
        # 리스폰 프레임 R 에서 이미 1씩 줄어든다 → ToHuman 은 R+(T4-1), T+0xf4=0 은 R+(Tf4-1), T+0=0 은 R+(T0-1)
        want = [(390, "리스폰"), (390 + t4 - 1, "0x710245fd38"), (390 + tf4 - 1, "T+0xf4=0"), (390 + t0 - 1, "T+0=0")]
        for wf, key in want:
            okk = any(f == wf and s.startswith(key) for f, s in ev)
            bad += not okk
            log(f"  기대 프레임 {wf} '{key}' → {'일치' if okk else '불일치'}")
    log()
    log("== C. 조작 기기가 아닐 때 (0x71024a2c98 원본 실행, T+8 시작 5) ==")
    seq, t0 = scenario_remote()
    okc = seq == [4, 3, 2, 1, 1, 1, 1, 1] and t0 == 0
    bad += not okc
    log(f"  T+8 프레임별 {seq}, T+0={t0} (기대 [4,3,2,1,1,1,1,1], 리스폰 없음) → {'일치' if okc else '불일치'}")
    log()
    log("== D. 무적 판정 0x71024c7624 (원본 실행, 한 조건씩 켬) ==")
    expd = {"모두 0": 0, "본체+0xf34=3": 0}
    for name, r in scenario_invincible():
        want = expd.get(name, 1)
        bad += r != want
        log(f"  {name}: {r} (기대 {want}) → {'일치' if r == want else '불일치'}")
    log()
    log(f"불일치 {bad}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
