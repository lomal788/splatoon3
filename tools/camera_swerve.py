"""슈터 조준 흔들림(발사 방향 수평 분산) 재구현.

원본 판독 근거 (analysis/decomp/camera/batch1.c, analysis/camera/shot_7102583008.asm):
  - 0x7102583008  PlayerInkActionShooter 발사 프레임 처리 (난수 시드, bias 곡선, Y축 회전)
  - 0x7102580f98  흔들림 각/점프 bias 계산
  - 0x7102899e18  WeaponShooter: Stand_DegSwerve / Jump_DegSwerve(+기어 ReduceJumpSwerveRate 보간)
  - 0x7102580c4c  점프 카운터 = Jump_DegBiasEndFrame 대입
  - 0x7102551530  연사 타이머(RepeatFrame)

사용:
  camera_swerve.py table              # 35개 WeaponShooterParam 표 (기본값 채움, $parent 병합)
  camera_swerve.py selftest           # 합성 검사 (난수기, bias 곡선, 회전, 상태 전이)
  camera_swerve.py sim <표이름> [--frames N] [--jump F] [--seed a,b,c,d] [--frame0 N]
"""
import sys, json, math, struct, argparse
import numpy as np
from pathlib import Path

ROOT = Path(r"C:/dev/splatoon3")
GPT = ROOT / "extracted/params/Component/GameParameterTable"
IMG = ROOT / "extracted/exefs/main.img"
BASE = 0x7100000000

f32 = np.float32
M32 = 0xFFFFFFFF

# ---- spl::WeaponShooterParam 기본값 (팩토리 0x7102811104, analysis/param_reflect) ----
DEFAULTS = json.load(open(ROOT / "analysis/param_reflect/spl__WeaponShooterParam.json"))["classes"][0]["defaults"]


def load_table(name):
    p = GPT / f"{name}.game__GameParameterTable.bgyml.json"
    d = json.load(open(p, encoding="utf-8"))
    chain = [d]
    while "$parent" in chain[-1]:
        pn = chain[-1]["$parent"].split("/")[-1].split(".")[0]
        chain.append(json.load(open(GPT / f"{pn}.game__GameParameterTable.bgyml.json", encoding="utf-8")))
    return chain


def shooter_param(name, key="WeaponParam"):
    """필드 단위로 자식→부모→기본값 순서 (코드의 '설정됨 플래그' 체인과 같은 결과 [판독: bullet 공유 사실])."""
    chain = load_table(name)
    out = {}
    for k, v in DEFAULTS.items():
        val = v
        for t in chain:
            gp = t.get("GameParameters", {}).get(key)
            if gp and k in gp:
                val = gp[k]
                break
        out[k] = val
    return out


# ---- sead::Random (xorshift128) — 시드는 발사마다 새로 만든다 (0x7102583a00~0x7102583ab4) ----
def seed_state(frame, a, b, c, d):
    """frame = max([*0x710580e758]+0x148, 0), a..d = [*0x7105850620]+0x124/0x128/0x12c/0x130 (u32 산술)."""
    M = 0x6C078965
    s0 = (frame + ((b + a) & M32) * 0x89) & M32
    x = (M * (s0 ^ (s0 >> 30)) + 1) & M32
    y = (M * (x ^ (x >> 30)) + ((c + b) & M32) * 0x1C1 + 2) & M32
    z = (M * (y ^ (y >> 30)) + ((d + c) & M32) * 0x233 + 3) & M32
    w = (M * (z ^ (z >> 30)) + ((d + a) & M32) * 0x3DF + 4) & M32
    if (x | y | z | w) == 0:
        x, w = 1, 0x48077044      # sead 기본 상태 (y,z 는 첫 값에 쓰이지 않음)
    return [x, y, z, w]


def rand_u32(st):
    x, y, z, w = st
    t = (x ^ (x << 11)) & M32
    nw = (w ^ (w >> 19) ^ t ^ (t >> 8)) & M32
    st[:] = [y, z, w, nw]
    return nw


def rand_f32(st):
    """sead::Random::getF32: asfloat(0x3f800000 | u32>>9) - 1.0  → [0,1)"""
    u = rand_u32(st)
    v = struct.unpack("<f", struct.pack("<I", 0x3F800000 | (u >> 9)))[0]
    return f32(f32(v) - f32(1.0))


# ---- bias 곡선 (Perlin bias, 0x7102583ad8~0x7102583b80) ----
def bias_curve(u, bias):
    u = f32(u); bias = f32(bias)
    d = f32(bias - f32(0.5))
    if not (d < f32(-0.001) or d > f32(0.001)):
        return u                                  # bias==0.5 → 그대로
    au = f32(abs(u))
    if au < f32(0.001):
        return f32(0.0)
    if bias < f32(0.001):
        return f32(0.0) if au < f32(0.999) else f32(1.0)   # 부호 없이 1.0 (원본 그대로)
    lb = f32(math.log(float(bias)))
    s12 = f32(lb * f32(-1.442695))
    p = f32(math.exp(float(f32(f32(math.log(float(au))) * s12))))
    return f32(-p) if u < 0 else p


# ---- sead 사인/코사인 표 (0x7104aa5b5c, 256항목 × (sin, dsin, cos, dcos)) ----
_TBL = None


def sincos_idx(rad):
    global _TBL
    if _TBL is None:
        m = IMG.read_bytes()
        _TBL = struct.unpack_from("<1028f", m, 0x7104AA5B5C - BASE)
    v = int(f32(f32(rad) * f32(6.8356525e08)))   # fcvtzs x8 (64bit, 0 방향 절삭)
    i = (v >> 24) & 0xFF
    fr = f32(f32(v & 0xFFFFFF) * f32(5.9604645e-08))
    s = f32(f32(_TBL[4 * i]) + f32(f32(_TBL[4 * i + 1]) * fr))
    c = f32(f32(_TBL[4 * i + 2]) + f32(fr * f32(_TBL[4 * i + 3])))
    return s, c


def rotate_y(vec, rad):
    """0x7102583bac~0x7102583c64: 세계 Y축 회전 x'=x cos + z sin, z'=-x sin + z cos"""
    s, c = sincos_idx(rad)
    x, y, z = (f32(v) for v in vec)
    return (f32(x * c + z * s), y, f32(z * c - x * s))


# ---- 흔들림 상태 (PlayerInkActionShooter 필드) ----
class SwerveState:
    """bias(+0x8c), jumpCounter(+0x88)"""

    def __init__(self, P):
        self.P = P
        self.bias = f32(0.0)      # 생성 초기화 0x7102580e68 계열에서 0 [판독: +0x88 대입 0]
        self.jump = 0

    def on_jump(self):            # 0x7102580c4c
        self.jump = int(self.P["Jump_DegBiasEndFrame"])

    def swerve_and_jumpbias(self, jump_swerve_eff=None):
        """0x7102580f98. jump_swerve_eff = 기어 보간 후 Jump 흔들림 (없으면 Jump_DegSwerve 그대로=기어 0)"""
        P = self.P
        stand = f32(P["Stand_DegSwerve"])
        jmp = f32(P["Jump_DegSwerve"] if jump_swerve_eff is None else jump_swerve_eff)
        if self.jump < 1:
            return stand, f32(0.0)
        t = f32(f32(self.jump) / f32(P["Jump_DegBiasEndFrame"] - P["Jump_DegBiasDecreaseStartFrame"]))
        if t > 1.0:
            t = f32(1.0)
        sw = f32(stand + f32(t * f32(jmp - stand)))
        smin = f32(P["Stand_DegBiasMin"])
        jb = f32(smin + f32(t * f32(f32(P["Jump_DegBiasMax"]) - smin)))
        return sw, jb

    def fire(self, aim_dir, rnd_state, debug_no_swerve=False):
        sw, jb = self.swerve_and_jumpbias()
        rad = f32(0.0) if debug_no_swerve else f32(sw * f32(0.017453292))
        b = self.bias if self.bias > jb else jb                  # fcsel gt
        r = rand_f32(rnd_state)
        u = f32(f32(r + r) + f32(-1.0))
        ub = bias_curve(u, b)
        ang = f32(rad * ub)
        d = rotate_y(aim_dir, ang)
        # 발사 후 bias 누적 (0x71025843e0~0x7102584574)
        nb = f32(self.bias + f32(self.P["Stand_DegBiasKf"]))
        mx = f32(self.P["Stand_DegBiasMax"])
        self.bias = nb if nb <= mx else mx
        return dict(swerve_deg=float(sw), jump_bias=float(jb), bias_used=float(b), r=float(r), u=float(u),
                    u_biased=float(ub), angle_deg=float(ang) * 180 / math.pi, dir=tuple(float(v) for v in d))

    def end_frame(self, trigger_held, timer_rem_is_one, player_c0_ge_const):
        """0x71025830d0~0x71025835c4 (발사 처리 뒤 매 프레임)"""
        if timer_rem_is_one and not trigger_held:
            self.bias = f32(self.bias - f32(self.P["Stand_DegBiasDecrease"]))
        mn = f32(self.P["Stand_DegBiasMin"])
        if self.bias < mn:                                      # fcsel mi
            self.bias = mn
        step = -1 if player_c0_ge_const else -2
        self.jump = max(self.jump + step, 0)


# ---- 연사 타이머 (0x7102551530, 구조체 기준 = PlayerInkActionShooter+0x68) ----
class RepeatTimer:
    def __init__(self):
        self.phase = f32(0.0)   # +0x68
        self.rem = f32(0.0)     # +0x6c
        self.cnt8 = 0           # +0x70
        self.c0 = self.c1 = self.c2 = 0   # +0x74 +0x78 +0x7c
        self.limit = 0x7FFFFFFF  # +0x80 (원본 기본 0: 별도 설정 경로 미확정 → 제한 없음으로 둠)
        self.flag = 0           # +0x84 byte

    def update(self, repeat_frame):
        c0 = max(self.c0, 1) - 1; c1 = max(self.c1, 1) - 1; c2 = max(self.c2, 1) - 1
        self.c0, self.c1, self.c2 = c0, c1, c2
        if c0 > 0:
            return False
        if self.cnt8 >= self.limit:
            return False
        one = f32(1.0)
        adv = (c1 == 0) or (self.flag and self.phase < one)
        if adv:
            inc = f32(one / f32(repeat_frame))
            self.phase = f32(inc + self.phase)
            rem = f32(f32(one - self.phase) / inc)
            self.rem = rem if rem > 0 else f32(0.0)
            if self.phase >= one:
                pass
            else:
                d = f32(self.phase - one)
                if f32(-1e-5) <= d <= f32(1e-5):
                    self.phase = one
        else:
            if self.phase < one:
                d = f32(self.phase - one)
                if f32(-1e-5) <= d <= f32(1e-5):
                    self.phase = one
        if self.phase < one:
            return False
        if c1 != 0 and self.flag:
            return False
        self.phase = f32(self.phase - one)
        return True


def cmd_table():
    names = sorted(p.name.split(".")[0] for p in GPT.glob("*.json")
                   if '"spl__WeaponShooterParam"' in p.read_text(encoding="utf-8"))
    keys = ["RepeatFrame", "Stand_DegSwerve", "Jump_DegSwerve", "Stand_DegBiasMin", "Stand_DegBiasMax",
            "Stand_DegBiasKf", "Stand_DegBiasDecrease", "Jump_DegBiasMax", "Jump_DegBiasDecreaseStartFrame",
            "Jump_DegBiasEndFrame", "PreDelayFrame_HumanShot", "PreDelayFrame_SquidShot", "SquidShotShorteningFrame",
            "PostDelayFrame", "ShotGuideFrame"]
    rows = []
    for n in names:
        try:
            P = shooter_param(n)
        except FileNotFoundError:
            continue
        rows.append([n] + [P[k] for k in keys])
    print("| 표 | " + " | ".join(keys) + " |")
    print("|---" * (len(keys) + 1) + "|")
    for r in rows:
        print("| " + " | ".join(str(round(v, 4)) if isinstance(v, float) else str(v) for v in r) + " |")
    json.dump({r[0]: dict(zip(keys, r[1:])) for r in rows},
              open(ROOT / "analysis/camera/shooter_swerve_table.json", "w"), indent=1)


def cmd_selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name)

    # 1) sead 기본 상태 (모든 시드 0 → 1, 0x6C078967, 0x714ACB41, 0x48077044 중 X,W만 사용)
    st = seed_state(0, 0, 0, 0, 0)
    chk("seed(0,0,0,0,0): X=M*0+1=1, Y=M*1+2 (sead init 수식)", st[0] == 1 and st[1] == (0x6C078965 + 2) & M32)
    st2 = [1, 0x6C078967, 0x714ACB41, 0x48077044]
    u = rand_u32(st2)
    t = 1 ^ (1 << 11)
    chk("xorshift 첫 값 수식", u == ((0x48077044 ^ (0x48077044 >> 19) ^ t ^ (t >> 8)) & M32))
    # 2) bias 곡선: bias=0.5 항등, bias=0.25 → u^2, bias 0.8 → |u|^0.3219
    chk("bias 0.5 항등", bias_curve(0.3, 0.5) == f32(0.3))
    chk("bias 0.25 ≈ u^2", abs(bias_curve(0.6, 0.25) - 0.36) < 1e-5)
    chk("bias 0.25 부호 유지", abs(bias_curve(-0.6, 0.25) + 0.36) < 1e-5)
    chk("bias 0.8 ≈ u^0.32193", abs(bias_curve(0.5, 0.8) - 0.5 ** 0.321928) < 1e-5)
    chk("|u|<0.001 → 0", bias_curve(0.0005, 0.25) == 0)
    # 3) 사인표 회전 = math 회전 (오차 < 1e-5)
    for deg in (0.0, 6.0, -6.0, 12.0, 37.5, -90.0):
        d = rotate_y((0.0, 0.0, 1.0), deg * math.pi / 180)
        chk(f"회전 {deg}°", abs(d[0] - math.sin(math.radians(deg))) < 1e-4 and abs(d[2] - math.cos(math.radians(deg))) < 1e-4)
    # 4) 상태 전이 (스플래시슈터)
    P = shooter_param("WeaponShooterNormal")
    s = SwerveState(P)
    s.bias = f32(P["Stand_DegBiasMin"])
    for i in range(30):
        s.fire((0, 0, 1), seed_state(i, 1, 2, 3, 4))
    chk("연사 30발 후 bias = Max", s.bias == f32(P["Stand_DegBiasMax"]))
    s.on_jump()
    sw, jb = s.swerve_and_jumpbias()
    chk("점프 직후 흔들림 = Jump_DegSwerve(12)", sw == f32(12.0))
    chk("점프 직후 jumpBias = Jump_DegBiasMax(0.4)", abs(jb - 0.4) < 1e-6)
    for i in range(P["Jump_DegBiasEndFrame"]):
        s.end_frame(True, False, True)
    sw, jb = s.swerve_and_jumpbias()
    chk("End 프레임 경과(감소 1/프레임) → 서기 값", sw == f32(P["Stand_DegSwerve"]) and jb == 0)
    # 5) 타이머: RepeatFrame 6, 계속 당김 → 6프레임마다 발사 (첫 발은 phase 초기값에 의존)
    tm = RepeatTimer(); tm.phase = f32(1.0) - f32(1.0) / f32(6)   # 대기 상태(rem=1) 가정 [판독: 0x710258295c]
    fired = [i for i in range(30) if tm.update(6)]
    chk("RepeatFrame 6 연사 간격", all(b - a == 6 for a, b in zip(fired, fired[1:])) and fired[0] == 0)
    print("ALL PASS" if ok else "SOME FAIL")


def cmd_sim(a):
    P = shooter_param(a.table)
    s = SwerveState(P)
    s.bias = f32(P["Stand_DegBiasMin"])
    seed = [int(x) for x in a.seed.split(",")]
    tm = RepeatTimer(); tm.phase = f32(1.0) - f32(1.0) / f32(P["RepeatFrame"])
    for fr in range(a.frames):
        if fr == a.jump:
            s.on_jump()
        if tm.update(P["RepeatFrame"]):
            r = s.fire((0.0, 0.0, 1.0), seed_state(a.frame0 + fr, *seed))
            print(f"f{fr:3d} swerve={r['swerve_deg']:.3f} bias={r['bias_used']:.4f} r={r['r']:.6f} "
                  f"u={r['u']:+.6f} ub={r['u_biased']:+.6f} angle={r['angle_deg']:+.4f}°")
        s.end_frame(True, False, True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd")
    sp.add_parser("table"); sp.add_parser("selftest")
    s = sp.add_parser("sim"); s.add_argument("table"); s.add_argument("--frames", type=int, default=60)
    s.add_argument("--jump", type=int, default=-1); s.add_argument("--seed", default="0,0,0,0")
    s.add_argument("--frame0", type=int, default=1000)
    a = ap.parse_args()
    {"table": lambda: cmd_table(), "selftest": lambda: cmd_selftest(), "sim": lambda: cmd_sim(a)}.get(a.cmd, ap.print_help)()


if __name__ == "__main__":
    main()
