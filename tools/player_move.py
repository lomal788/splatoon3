"""플레이어 이동 속도 상한(목표 속도) 계산의 재구현 — 원본 0x710245b2b4 앞부분 중 판독이 끝난 경로만.

재현 범위([판독] 경로만):
  1) 인간 목표 속도: WeaponSpeedType(0 Slow/1 Mid/2 Fast)로 PlayerParam +0xb4/+0xb0/+0xb8 선택,
     발밑 적 잉크율 e(PlayerStepPaint+0x54)>0이면 OpInk_MoveVel(+0x104)이 더 작을 때 lerp(v, opink, e).
  2) 오징어(잠복 상태 집합) 목표 속도:
     0.072 + (squidVel*k - 0.072)*own + (0.012 - 0.072)*e   (own=PlayerStepPaint+0x3c, k=0x710266c6e4 반환값; 기본 1로 둠)
  3) 상한 갱신: cap += rate*(target - cap), rate 기본 0.3(가속 쪽). 이동 입력 크기 m=|stick|^4.
     목표 이동 벡터 = dir * cap * m.
가속(속도 벡터를 목표 벡터로 끌어가는 최대 변화량 fVar33)과 그 밖의 분기(특수무기, 사격, 경사, 레일 등)는 재현하지 않는다.

사용: player_move.py demo
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from player_gear import HUMAN, SQUID, OPINK, ap_to_rate, gear_lerp

f32 = np.float32
C_SQUID_DRY = f32(0.072)      # [0x71058bbdb8]
C_SQUID_ENEMY = f32(0.012)    # [0x71058bbde4]
C_CAP_RATE_UP = f32(0.3)      # [0x71058bbdcc]
C_STICK_POW = f32(4.0)        # [0x71058bbdf8]


def human_target(speed_type, human_ap, opink_ap, enemy):
    r = ap_to_rate(human_ap)
    key = {0: "Slow", 1: "Mid", 2: "Fast"}[speed_type]
    v = gear_lerp(*HUMAN[key], r)
    e = f32(enemy)
    if e > 0:
        op = gear_lerp(*OPINK["MoveVel"], ap_to_rate(opink_ap))
        if op < v:
            v = f32(v + f32(f32(op - v) * e))
    return v


def squid_target(speed_type, squid_ap, own, enemy, k=1.0):
    key = {0: "Slow", 1: "Mid", 2: "Fast"}[speed_type]
    sv = gear_lerp(*SQUID[key], ap_to_rate(squid_ap))
    own, enemy = f32(own), f32(enemy)
    return f32(C_SQUID_DRY + f32(f32(sv * f32(k)) - C_SQUID_DRY) * own + f32(C_SQUID_ENEMY - C_SQUID_DRY) * enemy)


def cap_step(cap, target, rate=C_CAP_RATE_UP):
    return f32(cap + f32(rate) * f32(target - cap))


def demo():
    print("인간 목표 속도(유닛/프레임) — 무기속도 Mid, 기어 0AP")
    for e in (0.0, 0.5, 1.0):
        print(f"  적잉크율 {e:.1f}: {float(human_target(1, 0, 0, e)):.6f}")
    print("오징어 목표 속도 — Mid, 0AP / 57AP")
    for own, e in ((1, 0), (0, 0), (0, 1), (0.5, 0.5)):
        print(f"  아군 {own} 적 {e}: 0AP {float(squid_target(1, 0, own, e)):.6f}  57AP {float(squid_target(1, 57, own, e)):.6f}")
    print("상한 cap 수렴(0 → 인간 0.096, rate 0.3):")
    cap = f32(0)
    for f in range(1, 16):
        cap = cap_step(cap, f32(0.096))
        if f in (1, 2, 3, 5, 10, 15):
            print(f"  {f:2d}프레임: {float(cap):.6f} ({float(cap) / 0.096 * 100:.1f}%)")
    print("입력 크기 m=|stick|^4:", ", ".join(f"{s}→{float(f32(s) ** C_STICK_POW):.4f}" for s in (0.25, 0.5, 0.75, 1.0)))


if __name__ == "__main__":
    demo()
