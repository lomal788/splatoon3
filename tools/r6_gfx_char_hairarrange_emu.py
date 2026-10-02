"""원본 실행: HairArrange 뼈 적용 0x71026df700(머리카락 객체) — BoneParam 마다 머리카락 뼈 로컬 변환을 바꾼다.

원본 그대로 실행: 0x71026df700 본문, 캐시 트리 조회 0x71026e12e4·삽입 0x71026e3a28, 개수 0x71038b6944,
  변형 33 전용 가시성 0x71026e0f9c(머리카락 +0x11c != 0x21 이라 즉시 복귀).
가짜 객체(파이썬 훅):
  - 머리카락 모델(+0x3a0) 뼈 집합 vt+0x40 이름→번호, vt+0x68 바인드(로컬 3×4·스케일) 조회, vt+0x50 로컬 설정(기록), vt+0xa0 번호 변환.
  - PLT sinf/cosf 는 파이썬 math 를 f32 로 반올림(원본 SDK libm 아님 — 비교식도 같은 값을 씀).
  - 액터(+0x10)+0x208 = 0 → 스켈레탈 애니 가중(+0xa4) 경로는 실행하지 않음.
판독식(비교 대상):
  S' = S_bind ⊙ max(Scale, 0.01)     (Scale = BoneParam +0x54/+0x58/+0x5c, 0.01 이하이면 0.01)
  R' = R_bind · Mᵀ ... 아래 rot() 참고: M 의 행 = (cy·cz, sz·cy, −sy), (sx·sy·cz − sz·cx, sx·sy·sz + cx·cz, sx·cy),
       (sx·sz + sy·cx·cz, sy·sz·cx − sx·cz, cx·cy), x/y/z = +0x48/+0x4c/+0x50(라디안), new[r][c] = Σk B[r][k]·M[c][k]
  t' = t_bind + (Tx, Ty, Tz)   (Transform +0x60/+0x64/+0x68). 머리카락 +0x338 이 켜져 있고 뼈가 +0x348/+0x34a 의 뼈면
       t' = t_bind + (Ty, Tz, Tx)
사용: PY web/tools/r6_gfx_char_hairarrange_emu.py → analysis/completion/r6/gfx_char_hairarrange_emu.json
"""
import json
import math
import random
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_X0, UC_ARM64_REG_X1,
                                 UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_S0)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC, PLT_LO, PLT_HI  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = 0x71026df700
FAKE = 0x40000000


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def fb(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


class HUC(GUC):
    def _plt(self, mu, addr, size, user):
        w0 = struct.unpack_from("<I", self._raw, addr - 0x7100000000)[0]
        if (w0 & 0x9F000000) == 0x90000000:
            w1 = struct.unpack_from("<I", self._raw, addr + 4 - 0x7100000000)[0]
            immlo = (w0 >> 29) & 3
            immhi = (w0 >> 5) & 0x7FFFF
            page = ((immhi << 2) | immlo) << 12
            got = (addr & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
            name = self.got.get(got)
            if name in ("sinf", "cosf"):
                s = struct.unpack("<f", struct.pack("<I", mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
                r = f32(math.sin(s) if name == "sinf" else math.cos(s))
                mu.reg_write(UC_ARM64_REG_S0, fb(r))
                self.libm.append(name)
                mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
                return
        super()._plt(mu, addr, size, user)


def fma32(a, b, c):
    from fractions import Fraction
    return f32(float(Fraction(a) * Fraction(b) + Fraction(c)))


def rot_expect(B, ang):
    """0x71026e0b5c~0x71026e0c38 순서 그대로(f32, FMLA 융합)."""
    sx, sy, sz = (f32(math.sin(a)) for a in ang)
    cx, cy, cz = (f32(math.cos(a)) for a in ang)
    m = lambda a, b: f32(a * b)
    v4 = [m(cy, cz), f32(m(m(sx, sy), cz) - m(sz, cx)), f32(m(sx, sz) + m(sy, m(cx, cz)))]
    v6 = [m(sz, cy), f32(m(m(sx, sy), sz) + m(cx, cz)), f32(m(sy, m(sz, cx)) - m(sx, cz))]
    v7 = [-sy, m(sx, cy), m(cx, cy)]
    out = []
    for r in range(3):
        b0, b1, b2 = B[r][0], B[r][1], B[r][2]
        out.append([f32(fma32(v7[c], b2, fma32(v6[c], b1, m(v4[c], b0))) + 0.0) for c in range(3)])
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    u = HUC()
    u.libm = []
    m = u.mu
    m.mem_map(FAKE, 0x1000)
    m.mem_write(FAKE, struct.pack("<I", 0xD65F03C0) * 0x400)
    vt = u.alloc(0x200)
    for off in range(0, 0x200, 8):
        u.wq(vt + off, FAKE + off)
    bone_names = ["Hair_1_L", "ScalerA", "ScalerB", "Knot_1", "Front_1"]
    st = {"bind": {}, "set": [], "a0": []}

    def hk(mu, addr, size, d):
        off = addr - FAKE
        x1, x2, x3 = (mu.reg_read(r) for r in (UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3))
        ret = 0
        if off == 0x40:
            nm = u._cstr(u.rq(x1)).decode()
            ret = bone_names.index(nm) if nm in bone_names else 0xFFFFFFFF
        elif off == 0x68:
            idx = x3 & 0xFFFF
            Bm, Sc = st["bind"][idx]
            mu.mem_write(x1, struct.pack("<12f", *[Bm[r][c] for r in range(3) for c in range(4)]))
            mu.mem_write(x2, struct.pack("<3f", *Sc))
        elif off == 0x50:
            mat = struct.unpack("<12f", mu.mem_read(x1, 48))
            sc = struct.unpack("<3f", mu.mem_read(x2, 12))
            st["set"].append((x3 & 0xFFFFFFFF, mat, sc))
        elif off == 0xa0:
            st["a0"].append(x1 & 0xFFFF)
            ret = x1 & 0xFFFF
        else:
            st.setdefault("other", []).append(off)
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    m.hook_add(UC_HOOK_CODE, hk, begin=FAKE, end=FAKE + 0xFFF)
    rng = random.Random(6)
    ok = total = 0
    fails = []
    for case in range(60):
        hair = u.alloc(0x400)
        res = u.alloc(0x200)
        arr = u.alloc(0x80)
        lst = arr + 0x30
        actor = u.alloc(0x300)
        model = u.alloc(0x80)
        pp = u.alloc(0x10)
        qq = u.alloc(0x10)
        kobj = u.alloc(0x10)
        u.wq(kobj, vt)
        u.wq(qq, kobj)
        u.wq(pp, qq)
        u.wq(hair + 0x350, res)
        u.wq(res + 0x158, arr)
        m.mem_write(arr + 0x5c, b"\x01\x01")
        u.wq(hair + 0x10, actor)
        u.wq(actor + 0x208, 0)
        u.u32(hair + 0x11c, 7)
        u.wq(hair + 0x3a0, model)
        u.u32(model + 0x38, 1)
        u.wq(model + 0x40, pp)
        pool = [u.alloc(0xa0) for _ in range(8)]
        for a, b in zip(pool, pool[1:] + [0]):
            u.wq(a, b)
        u.wq(hair + 0x318, 0)
        u.wq(hair + 800, pool[0])
        u.u32(hair + 0x330, 0)
        u.u32(hair + 0x334, 8)
        flag338 = case % 3 == 2
        m.mem_write(hair + 0x338, bytes([1 if flag338 else 0]))
        n = rng.randint(1, 4)
        elems = u.alloc(8 * n)
        u.u32(lst + 8, n)
        u.wq(lst + 0x10, elems)
        u.wq(lst + 0x18, 0)
        params = []
        st["bind"] = {}
        names = rng.sample(bone_names, n)
        for i, nm in enumerate(names):
            e = u.alloc(0x80)
            u.wq(elems + 8 * i, e)
            m.mem_write(e + 0x6c, b"\x01" * 5)
            u.wq(e + 0x30, u.cstr(nm))
            ang = [f32(rng.uniform(-3.2, 3.2)) for _ in range(3)]
            scl = [f32(rng.choice([rng.uniform(0.3, 2.0), 0.0, 0.01, -1.0])) for _ in range(3)]
            trn = [f32(rng.uniform(-0.2, 0.2)) for _ in range(3)]
            rt = f32(rng.uniform(0, 1))
            m.mem_write(e + 0x38, struct.pack("<f", rt))
            m.mem_write(e + 0x48, struct.pack("<3f", *ang))
            m.mem_write(e + 0x54, struct.pack("<3f", *scl))
            m.mem_write(e + 0x60, struct.pack("<3f", *trn))
            bi = bone_names.index(nm)
            q = [rng.uniform(-1, 1) for _ in range(4)]
            ql = math.sqrt(sum(v * v for v in q))
            w, x, y, z = (v / ql for v in q)
            R = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                 [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                 [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
            Bm = [[f32(R[r][0]), f32(R[r][1]), f32(R[r][2]), f32(rng.uniform(-0.3, 0.3))] for r in range(3)]
            Sc = [f32(rng.uniform(0.5, 1.5)) for _ in range(3)]
            st["bind"][bi] = (Bm, Sc)
            params.append((bi, ang, scl, trn, Bm, Sc))
        root_bi = params[0][0]
        if flag338:
            m.mem_write(hair + 0x348, struct.pack("<HH", 0, root_bi))
            st["a0ret"] = root_bi
        st["set"] = []
        st["a0"] = []
        u.call(F, hair)
        got = st["set"]
        good = len(got) == len(params)
        if good:
            for (bi, ang, scl, trn, Bm, Sc), (gidx, mat, sc) in zip(params, got):
                es = [f32(Sc[k] * f32(scl[k] if scl[k] > 0.01 else 0.01)) for k in range(3)]
                rr = rot_expect(Bm, ang)
                t = trn
                if flag338 and bi == root_bi:
                    t = [trn[1], trn[2], trn[0]]
                exp = []
                for r in range(3):
                    exp += [rr[r][0], rr[r][1], rr[r][2], f32(f32(Bm[r][3] + 0.0) + t[r])]
                g_ok = gidx == bi and all(fb(a) == fb(b) for a, b in zip(mat, exp)) and \
                    all(fb(a) == fb(b) for a, b in zip(sc, es))
                if not g_ok:
                    good = False
                    if len(fails) < 4:
                        fails.append({"case": case, "bone": bi, "got": [gidx, mat, sc], "exp": [exp, es]})
        else:
            if len(fails) < 4:
                fails.append({"case": case, "n_set": len(got), "n_param": n})
        total += 1
        ok += good
    out = {"function": hex(F), "cases": total, "matches": ok, "fail_examples": fails,
           "compare": "회전·평행이동·스케일 모두 f32 비트 일치(회전은 FMLA 융합 순서 재현)",
           "stubs": ["머리카락 모델 뼈 vt+0x40/+0x68/+0x50/+0xa0: 파이썬 훅(이름→번호, 합성 바인드 공급, 설정 기록)",
                     "PLT sinf/cosf: 파이썬 math 를 f32 반올림(SDK libm 아님)",
                     "액터+0x208 = 0 으로 애니 가중(+0xa4 = AnimReduceRt) 경로 미실행",
                     "BoneParam 부모 상속 사슬(+0x6c~+0x70 플래그 0)은 모두 1 로 두어 미실행"],
           "libm_calls": len(u.libm), "plt_stubbed": sorted(set(u.plt_stubbed)), "other_vcalls": sorted(set(st.get("other", [])))}
    p = ROOT / "analysis/completion/r6/gfx_char_hairarrange_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cases", "matches", "libm_calls", "plt_stubbed", "other_vcalls")}, ensure_ascii=False))
    for f in fails[:2]:
        print(f)
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
