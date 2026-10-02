"""r5 range: SighterTarget 관련 원본 함수를 unicorn으로 실행해 독립 재구현과 비트 대조.

대상(원본 주소):
  A. 휨 계산기  0x7101e3422c(충격) / 0x7101e33ed8(갱신) / 0x7101e34468(방향각, 내부 0x7101252998 atan2Idx 포함)
  B. 몸 캡슐 A 정점 보간 0x71021f0dcc
  C. 애니 보조: 재생 0x7101266974 → 갱신 0x71012664cc → 끝 판정 0x710126006c (연속 실행)
  D. 로케이터 영역 안쪽 판정 0x71012496e8 (case 1~7)
스텁(외부 함수만): PLT sqrtf/logf/expf/cosf/LockMutex/UnlockMutex/guard, 가짜 vtable 의 dynamic cast(1 반환),
  C 의 모델 바인드 0x71036731d0(ret)·애니 이름 검색 0x71036c29ec(고정 인덱스)·프레임 평가 콜백(ret).
결과: analysis/completion/r5/range_emu.json
"""
import ctypes
import json
import math
import random
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

from network_uc import UC, STUB, BASE
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = (ROOT / "extracted" / "exefs" / "main.reloc.img").read_bytes()
crt = ctypes.CDLL("ucrtbase")
for n in ("logf", "expf", "cosf", "sqrtf"):
    getattr(crt, n).argtypes = [ctypes.c_float]
    getattr(crt, n).restype = ctypes.c_float


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def fb(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def img_u32(a):
    return struct.unpack_from("<I", IMG, a - BASE)[0]


def img_f32(a):
    return struct.unpack_from("<f", IMG, a - BASE)[0]


def img_u64(a):
    return struct.unpack_from("<Q", IMG, a - BASE)[0]


u = UC()
m = u.mu
STUBS_USED = set()


def wq(a, v):
    m.mem_write(a, struct.pack("<Q", v))


def wf(a, v):
    m.mem_write(a, struct.pack("<f", v))


def wu(a, v):
    m.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))


def rf(a):
    return struct.unpack("<f", m.mem_read(a, 4))[0]


def ru(a):
    return struct.unpack("<I", m.mem_read(a, 4))[0]


# ---- PLT 훅: 진입 시 결과를 넣고 LR 로 복귀
def _s0():
    return struct.unpack("<f", struct.pack("<I", m.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]


def _ret_s0(v):
    m.reg_write(UC_ARM64_REG_S0, fb(v))


PLT = {
    0x7103e9bb50: ("sqrtf", lambda: _ret_s0(crt.sqrtf(_s0()))),
    0x7103e9c2a0: ("logf", lambda: _ret_s0(crt.logf(_s0()))),
    0x7103e9be20: ("expf", lambda: _ret_s0(crt.expf(_s0()))),
    0x7103e9be30: ("cosf", lambda: _ret_s0(crt.cosf(_s0()))),
    0x7103e99fd0: ("LockMutex", lambda: None),
    0x7103e99ff0: ("UnlockMutex", lambda: None),
    0x7103e99ef0: ("__cxa_guard_acquire", lambda: m.reg_write(UC_ARM64_REG_X0, 0)),
    0x7103e99f00: ("__cxa_guard_release", lambda: None),
}
EXTRA = {}


def _plt_hook(mu, addr, size, user):
    ent = PLT.get(addr) or EXTRA.get(addr)
    if ent is None:
        return
    STUBS_USED.add(ent[0])
    ent[1]()
    mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))


for a in list(PLT):
    m.hook_add(UC_HOOK_CODE, _plt_hook, begin=a, end=a)


def add_extra(addr, name, fn):
    EXTRA[addr] = (name, fn)
    m.hook_add(UC_HOOK_CODE, _plt_hook, begin=addr, end=addr)


# 가짜 코드: STUB+0x800 = mov w0,#1; ret (dynamic cast 성공)
m.mem_write(STUB + 0x800, struct.pack("<II", 0x52800020, 0xD65F03C0))
CAST1 = STUB + 0x800
cast_vt = u.alloc(0x100)
for off in range(0, 0x100, 8):
    wq(cast_vt + off, CAST1)

rng = random.Random(0x5137A)
C10 = f32(10.0); C60 = f32(0.016666668); C04 = f32(0.4); C001 = f32(0.001); CEXP = f32(2.321928)
CANG = f32(1.4629181e-09); C2PI = f32(6.2831855); CPI = f32(3.1415927)
OUT = {}

# =====================================================================
# A. 휨 계산기
# =====================================================================
TABLE_K = [img_f32(0x7104a9d010 + 4 * i) for i in range(3)]
ATAN_TAB = img_u64(0x7105794808)


def atan_idx(t):
    # fcvtzs #7: trunc(t*128); t ∈ [0,1]
    ts = f32(t * 128.0)
    i = int(ts) if ts >= 0 else -int(-ts)
    idx = img_u32(ATAN_TAB + 8 * i)
    slope = img_f32(ATAN_TAB + 8 * i + 4)
    fr = f32(ts - float(i))
    p = f32(fr * slope)
    pu = 0 if p <= 0 else min(int(p), 0xFFFFFFFF)
    return (idx + pu) & 0xFFFFFFFF


def atan2_idx(y, x):
    """0x7101252998(y=s0, x=s1) 판독 재구현(sead atan2Idx 형)."""
    if math.isnan(x) or math.isnan(y) or (x == 0.0 and y == 0.0):
        return 0
    inf = math.inf
    if abs(y) == inf:
        if abs(x) == inf:
            if x >= 0:
                return 0xE0000000 if y < 0 else 0x20000000
            return 0xA0000000 if y < 0 else 0x60000000
        return 0xC0000000 if y < 0 else 0x40000000
    if abs(x) == inf:
        return 0x80000000 if x < 0 else 0
    if x >= 0:
        if y >= 0:
            if x >= y:
                return atan_idx(f32(y / x))
            return (0x40000000 - atan_idx(f32(x / y))) & 0xFFFFFFFF
        ny = -y
        if ny >= x:
            return (0xC0000000 + atan_idx(f32(x / ny))) & 0xFFFFFFFF
        return (0 - atan_idx(f32(ny / x))) & 0xFFFFFFFF
    nx = -x
    if y >= 0:
        if nx > y:
            return (0x80000000 - atan_idx(f32(y / nx))) & 0xFFFFFFFF
        return (0x40000000 + atan_idx(f32(nx / y))) & 0xFFFFFFFF
    ny = -y
    if nx > ny:
        return (0x80000000 + atan_idx(f32(ny / nx))) & 0xFFFFFFFF
    return (0xC0000000 - atan_idx(f32(nx / ny))) & 0xFFFFFFFF


def dot3(a, b):
    return f32(f32(f32(a[0] * b[0]) + f32(a[1] * b[1])) + f32(a[2] * b[2]))


def bend_impulse_ref(st, scale, c, J, k):
    if k >= 3:
        return
    P, X, Y, Z = st["P"], st["X"], st["Y"], st["Z"]
    d = [f32(c[i] - P[i]) for i in range(3)]
    a = f32(dot3(d, X) * -C10)
    e = f32(dot3(d, Z) * -C10)
    L2 = f32(f32(f32(a * a) + 0.0) + f32(e * e))
    L = f32(math.sqrt(L2))
    if L <= 0.0:
        nx, ny, nz = a, 0.0, e
    else:
        inv = f32(1.0 / L)
        nx, ny, nz = f32(a * inv), f32(inv * 0.0), f32(e * inv)
    jx = f32(f32(dot3(J, X) * C10) * C60)
    jy = f32(f32(dot3(J, Y) * C10) * C60)
    jz = f32(f32(dot3(J, Z) * C10) * C60)
    s = f32(TABLE_K[k] * f32(f32(f32(jx * nx) + f32(jy * ny)) + f32(jz * nz)))
    if s > 1.0:
        s = 1.0
    sc = scale if not (C04 < scale) else C04
    r = f32(sc / C04)
    ar = r if r >= 0 else -r
    g = 0.0
    if ar >= C001:
        q = crt.expf(f32(crt.logf(ar) * CEXP))
        g = q if r >= 0 else -q
    imp = st["imp"]
    imp[0] = f32(imp[0] + f32(f32(nx * s) * g))
    imp[1] = f32(f32(f32(ny * s) * g) + imp[1])
    imp[2] = f32(f32(f32(nz * s) * g) + imp[2])


def bend_update_ref(st, Kd, Kp):
    v, p, imp = st["v"], st["p"], st["imp"]
    for i in range(3):
        v[i] = f32(v[i] + imp[i])
    for i in range(3):
        v[i] = f32(Kd * v[i])
    for i in range(3):
        v[i] = f32(v[i] - f32(p[i] * Kp))
        p[i] = f32(v[i] + p[i])
    q = f32(f32(f32(p[0] * p[0]) + f32(p[1] * p[1])) + f32(p[2] * p[2]))
    if q > 1.0:
        inv = f32(1.0 / f32(math.sqrt(q)))
        p[0] = f32(p[0] * inv)
        p[1] = f32(inv * p[1])
        p[2] = f32(inv * p[2])
    st["imp"] = [0.0, 0.0, 0.0]


def bend_angle_ref(st):
    X, Y, Z, p = st["X"], st["Y"], st["Z"], st["p"]
    w = [f32(f32(f32(X[i] * p[0]) + f32(Y[i] * p[1])) + f32(Z[i] * p[2])) for i in range(3)]
    # 판독식: a = (Y1*w2 - w1*Y2)*Z0 + (w0*Y2 - w2*Y0)*Z1 + (w1*Y0 - w0*Y1)*Z2 ... 아래는 디컴파일 그대로
    f6, f7, f8 = Y  # B+0x48,+0x4c,+0x50 (디컴파일 fVar6~8)
    f10, f11, f12 = Z  # B+0x54,+0x58,+0x5c (fVar10~12)
    f5, f2, f3 = w
    a = f32(f32(f32(f32(f32(f11 * f3) - f32(f2 * f12)) * f6) + f32(f32(f32(f5 * f12) - f32(f3 * f10)) * f7))
            + f32(f32(f32(f2 * f10) - f32(f5 * f11)) * f8))
    yz = f32(f32(f32(f10 * f6) + f32(f11 * f7)) + f32(f12 * f8))
    wz = f32(f32(f32(f5 * f6) + f32(f2 * f7)) + f32(f3 * f8))
    wy = f32(f32(f32(f11 * f2) + f32(f5 * f10)) + f32(f3 * f12))  # 명령 순서(0x7101e344f8~0x7101e34510): (Zy·wy + wx·Zx) + wz·Zz
    b = f32(wy - f32(yz * wz))
    idx = atan2_idx(a, b)
    ang = f32(f32(float(idx)) * CANG)
    r = f32(ang + -C2PI)
    if r <= -CPI:
        r = -CPI
    if ang <= CPI:
        r = ang
    out = f32(r + C2PI)
    if r >= 0.0:
        out = r
    return out, idx


def rand_rot():
    # 임의 회전(직교) — 행: 액터 행렬 3x3
    yaw, pitch, roll = (rng.uniform(-math.pi, math.pi) for _ in range(3))
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    R = [[cy * cr + sy * sp * sr, -cy * sr + sy * sp * cr, sy * cp],
         [cp * sr, cp * cr, -sp],
         [-sy * cr + cy * sp * sr, sy * sr + cy * sp * cr, cy * cp]]
    return [[f32(x) for x in row] for row in R]


def run_bend():
    B = u.alloc(0x90)
    actor = u.alloc(0x300)
    prm = u.alloc(0x80)
    wq(B + 0x28, actor)
    wq(B + 0x88, prm)
    m.mem_write(prm + 0x38, b"\x01\x01")
    cp = u.alloc(16)
    jp = u.alloc(16)
    cases = 0
    impulses = 0
    angle_ok = 0
    examples = []
    for trial in range(400):
        Kd = f32(0.9) if trial % 4 else f32(rng.uniform(0.0, 1.0))
        Kp = f32(0.05) if trial % 4 else f32(rng.uniform(0.0, 0.3))
        wf(prm + 0x30, Kd)
        wf(prm + 0x34, Kp)
        R = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]] if trial < 20 else rand_rot()
        P = [f32(rng.uniform(-50, 50)) for _ in range(3)]
        # 액터 +0x28c 위치, +0x298 행렬(행 우선 3x4: 행 r = +0x298+0xc*r)
        for i in range(3):
            wf(actor + 0x28c + 4 * i, P[i])
        for r in range(3):
            for c in range(3):
                wf(actor + 0x298 + 0xC * r + 4 * c, R[r][c])
        X = [R[0][0], R[1][0], R[2][0]]
        Y = [R[0][1], R[1][1], R[2][1]]
        Z = [R[0][2], R[1][2], R[2][2]]
        m.mem_write(B + 0x30, b"\0" * 0x58)
        v0 = [f32(rng.uniform(-0.05, 0.05)) for _ in range(3)] if trial % 3 == 0 else [0.0] * 3
        p0 = [f32(rng.uniform(-0.3, 0.3)) for _ in range(3)] if trial % 3 == 0 else [0.0] * 3
        for i in range(3):
            wf(B + 0x6C + 4 * i, p0[i])
            wf(B + 0x78 + 4 * i, v0[i])
        st = {"P": P, "X": X, "Y": Y, "Z": Z, "v": list(v0), "p": list(p0), "imp": [0.0] * 3}
        # 첫 갱신으로 B+0x30.. 축 복사 (원본 동작) — 재구현도 같은 갱신을 거침
        u.call(0x7101e33ed8, B)
        bend_update_ref(st, Kd, Kp)
        steps = rng.randint(1, 40)
        for s in range(steps):
            n_imp = rng.choice([0, 0, 1, 1, 2, 3])
            for _ in range(n_imp):
                k = rng.choice([0, 0, 0, 1, 2, 3])
                scale = rng.choice([1.0, 1.0, 1.3, 0.2, 0.4, 0.0005, -0.3])
                lc = [f32(rng.uniform(-0.5, 0.5)), f32(rng.uniform(0, 1.6)), f32(rng.uniform(-0.5, 0.5))]
                if rng.random() < 0.05:
                    lc = [0.0, lc[1], 0.0]
                c = [f32(P[i] + X[i] * lc[0] + Y[i] * lc[1] + Z[i] * lc[2]) for i in range(3)]
                J = [f32(rng.uniform(-3, 3)) for _ in range(3)]
                m.mem_write(cp, struct.pack("<3f", *c))
                m.mem_write(jp, struct.pack("<3f", *J))
                u.call(0x7101e3422c, B, cp, jp, k, fargs=(scale,))
                bend_impulse_ref(st, scale, c, J, k)
                got = [rf(B + 0x60 + 4 * i) for i in range(3)]
                assert [fb(x) for x in got] == [fb(x) for x in st["imp"]], ("impulse", trial, s, got, st["imp"])
                impulses += 1
            u.call(0x7101e33ed8, B)
            bend_update_ref(st, Kd, Kp)
            gp = [rf(B + 0x6C + 4 * i) for i in range(3)]
            gv = [rf(B + 0x78 + 4 * i) for i in range(3)]
            assert [fb(x) for x in gp] == [fb(x) for x in st["p"]], ("p", trial, s, gp, st["p"])
            assert [fb(x) for x in gv] == [fb(x) for x in st["v"]], ("v", trial, s, gv, st["v"])
            assert rf(B + 0x60) == 0.0 and rf(B + 0x68) == 0.0
            m.reg_write(UC_ARM64_REG_S0, 0)
            u.call(0x7101e34468, B)
            ga = struct.unpack("<f", struct.pack("<I", m.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
            ra, idx = bend_angle_ref(st)
            assert fb(ga) == fb(ra), ("angle", trial, s, ga, ra, st["p"])
            angle_ok += 1
            cases += 1
            if len(examples) < 3 and any(st["p"]):
                examples.append({"p": st["p"][:], "angle_rad": ga, "angle_deg_x57": f32(ga * 57.295776), "weight": min(1.0, math.sqrt(sum(x * x for x in st["p"])))})
    # atan2Idx 단독(경계 포함)
    at = 0
    special = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0), (1.0, 1.0), (-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0),
               (math.inf, 1.0), (-math.inf, 1.0), (1.0, math.inf), (1.0, -math.inf), (math.inf, math.inf), (-math.inf, -math.inf)]
    vals = special + [(f32(rng.uniform(-5, 5)), f32(rng.uniform(-5, 5))) for _ in range(3000)]
    for y, x in vals:
        m.reg_write(UC_ARM64_REG_S0, fb(y))
        m.reg_write(UC_ARM64_REG_S1, fb(x))
        got = u.call(0x7101252998) & 0xFFFFFFFF
        exp = atan2_idx(y, x)
        assert got == exp, ("atan2idx", y, x, hex(got), hex(exp))
        at += 1
    OUT["A_bend"] = {"functions": ["0x7101e3422c", "0x7101e33ed8", "0x7101e34468", "0x7101252998"],
                     "trials": 400, "impulse_calls": impulses, "update_angle_steps": cases, "atan2idx_cases": at,
                     "bit_matches": "all", "table_k": TABLE_K, "examples": examples}


# =====================================================================
# B. 몸 캡슐 A 정점 보간 0x71021f0dcc
# =====================================================================
def run_capsule():
    tgt = u.alloc(0x200)
    shapes = []
    for off in (0x108, 0x110):
        body = u.alloc(0x100)
        shape = u.alloc(0x100)
        wq(tgt + off, body)
        wq(body + 0x28, shape)
        wq(shape, cast_vt)
        wu(shape + 0x14, 0x20)  # bit5: 갱신 큐 경로 생략
        shapes.append(shape)
    n = 0
    data = [("Main", 1.26, (0.0, 0.39, 0.0), (0.0, 1.26, 0.35)), ("ColBullet", 1.3, (0.0, 0.35, 0.0), (0.0, 1.3, 0.0))]
    for trial in range(600):
        ts = [0.0, 1.0, -0.5, 1 / 45, 44 / 45, 2.0] if trial == 0 else [f32(rng.uniform(-0.2, 1.2))]
        for t in ts:
            t = f32(t)
            inits = [f32(data[0][1]), f32(data[1][1])] if trial < 3 else [f32(rng.uniform(0, 3)) for _ in range(2)]
            wf(tgt + 0x118, inits[0])
            wf(tgt + 0x11c, inits[1])
            exp = []
            for i, sh in enumerate(shapes):
                A = data[i][3] if trial < 3 else tuple(f32(rng.uniform(-1, 2)) for _ in range(3))
                Bv = data[i][2] if trial < 3 else tuple(f32(rng.uniform(-1, 2)) for _ in range(3))
                m.mem_write(sh + 0xd8, struct.pack("<3f", *A))
                m.mem_write(sh + 0xe4, struct.pack("<3f", *Bv))
                tt = 0.0 if t < 0.0 else min(t, 1.0)  # 0x71021f0dec~0x71021f0e04: fcmp/fmin/fcsel
                by = f32(Bv[1])
                y = f32(by + f32(tt * f32(inits[i] - by)))
                exp.append(((0.0, y, 0.0), tuple(f32(x) for x in Bv)))
            u.call(0x71021f0dcc, tgt, fargs=(t,))
            for i, sh in enumerate(shapes):
                gotA = struct.unpack("<3f", m.mem_read(sh + 0xd8, 12))
                gotB = struct.unpack("<3f", m.mem_read(sh + 0xe4, 12))
                assert [fb(x) for x in gotA] == [fb(x) for x in exp[i][0]], ("capA", trial, t, gotA, exp[i][0])
                assert [fb(x) for x in gotB] == [fb(x) for x in exp[i][1]], ("capB", trial, t, gotB)
                n += 1
    # 실제 데이터 표본: Main A=(0,1.26,0.35) → t=1 이후 (0,1.26,0)
    wf(tgt + 0x118, f32(1.26))
    wf(tgt + 0x11c, f32(1.3))
    m.mem_write(shapes[0] + 0xd8, struct.pack("<6f", 0.0, 1.26, 0.35, 0.0, 0.39, 0.0))
    m.mem_write(shapes[1] + 0xd8, struct.pack("<6f", 0.0, 1.3, 0.0, 0.0, 0.35, 0.0))
    samples = {}
    for t in (1.0, 0.0, 22 / 45):
        u.call(0x71021f0dcc, tgt, fargs=(f32(t),))
        samples[str(round(t, 4))] = {"Main_A": list(struct.unpack("<3f", m.mem_read(shapes[0] + 0xd8, 12))),
                                     "ColBullet_A": list(struct.unpack("<3f", m.mem_read(shapes[1] + 0xd8, 12)))}
    OUT["B_capsule"] = {"function": "0x71021f0dcc", "shape_writes": n, "bit_matches": n,
                        "formula": "t'=(t<0)?0:min(t,1); A=(0, B.y+t'*(A0.y-B.y), 0); B 불변 (디컴파일의 max(t,0)만은 정정)",
                        "data_samples": samples,
                        "stub_scope": "shape+0x14 bit5=1 로 dirty 큐(0x7103a66ea4·월드 링) 경로 미실행, dynamic cast=1"}


# =====================================================================
# C. 애니 보조 재생 → 갱신 → 끝 판정
# =====================================================================
def run_anim():
    helper = u.alloc(0xa0)
    holder = u.alloc(0x80)
    animset = u.alloc(0x100)
    slots = u.alloc(0x40)
    res_list = u.alloc(0x40)
    res = u.alloc(0x100)
    res_inner = u.alloc(0x100)
    entries = u.alloc(0x400)
    model_ch = u.alloc(0x1000)
    anim_res = [u.alloc(0x80) for _ in range(4)]
    # helper 생성자 값(vt8 0x71021eec40 판독)
    wq(helper + 0, holder)
    wq(helper + 8, slots)
    wq(helper + 0x10, 0x41a0000000000002)
    wu(helper + 0x18, 0)
    wq(helper + 0x20, 0x7104a98138)
    wu(helper + 0x28, 0)
    m.mem_write(helper + 0x2c, b"\0")
    wu(helper + 0x3c, 0xFFFFFFFF)
    wu(helper + 0x64, 0xFFFFFFFF)
    wf(helper + 0x50, 1.0)
    wf(helper + 0x78, 1.0)
    wf(helper + 0x90, 1.0)
    wq(helper + 0x80, 0)
    for i in range(2):
        m.mem_write(slots + 0x14 * i, struct.pack("<Iffff", 0xFFFFFFFF, 0, 0, 0, 0))
    wf(slots + 0xc, 1.0)
    wq(holder + 0x58, animset)
    # 애니 세트: +200 리소스 수, +0xd0 리소스 포인터 배열, +0x80/+0x88 항목(0x28 B) 배열
    wu(animset + 200, 1)
    wq(animset + 0xd0, res_list)
    wq(res_list, res)
    wq(res + 0x20, res_inner)
    m.mem_write(res_inner + 0xe2, struct.pack("<H", 4))
    wu(animset + 0x80, 4)
    wq(animset + 0x88, entries)
    frames = [30, 1, 45, 24]
    for i, fr in enumerate(frames):
        ent = entries + 0x28 * i
        ptr = u.alloc(8)
        wq(ent, ptr)
        wq(ptr, anim_res[i])
        wu(anim_res[i] + 4, 0)  # 루프 비트(bit2) 없음
        wu(anim_res[i] + 0x40, fr)
        wq(anim_res[i] + 8, 0)
    # 모델 채널 표: +0x38 개수, +0x40 배열(0xb8 B)
    wu(animset + 0x38, 4)
    wq(animset + 0x40, model_ch)
    evalobj = u.alloc(0x40)
    m.mem_write(STUB + 0x810, struct.pack("<I", 0xD65F03C0))
    wq(evalobj + 0x10, STUB + 0x810)
    for i in range(4):
        wu(model_ch + 0xb8 * i, 0xFFFFFFFF)
        wq(model_ch + 0xb8 * i + 0x20, evalobj)
    # 외부: 이름 → 인덱스 검색(0x71036c29ec), 모델 바인드(0x71036731d0)
    cur = {"idx": 0}
    add_extra(0x71036c29ec, "anim_name_search(fixed index)", lambda: m.reg_write(UC_ARM64_REG_X0, cur["idx"]))

    def bind():
        ch = m.reg_read(UC_ARM64_REG_X1)
        aid = m.reg_read(UC_ARM64_REG_X2) & 0xFFFFFFFF
        wu(ch, aid)
        wq(ch + 8, 0)
    add_extra(0x71036731d0, "model_bind", bind)

    nomat = u.alloc(0x80)  # 재질 채널 모델: +0x58 = 0 → 재질 애니 검색 생략
    wq(helper + 0x40, nomat)
    wq(helper + 0x68, nomat)
    namebuf = u.alloc(0x40)
    nameptr = u.alloc(8)
    timelines = {}
    for rate in (1.0, 0.5):
        wf(helper + 0x90, rate)
        for ai, name in enumerate(["DamageShot", "Brust", "Expand", "Flick"]):
            cur["idx"] = ai
            m.mem_write(namebuf, name.encode() + bytes(1))
            wq(nameptr, namebuf)
            ok = u.call(0x710125f27c, helper, nameptr)
            assert ok & 1
            sl = struct.unpack("<Iffff", m.mem_read(slots, 20))
            assert sl[0] >> 16 == ai and sl[1] == 0.0 and sl[2] == f32(rate) and sl[3] == 0.0 and sl[4] == 1.0 and ru(helper + 0x18) == 0, sl
            seq = []
            ref_frame, ref_tick = 0.0, 0
            N = frames[ai]
            for upd in range(int(N / rate) + 5):
                end = u.call(0x710126006c, helper) & 1
                fr = rf(slots + 4)
                ref_end = 1 if ref_frame >= N else 0
                assert fb(fr) == fb(ref_frame) and end == ref_end, (name, upd, fr, ref_frame, end, ref_end)
                seq.append((fr, end))
                u.call(0x71012664cc, helper)
                if ref_tick > 0:
                    ref_frame = min(f32(ref_frame + f32(rate)), float(N))
                ref_tick += 1
            first_end = next(i for i, (_, e) in enumerate(seq) if e)
            timelines[f"{name}@rate{rate}"] = {"frames": N, "end_check_true_at_check_index": first_end,
                                              "frames_seen": [x[0] for x in seq[:6]] + ["..."] + [x[0] for x in seq[-3:]]}
    OUT["C_anim"] = {"functions": ["0x710125f27c(→0x7101266974, 0x710125fa40)", "0x71012664cc", "0x710126006c"],
                     "rule": "재생: frame=0, rate=helper+0x90(생성자 1.0; +0x80 파라미터 없음), blend t=0/rate 1, +0x18 tick=0. 갱신: tick>0 일 때만 frame+=rate 후 [0,N] 클램프(루프 비트 없음), tick++. 끝: frame>=N",
                     "timelines": timelines,
                     "stub_scope": "이름 검색 0x71036c29ec(고정 인덱스 반환)·모델 바인드 0x71036731d0(채널 id 기록만)·프레임 평가 콜백(ret)·cosf(ucrtbase); 재질 채널 id=-1(사용 안 함)"}


# =====================================================================
# D. 영역 안쪽 판정 0x71012496e8
# =====================================================================
def area_ref(shape, s, T, M, S, p):
    d = [f32(p[i] - T[i]) for i in range(3)]
    def col(c):
        return f32(f32(f32(M[c] * d[0]) + f32(M[3 + c] * d[1])) + f32(M[6 + c] * d[2]))
    if shape == 2:
        lx = col(0)
        if abs(lx) <= f32(f32(s * S[0]) * 0.5):
            ly = f32(f32(f32(d[0] * M[1]) + f32(d[1] * M[4])) + f32(d[2] * M[7]))
            if abs(ly) <= f32(f32(s * S[1]) * 0.5):
                lz = col(2)
                return abs(lz) <= f32(f32(s * S[2]) * 0.5)
        return False
    if shape == 3:
        ly = col(1)
        if ly < 0.0:
            return False
        h = f32(s * S[1])
        if f32(h + h) <= ly:
            return False
        lx = col(0)
        lz = col(2)
        r = f32(s * S[0])
        return f32(f32(lx * lx) + f32(lz * lz)) < f32(r * r)
    if shape == 5:
        r = f32(S[0] * s)
        dd = [f32(T[i] - p[i]) for i in range(3)]
        return f32(f32(f32(dd[0] * dd[0]) + f32(dd[1] * dd[1])) + f32(dd[2] * dd[2])) <= f32(r * r)
    if shape == 7:
        r = f32(S[0] * s)
        if f32(f32(f32(d[0] * d[0]) + f32(d[1] * d[1])) + f32(d[2] * d[2])) <= f32(r * r):
            return f32(f32(f32(d[0] * M[1]) + f32(d[1] * M[4])) + f32(d[2] * M[7])) >= 0.0
        return False
    if shape in (1, 6):
        ly = col(1)
        h = f32(s * S[1])
        h2 = f32(h + h)
        if shape == 1:
            if not (ly >= 0.0 and ly < h2):
                return False
            hh = f32(h2 - ly)
        else:
            if ly < 0.0 and ly < -h2:
                return False
            if ly >= 0.0:
                return False
            hh = f32(-ly)
        lx = col(0)
        lz = col(2)
        rad = f32(math.sqrt(f32(f32(lx * lx) + f32(lz * lz))))
        r = f32(s * S[0])
        return f32(rad / hh) < f32(r / h2)
    return False


def run_area():
    area = u.alloc(0x40)
    loc = u.alloc(0x100)
    wq(area + 0x18, loc)
    pt = u.alloc(16)
    n = 0
    per = {}
    for shape in (1, 2, 3, 4, 5, 6, 7):
        cnt_in = 0
        for trial in range(1500):
            T = [f32(rng.uniform(-20, 20)) for _ in range(3)]
            R = rand_rot() if trial % 2 else [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
            M = [R[r][c] for r in range(3) for c in range(3)]
            S = [f32(rng.uniform(0.5, 8)) for _ in range(3)]
            s = f32(rng.choice([1.0, 1.0, 0.5, 2.0]))
            p = [f32(T[i] + rng.uniform(-10, 10)) for i in range(3)]
            if trial % 7 == 0:  # 경계 근처
                p = [f32(T[i] + R[i][0] * s * S[0] * 0.5) for i in range(3)]
            wu(area + 0x20, shape)
            wf(area + 0x24, s)
            m.mem_write(loc + 0x40, struct.pack("<3f", *T))
            m.mem_write(loc + 0x4c, struct.pack("<9f", *M))
            m.mem_write(loc + 0x70, struct.pack("<3f", *S))
            m.mem_write(pt, struct.pack("<3f", *p))
            got = u.call(0x71012496e8, area, pt) & 1
            exp = 1 if (shape != 4 and area_ref(shape, s, T, M, S, p)) else 0
            assert got == exp, ("area", shape, trial, got, exp, T, S, s, p)
            cnt_in += got
            n += 1
        per[str(shape)] = {"cases": 1500, "inside": cnt_in}
    OUT["D_area"] = {"function": "0x71012496e8", "cases": n, "bit_matches": n, "per_shape": per,
                     "enum": "LocatorInfo ShapeType 문자열 순번+1 (0x71013ca4d4): 1 Cone 2 Cube 3 Cylinder 4 Plane(항상 거짓) 5 Sphere 6 ConeShift 7 Hemisphere"}


# =====================================================================
# E. 데미지 숫자 텍스트 갱신 0x710338d2d0 (Shr_Points_00 "T_Num_00" ← 메시지 "000" 인자 2개)
# =====================================================================
def floor_i(v):
    i = int(v) if v >= 0 else -int(-v)  # fcvtzs
    if v < 0.0 and float(i) != v:
        i -= 1
    return i


def run_points():
    obj = u.alloc(0x400)
    arr = u.alloc(0x100)
    tbl = u.alloc(0x100)
    dummy = u.alloc(0x40)
    wu(obj + 0x2b0, 1)
    wq(obj + 0x2b8, arr)
    m.mem_write(arr + 8, b"")
    wu(arr + 0xc, 0)
    wu(arr + 0x3c, 0)
    wq(obj + 0x28, dummy)
    wq(obj + 0x298, tbl)
    wq(tbl, dummy)
    cap = {}

    def settext():
        sp = m.reg_read(UC_ARM64_REG_SP)
        cap["args"] = struct.unpack("<ii", m.mem_read(sp + 0x28, 8))
        cap["n"] = cap.get("n", 0) + 1
    add_extra(0x71013621d0, "text_set(capture)", settext)
    add_extra(0x71032031d0, "layout_base_calc", lambda: None)
    vals = [0.0, 36.0, 108.0, 0.1, 0.7, 35.7, 99.9, 100.0, 0.3, 123.4, 9999.8, -0.5, -1.0, -12.3]
    vals += [f32(a / 10.0) for a in range(0, 20001, 7)]
    vals += [f32(rng.uniform(0, 1000)) for _ in range(2000)]
    n = 0
    skipped = 0
    for v in vals:
        v = f32(v)
        wf(obj + 0x338, v)
        wf(obj + 0x378, f32(v + 1.0) if v != f32(v + 1.0) else 12345.0)
        cap.pop("args", None)
        u.call(0x710338d2d0, obj)
        i = floor_i(v)
        fr = f32(v - f32(float(i)))
        d = floor_i(f32(fr * 10.0))
        assert cap.get("args") == (i, d), (v, cap.get("args"), (i, d))
        assert fb(rf(obj + 0x378)) == fb(v)
        n += 1
    # 값이 이전과 같으면 텍스트를 다시 쓰지 않음
    wf(obj + 0x338, 36.0)
    wf(obj + 0x378, 36.0)
    cap.pop("args", None)
    u.call(0x710338d2d0, obj)
    assert "args" not in cap
    skipped += 1
    ex = {}
    for a in (360, 357, 3, 7, 1080, 999):
        v = f32(float(a) / 10.0)
        i = floor_i(v)
        ex[str(a)] = f"{i}.{floor_i(f32(f32(v - float(i)) * 10.0))}"
    OUT["E_points"] = {"function": "0x710338d2d0", "cases": n, "bit_matches": n, "unchanged_skip_cases": skipped,
                       "rule": "v!=이전값일 때만: i=floor(v)(fcvtzs, 음수·비정수면 −1), d=floor((v−i)×10) → T_Num_00 에 메시지 \"000\"=[i].[d]",
                       "examples_accum_to_text": ex,
                       "stub_scope": "레이아웃 기반 calc 0x71032031d0(ret)·텍스트 설정 0x71013621d0(인자 캡처만); 슬롯 age(+0x3c)=0 으로 Out 분기 미실행"}


if __name__ == "__main__":
    run_points()
    run_bend()
    run_capsule()
    run_anim()
    run_area()
    OUT["stubs_used"] = sorted(STUBS_USED)
    p = ROOT / "analysis/completion/r5/range_emu.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(OUT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("examples", "timelines", "data_samples", "per_shape")} if isinstance(v, dict) else v for k, v in OUT.items()}, ensure_ascii=False, indent=1))
