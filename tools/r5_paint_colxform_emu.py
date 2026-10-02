"""[r5 paint] 지형(Col, kind 2) 도색 대상 좌표 변환 원본 실행 검증.

  0x7102c3fef0(out[9], 강체, 셰이프키, req)  월드 요청(위치·법선·방향) → 패널 좌표 (u,v,w)
  0x7102c4a6bc(kind, &id, pos)              패널 좌표 → 시드용 위치(0x7102c11f80 이 시드 |fcvtzs((z+(x+y))·100)| + N+4 에 씀)
재구현(독립): q = Rᵀ(p − t) (강체 +0xd8 3×4 행 우선), 패널 좌표 = (B0·q, B1·q, B2·q) (B = 0x7102bd7b2c(패널+0x54),
  paint4_colpaint.basis — 원본 45/45 비트 일치 재구현), 되돌림 p' = u·B0 + v·B1 + w·B2 → 트리 행렬(없으면 단위 0x7104a98200).
스텁·가짜 객체:
  - 0x7102c71e50(대상 정보) → kind 2, id 를 쓰고 반환(충돌 셀→패널 id 조회 0x7102c0e04c 경로는 실행 안 함)
  - 강체 +0x28 = 0 → 복합 형상 부분 변환(0x71012ed9c0)·0x7102c0df24 의 메시 트리(+0x3a8)는 비어 있음(단위)
  - 관리자 *0x71058f07b8 / +0x2c0 ColPaint 관리자 / 패널 표 / 트리 +0x3d8 = 0(단위) 는 가짜 메모리
  - PLT(LockMutex 등) x0=0 반환
사용: PY web/tools/r5_paint_colxform_emu.py [--n 2000]
"""
import argparse
import math
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X8, UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_paint_stamp_emu import S, fb, bits  # noqa: E402
import paint4_colpaint as cp  # noqa: E402

f32 = np.float32
ROOT = Path(__file__).resolve().parents[2]
MGR_VAR = 0x71058F07B8


def fcvtzs(x):
    x = float(x)
    if x != x:
        return 0
    return max(-2**31, min(2**31 - 1, int(x)))


def dot3(a, b):
    return f32(f32(f32(a[0] * b[0]) + f32(a[1] * b[1])) + f32(a[2] * b[2]))


def re_to_panel(R, t, p, n, d, B):
    dx = [f32(p[i] - t[i]) for i in range(3)]
    col = lambda j: (R[0][j], R[1][j], R[2][j])      # Rᵀ 의 행 = R 의 열
    q = [dot3(col(j), dx) for j in range(3)]
    nl = [dot3(col(j), n) for j in range(3)]
    dl = [dot3(col(j), d) for j in range(3)]
    out = []
    for v in (q, nl, dl):
        out += [dot3(v, B[0]), dot3(v, B[1]), dot3(v, B[2])]
    return out


def re_from_panel(B, u):
    x = f32(f32(f32(B[0][0] * u[0]) + f32(B[1][0] * u[1])) + f32(B[2][0] * u[2]))
    y = f32(f32(f32(B[0][1] * u[0]) + f32(B[1][1] * u[1])) + f32(B[2][1] * u[2]))
    z = f32(f32(f32(B[0][2] * u[0]) + f32(B[1][2] * u[1])) + f32(B[2][2] * u[2]))
    # 단위 트리 행렬: M3 + ((M0·x + M1·y) + M2·z)
    I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
    o = []
    for r in range(3):
        m = [f32(v) for v in I[r * 4:r * 4 + 4]]
        o.append(f32(m[3] + f32(f32(f32(m[0] * x) + f32(y * m[1])) + f32(z * m[2]))))
    return o


def seed_of(p, n4):
    s = f32(f32(f32(p[2]) + f32(f32(p[0]) + f32(p[1]))) * f32(100.0))
    return (abs(fcvtzs(s)) + n4) & 0xFFFFFFFF


def rot(rng):
    ax = np.array([rng.gauss(0, 1) for _ in range(3)]); ax /= np.linalg.norm(ax)
    a = rng.uniform(-math.pi, math.pi)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--out", default=str(ROOT / "analysis" / "paint" / "r5_colxform_emu_out.txt"))
    a = ap.parse_args()
    lines = []
    log = lambda s: (lines.append(s), print(s))
    e = S()
    st = {"kind": 2, "id": 0}

    def hook(uc, addr, size, ud):
        o = uc.reg_read(UC_ARM64_REG_X8)      # 결과 구조체는 x8(간접 반환)
        uc.mem_write(o + 8, struct.pack("<I", st["kind"]))
        uc.mem_write(o + 0xC, struct.pack("<HBB", st["id"], 0, 0))
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))
    e.uc.hook_add(UC_HOOK_CODE, hook, begin=0x7102C71E50, end=0x7102C71E50)

    NP = 64
    mgr = e.alloc(0x400)
    cpm = e.alloc(0x400)
    tab = e.alloc(8 * NP)
    uvo = e.alloc(0x40)
    e.w(uvo + 0x18, struct.pack("<i", 0))
    panels = []
    for i in range(NP):
        pn = e.alloc(0x80)
        e.w(pn + 0x18, struct.pack("<Q", uvo))
        e.w(pn + 0x10, struct.pack("<I", i))
        e.w(tab + 8 * i, struct.pack("<Q", pn))
        panels.append(pn)
    e.w(MGR_VAR, struct.pack("<Q", mgr))
    e.w(mgr + 0x2C0, struct.pack("<Q", cpm))
    e.w(cpm + 0x390, struct.pack("<I", NP))
    e.w(cpm + 0x398, struct.pack("<Q", tab))
    body = e.alloc(0x300)
    e.w(body + 0x230, struct.pack("<Q", e.alloc(0x10)))
    req = e.alloc(0x40)
    out = e.alloc(0x40)
    idp = e.alloc(8)
    rng = random.Random(20261003)
    bad1 = bad2 = 0
    same_pos = same_seed = 0
    seed_diff_examples = []
    for k in range(a.n):
        pid = rng.randrange(NP)
        mdir = rng.randrange(0x2A)
        e.w(panels[pid] + 0x54, bytes([mdir]))
        st["id"] = pid
        ident = k % 2 == 0
        if ident:
            Rm, tv = np.eye(3), np.zeros(3)
        else:
            Rm, tv = rot(rng), np.array([rng.uniform(-50, 50) for _ in range(3)])
        R = [[f32(Rm[i][j]) for j in range(3)] for i in range(3)]
        t = [f32(v) for v in tv]
        m34 = b"".join(fb(R[i][j]) for i in range(3) for j in range(3)) if False else b"".join(
            fb(R[i][0]) + fb(R[i][1]) + fb(R[i][2]) + fb(t[i]) for i in range(3))
        e.w(body + 0xD8, m34)
        p = [f32(rng.uniform(-200, 200)) for _ in range(3)]
        n = [f32(rng.uniform(-1, 1)) for _ in range(3)]
        d = [f32(rng.uniform(-1, 1)) for _ in range(3)]
        e.w(req, b"".join(fb(v) for v in p + n + d))
        e.w(out, b"\0" * 0x40)
        e.call(0x7102C3FEF0, out, body, 0x1234, req)
        got = e.rf(out, 9)
        B = [[f32(x) for x in v] for v in cp.basis(mdir)]
        exp = re_to_panel(R, t, p, n, d, B)
        if any(bits(f32(got[i])) != bits(exp[i]) for i in range(9)):
            bad1 += 1
            if bad1 <= 3:
                log(f"  to_panel 불일치 dir={mdir:#x} 원본={got} 재구현={[float(x) for x in exp]}")
        # 되돌림
        e.w(idp, struct.pack("<H", pid))
        posb = e.alloc(16)
        e.w(posb, b"".join(fb(v) for v in got[:3]))
        e.call(0x7102C4A6BC, 2, idp, posb)
        back = [struct.unpack("<f", struct.pack("<I", e.uc.reg_read(r) & 0xFFFFFFFF))[0]
                for r in (UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2)]
        expb = re_from_panel(B, [f32(v) for v in got[:3]])
        if any(bits(f32(back[i])) != bits(expb[i]) for i in range(3)):
            bad2 += 1
            if bad2 <= 3:
                log(f"  from_panel 불일치 dir={mdir:#x} 원본={back} 재구현={[float(x) for x in expb]}")
        if ident:
            if all(bits(f32(back[i])) == bits(p[i]) for i in range(3)):
                same_pos += 1
            n4 = rng.randrange(1 << 20)
            if seed_of(back, n4) == seed_of(p, n4):
                same_seed += 1
            elif len(seed_diff_examples) < 3:
                seed_diff_examples.append((p, back))
    nid = (a.n + 1) // 2
    log(f"to_panel 0x7102c3fef0 (kind 2, 강체 단위/임의 반반): {a.n - bad1}/{a.n} 9성분 비트 일치")
    log(f"from_panel 0x7102c4a6bc (kind 2, 트리 비어 단위): {a.n - bad2}/{a.n} 3성분 비트 일치")
    log(f"강체 단위일 때 되돌린 위치 == 원래 월드 위치(비트): {same_pos}/{nid}, 시드 같음: {same_seed}/{nid}")
    for p, b in seed_diff_examples:
        log(f"  시드 다른 예: 월드 {[float(v) for v in p]} → 되돌림 {b}")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
