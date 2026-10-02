"""카메라 쉐이크(game::CameraModuleParam.Rumble)와 컨트롤러 진동(.bnvib) 데이터 도구.

근거:
  곡선 평가 함수 표 0x7105738610 (Linear 0x71038c8990, Hermit 0x71038c89f0, Step 0x71038c8ad0,
    Sin 0x71038c8b00, Cos 0x71038c8b40, SinPow2 0x71038c8b80, ...). 타입 0~2만 t를 MaxX로 나눈다(호출부).
  카메라 쉐이크 인스턴스 갱신 0x71010182e8: out = Axis * curve(frame) * gain * Scale, frame += 1,
    IsLooped 이면 frame >= MaxX 에서 0.
  CameraRumbleParam 팩토리 0x710100e6b4: Axis 기본 (0,1,0), Scale 1.0, IsLooped false.

사용:
  camera_shake.py selftest
  camera_shake.py rumble            # CameraModuleParam.Rumble 각 항목 프레임별 값 → analysis/camera/camera_rumble_samples.json
  camera_shake.py bnvib             # Rumble/Common.bnvib.sarc 115개 헤더 요약 → analysis/camera/bnvib_summary.json
"""
import sys, json, math, struct, argparse
from pathlib import Path

ROOT = Path(r"C:/dev/splatoon3")
CMP = ROOT / "analysis/camera/SingletonParam/Gyml/Singleton/game__CameraModuleParam.game__CameraModuleParam.bgyml.json"
BNV = ROOT / "analysis/camera/rumble_bnvib"
TYPES = ["Linear", "Hermit", "Step", "Sin", "Cos", "SinPow2", "Linear2D", "Hermit2D", "Step2D",
         "NonuniformSpline", "Hermit2DSmooth", "Hermit2DSplit"]


def curve_eval(ctype, data, t):
    """t: 타입 0~2 는 정규화된 값(frame/MaxX), 3 이상은 frame 그대로 (호출부 0x71010182e8)."""
    n = len(data)
    if ctype == "Linear":
        if t < 0: return data[0]
        m = n - 1; x = m * t; i = int(x)
        if i < m: return data[i] + (x - i) * (data[i + 1] - data[i])
        return data[m]
    if ctype == "Hermit":
        if n & 1: return 0.0
        if t < 0: return data[0]
        m = n // 2 - 1; x = m * t; i = int(x)
        if i >= m: return data[2 * m]
        f = x - i
        h00 = 2 * f ** 3 - 3 * f * f + 1; h01 = 3 * f * f - 2 * f ** 3
        h10 = f ** 3 - 2 * f * f + f; h11 = f ** 3 - f * f
        return h00 * data[2 * i] + h10 * data[2 * i + 1] + h01 * data[2 * i + 2] + h11 * data[2 * i + 3]
    if ctype == "Step":
        tt = 0.0 if t < 0 else min(t, 1.0)
        return data[int(tt * (n - 1))]
    if ctype == "Sin":
        return math.sin(data[0] * t * 6.2831855) * data[1]
    if ctype == "Cos":
        return math.cos(data[0] * t * 6.2831855) * data[1]
    if ctype == "SinPow2":
        return math.sin(data[0] * t * 6.2831855) ** 2 * data[1]
    raise NotImplementedError(ctype)   # 2D 계열은 미판독


class CameraShake:
    """0x71010182e8 의 인스턴스 (gain = 호출부가 넣는 세기, 예: 거리 감쇠) [gain 출처 미확정]"""

    def __init__(self, p, gain=1.0):
        self.p = p; self.frame = 0; self.gain = gain
        self.axis = p.get("Axis", {"X": 0.0, "Y": 1.0, "Z": 0.0})
        self.scale = p.get("Scale", 1.0); self.loop = p.get("IsLooped", False)
        self.alive = True

    def step(self):
        c = self.p["Curve"]; ty = c.get("Type", "Linear"); mx = c.get("MaxX", 1.0)
        t = self.frame / mx if TYPES.index(ty) < 3 else float(self.frame)
        v = curve_eval(ty, c["Data"], t) * self.gain * self.scale
        out = (self.axis["X"] * v, self.axis["Y"] * v, self.axis["Z"] * v)
        self.frame += 1
        if self.loop and mx <= self.frame:
            self.frame = 0
        if not self.loop and self.frame > mx:
            self.alive = False   # 비루프 종료 조건 0x7101018998 [미확정: 정확한 비교]
        return out


def cmd_rumble():
    d = json.load(open(CMP, encoding="utf-8"))
    res = {}
    for name, p in d["Rumble"].items():
        sh = CameraShake(p)
        mx = int(p["Curve"]["MaxX"])
        vals = [sh.step()[1 if p.get("Axis", {"Y": 1}).get("Y", 0) else 0] for _ in range(mx + 1)]
        res[name] = {"type": p["Curve"]["Type"], "MaxX": mx, "Scale": p.get("Scale", 1.0), "loop": p.get("IsLooped", False),
                     "axis": p.get("Axis", "기본(0,1,0)"), "samples": [round(v, 5) for v in vals]}
        pk = max(abs(v) for v in vals)
        print(f"{name:18s} {p['Curve']['Type']:7s} MaxX={mx:3d} Scale={p.get('Scale', 1.0):.3f} loop={str(p.get('IsLooped', False)):5s} 최대|v|={pk:.4f}")
    json.dump(res, open(ROOT / "analysis/camera/camera_rumble_samples.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def parse_bnvib(b):
    """헤더: u32 메타크기(4|0xC), u16 포맷(3), u16 샘플레이트(200) [데이터],
    메타크기 0xC 이면 u32 loopStart, u32 loopEnd [추정], 그 뒤 u32 데이터크기, 샘플 4바이트씩.
    샘플 = (ampLow, freqLow, ampHigh, freqHigh) 코드 [추정: Simple240Hz 의 0x93 → 10*2^(147/32)=241Hz]"""
    meta, fmt, rate = struct.unpack_from("<IHH", b, 0)
    off = 8; loop = None
    if meta == 0xC:
        loop = struct.unpack_from("<II", b, off); off += 8
    size = struct.unpack_from("<I", b, off)[0]; off += 4
    n = size // 4
    smp = [tuple(b[off + 4 * i: off + 4 * i + 4]) for i in range(n)]
    return dict(meta=meta, fmt=fmt, rate=rate, loop=loop, n=n, dur_ms=n * 1000 / rate if rate else None,
                consistent=(off + size == len(b)), smp=smp)


def freq_hz(code):
    return 10.0 * 2 ** (code / 32.0)


def cmd_bnvib():
    out = {}
    for p in sorted(BNV.glob("*.bnvib")):
        r = parse_bnvib(p.read_bytes())
        amp_l = max((s[0] for s in r["smp"]), default=0); amp_h = max((s[2] for s in r["smp"]), default=0)
        out[p.name] = dict(meta=r["meta"], fmt=r["fmt"], rate=r["rate"], loop=r["loop"], samples=r["n"],
                           dur_ms=r["dur_ms"], size_ok=r["consistent"], max_amp_low=amp_l, max_amp_high=amp_h)
    json.dump(out, open(ROOT / "analysis/camera/bnvib_summary.json", "w"), indent=1)
    bad = [k for k, v in out.items() if not v["size_ok"]]
    print(len(out), "files; size 불일치:", bad)
    print("rate:", sorted({v['rate'] for v in out.values()}), "fmt:", sorted({v['fmt'] for v in out.values()}),
          "meta:", sorted({v['meta'] for v in out.values()}))
    for k in ["GMBT_NormalShotLong00.bnvib", "GMBT_damageInk.bnvib", "GMBT_inkHit09.bnvib", "GMBT_ToSquidMix00.bnvib", "Simple240HzLoop.bnvib"]:
        if k in out: print(k, out[k])


def shake_gain(d, distance_attenuate=1, max_power_dist=15.0, min_power_dist=25.0):
    """ELink 쉐이크 시작(0x710137b000)의 gain. DistanceAttenuate>=1 이면 0x710130d3a8 거리 감쇠,
    아니면 시작값 1.0(0x7101010f14 가 +0x28 에 1.0 기록). 거리 = |카메라 모듈+0x1c8 - 이미터 위치|.
    기본 거리값은 game::RumbleModuleParam CameraMaxPowerDist 15 / CameraMinPowerDist 25(데이터 덮어쓰기 없음)."""
    if distance_attenuate < 1:
        return 1.0
    a, b = min_power_dist, max_power_dist        # s10=+0x5c, s0=+0x58
    if a > b:
        t = 0.0 if d <= b else 1.0 if d >= a else (d - b) / (a - b)
        return 1.0 - t
    return 0.0 if d <= a else 1.0 if d >= b else (d - a) / (b - a)


def spinner_gain(c):
    """스피너 발사 쉐이크(0x71025c4250~): s=(c-0.15)/0.85, s<=0 이면 정지, |s|<0.001 이면 0, 아니면 sign(s)|s|^0.51457(=bias 0.7)."""
    s = (c - 0.15) / 0.85
    if s <= 0:
        return None
    if abs(s) < 0.001:
        return 0.0
    return math.copysign(abs(s) ** 0.51457, s)


def cmd_selftest():
    ok = True

    def chk(n, c):
        nonlocal ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    chk("Linear 중간", abs(curve_eval("Linear", [0, 1], 0.25) - 0.25) < 1e-9)
    chk("Linear t>=1 끝값", curve_eval("Linear", [0, 1, 3], 1.0) == 3)
    chk("Hermit 키 위 값", abs(curve_eval("Hermit", [0, 4.58, 0, -5.1, 0, 1.0], 0.5)) < 1e-9)
    chk("Hermit 홀수 개수 → 0", curve_eval("Hermit", [1, 2, 3], 0.3) == 0.0)
    chk("EaseInOut30(Hermit 0,0,1,0) 중간 0.5", abs(curve_eval("Hermit", [0, 0, 1, 0], 0.5) - 0.5) < 1e-9)
    chk("Step", curve_eval("Step", [1, 2, 3], 0.6) == 2)
    chk("Sin 주기 1/0.18 프레임", abs(curve_eval("Sin", [0.18, 1.0], 1 / 0.18 / 4) - 1.0) < 1e-5)
    b = (BNV / "Simple240HzLoop.bnvib").read_bytes()
    r = parse_bnvib(b)
    chk("Simple240HzLoop 헤더 크기 일치", r["consistent"] and r["rate"] == 200 and r["meta"] == 0xC)
    chk("Simple240Hz 저역 주파수 코드 0x93 ≈ 240Hz", abs(freq_hz(0x93) - 240) < 3)
    chk("쉐이크 gain: DistanceAttenuate 0 → 1.0", shake_gain(100.0, 0) == 1.0)
    chk("쉐이크 gain: 거리 10 → 1.0", shake_gain(10.0) == 1.0)
    chk("쉐이크 gain: 거리 20 → 0.5", abs(shake_gain(20.0) - 0.5) < 1e-9)
    chk("쉐이크 gain: 거리 25 이상 → 0", shake_gain(30.0) == 0.0)
    chk("스피너 gain: 비율 0.15 이하 → 정지", spinner_gain(0.15) is None)
    chk("스피너 gain: 비율 1 → 1", abs(spinner_gain(1.0) - 1.0) < 1e-9)
    chk("스피너 gain: 비율 0.575 → 0.5^0.51457", abs(spinner_gain(0.575) - 0.5 ** 0.51457) < 1e-6)
    print("ALL PASS" if ok else "SOME FAIL")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["selftest", "rumble", "bnvib"])
    a = ap.parse_args()
    {"selftest": cmd_selftest, "rumble": cmd_rumble, "bnvib": cmd_bnvib}[a.cmd]()
