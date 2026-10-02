"""[gauge] 스페셜 게이지 재구현 계산(웹 포팅 기준식). 원본 대조는 gauge_emu.py.
사용: PY web/tools/gauge_sim.py  → analysis/gauge/gauge_sim_out.txt
"""
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def gear(gp, low, mid, high):
    """기어 보간(0x7102663808 판독식). gp = 주 능력×10 + 부 능력×3 (57 상한)"""
    gp = min(57, gp)
    x = min(1.0, max(0.0, gp * (3.3 - 0.027 * gp) / 100))
    t = (mid - low) / (high - low)
    t = min(1.0, max(0.0, t))
    if abs(t - 0.5) <= 0.001:
        f = x
    elif abs(x) < 0.001:
        f = 0.0
    elif t < 0.001:
        f = 1.0 if abs(x) >= 0.999 else 0.0
    else:
        f = math.exp(math.log(abs(x)) * (math.log(t) * -1.442695))
    return low + (high - low) * f


def full_texels(sp):
    return int(f32(sp * f32(211.2)))


def main():
    out = []
    out.append("# 필요 텍셀 = (int)(SpecialPoint*211.2f)")
    for sp in (180, 190, 200):
        out.append(f"SpecialPoint {sp}: full {full_texels(sp)} 텍셀")
    out.append("# SpecialIncrease_Up 배율(+0xe8) Low1.0 Mid1.15 High1.3 → 200p 무기의 실제 필요 칠 p")
    for gp in (0, 3, 6, 10, 13, 16, 20, 29, 39, 57):
        r = gear(gp, 1.0, 1.15, 1.3)
        out.append(f"GP {gp:2d}: rate {r:.4f}  필요 p(200) = {200 / r:.1f}")
    out.append("# RespawnSpecialGauge_Save(+0xec) Low0.5 Mid0.8 High1.0 [같은 보간식이라는 가정 = 추정] → 사망 후 남는 비율")
    for gp in (0, 3, 10, 20, 57):
        out.append(f"GP {gp:2d}: keep {gear(gp, 0.5, 0.8, 1.0):.4f}")
    out.append("# 역경 강화(MinorityUp, +0x17c): 인원차 d → d단계값×2×(1/60)×211.2 텍셀/프레임")
    for d, k in ((1, 1.0), (2, 2.0), (3, 3.0)):
        per = f32(f32(f32(k * f32(2.0 * f32(1 / 60))) * f32(211.2)))
        out.append(f"인원차 {d}{'+' if d == 3 else ''}: {per:.5f} 텍셀/프레임 = {per * 60 / 211.2:.3f} p/초, 200p 무기 0→가득 {full_texels(200) / per / 60:.1f}초(칠 없음)")
    out.append("# 넷 % 양자화와 원격 복원")
    for r in (0.0, 0.333, 0.5, 0.995, 1.0):
        p = 100 if r >= 1 else min(99, int(f32(r * 100)))
        back = 1.0 if p >= 100 else min(p / 100, 0.99)
        out.append(f"ratio {r} → state {p} → 원격 목표 {back}")
    txt = "\n".join(out)
    print(txt)
    (ROOT / "analysis" / "gauge").mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis" / "gauge" / "gauge_sim_out.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
