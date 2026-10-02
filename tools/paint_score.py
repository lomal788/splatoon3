"""도색 점수류 재구현 (원본 판독 기반).

근거 함수 (main, 0x7100000000 기준)
  0x7103092a4c  나와바리 결과: 팀 p = uint(count * 0.015625 * 0.3030303), 플레이어 p = uint(u32 +0xbd4 / 211.2)
  0x7103042394  VersusRefereePaint 슬롯19: 만분율 차로 우세 5단계
  0x7102663808  SpecialIncrease_Up 기어 효과 (IncreaseRt_Special_High/Mid/Low)

사용:
  python web/tools/paint_score.py         # 표 출력 + analysis/paint/score_check.json
"""
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/paint"


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


C_INV64 = f32(0.015625)
C_INV33 = f32(0.3030303)


def team_point(count):
    """0x7103092a4c: (float)count * 0.015625 * 0.3030303 -> fcvtzu, 음수면 0."""
    v = f32(f32(f32(float(count)) * C_INV64) * C_INV33)
    return max(int(v), 0)


def player_point(count):
    """0x7103092a4c / ui hud: (int)((float)count / 211.2)."""
    return int(f32(f32(float(count)) / f32(211.2)))


def referee_level(a, b, total):
    """0x7103042394: 0=Alpha 크게 우세 ... 4=Bravo 크게 우세. total==0 이면 판정 안 함(None)."""
    if total == 0:
        return None
    ra = min(f32(float(a)) / f32(float(total)), 1.0)
    rb = min(f32(float(b)) / f32(float(total)), 1.0)
    diff = int(f32(ra * 10000.0)) - int(f32(rb * 10000.0))
    if diff >= 0x5dd:
        return 0
    if diff >= 0x3e9:
        return 1
    if diff >= -1000:
        return 2
    if diff >= -0x5dc:
        return 3
    return 4


def gear_rate(gp, high, mid, low):
    """0x7102663808. gp = 주+부 포인트 합(단위는 [추정] 주10/부3)."""
    g = min(float(gp), 57.0)
    x = (g * (g * -0.027 + 3.3)) / 100.0
    x = min(max(x, 0.0), 1.0)
    if low <= high:
        if mid <= low:
            t = 0.0
        elif mid >= high:
            t = 1.0
        else:
            t = (mid - low) / (high - low) if high != low else 0.0
    else:
        if mid <= high:
            t = 0.0
        elif mid >= low:
            t = 1.0
        else:
            t = (mid - high) / (low - high)
        t = 1.0 - t
    d = t - 0.5
    if -0.001 <= d <= 0.001:
        f = x
    elif abs(x) < 0.001:
        f = 0.0
    elif t < 0.001:
        f = 1.0 if abs(x) >= 0.999 else 0.0
    else:
        f = math.exp(math.log(x) * (math.log(t) * -1.442695))
    return low + (high - low) * f


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    res["team_point"] = {c: team_point(c) for c in (0, 211, 212, 2112, 42240, 100000)}
    res["player_point"] = {c: player_point(c) for c in (0, 211, 212, 2112, 42240, 100000)}
    res["referee_level"] = {
        f"{a}/{b}/{t}": referee_level(a, b, t)
        for a, b, t in ((50, 50, 100), (60, 49, 100), (60, 50, 100), (65, 50, 100), (66, 50, 100),
                        (50, 60, 100), (50, 66, 100), (0, 0, 0), (1501, 0, 10000), (1500, 0, 10000))
    }
    res["special_increase_rate"] = {gp: round(gear_rate(gp, 1.3, 1.15, 1.0), 6) for gp in
                                    (0, 3, 6, 10, 13, 16, 19, 20, 29, 30, 39, 48, 57, 60)}
    (OUT / "score_check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
