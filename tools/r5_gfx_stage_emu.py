"""r5 gfx_stage: 원본 함수를 unicorn 으로 실행해 독립 재구현(판독식)과 비트 대조한다.

대상(모두 외부 호출 없는 리프이거나 리프만 부름 — 스텁 없음):
  A 0x7101033b78  방향광(dir,color,n) → SH 7×vec4(cAr..cC) 투영
  B 0x7101033dc0  SH 7×vec4 를 방향으로 평가(max 0)  — 반환 s0
  C 0x71010325d4  (x0=리드백 객체, x8=결과) 리드백 텍스처 7장(RGBA32F 0x2e / RGBA16F 0x2b) → SH 7×vec4 + 유효 플래그 (0x7101034608 텍셀 읽기 포함)
  D 0x710112215c  HDRCompose 변형 번호 선택(블룸·색보정·톤매핑·감마·비네트 매크로)
  E 0x7103744058  HDRCompose 플래그(+0x48 bit0 블룸, bit1 색보정, bit2 감마) · +0x1c 블룸 합성 종류 기록
사용: PY web/tools/r5_gfx_stage_emu.py [건수=2000] → analysis/completion/r5/gfx_stage_emu.json
재구현은 디컴파일 텍스트를 따라 numpy float32 연산 순서로 따로 짠 것이다(원본 바이트를 읽지 않는다).
"""
import json
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK = 0x10000000
HEAP = 0x20000000
RET = 0x30000000
f32 = np.float32


class Emu:
    def __init__(self):
        img = IMG.read_bytes()
        self.mu = mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x400000)
        mu.mem_map(RET, 0x1000)
        mu.mem_write(RET, struct.pack("<I", 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.hp = HEAP

    def reset_heap(self):
        self.hp = HEAP
        self.mu.mem_write(HEAP, b"\0" * 0x400000)

    def alloc(self, n):
        a = self.hp
        self.hp += (n + 0xF) & ~0xF
        return a

    def w(self, a, fmt, *v):
        self.mu.mem_write(a, struct.pack("<" + fmt, *v))

    def r(self, a, fmt):
        return struct.unpack("<" + fmt, bytes(self.mu.mem_read(a, struct.calcsize("<" + fmt))))

    def call(self, fn, x=(), s=(), x8=None):
        mu = self.mu
        if x8 is not None:
            mu.reg_write(UC_ARM64_REG_X8, x8)
        for i, v in enumerate(x):
            mu.reg_write(UC_ARM64_REG_X0 + i, v)
        for i, v in enumerate(s):
            mu.reg_write(UC_ARM64_REG_Q0 + i, struct.unpack("<I", struct.pack("<f", v))[0])
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(fn, RET, count=200000)
        return mu


def fbits(v):
    return struct.unpack("<I", struct.pack("<f", float(v)))[0]


# ---------- 재구현 (디컴파일 판독식) ----------
def re_dirlight_sh(d, c, n):
    """0x7101033b78 판독식. 연산 순서는 디스어셈블 순서(fmul 결합)를 따른다."""
    d0, d1, d2 = f32(d[0]), f32(d[1]), f32(d[2])
    c0, c1, c2 = f32(c[0]), f32(c[1]), f32(c[2])
    k = f32(12.566371) / f32(n)
    a1 = k * f32(0.488603)
    s14 = a1 * d2; s13 = a1 * d1; s10 = a1 * d0
    s12 = (k * f32(0.546274)) * (d0 * d0 - d1 * d1)
    s11 = (k * f32(0.315392)) * (d2 * (d2 * f32(3.0)) + f32(-1.0))
    s9 = k * f32(0.282095)
    b = k * f32(1.092548)
    s7 = b * d1
    s6 = s7 * d2
    s7b = d0 * s7
    s3 = d0 * (b * d2)          # 정정: 디컴파일 표기 ((d0*k)*1.092548)*d2 와 달리 실제 결합은 d0*((k*1.092548)*d2)
    o = [f32(0)] * 28
    K1, K0, K2, K3, K4 = f32(0.32534343), f32(0.28175688), f32(0.07875311), f32(0.27280876), f32(0.23625931)
    K5 = f32(0.13640438)
    for ch, cc in enumerate((c0, c1, c2)):
        base = ch * 4
        o[base + 0] = (s10 * cc) * K1
        o[base + 1] = (s13 * cc) * K1
        o[base + 2] = (s14 * cc) * K1
        o[base + 3] = (s9 * cc) * K0 - (cc * s11) * K2
        o[12 + base + 0] = (cc * s7b) * K3
        o[12 + base + 1] = (cc * s6) * K3
        o[12 + base + 2] = (cc * s11) * K4
        o[12 + base + 3] = (cc * s3) * K3
    o[24] = (c0 * s12) * K5
    o[25] = (c1 * s12) * K5
    o[26] = (s12 * c2) * K5
    o[27] = f32(1.0)
    return o


def re_sh_eval(d, sh):
    """0x7101033dc0: R,G,B 세 채널 평가 후 fmaxnm(·,0), 4번째 반환 1.0.
    채널 c: L=(x*A0+y*A1)+z*A2; L=A3+L; Q=((xy*B0+yz*B1)+zz*B2)+xz*B3; v=(L+Q)+(xx-yy)*C (디스어셈블 결합 순서)."""
    x, y, z = f32(d[0]), f32(d[1]), f32(d[2])
    p = [f32(v) for v in sh]
    xx, yy, zz = x * x, y * y, z * z
    xy, yz, xz = x * y, y * z, x * z
    q = xx - yy
    out = []
    for c in range(3):
        a = p[4 * c:4 * c + 4]; b = p[12 + 4 * c:16 + 4 * c]
        L = a[3] + ((x * a[0] + y * a[1]) + z * a[2])
        Q = ((xy * b[0] + yz * b[1]) + zz * b[2]) + xz * b[3]
        v = (L + Q) + q * p[24 + c]
        out.append(v if v > f32(0.0) else f32(0.0))
    return out


def half_to_f32_flush(h):
    """0x7101034608 의 half→float: 지수 0(비정규·0)은 부호 있는 0, 지수 31 은 inf/nan."""
    sgn = (h & 0x8000) << 16
    e = h & 0x7C00
    if e == 0:
        return sgn
    if e == 0x7C00:
        return sgn | (h << 13) | 0x7F800000
    return sgn | ((h & 0x3FF) << 13) | (0x38000000 + (e << 13))


def f32_flush(u):
    e = u & 0x7F800000
    if e == 0:
        return u & 0x80000000
    if e == 0x7F800000:
        return u | 0x7F800000
    return u


def re_readback_sh(tex):
    """0x71010325d4 판독식: tex[i] = (x,y,z,w) 7개 → cAr..cC."""
    t = [[f32(v) for v in tx] for tx in tex]
    K1, K0, K2, K3, K4, K5 = (f32(0.32534343), f32(0.28175688), f32(0.07875311), f32(0.27280876),
                              f32(0.23625931), f32(0.13640438))
    o = [f32(0)] * 28
    o[0] = t[2][1] * K1; o[1] = t[0][3] * K1; o[4] = t[2][2] * K1; o[5] = t[1][0] * K1
    o[8] = t[2][3] * K1; o[9] = t[1][1] * K1; o[2] = t[1][2] * K1
    o[3] = t[0][0] * K0 - t[4][2] * K2
    o[6] = t[1][3] * K1
    o[7] = t[0][1] * K0 - t[4][3] * K2
    o[10] = t[2][0] * K1
    o[11] = t[0][2] * K0 - t[5][0] * K2
    o[12] = t[3][0] * K3; o[13] = t[3][3] * K3; o[14] = t[4][2] * K4; o[15] = t[5][1] * K3
    o[20] = t[3][2] * K3; o[21] = t[4][1] * K3; o[16] = t[3][1] * K3; o[17] = t[4][0] * K3
    o[18] = t[4][3] * K4; o[19] = t[5][2] * K3; o[22] = t[5][0] * K4; o[23] = t[5][3] * K3  # 정정: 디컴파일은 tex6.w 로 보이나 디스어셈블(0x710103281c s11)은 tex5.w
    o[27] = f32(1.0)
    o[24] = t[6][0] * K5; o[25] = t[6][1] * K5; o[26] = t[6][2] * K5
    return o


MACRO_COUNTS = [3, 2, 6, 3, 3]          # BLOOM, CC, TONEMAP, GAMMA, VIGNETTE (sharc 순서)
STRIDES = [108, 54, 9, 3, 1]


def re_variant(bloom_tex, cc_tex, flags, tone, bloom_mode, vig_en, vig_shape):
    """0x710112215c 판독식 → 매크로 값 → 혼합 기수 번호."""
    bloom = (1 + bloom_mode) if (bloom_tex and (flags & 1)) else 0
    cc = 1 if (cc_tex and (flags >> 1) & 1) else 0
    if (flags >> 7) & 1:
        gamma = 2
    elif (flags >> 2) & 1:
        gamma = 1
    else:
        gamma = 0
    vig = 0
    if vig_en:
        if vig_shape == 1:
            vig = 2
        elif vig_shape == 0:
            vig = 1
    vals = [bloom, cc, tone, gamma, vig]
    return sum(v * s for v, s in zip(vals, STRIDES)) & 0xFFFFFFFF, vals


def re_flags(cfg, p288, cc_obj, bloom_obj, p280, gamma_arg, old48, old1c):
    """0x7103744058 판독식(HDR 객체 쪽 결과만)."""
    hb8, hd0, h850 = cfg['8b0'], cfg['8d0'], cfg['850']
    if (not hb8) or (p288 & 1):
        return old48, old1c
    def bloom_bit():
        if bloom_obj is None:
            return 0
        if bloom_obj['7d8'] == 0 or bloom_obj['8'] == 0 or ((bloom_obj['438'] - 1) & 0xFFFFFFFF) > 1:
            return 0
        return p280 & 1
    if cc_obj is None or not hd0:
        u5 = 0
        u4 = bloom_bit() if h850 else 0
    elif cc_obj['218'] == 0:
        u5 = 0
        u4 = bloom_bit() if h850 else 0
    else:
        u5 = (cc_obj['2410'] >> 3) & 2
        u4 = bloom_bit() if h850 else 0
    f = (old48 & 0xFFFFFFFD) | u5
    f = (f & 0xFFFFFFFE) | u4
    n1c = old1c
    if u4:
        n1c = 1 if bloom_obj['438'] == 2 else 0
    f = (f & 0xFFFFFFF3) | (4 if gamma_arg & 1 else 0)
    return f, n1c


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    rnd = random.Random(20261003)
    E = Emu()
    res = {}

    # A
    bad = []
    for i in range(N):
        E.reset_heap()
        d = [rnd.uniform(-1, 1) for _ in range(3)]
        c = [rnd.uniform(0, 20) for _ in range(3)]
        n = rnd.choice([1, 1, 2, 3, 7])
        out, dp, cp = E.alloc(0x80), E.alloc(16), E.alloc(16)
        E.w(dp, "3f", *d); E.w(cp, "3f", *c)
        E.call(0x7101033B78, x=(out, dp, cp, n))
        got = E.r(out, "28I")
        exp = [fbits(v) for v in re_dirlight_sh([f32(v) for v in d], [f32(v) for v in c], n)]
        if list(got) != exp:
            bad.append({"i": i, "idx": [k for k in range(28) if got[k] != exp[k]][:6]})
    res["A_dirlight_sh_0x7101033b78"] = {"cases": N, "mismatch": len(bad), "first": bad[:3]}

    # B
    bad = []
    for i in range(N):
        E.reset_heap()
        d = [rnd.uniform(-1, 1) for _ in range(3)]
        sh = [rnd.uniform(-2, 2) for _ in range(28)]
        dp, sp = E.alloc(16), E.alloc(0x80)
        E.w(dp, "3f", *d); E.w(sp, "28f", *sh)
        mu = E.call(0x7101033DC0, x=(dp, sp))
        got = [mu.reg_read(UC_ARM64_REG_Q0 + k) & 0xFFFFFFFF for k in range(4)]
        exp = [fbits(v) for v in re_sh_eval([f32(v) for v in d], [f32(v) for v in sh])] + [fbits(1.0)]
        if got != exp:
            bad.append({"i": i, "got": [hex(g) for g in got], "exp": [hex(e) for e in exp]})
    res["B_sh_eval_0x7101033dc0"] = {"cases": N, "mismatch": len(bad), "first": bad[:3]}

    # C
    bad = []
    for i in range(N):
        E.reset_heap()
        fmt = rnd.choice([0x2E, 0x2B, 0x2E, 0x1D])
        obj = E.alloc(0xD00)
        E.w(obj + 2000, "H", fmt)
        tex = []
        for t in range(7):
            rec = obj + 0x720 + 8 + t * 0xB0
            l1, l2, data = E.alloc(0x20), E.alloc(0x110), E.alloc(0x40)
            E.w(rec, "I", 0x10); E.w(rec + 0x10, "Q", l1); E.w(l1 + 0x18, "Q", l2); E.w(l2 + 0x100, "Q", data)
            E.w(rec + 0xA8, "H", fmt)
            if fmt == 0x2B:
                hs = [rnd.choice([rnd.getrandbits(16) & 0x7BFF | (rnd.getrandbits(1) << 15), rnd.getrandbits(16)]) for _ in range(4)]
                E.w(data + 0x10, "4H", *hs)
                tex.append([struct.unpack("<f", struct.pack("<I", half_to_f32_flush(h)))[0] for h in hs])
            else:
                us = [rnd.choice([fbits(rnd.uniform(-5, 5)), rnd.getrandbits(32) & 0x807FFFFF, rnd.getrandbits(32)]) for _ in range(4)]
                E.w(data + 0x10, "4I", *us)
                tex.append([struct.unpack("<f", struct.pack("<I", f32_flush(u)))[0] for u in us])
        out = E.alloc(0x80)
        E.w(out, "29I", *([0xDEADBEEF] * 29))
        E.call(0x71010325D4, x=(obj,), x8=out)  # 원본: 결과 구조체는 x8(간접 결과), 객체는 x0
        got = list(E.r(out, "28I")); flag = E.r(out + 0x70, "B")[0]
        if fmt in (0x2B, 0x2E):
            exp = [fbits(v) for v in re_readback_sh(tex)]
            ok = (flag == 1) and all(g == e or ((g & 0x7F800000) == 0x7F800000 and (g & 0x7FFFFF) and (e & 0x7F800000) == 0x7F800000 and (e & 0x7FFFFF)) for g, e in zip(got, exp))
        else:
            ok = flag == 0 and all(g == 0 for g in got)
        if not ok:
            bad.append({"i": i, "fmt": fmt, "idx": [k for k in range(28) if got[k] != (exp[k] if fmt in (0x2B, 0x2E) else 0)][:6]})
    res["C_readback_sh_0x71010325d4"] = {"cases": N, "mismatch": len(bad), "first": bad[:3],
                                          "note": "NaN 은 비트 대신 NaN 여부로 비교(곱셈 NaN 전파 페이로드는 비교 제외)"}

    # D
    bad = []
    prog_tbl_ptr = 0x71058161A0
    for i in range(N):
        E.reset_heap()
        macros = E.alloc(0x28 * 5)
        for k in range(5):
            E.w(macros + 0x28 * k + 0x20, "H", STRIDES[k])
        info = E.alloc(0x40); E.w(info + 0x28, "I", 5); E.w(info + 0x30, "Q", macros)
        prog = E.alloc(0x20); E.w(prog + 8, "Q", info)
        arr = E.alloc(0x40); E.w(arr + 8 * 3, "Q", prog)
        cont = E.alloc(0x30); E.w(cont + 0x18, "I", 8); E.w(cont + 0x20, "Q", arr)
        E.w(prog_tbl_ptr, "Q", cont); E.w(0x7105562838, "I", 3)
        hdr = E.alloc(0x60)
        flags = rnd.getrandbits(8); tone = rnd.randrange(6); bm = rnd.randrange(2)
        E.w(hdr + 0x18, "i", tone); E.w(hdr + 0x1C, "i", bm); E.w(hdr + 0x48, "I", flags)
        env = E.alloc(0x2B00); E.w(env + 0x2AE0, "Q", hdr)
        bt, ct = rnd.randrange(2), rnd.randrange(2)
        args = E.alloc(0x80); E.w(args + 0x38, "Q", bt * 0x1234); E.w(args + 0x40, "Q", ct * 0x5678); E.w(args + 0x58, "Q", env)
        vig = E.alloc(0x40); ve, vs = rnd.randrange(2), rnd.choice([0, 1, 2])
        E.w(vig + 8, "B", ve); E.w(vig + 0x34, "i", vs)
        mu = E.call(0x710112215C, x=(vig, 0, args))
        got = mu.reg_read(UC_ARM64_REG_X0) & 0xFFFFFFFF
        exp, vals = re_variant(bt, ct, flags, tone, bm, ve, vs)
        if got != exp:
            bad.append({"i": i, "got": got, "exp": exp, "vals": vals, "flags": flags})
    res["D_hdr_variant_0x710112215c"] = {"cases": N, "mismatch": len(bad), "first": bad[:3]}

    # E
    bad = []
    for i in range(N):
        E.reset_heap()
        envp = E.alloc(0x300)
        cfgp = E.alloc(0x900)
        cfg = {'8b0': rnd.randrange(2), '8d0': rnd.randrange(2), '850': rnd.randrange(2)}
        E.w(cfgp + 0x8B0, "B", cfg['8b0']); E.w(cfgp + 0x8D0, "B", cfg['8d0']); E.w(cfgp + 0x850, "B", cfg['850'])
        E.w(cfgp + 0x890, "B", 0)
        E.w(envp + 8, "Q", cfgp)
        p288 = rnd.randrange(4); E.w(envp + 0x288, "B", p288)
        p280 = rnd.randrange(4); E.w(envp + 0x280, "B", p280)
        cc_obj = None
        if rnd.randrange(3):
            cc_obj = {'218': rnd.randrange(2), '2410': rnd.getrandbits(8)}
            cp = E.alloc(0x2420); E.w(cp + 0x218, "B", cc_obj['218']); E.w(cp + 0x2410, "I", cc_obj['2410'])
            E.w(envp + 0x2B0, "Q", cp)
        bloom_obj = None
        if rnd.randrange(3):
            bloom_obj = {'7d8': rnd.randrange(2), '8': rnd.randrange(3), '438': rnd.randrange(5)}
            bp = E.alloc(0x7E0); E.w(bp + 0x7D8, "B", bloom_obj['7d8']); E.w(bp + 8, "i", bloom_obj['8'])
            E.w(bp + 0x438, "i", bloom_obj['438'])
            E.w(envp + 0x290, "Q", bp)
        hp = E.alloc(0x60); old48 = rnd.getrandbits(32); old1c = rnd.randrange(7)
        E.w(hp + 0x48, "I", old48); E.w(hp + 0x1C, "i", old1c)
        E.w(envp + 0x2B8, "Q", hp)
        ga = rnd.getrandbits(32)
        E.call(0x7103744058, x=(envp, 0, ga))
        g48 = E.r(hp + 0x48, "I")[0]; g1c = E.r(hp + 0x1C, "i")[0]
        e48, e1c = re_flags(cfg, p288, cc_obj, bloom_obj, p280, ga, old48, old1c)
        if (g48, g1c) != (e48, e1c):
            bad.append({"i": i, "got": [hex(g48), g1c], "exp": [hex(e48), e1c]})
    res["E_hdr_flags_0x7103744058"] = {"cases": N, "mismatch": len(bad), "first": bad[:3],
                                        "note": "자동노출 배열(+0x2a8)은 0(없음)으로 두어 뒤쪽 프레임 버퍼 교대 루프는 실행 안 함"}

    out = ROOT / "analysis" / "completion" / "r5" / "gfx_stage_emu.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in res.items():
        print(k, v["cases"], "mismatch", v["mismatch"], v["first"][:1])


if __name__ == "__main__":
    main()
