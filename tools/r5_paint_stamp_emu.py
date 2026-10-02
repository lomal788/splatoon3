"""[r5 paint] 도색 스탬프 배치(회전·경사 보정·행렬·깊이) 원본 실행 검증.

원본 함수를 unicorn 으로 실행하고, 판독한 식을 독립적으로 옮긴 재구현과 비교한다.
  cam   0x710358857c  렌더러 카메라(렌더러+0x8a8, vtable 0x7105721238) vt+0x20 = LookAt 행렬 갱신
                      (pos=(0,1048575.875,0) double, at=0, up=(0,0,-1): 0x7102c16ed0 이 넣는 값)
  proj  0x7103589f84 / 0x7103589b48  직교 투영 vt+0x58 / vt+0x60(장치 행렬, posture 0)
                      Floor 대상 vt+0x60(0x7102c1b5a4)이 넣는 값: near 0, far 1048575.875, 상하좌우 ±size/2
  theta 0x7102c1233c  스탬프 회전 각(Floor kind 1 / Col kind 2 기저)
  slope 0x7102c124bc  경사 보정 (φ, c)
  wvp   0x7102c17ae0  스탬프 월드-뷰-투영 행렬
재구현:
  - sincos(idx): 표 0x7104aa5b5c(256칸×(sin,dsin,cos,dcos)) [데이터] 보간.
  - 행렬: M0 = rows (W,0,0 | 0) (0,0,1 | 0) (0,-L,0 | 0); c≠1 이면 Ry(-ψ)·Sx(c)·Ry(ψ), ψ=φ+θ; Ry(θ);
          T(p0,p1,-p2); 그 뒤 V(3x4)·, P(4x4)·. Ry(a): r0'=fma(r2,sin,r0·cos), r2'=fma(r2,cos,r0·(-sin)) (원본 fmla 순서, 한 번 반올림).
  - θ, φ 는 atan2 색인이라 비트 재구현 대신 sincos(θ) 가 (y,x)/|·| 와 1e-4 안인지로 본다(검증 범위 밖).
정적 초기화 0x7102c2e270·0x7102bd77e0 을 먼저 실행해 기저 전역을 채운다.
스텁: PLT(sqrtf 등)는 paint4_emu.PEmu 의 math 훅(파이썬 double → f32). 이번 경로는 NaN 일 때만 sqrtf 를 부름.
사용: PY web/tools/r5_paint_stamp_emu.py [--n 400] [--out analysis/paint/r5_stamp_emu_out.txt]
"""
import argparse
import math
import random
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paint4_emu import PEmu  # noqa: E402

f32 = np.float32
ROOT = Path(__file__).resolve().parents[2]
SIN_TAB = 0x7104AA5B5C


def fb(x):
    return struct.pack("<f", float(f32(x)))


def bits(x):
    return struct.unpack("<I", struct.pack("<f", float(f32(x))))[0]


class Tab:
    def __init__(self, e):
        raw = e.r(SIN_TAB, 256 * 16)
        self.t = [struct.unpack_from("<4f", raw, i * 16) for i in range(256)]

    def sincos(self, idx):
        idx &= 0xFFFFFFFF
        a, b, c, d = (f32(v) for v in self.t[idx >> 24])
        fr = f32(f32(idx & 0xFFFFFF) * f32(5.9604645e-08))
        return f32(a + f32(b * fr)), f32(c + f32(fr * d))


def fma32(a, b, c):
    """f32 융합 곱셈-덧셈(한 번 반올림, 짝수 쪽). Fraction 으로 정확히 계산한 뒤 가장 가까운 f32."""
    from fractions import Fraction
    a, b, c = f32(a), f32(b), f32(c)
    if not (np.isfinite(a) and np.isfinite(b) and np.isfinite(c)):
        return f32(float(a) * float(b) + float(c))
    ex = Fraction(float(a)) * Fraction(float(b)) + Fraction(float(c))
    if ex == 0:
        pz = float(a) * float(b)
        return f32(0.0) if (pz == 0 and math.copysign(1, pz) != math.copysign(1, float(c))) or (pz != 0) else f32(float(c) + pz)
    x = f32(float(ex))
    best = x
    for y in (np.nextafter(x, f32(np.inf)), np.nextafter(x, f32(-np.inf))):
        dy, db = abs(Fraction(float(y)) - ex), abs(Fraction(float(best)) - ex)
        if dy < db or (dy == db and (bits(y) & 1) == 0):
            best = y
    return f32(best)


def mul_rows(rows, c, s):
    """Ry (원본 fmla 순서): r0' = fma(r2, s, r0·c) + 0, r1' = r1, r2' = fma(r2, c, r0·(−s)) + 0."""
    r0, r1, r2 = rows
    n0 = [f32(fma32(r2[j], s, f32(r0[j] * c)) + f32(0)) for j in range(4)]
    n2 = [f32(fma32(r2[j], c, f32(r0[j] * f32(-s))) + f32(0)) for j in range(4)]
    return [n0, list(r1), n2]


def re_stamp(tab, W, L, theta, phi, k, p, V, P):
    rows = [[f32(W), f32(0), f32(0), f32(0)], [f32(0), f32(0), f32(1), f32(0)], [f32(0), f32(-L), f32(0), f32(0)]]
    if f32(k) != f32(1.0):
        psi = (phi + theta) & 0xFFFFFFFF
        s1, c1 = tab.sincos(psi)
        rows = mul_rows(rows, c1, s1)
        rows[0] = [f32(v * f32(k)) for v in rows[0]]
        s2, c2 = tab.sincos((-psi) & 0xFFFFFFFF)
        rows = mul_rows(rows, c2, s2)
    s, c = tab.sincos(theta)
    rows = mul_rows(rows, c, s)
    t = [f32(p[0]), f32(p[1]), f32(-f32(p[2]))]
    rows = [[f32(f32(0) + r[0]), f32(f32(0) + r[1]), f32(f32(0) + r[2]), f32(t[i] + r[3])] for i, r in enumerate(rows)]
    # V(3x4)·M, P(4x4)·VM: 원본 = (0,0,0,X_i3) + fma(M2, X_i2, fma(M1, X_i1, M0·X_i0)) (행 단위 SIMD)
    def mul(X, Mr, nrow):
        o = []
        for i in range(nrow):
            row = []
            for j in range(4):
                acc = fma32(Mr[2][j], X[i][2], fma32(Mr[1][j], X[i][1], f32(Mr[0][j] * X[i][0])))
                row.append(f32((X[i][3] if j == 3 else f32(0)) + acc))
            o.append(row)
        return o
    VM = mul(V, rows, 3)
    out = mul(P, VM, 4)
    return out


def re_lookat(pos, at, up):
    """sead LookAt(0x710358857c 판독): z=norm(pos-at) (double 차 → f32), x=norm(up×z), y=z×x, t=-(row·pos) double."""
    z = [f32(pos[i] - at[i]) for i in range(3)]
    l2 = f32(f32(f32(z[0] * z[0]) + f32(z[1] * z[1])) + f32(z[2] * z[2]))
    ln = f32(math.sqrt(float(l2)))
    if ln > 0:
        r = f32(f32(1.0) / ln)
        z = [f32(r * v) for v in z]
    x = [f32(f32(z[2] * up[1]) - f32(z[1] * up[2])), f32(f32(z[0] * up[2]) - f32(z[2] * up[0])),
         f32(f32(z[1] * up[0]) - f32(z[0] * up[1]))]
    l2 = f32(f32(f32(x[2] * x[2]) + f32(x[0] * x[0])) + f32(x[1] * x[1]))
    ln = f32(math.sqrt(float(l2)))
    if ln > 0:
        r = f32(f32(1.0) / ln)
        x = [f32(x[0] * r), f32(r * x[1]), f32(r * x[2])]
    y = [f32(f32(z[1] * x[2]) - f32(z[2] * x[1])), f32(f32(z[2] * x[0]) - f32(z[0] * x[2])),
         f32(f32(z[0] * x[1]) - f32(z[1] * x[0]))]
    tx = -f32(pos[0] * float(x[0]) + pos[1] * float(x[1]) + pos[2] * float(x[2]))
    ty = -f32(pos[2] * float(y[2]) + pos[0] * float(y[0]) + pos[1] * float(y[1]))
    tz = -f32(pos[0] * float(z[0]) + pos[1] * float(z[1]) + pos[2] * float(z[2]))
    return [[x[0], x[1], x[2], f32(tx)], [y[0], y[1], y[2], f32(ty)], [z[0], z[1], z[2], f32(tz)]]


def re_ortho(near, far, top, bottom, left, right):
    """0x7103589f84 판독식 (+ 장치 행렬 posture 0, ZScale 1, ZOffset 0)."""
    h = f32(f32(right - left) * f32(0.5))
    v = f32(f32(top - bottom) * f32(0.5))
    m = [[f32(1) / h, 0, 0, f32(f32(f32(left + right) * f32(-0.5)) / h)],
         [0, f32(1) / v, 0, f32(f32(f32(top + bottom) * f32(-0.5)) / v)],
         [0, 0, 0, 0], [0, 0, 0, f32(1)]]
    r = f32(f32(1) / f32(far - near))
    m[2][2] = f32(r * f32(-2.0))
    m[2][3] = f32(r * f32(-f32(near + far)))
    return [[f32(v) for v in row] for row in m]


class S(PEmu):
    def call(self, func, *args):
        from unicorn import arm64_const as k
        regs = [k.UC_ARM64_REG_X0, k.UC_ARM64_REG_X1, k.UC_ARM64_REG_X2, k.UC_ARM64_REG_X3,
                k.UC_ARM64_REG_X4, k.UC_ARM64_REG_X5, k.UC_ARM64_REG_X6, k.UC_ARM64_REG_X7]
        for r, v in zip(regs, args):
            self.uc.reg_write(r, v)
        res = self.run(func, count=0)
        if res is not True:
            raise RuntimeError(f"{hex(func)}: {res}")
        return self.uc.reg_read(k.UC_ARM64_REG_X0)

    def rf(self, a, n):
        return list(struct.unpack("<%df" % n, self.r(a, 4 * n)))


def mat_rows(vals, nrow, ncol):
    return [[f32(vals[i * ncol + j]) for j in range(ncol)] for i in range(nrow)]


def same(a, b):
    return bits(a) == bits(b) or (float(a) == 0.0 and float(b) == 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--out", default=str(ROOT / "analysis" / "paint" / "r5_stamp_emu_out.txt"))
    a = ap.parse_args()
    lines = []
    log = lambda s: (lines.append(s), print(s))
    e = S()
    tab = Tab(e)
    rng = random.Random(20261003)
    # 기저 전역(bss)은 정적 초기화가 채운다: Floor 0x71058ef334 ← 0x7102c2e270, Col 0x71058ed114 ← 0x7102bd77e0
    e.call(0x7102C2E270)
    e.call(0x7102BD77E0)
    log(f"기저 Floor 0x71058ef334 = {[round(v, 6) for v in e.rf(0x71058EF334, 9)]}, Col 0x71058ed114 = {[round(v, 6) for v in e.rf(0x71058ED114, 9)]} (원본 정적 초기화 실행)")

    # 1) 카메라 LookAt
    cam = e.alloc(0x100)
    e.w(cam + 0x50, fb(0) + fb(0) + fb(-1))
    e.w(cam + 0x60, struct.pack("<3d", 0.0, 1048575.875, 0.0) + struct.pack("<3d", 0.0, 0.0, 0.0))
    mtx = e.alloc(0x40)
    e.call(0x710358857C, cam, mtx)
    V = mat_rows(e.rf(mtx, 12), 3, 4)
    Vr = re_lookat((0.0, 1048575.875, 0.0), (0.0, 0.0, 0.0), (f32(0), f32(0), f32(-1)))
    okV = all(same(V[i][j], Vr[i][j]) for i in range(3) for j in range(4))
    log(f"cam 0x710358857c: 원본 V = {[[float(x) for x in r] for r in V]}  재구현 {'일치' if okV else '불일치 ' + str(Vr)}")

    # 2) 직교 투영 (Floor 200×200)
    pj = e.alloc(0x100)
    e.w(pj + 0x98, fb(0.0) + fb(1048575.875) + fb(100.0) + fb(-100.0) + fb(-100.0) + fb(100.0))
    e.w(pj + 0x90, fb(1.0) + fb(0.0))
    e.call(0x7103589F84, pj, pj + 0xC)
    e.call(0x7103589B48, pj, pj + 0x4C, pj + 0xC, 0)
    P = mat_rows(e.rf(pj + 0x4C, 16), 4, 4)
    Pr = re_ortho(f32(0), f32(1048575.875), f32(100), f32(-100), f32(-100), f32(100))
    okP = all(same(P[i][j], Pr[i][j]) for i in range(4) for j in range(4))
    log(f"proj 0x7103589f84+0x7103589b48: 원본 P = {[[float(x) for x in r] for r in P]}  재구현 {'일치' if okP else '불일치 ' + str(Pr)}")

    # 3) θ (Floor·Col 기저), φ·c (Floor)
    D = e.alloc(0x100)
    I3 = [[f32(1), f32(0), f32(0), f32(0)], [f32(0), f32(1), f32(0), f32(0)], [f32(0), f32(0), f32(1), f32(0)]]
    I4 = I3 + [[f32(0), f32(0), f32(0), f32(1)]]
    th_bad = sl_bad = wv_bad = wv_zero = orient_bad = depth_bad = 0
    n = a.n
    for it in range(n):
        kind = 1 if it % 2 == 0 else 2
        d = [rng.uniform(-1, 1) for _ in range(3)]
        if it % 17 == 0:
            d = [0.0, rng.uniform(-1, 1), 0.0]
        e.w(D, b"\0" * 0x100)
        e.w(D + 0x3C, b"".join(fb(v) for v in d))
        e.w(D + 0x4C, struct.pack("<I", kind))
        th = e.call(0x7102C1233C, D, 0) & 0xFFFFFFFF
        if kind == 1:
            y, x = f32(-f32(d[0])), f32(-f32(d[2]))      # d·(B2×B1), d·B1 with B = 0x71058ef334 rows (1,0,0)(0,0,-1)(0,1,0)
        else:
            y, x = f32(-f32(d[0])), f32(d[1])            # Col 기저 = 단위(0x71058ed114)
        h = math.hypot(float(y), float(x))
        s, c = tab.sincos(th)
        if h > 1e-6 and (abs(float(s) - float(y) / h) > 1e-4 or abs(float(c) - float(x) / h) > 1e-4):
            th_bad += 1
            if th_bad <= 3:
                log(f"  θ 불일치 kind={kind} d={d} θ={th:#x} sincos={s},{c} 기대 {float(y)/h},{float(x)/h}")
        if kind != 1:
            continue
        # 경사 보정
        if it % 4 == 0:
            nrm = [0.0, 1.0, 0.0]
        else:
            tilt = math.radians(rng.uniform(1, 60))
            az = rng.uniform(0, 2 * math.pi)
            nrm = [math.sin(tilt) * math.sin(az) * 3.0, math.cos(tilt) * 3.0, math.sin(tilt) * math.cos(az) * 3.0]
        e.w(D + 0x30, b"".join(fb(v) for v in nrm))
        e.call(0x7102C124BC, D, 0)
        rv = e.uc.reg_read(__import__("unicorn").arm64_const.UC_ARM64_REG_X0)
        phi, kc = rv & 0xFFFFFFFF, struct.unpack("<f", struct.pack("<I", rv >> 32))[0]
        nn_ = [f32(v) for v in nrm]
        l2 = f32(f32(f32(nn_[0] * nn_[0]) + f32(nn_[1] * nn_[1])) + f32(nn_[2] * nn_[2]))
        r = f32(f32(1) / f32(math.sqrt(float(l2))))
        nh = [f32(v * r) for v in nn_]
        # c = |n̂·B2|, B2=(0,1,0): 원본 식 (n̂x*0 + n̂y*1) + n̂z*0
        exp_c = abs(f32(f32(f32(nh[0] * f32(0)) + f32(nh[1] * f32(1))) + f32(nh[2] * f32(0))))
        t = [f32(f32(nh[1] * 0) - f32(nh[2] * 1)), f32(f32(nh[2] * 0) - f32(nh[0] * 0)), f32(f32(nh[0] * 1) - f32(nh[1] * 0))]
        tl = math.sqrt(sum(float(v) ** 2 for v in t))
        if tl < 0.01:
            ok = phi == 0 and kc == 1.0
        else:
            ty_, tx_ = -float(t[2]) / tl, float(t[0]) / tl        # t·B1, t·B0 (B1=(0,0,-1))
            sp, cp = tab.sincos((-phi) & 0xFFFFFFFF)
            ok = bits(kc) == bits(exp_c) and abs(float(sp) - ty_) < 1e-4 and abs(float(cp) - tx_) < 1e-4
        if not ok:
            sl_bad += 1
            if sl_bad <= 3:
                log(f"  slope 불일치 n={nrm} φ={phi:#x} c={kc} 기대 c={float(exp_c)}")
        # WVP
        W, L = rng.uniform(0.2, 6), rng.uniform(0.2, 9)
        p = [rng.uniform(-90, 90), f32(rng.randrange(0, 1 << 20) * 0.0625), rng.uniform(-90, 90)]
        for VV, PP, tag in ((I3, I4, "I"), (V, P, "VP")):
            pb = e.alloc(16)
            e.w(pb, b"".join(fb(v) for v in p))
            vb = e.alloc(0x30)
            e.w(vb, b"".join(fb(VV[i][j]) for i in range(3) for j in range(4)))
            ppb = e.alloc(0x40)
            e.w(ppb, b"".join(fb(PP[i][j]) for i in range(4) for j in range(4)))
            sz = e.alloc(16)
            e.w(sz, fb(W) + fb(L) + fb(1.0))
            k7 = e.alloc(8)
            e.w(k7, struct.pack("<I", phi) + fb(kc))
            outb = e.alloc(0x40)
            e.call(0x7102C17AE0, outb, sz, th, pb, vb, ppb, k7)
            got = mat_rows(e.rf(outb, 16), 4, 4)
            exp = re_stamp(tab, f32(W), f32(L), th, phi, f32(kc), [f32(v) for v in p], VV, PP)
            for i in range(4):
                for j in range(4):
                    if bits(got[i][j]) != bits(exp[i][j]):
                        if float(got[i][j]) == 0.0 and float(exp[i][j]) == 0.0:
                            wv_zero += 1
                        else:
                            wv_bad += 1
                            if wv_bad <= 3:
                                log(f"  wvp({tag}) 불일치 [{i}][{j}] 원본 {got[i][j]} 재구현 {exp[i][j]}")
            if tag == "I":
                # 방향 검사(바닥 XZ 평면, 원본 행렬 그대로): 쿼드 +y(텍스처 v=0) → 진행 방향 d̂·L,
                # +x(u=1) → d̂×up·W, 그 뒤 등고선 방향 û = normalize(−n.z, n.x) 으로 c 배 압축(경사 보정)
                g = np.array([[float(v) for v in r] for r in got])
                F = np.array([g[0][1], g[2][1]])
                R = np.array([g[0][0], g[2][0]])
                dn = math.hypot(d[0], d[2])
                if dn < 1e-6:
                    continue
                dd = np.array([d[0], d[2]]) / dn
                F0, R0 = dd * L, np.array([-dd[1], dd[0]]) * W
                tt = np.array([-nrm[2], nrm[0]])
                if np.linalg.norm(tt) > 1e-6 * np.linalg.norm(nrm):
                    u = tt / np.linalg.norm(tt)
                    F0 = F0 - (1 - float(kc)) * np.dot(F0, u) * u
                    R0 = R0 - (1 - float(kc)) * np.dot(R0, u) * u
                if np.abs(F - F0).max() > 5e-4 * max(1, L) or np.abs(R - R0).max() > 5e-4 * max(1, W) or abs(g[1][0]) + abs(g[1][1]) > 0:
                    orient_bad += 1
                    if orient_bad <= 3:
                        log(f"  방향 불일치 d={d} n={nrm} F={F} R={R} 기대 F={F0} R={R0}")
            else:
                # 깊이: 같은 쿼드 중심 clip z, D+0xc 를 1/16 키우면 z 가 줄어야(가까워야) 함
                g = [[float(v) for v in r] for r in got]
                z0 = g[2][3]
                p2 = list(p)
                p2[1] = float(f32(p[1] + 0.0625))
                pb2 = e.alloc(16)
                e.w(pb2, b"".join(fb(v) for v in p2))
                outb2 = e.alloc(0x40)
                e.call(0x7102C17AE0, outb2, sz, th, pb2, vb, ppb, k7)
                z1 = struct.unpack("<f", e.r(outb2 + 0x2C, 4))[0]
                if not (z1 < z0):
                    depth_bad += 1
                    if depth_bad <= 3:
                        log(f"  깊이 순서 예외 y={p[1]} z0={z0} z1={z1}")
    nf = (n + 1) // 2
    log(f"theta 0x7102c1233c: {n - th_bad}/{n} (sincos(θ) 가 (y,x)/|·| 와 1e-4 이내; Floor·Col 반반)")
    log(f"slope 0x7102c124bc: {nf - sl_bad}/{nf} (c 비트 일치, φ 1e-4 이내)")
    log(f"wvp 0x7102c17ae0: 원소 불일치 {wv_bad} (±0 부호만 다른 원소 {wv_zero}), 대상 {nf * 2 * 16} 원소")
    log(f"방향(쿼드 +y=진행·L, +x=진행×위·W, 등고선 방향 c배 압축, Y 성분 0; 색인 각 보간 오차 때문에 5e-4·크기 허용): 불일치 {orient_bad}/{nf}")
    log(f"깊이(D+0xc 1/16 증가 → clip z 감소): 예외 {depth_bad}/{nf}")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
