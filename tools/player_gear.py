"""플레이어 기어(능력) 보간식 재구현.

원본: PlayerParam 계산 함수들(0x710265df40 HumanMoveUp, 0x710265fd48 SquidMoveUp,
0x7102665ee4 OpInkEffectReduction 등)에 인라인된 같은 식을 옮긴 것.
값은 f32로 반올림해 원본 정밀도에 맞춘다(numpy.float32).

사용:
  player_gear.py table            # HumanMoveUp/SquidMoveUp/OpInk 기본값으로 AP 0..57 표
  player_gear.py calc <Low> <Mid> <High> <AP> [--ninja]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

f32 = np.float32
ROOT = Path(__file__).resolve().parents[2]


def ap_to_rate(ap_main_sub_sum, ninja=False):
    ap = f32(ap_main_sub_sum)
    if ap > f32(57.0):
        ap = f32(57.0)
    p = f32(f32(ap * f32(f32(ap * f32(-0.027)) + f32(3.3))) / f32(100.0))
    q = f32(1.0) if p > f32(1.0) else p
    r = q if p >= f32(0.0) else f32(0.0)
    if ninja:
        # 0x710265fd48: 특수능력 비트(값 104-100=4)가 켜져 있으면 p *= [0x71058c034c]=0.8 (SquidMoveUp 전용)
        r = f32(r * f32(0.8))
        r = f32(1.0) if r > f32(1.0) else (r if r >= f32(0.0) else f32(0.0))
    return r


def inv_lerp_mid(low, mid, high):
    low, mid, high = f32(low), f32(mid), f32(high)
    rng = f32(high - low)
    if low <= high:
        if not (low < mid):
            return f32(0.0)
        if not (mid < high):
            return f32(1.0)
        return f32(0.0) if rng == 0 else f32((mid - low) / rng)
    t = f32(0.0)
    if high < mid:
        if low <= mid:
            t = f32(1.0)
        elif f32(low - high) != 0:
            t = f32((mid - high) / f32(low - high))
    return f32(f32(1.0) - t)


def gear_lerp(low, mid, high, rate):
    low, mid, high = f32(low), f32(mid), f32(high)
    rng = f32(high - low)
    s = inv_lerp_mid(low, mid, high)
    k = rate
    d = f32(s - f32(0.5))
    if d > f32(0.001) or d < f32(-0.001):
        a = abs(rate)
        if a < f32(0.001):
            k = f32(0.0)
        elif s < f32(0.001):
            k = f32(1.0) if a >= f32(0.999) else f32(0.0)
        else:
            ls = f32(math.log(s))
            la = f32(math.log(a))
            k = f32(math.exp(f32(f32(la * f32(ls * f32(-1.442695))))))
    return f32(low + f32(rng * k))


def load_reflect(t):
    d = json.loads((ROOT / "analysis" / "param_reflect" / f"{t}.json").read_text(encoding="utf-8"))
    out = {}
    for f in d["classes"][0]["fields"] if "fields" in d["classes"][0] else d["fields"]:
        out[f["name"]] = f.get("default")
    return out


HUMAN = {  # PlayerGearSkillParam_HumanMoveUp 생성자 기본값 [판독, param_reflect 0x7102370f44]
    "Mid": (0.096, 0.12, 0.144), "Slow": (0.088, 0.116, 0.144), "Fast": (0.104, 0.124, 0.144),
    "Shot": (1.0, 1.125, 1.25),
}
SQUID = {  # PlayerGearSkillParam_SquidMoveUp 기본값 [판독, 0x710237e514]
    "Mid": (0.192, 0.216, 0.24), "Slow": (0.1728, 0.216, 0.24), "Fast": (0.2016, 0.2208, 0.24),
}
OPINK = {  # PlayerGearSkillParam_OpInkEffectReduction 기본값 [판독, 0x7102378a54]
    "JumpVel": (0.08, 0.098, 0.11), "MoveVel": (0.024, 0.05568, 0.0768),
    "MoveVel_Shot": (0.012, 0.033, 0.042), "MoveVel_ShotK": (0.5, 0.75, 1.0),
    "DamagePerFrame": (0.003, 0.00225, 0.0015), "DamageLmt": (0.4, 0.3, 0.2), "ArmorHP": (0.0, 26.0, 39.0),
}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table")
    c = sub.add_parser("calc")
    c.add_argument("low", type=float); c.add_argument("mid", type=float); c.add_argument("high", type=float)
    c.add_argument("ap", type=int); c.add_argument("--ninja", action="store_true")
    a = ap.parse_args()
    if a.cmd == "calc":
        r = ap_to_rate(a.ap, a.ninja)
        print(f"rate={float(r):.9g} value={float(gear_lerp(a.low, a.mid, a.high, r)):.9g}")
        return
    aps = [0, 3, 6, 9, 10, 12, 13, 16, 19, 20, 22, 26, 29, 30, 32, 35, 39, 41, 45, 48, 51, 54, 57]
    rows = []
    for x in aps:
        r = ap_to_rate(x)
        row = {"AP": x, "rate": float(r)}
        for k, v in HUMAN.items():
            row["Human_" + k] = float(gear_lerp(*v, r))
        for k, v in SQUID.items():
            row["Squid_" + k] = float(gear_lerp(*v, r))
            row["SquidNinja_" + k] = float(gear_lerp(*v, ap_to_rate(x, True)))
        for k, v in OPINK.items():
            row["OpInk_" + k] = float(gear_lerp(*v, r))
        rows.append(row)
    keys = list(rows[0].keys())
    print("\t".join(keys))
    for row in rows:
        print("\t".join(f"{row[k]:.6g}" for k in keys))


if __name__ == "__main__":
    main()
