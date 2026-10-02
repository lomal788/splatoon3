"""원본 실행: (1) 슈터 무기 모델 부착 0x710289beb8(spl::WeaponShooter vt 슬롯49) + 모델 루트 행렬 분해 0x7100f735b0,
(2) 몸 표시 스프링 0x71014586a0(플레이어 모델 홀더).

(1) 스텁: 몸 모델 뼈 get(vt+0x78)은 합성 3x4 f32 12개를 공급(뼈 인덱스·모델 인덱스 기록),
    무기 모델 vt+0x1f8(꼬리 호출) ret, 0x7100f72b7c(모델 갱신) 진입 즉시 복귀, 모델 컴포넌트 vt+0xc8 은 유닛 포인터 반환.
    0x710289beb8·0x7100f735b0 본문은 원본 그대로 실행.
(2) 외부 호출 없음. 홀더·본체 필드를 합성 상태로 채워 프레임 열을 실행.
재구현(decompose, spring_step)은 디컴파일·명령 판독으로 독립 작성한 f32 식. 원본 실행 결과와 비트 비교.
사용: PY web/tools/r5_gfx_char_attach_emu.py → analysis/completion/r5/gfx_char_attach_emu.json
"""
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_LR, UC_ARM64_REG_PC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC, STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F_WPN49 = 0x710289beb8
F_SETMTX = 0x7100f735b0
F_UPDATE = 0x7100f72b7c
F_SPRING = 0x71014586a0


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def bits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def sqrt32(x):
    return f32(x ** 0.5) if x >= 0 else float("nan")


def decompose(m):
    """판독식: 열 노름 = 축 스케일, 열0·열2 정규화, Y축 = 열2×열0 (f32 곱·뺄셈 분리)."""
    m = [f32(v) for v in m]
    c0 = [m[0], m[4], m[8]]
    c1 = [m[1], m[5], m[9]]
    c2 = [m[2], m[6], m[10]]

    def nrm(c):
        s = f32(f32(f32(c[0] * c[0]) + f32(c[1] * c[1])) + f32(c[2] * c[2]))
        return sqrt32(s)
    sx = nrm(c0)
    if sx > 0:
        k = f32(1.0 / sx)
        c0 = [f32(v * k) for v in c0]
    sy = nrm(c1)
    sz = nrm(c2)
    if sz > 0:
        k = f32(1.0 / sz)
        c2 = [f32(v * k) for v in c2]
    x0, y0, z0 = c0
    x2, y2, z2 = c2
    yx = f32(f32(z0 * y2) - f32(y0 * z2))
    yy = f32(f32(x0 * z2) - f32(z0 * x2))
    yz = f32(f32(y0 * x2) - f32(x0 * y2))
    rot = [x0, yx, x2, y0, yy, y2, z0, yz, z2]
    return {"scale": [sx, sy, sz], "trans": [m[3], m[7], m[11]], "rot": rot}


def spring_step(st, body, hlf, squid, dead, special_slot):
    """판독식 재구현. 반환: 기록이 있으면 (x 값, 대상 슬롯) 아니면 None."""
    x_old = st["x"]
    if dead:
        st.update(a0=0, a1=0, x=0.0, v=0.0)
        return (0.0, special_slot) if x_old != 0.0 else None
    body_only = 1 if (body and not hlf and not squid) else 0
    x = x_old
    if st["a0"] != body_only:
        st["a0"] = body_only
        if body_only and st["a1"]:
            st["ac"] = 1
            st["trig"] = st.get("trig", 0) + 1
            x = f32(-0.03)
            st["v"] = f32(st["v"] + f32(0.02))
            st["x"] = x
    st["a1"] = 1 if (hlf or squid or body) else 0
    v = f32(f32(st["v"] + f32(x * f32(-0.2))) * f32(0.8))
    x2 = f32(x + v)
    t = f32(x2 - 1.0)
    st["x"], st["v"] = x2, v
    if -0.001 <= t <= 0.001 and -0.0001 <= v <= 0.0001:
        st["x"], st["v"] = 1.0, 0.0
        x2 = 1.0
    if x2 == x_old:
        return None
    return (x2, special_slot)


def spring_scale(x):
    s0 = f32(x + 1.0)
    s1 = f32(s0 + f32(x * 0.5))
    return [s1, s0, s1]


def main():
    u = GUC()
    m = u.mu
    rng = random.Random(0x5EA5)
    st = {"B": None, "bone_calls": []}

    BONE = STUB + 0x700
    COMP_GET = STUB + 0x708

    def hook_bone(mu, addr, size, d):
        st["bone_calls"].append((mu.reg_read(UC_ARM64_REG_X0), mu.reg_read(UC_ARM64_REG_X2) & 0xFFFFFFFF))
        mu.mem_write(mu.reg_read(UC_ARM64_REG_X1), struct.pack("<12f", *st["B"]))

    def hook_comp(mu, addr, size, d):
        mu.reg_write(UC_ARM64_REG_X0, st["unit"])

    def hook_update(mu, addr, size, d):
        st["update_called"] = st.get("update_called", 0) + 1
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    m.hook_add(UC_HOOK_CODE, hook_bone, begin=BONE, end=BONE)
    m.hook_add(UC_HOOK_CODE, hook_comp, begin=COMP_GET, end=COMP_GET)
    m.hook_add(UC_HOOK_CODE, hook_update, begin=F_UPDATE, end=F_UPDATE)

    # ---- (1) 무기 부착
    W = u.alloc(0x700)
    body = u.alloc(0x100)
    mlist = u.alloc(0x40)
    skel_objs = []
    for i in range(3):
        o = u.alloc(0x20)
        vt = u.alloc(0x100)
        u.wq(o, vt)
        u.wq(vt + 0x78, BONE)
        holder = u.alloc(0x10)
        u.wq(holder, o)
        u.wq(mlist + 8 * i, holder)
        skel_objs.append(o)
    u.wq(body + 0x40, mlist)
    u.wq(W + 0x110, body)
    model = u.alloc(0x600)
    mvt = u.alloc(0x400)
    u.wq(model, mvt)
    u.wq(mvt + 0x1f8, STUB + 0x10)
    comps = u.alloc(0x40)
    comp1 = u.alloc(0x20)
    cvt = u.alloc(0x100)
    u.wq(comp1, cvt)
    u.wq(cvt + 0xc8, COMP_GET)
    u.wq(comps, u.alloc(0x10))
    u.wq(comps + 8, comp1)
    u.wq(model + 0x208, comps)
    u.u32(model + 0x200, 2)
    unit = u.alloc(0x300)
    st["unit"] = unit
    u.wq(W + 0x10, model)

    def rot(ax, ay, az):
        import math
        cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
        # Rz*Ry*Rx
        return [[cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz],
                [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz],
                [-sy, sx * cy, cx * cy]]

    cases = []
    cases.append([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    cases.append([-0.0, 0, 1, -0.7321, 1, 0, 0, 1.0949, 0, 1, 0, -0.02])
    cases.append([0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 3])
    for i in range(400):
        R = rot(rng.uniform(-3.2, 3.2), rng.uniform(-1.6, 1.6), rng.uniform(-3.2, 3.2))
        s = [rng.choice([1.0, rng.uniform(0.2, 3.0)]) for _ in range(3)]
        t = [rng.uniform(-50, 50) for _ in range(3)]
        mm = []
        for r in range(3):
            mm += [R[r][0] * s[0], R[r][1] * s[1], R[r][2] * s[2], t[r]]
        if i % 50 == 7:
            mm = [rng.uniform(-4, 4) for _ in range(12)]
        cases.append([f32(v) for v in mm])
    wpn_ok = 0
    wpn_fail = []
    for ci, B in enumerate(cases):
        mi, bi = ci % 3, (ci * 7) % 87
        m.mem_write(W + 0x3b8, struct.pack("<hh", mi, bi))
        st["B"] = B
        st["bone_calls"] = []
        m.mem_write(model + 0x28c, b"\xcc" * 0x30)
        m.mem_write(unit + 0x268, b"\xcc" * 12)
        m.mem_write(unit + 0x280, b"\x00")
        u.call(F_WPN49, W)
        got_rot = struct.unpack("<9f", m.mem_read(model + 0x298, 36))
        got_t = struct.unpack("<3f", m.mem_read(model + 0x28c, 12))
        got_s = struct.unpack("<3f", m.mem_read(unit + 0x268, 12))
        exp = decompose(B)
        okb = ([bits(v) for v in got_rot] == [bits(v) for v in exp["rot"]]
               and [bits(v) for v in got_t] == [bits(v) for v in exp["trans"]]
               and [bits(v) for v in got_s] == [bits(v) for v in exp["scale"]]
               and st["bone_calls"] == [(skel_objs[mi], bi)]
               and m.mem_read(unit + 0x280, 1)[0] & 1 == 1)
        wpn_ok += okb
        if not okb and len(wpn_fail) < 5:
            wpn_fail.append({"case": ci, "got": [got_rot, got_t, got_s], "exp": exp, "calls": st["bone_calls"]})
    # 몸 포인터 없음: 뼈 get·분해 없이 갱신만
    u.wq(W + 0x110, 0)
    st["bone_calls"] = []
    sentinel = bytes(range(0x30))
    m.mem_write(model + 0x28c, sentinel)
    st["update_called"] = 0
    u.call(F_WPN49, W)
    nobody_ok = bytes(m.mem_read(model + 0x28c, 0x30)) == sentinel and not st["bone_calls"] and st["update_called"] == 1

    # ---- (2) 스프링
    H = u.alloc(0x100)
    P = u.alloc(0x200)
    Bd = u.alloc(0xb000)
    D = u.alloc(0x40)
    u.wq(H + 0x50, P)
    u.wq(P + 0x108, Bd)
    u.wq(Bd + 0xa650, D)
    units = {k: u.alloc(0x300) for k in (0x20, 0x28, 0x30)}
    for k, a in units.items():
        u.wq(H + k, a)
    sp_frames = 0
    sp_ok = 0
    sp_fail = []
    triggers = 0
    for seq in range(60):
        m.mem_write(H + 0xa0, b"\0" * 0x10)
        stt = {"a0": 0, "a1": 0, "x": 0.0, "v": 0.0, "ac": 0}
        body = hlf = squid = 0
        for fr in range(240):
            r = rng.random()
            if r < 0.06:
                body, hlf, squid = rng.choice([(1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0), (1, 1, 0), (1, 0, 1)])
            dead = 1 if rng.random() < 0.01 else 0
            special = rng.random() < 0.2
            u.wq(Bd + 0x678, 0x1234 if special else 0)
            u.wq(Bd + 0x688, 0x1234)
            u.wq(Bd + 0x588, 0)
            m.mem_write(Bd + 0x926c, b"\0")
            u.u32(Bd + 0x65c, 0xf if rng.random() < 0.7 else 3)
            slot = 0x30 if (special and u.ru32(Bd + 0x65c) == 0xf) else 0x28
            m.mem_write(D + 0x30, bytes([dead, 0]))
            m.mem_write(H + 0x60, bytes([body, hlf, squid]))
            for a in units.values():
                m.mem_write(a + 0x268, b"\xee" * 12)
            u.call(F_SPRING, H)
            exp = spring_step(stt, body, hlf, squid, dead, slot)
            got_state = struct.unpack("<BBxxff", m.mem_read(H + 0xa0, 12))
            ok = (got_state[0] == stt["a0"] and got_state[1] == stt["a1"]
                  and bits(got_state[2]) == bits(stt["x"]) and bits(got_state[3]) == bits(stt["v"]))
            for k, a in units.items():
                raw = bytes(m.mem_read(a + 0x268, 12))
                want = None
                if exp is not None and (k == 0x20 or k == exp[1]):
                    want = struct.pack("<3f", *spring_scale(exp[0]))
                ok = ok and ((raw == b"\xee" * 12) if want is None else raw == want)
            sp_frames += 1
            sp_ok += ok
            if not ok and len(sp_fail) < 5:
                sp_fail.append({"seq": seq, "frame": fr, "in": [body, hlf, squid, dead, slot], "got": got_state, "exp": dict(stt)})
        triggers += stt.get("trig", 0)
    out = {
        "weapon_attach": {"function": [hex(F_WPN49), hex(F_SETMTX)], "cases": len(cases), "bit_matches": wpn_ok,
                          "body_absent_ok": nobody_ok, "fail_examples": wpn_fail,
                          "stubs": ["몸 모델 뼈 get vt+0x78: 합성 12 f32 공급", "무기 모델 vt+0x1f8 ret", "0x7100f72b7c 진입 즉시 복귀", "모델 컴포넌트 vt+0xc8 → 유닛 포인터"]},
        "spring": {"function": hex(F_SPRING), "frames": sp_frames, "bit_matches": sp_ok, "triggers": triggers, "fail_examples": sp_fail,
                   "stubs": ["없음(외부 호출 없음). 홀더·본체 필드는 합성"]},
        "plt_stubbed": sorted(set(u.plt_stubbed)),
        "not_executed": ["실제 뼈 행렬 producer(스켈레톤 vt+0x78)", "0x7100f72b7c 모델 갱신·자식 전파", "프레임 스케줄(무기 슬롯49 호출 시점)", "홀더 표시 플래그 producer 0x71014595b0"],
    }
    p = ROOT / "analysis/completion/r5/gfx_char_attach_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"weapon": [len(cases), wpn_ok, nobody_ok], "spring": [sp_frames, sp_ok, triggers], "plt": out["plt_stubbed"]}))
    if wpn_fail:
        print(json.dumps(wpn_fail[:2], default=str)[:2000])
    if sp_fail:
        print(json.dumps(sp_fail[:3], default=str)[:2000])
    sys.exit(0 if (wpn_ok == len(cases) and nobody_ok and sp_ok == sp_frames) else 1)


if __name__ == "__main__":
    main()
