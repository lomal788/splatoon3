"""[move] 점프 곡선을 원본 함수 실행(unicorn)으로 검증한다.

원본 실행(수정 없음):
  0x71024a7d00 수직 속도 갱신(본체+0xa5f9, &본체+0xc0, PC, &본체+0x72c, &본체+0x750)
               내부에서 0x71024c9684(중력값)도 원본 그대로 실행
  0x710246b574 공중 프레임 카운터 증가(슬롯19 접촉 정리 0x71024abcf0 의 공중 경로가 부르는 것)
프레임 순서(판독, web/docs/player/movement_physics.md §6.4):
  슬롯18 메인 계산: 0x71024a7d00(0x710247c860) → [점프 프레임이면] 본체+0x73c = 점프 속도,
                    0x710246b32c(..,1) 로 공중 프레임 0 리셋(0x710248xxxx, 메인 계산 줄 5799)
                    → 최종 속도 y = +0x73c(+0x754 등, 0x710245aed8) → Phive 공중 상태가 그대로 적분
  슬롯19 0x71024abcf0: PC+0xd0(Phive 상태 OnGround && 지지) 거짓이면 0x710246b574 → 공중 프레임 +1
스텁/가정: Phive 스텝은 y += 최종 속도 y(유닛/프레임) 로 대체(GameInAir +0x1c=1 모드 판독),
          착지 판정은 y <= 0 이면 접지로 대체(실제는 Phive 접촉), 점프 프레임에 Phive 가 공중 상태로 유지된다고 가정.
          0x710246b574 의 vt+0x100(그라인드 레일) 호출은 1 을 돌려 뒤쪽 블록을 건너뜀.
  0x710245f964 공중/접지 보정(0x710245b2b4 끝 0x710245edc0 에서 이동 속도 본체+0x114 에 적용) — 원본 실행
재구현(판독, 원본 실행 아님): 점프 유지 가산 0x7102482df8 — 상승 중(+0x73c > 0.001)·지상 카운터 본체+0x268 < 1·
          점프 버튼 유지(본체+0x72c)면 +0x73c += 0.005·(1 − 0x710249bb60(...)); 평지·본체+0xa38 ≤ 0 이면 함수값 0.
          평지에서 이동 속도 y 는 0x710245b2b4 의 법선 성분 제거로 가속 단계에서 바뀌지 않고 0x710245f964 만 바꾼다고 둠.
사용: PY web/tools/move_jump_emu.py [--hold N] [--json 출력]   (N = 점프 버튼 유지 프레임 수, 0 = 탭)
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
CONSTS = ROOT / "analysis" / "player" / "bss_consts_58bb000.json"
BASE = 0x7100000000
STACK = 0x10000000
HEAP = 0x20000000
RET = 0x30000000
STUB_TRUE = 0x30000100
F = np.float32


def fb(h):
    return F(struct.unpack("<f", struct.pack("<I", h))[0])


G_BITS = fb(0x3C03126E)      # [0x71058bbc84] 0.00799999945 (0.008 의 최근접 f32 0x3c03126f 보다 1ulp 작음)
JUMP_BITS = fb(0x3DEB851E)   # [0x71058bbc60] 0.114999995 (최근접 0x3deb851f 보다 1ulp 작음)
K_BITS = fb(0x3F7AE148)      # [0x71058bbc74] 0.98
HOLD_BITS = fb(0x3BA3D70A)   # [0x71058bbc98] 0.005


class Emu:
    def __init__(self):
        img = IMG.read_bytes()
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0x10FFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        for k, v in json.loads(CONSTS.read_text(encoding="utf-8")).items():
            mu.mem_write(int(k, 16), struct.pack("<I", v["u32"]))
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x400000)
        mu.mem_map(RET, 0x1000)
        mu.mem_write(RET, struct.pack("<I", 0xD65F03C0))
        mu.mem_write(STUB_TRUE, struct.pack("<II", 0x52800020, 0xD65F03C0))  # mov w0,#1 ; ret
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.mu = mu
        self.heap = HEAP

    def alloc(self, n):
        a = self.heap
        self.heap += (n + 0xFF) & ~0xFF
        self.mu.mem_write(a, b"\0" * n)
        return a

    def call(self, fn, *args):
        mu = self.mu
        sp = STACK + 0xF0000
        mu.reg_write(UC_ARM64_REG_SP, sp)
        for k, v in enumerate(args[8:]):  # 9번째 인자부터 스택
            mu.mem_write(sp + 8 * k, struct.pack("<Q", v))
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
                UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7]
        for r, v in zip(regs, args):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(fn, RET, count=2_000_000)

    def q(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v))

    def i(self, a, v=None):
        if v is None:
            return struct.unpack("<i", self.mu.mem_read(a, 4))[0]
        self.mu.mem_write(a, struct.pack("<i", v))

    def f(self, a, v=None):
        if v is None:
            return struct.unpack("<f", self.mu.mem_read(a, 4))[0]
        self.mu.mem_write(a, struct.pack("<f", float(v)))


def build(e, special=0):
    body = e.alloc(0xAD00)
    peri = e.alloc(0x200)  # spl::PlayerPeriscope(+0xa818) +0x38/+0xb0 = 0 -> 중력 차단 없음
    e.q(body + 0xA818, peri)
    jet = e.alloc(0x200)
    e.q(body + 0xA680, jet)
    e.q(body + 0xA7E8, e.alloc(0x200))
    # Phive: PC+0xe3b8 -> W, W+8 -> ctrl, ctrl+0x40 -> M(+0x28/+0x30/+0x38 상태 객체, +0x40 현재 번호)
    pc = e.alloc(0xE400)
    w = e.alloc(0x40)
    ctrl = e.alloc(0x80)
    m = e.alloc(0x80)
    st = [e.alloc(0x40) for _ in range(3)]
    e.q(pc + 0xE3B8, w)
    e.q(w + 8, ctrl)
    e.q(ctrl + 0x40, m)
    for k, s in enumerate(st):
        e.q(m + 0x28 + 8 * k, s)
    e.i(m + 0x40, 1)  # 공중(InAir) — 점프 프레임에 메인 계산이 [1]로 강제(줄 6489~6505)
    # 그라인드 레일 객체(+0xa670): vt+0x100 -> 1
    rail = e.alloc(0x40)
    vt = e.alloc(0x200)
    e.q(vt + 0x100, STUB_TRUE)
    e.q(rail, vt)
    e.q(body + 0xA670, rail)
    e.i(body + 0x65C, special)
    # 0x710245f964 가 읽는 것: [본체+8]+0x290, [본체+0xa690(PC)]+0xe378 → +0x1746, [본체+0xa828]+0x30
    e.q(body + 8, e.alloc(0x400))
    e.q(body + 0xA690, pc)
    e.q(pc + 0xE378, e.alloc(0x2000))
    e.q(body + 0xA828, e.alloc(0x100))
    e.f(body + 0x184, 1.0)  # 바닥 법선 본체+0x180 = (0,1,0)
    return body, pc, rail


def run(v0=None, frames=60, special=0, hold=0):
    v0 = JUMP_BITS if v0 is None else F(v0)
    e = Emu()
    body, pc, rail = build(e, special)
    a = body + 0xA5F9
    y = F(0.0)
    rows = []
    for n in range(frames):
        air_before = e.i(body + 0xC0)
        # 슬롯18: 수직 속도 갱신(원본)
        e.call(0x71024A7D00, a, body + 0xC0, pc, body + 0x72C, body + 0x750)
        if n == 0:  # 점프 프레임: 갱신 뒤 점프 속도 대입 + 공중 프레임 0 리셋(0x710246b32c 의 *param_3=0)
            e.f(body + 0x73C, v0)
            e.i(body + 0xC0, 0)
            e.i(body + 0x734, 0)  # 0x71024a8000(점프 시작, 0x7102480e00): 본체+0x72c+8 = 0
        # 점프 유지 가산(재구현, 0x7102482df8): 상승 중·공중(지상 카운터 0)·버튼 유지
        if 0 < n < hold and F(e.f(body + 0x73C)) > F(0.001):
            e.f(body + 0x73C, F(F(e.f(body + 0x73C)) + HOLD_BITS))
        # 0x710245b2b4 끝: 이동 속도 y 보정(원본 0x710245f964)
        e.call(0x710245F964, body + 0xD2C, body + 0x7B8, body + 0xC0, body + 0x72C,
               int.from_bytes(e.mu.mem_read(body + 0xA680, 8), "little"),
               int.from_bytes(e.mu.mem_read(body + 0xA828, 8), "little"), body + 0x180, body + 0xA50, body + 0xF88, body + 0x114)
        vy = F(e.f(body + 0x73C))
        my = F(e.f(body + 0x118))
        y = F(y + F(vy + my))  # 최종 속도 y = 이동 y + 수직 속도(0x710245aed8), Phive GameInAir 그대로 적분
        # 슬롯19: 공중이면 카운터 증가(원본 0x710246b574)
        if y > 0:
            e.call(0x710246B574, a, body + 0x7B8, rail, body + 0x350, body + 0x180, body + 0xC0,
                   body + 0xF88, 1)
        rows.append(dict(frame=n + 1, air_before=air_before, vy=float(vy), my=float(my), y=float(y),
                         air_after=e.i(body + 0xC0), cnt734=e.i(body + 0x734)))
        if y <= 0 and n > 0:
            break
    return rows


def reimpl(v0=None, frames=60, hold=0):
    g, k = G_BITS, K_BITS
    v, y, air, my = (JUMP_BITS if v0 is None else F(v0)), F(0.0), 0, F(0.0)
    out = []
    for n in range(frames):
        if n > 0:
            v = F(k * v)
            if air >= 3:
                v = F(v - g)
            if n < hold and v > F(0.001):
                v = F(v + HOLD_BITS)
            if air >= 4:
                my = F(F(fb(0x3F6B851F) * my) - fb(0x3951B718))   # 0.92y − 0.0002 ([0x71058bbc40]/[+0x44])
            elif air > 0:
                my = F(my - F(fb(0x3B03126E) * F(1.0)))          # y −= 0.002·n.y ([0x71058bbd8c])
        else:
            my = F(my - F(fb(0x3B03126E) * F(1.0)))              # 점프 프레임: +0x734==0 && vy>0.001 이라 같은 누름
        y = F(y + F(v + my))
        out.append((float(v), float(y)))
        air = air + 1 if y > 0 else 0
        if y <= 0 and n > 0:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--hold", type=int, default=0)
    a = ap.parse_args()
    ap_hold = a.hold
    rows = run(hold=ap_hold)
    re = reimpl(hold=ap_hold)
    bad = sum(1 for r, (v, y) in zip(rows, re) if (r["vy"], r["y"]) != (v, y)) + abs(len(rows) - len(re))
    apex = max(rows, key=lambda r: r["y"])
    for r in rows:
        print(f"{r['frame']:3d} air(전)={r['air_before']:2d} vy={r['vy']:+.7f} my={r['my']:+.7f} y={r['y']:.7f} air(후)={r['air_after']:2d}")
    print(f"최고점 {apex['frame']}프레임 y={apex['y']:.6f}, 착지(y<=0) {rows[-1]['frame']}프레임, 재구현 불일치 {bad}")
    if a.json:
        Path(a.json).write_text(json.dumps(dict(rows=rows, apex=apex, mismatch=bad), indent=1), encoding="utf-8")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
