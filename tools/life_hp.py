"""[life] 플레이어/오브젝트 HP 홀더 재구현 (원본 0x7101a88ce0 / 0x7101a88e1c / 0x7101a89524 / 0x7101a89790 / 0x7101a8905c)
그리고 적 잉크 지속 데미지 1프레임 계산(0x710268b3b8 안 0x710268bc7c~0x710268bd44).

모든 f32 연산은 numpy.float32 로 원본 명령 순서를 따른다.
사용(모듈): from life_hp import HpHolder, ink_damage
자체 검사: PY web/tools/life_hp.py selftest
"""
import sys

import numpy as np

F = np.float32


def fcvtzs(x):
    """f32 -> s32, 0 방향 절삭(NaN->0, 포화)."""
    x = float(x)
    if x != x:
        return 0
    if x >= 2147483647.0:
        return 2147483647
    if x <= -2147483648.0:
        return -2147483648
    return int(x)


def floor_s32(x):
    """원본: iVar = (int)f - (f<0 && f != (float)(int)f) = floor."""
    i = fcvtzs(x)
    if float(x) < 0.0 and float(x) != float(F(i)):
        i -= 1
    return i


class HpHolder:
    """기준 객체: HP 홀더 H (PlayerDamage+0x30, PlayerArmor+0x38, DamageHelper 대상+0x58 이 가리키는 것)."""

    def __init__(self, init_max=0):
        # 0x7101a88ce0
        self.flags = 6            # H+0x00 (bit0: 음수 HP 허용, bit1: 감소율로는 1 미만 안 됨(bit0=0일 때), bit2: 피격 시 회복 대기 재설정)
        self.max = init_max       # H+0x48
        self.hp = 0               # H+0x4c
        self.pending = 0          # H+0x50 이번 프레임 누적 데미지
        self.pend_team = 3        # H+0x54 (가장 큰 히트의 팀)
        self.pend_attacker = -1   # H+0x58
        self.pend_max = 0         # H+0x118 이번 프레임 최대 단일 데미지
        self.hit_flag = 0         # H+0x11c 이번 프레임 피격
        self.drain = F(0)         # H+0x120 감소율(초당)
        self.regen = F(0)         # H+0x124 회복률(초당)
        self.drain_acc = F(0)     # H+0x128 소수 누적
        self.regen_acc = F(0)     # H+0x12c
        self.wait = 0             # H+0x130 회복 대기 프레임
        self.last_dmg = 0         # H+0x138 마지막으로 적용된 데미지
        self.last_team = 3        # H+0x13c
        self.last_attacker = -1   # H+0x140
        self.hist = []            # H+0x200 데미지 이력(용량 8)
        self.cure_hist = []       # H+0x858 회복 이력(용량 8)

    def reset(self):
        """0x7101a88e1c: hp=max, 감소/회복 누적 0, 대기 0, 이력 비움, 마지막 히트 초기화."""
        self.hp = self.max
        self.drain_acc = F(0)
        self.regen_acc = F(0)
        self.last_dmg, self.last_team, self.last_attacker = 0, 3, -1
        self.wait = 0
        self.hist = []
        self.cure_hist = []

    def lo(self):
        # -(flags&1) & -max  : bit0 이면 -max, 아니면 0
        return -self.max if (self.flags & 1) else 0

    def clamp(self, v):
        mx = self.max
        lo = self.lo()
        hi = v if v <= mx else mx
        return lo if v < lo else hi

    def add_damage(self, dmg, team=3, attacker=-1, accumulate=True):
        """0x7101a89524(H, info, accumulate)."""
        if accumulate:
            s = self.pending + dmg
            self.hit_flag = 1
            self.pending = s
            if self.pend_max < dmg:
                self.pend_max = dmg
                self.pend_team = team
                self.pend_attacker = attacker
                self.pending = s
        self.hist = (self.hist + [dmg])[-8:]

    def cure(self, amount):
        """0x7101a89790(H, info): hp = clamp(hp + amount)."""
        self.hp = self.clamp(self.hp + amount)
        self.cure_hist = (self.cure_hist + [amount])[-8:]

    def update(self, dt, wait_frames=60):
        """0x7101a8905c(dt, H). wait_frames = [0x71058bbb78+0x1c0] (=60)."""
        fl = self.flags
        if (fl & 1) or self.hp > 0:
            acc = F(self.drain_acc + F(self.drain * F(dt)))
            n = floor_s32(acc)
            self.drain_acc = F(acc - F(n))
            if n > 0:
                v = self.hp - n
                if (fl & 3) == 2:
                    v = max(v, 1) if v < 2 else v
                self.hp = v
                if (fl >> 2) & 1:
                    self.wait = wait_frames
            if self.pending > 0:
                self.hp -= self.pending
                self.last_dmg = self.pending
                self.last_team = self.pend_team
                self.last_attacker = self.pend_attacker
            if self.hit_flag and ((fl >> 2) & 1):
                self.wait = wait_frames
            if self.wait < 1:
                acc = F(self.regen_acc + F(self.regen * F(dt)))
                n = floor_s32(acc)
                self.hp += n
                self.regen_acc = F(acc - F(n))
            else:
                self.wait -= 1
            self.hp = self.clamp(self.hp)
        # 끝: 이번 프레임 누적 초기화
        self.pending = 0
        self.pend_team = 3
        self.pend_attacker = -1
        self.pend_max = 0
        self.hit_flag = 0


def ink_damage(per_frame, enemy_ratio, hp, lmt, armor_frames, force_003=False):
    """적 잉크 1프레임 데미지(0x710268bc7c~0x710268bd44).
    per_frame = PlayerParam+0x110 (OpInk_DamagePerFrame), lmt = PlayerParam+0x114 (OpInk_DamageLmt),
    enemy_ratio = PlayerStepPaint+0x48, hp = PlayerDamage+0x7c, armor_frames = PlayerStepPaint+0xac(f32).
    force_003: 전역 0x71058e8784|0x71058e8788 가 켜지면 per_frame 대신 0.003.
    PlayerStepPaint+0xb5 는 생성자(0x710268b388)만 1로 쓰므로 상한 처리는 항상 수행."""
    s1 = F(F(enemy_ratio) * F(1000.0))
    s0 = F(0.003) if force_003 else F(per_frame)
    d = fcvtzs(F(s0 * s1))
    v = F(0.0) if F(armor_frames) > F(0.0) else F(F(lmt) * F(1000.0))
    w = fcvtzs(v)
    if w <= 999:
        cap = F(max(float(F(w + hp - 1000)), 0.0))
        d = fcvtzs(cap if cap < F(d) else F(d))
    return d


def selftest():
    ok = True

    def chk(name, got, exp):
        nonlocal ok
        r = "OK" if got == exp else "NG"
        if got != exp:
            ok = False
        print(f"{r} {name}: {got} (기대 {exp})")

    # 적 잉크: 기본 0.003, 비율 1.0 -> 3 (0.3HP/프레임)
    chk("ink 0.003 ratio1", ink_damage(0.003, 1.0, 1000, 0.4, 0), 3)
    chk("ink 57AP 0.0015", ink_damage(0.0015, 1.0, 1000, 0.2, 0), 1)
    chk("ink cap at hp 601", ink_damage(0.003, 1.0, 601, 0.4, 0), 1)
    chk("ink cap at hp 600", ink_damage(0.003, 1.0, 600, 0.4, 0), 0)
    chk("ink hp below lmt", ink_damage(0.003, 1.0, 300, 0.4, 0), 0)
    chk("ink armor frames", ink_damage(0.003, 1.0, 1000, 0.4, 5), 0)
    chk("ink ratio 0.5", ink_damage(0.003, 0.5, 1000, 0.4, 0), 1)
    # HP 홀더
    h = HpHolder()
    h.max = 1000
    h.flags = 6
    h.reset()
    h.add_damage(300, team=1, attacker=5)
    h.add_damage(360, team=1, attacker=6)
    h.update(F(1) / F(60))
    chk("2hits same frame", (h.hp, h.last_dmg, h.last_attacker, h.wait), (340, 660, 6, 59))
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(0 if selftest() else 1)
    print(__doc__)
