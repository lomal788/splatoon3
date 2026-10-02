"""[gauge] 스페셜 게이지·칠 결과 계산을 원본 명령으로 실행(unicorn)하고 재구현과 비교한다.

원본 함수/명령 구간을 합성 메모리 상태로 실행한다. 스텁 없음(호출 없는 구간만 실행).
  A. PaintPermille 계산 0x710303bd80 (함수 전체, 호출 없음)
  B. 게이지 누적 구간 0x7102488d68 ~ 0x7102488e1c (0x7102483134 안)
  C. 비율 계산 구간 0x71024855e0 ~ 0x7102485618 (0x7102483134 안)
  D. 필요 텍셀 구간 0x7102485508 ~ 0x7102485524
  E. 넷 상태 % 구간 0x71024876e4 ~ 0x7102487714
  F. 스페셜 사용 중 비율 구간 0x71024854d8 ~ (0x7102485844 | 0x7102485508)
사용: PY web/tools/gauge_emu.py   → analysis/gauge/gauge_emu_out.txt 에도 저장
"""
import math
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK = 0x10000000
HEAP = 0x20000000
CODE = 0x30000000
RULE_GLOBAL = 0x71058367F8  # *0x7105796510 가 가리키는 규칙(심판) 싱글턴 포인터 변수


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def rnd_half_away(x):
    x = f32(x)
    return int(f32(x + (0.5 if x >= 0 else -0.5)))


class Emu:
    def __init__(self):
        img = IMG.read_bytes()
        self.mu = mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x400000)
        mu.mem_map(CODE, 0x1000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        # 규칙 객체 vt+0x48 스텁: s0 = [x0+8]; ret
        mu.mem_write(CODE, struct.pack("<II", 0xBD400800, 0xD65F03C0))
        mu.mem_write(CODE + 0x100, struct.pack("<I", 0xD65F03C0))  # 복귀용 ret

    def w(self, a, fmt, *v):
        self.mu.mem_write(a, struct.pack(fmt, *v))

    def r(self, a, fmt):
        return struct.unpack(fmt, self.mu.mem_read(a, struct.calcsize(fmt)))

    def clear(self):
        self.mu.mem_write(HEAP, b"\0" * 0x400000)
        self.w(RULE_GLOBAL, "<Q", 0)

    def run(self, start, until, regs=None, sregs=None, count=20000):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
        mu.reg_write(UC_ARM64_REG_X30, CODE + 0x100)
        for k, v in (regs or {}).items():
            mu.reg_write(getattr(sys.modules[__name__], f"UC_ARM64_REG_{k.upper()}"), v)
        for k, v in (sregs or {}).items():
            mu.reg_write(getattr(sys.modules[__name__], f"UC_ARM64_REG_{k.upper()}"),
                         struct.unpack("<I", struct.pack("<f", v))[0])
        stops = until if isinstance(until, (list, tuple)) else [until]
        hit = []

        def hook(m, addr, size, user):
            if addr in stops:
                hit.append(addr)
                m.emu_stop()
        from unicorn import UC_HOOK_CODE
        h = mu.hook_add(UC_HOOK_CODE, hook)
        mu.emu_start(start, CODE + 0x100, count=count)
        mu.hook_del(h)
        return hit[0] if hit else None

    def sreg(self, n):
        v = self.mu.reg_read(getattr(sys.modules[__name__], f"UC_ARM64_REG_S{n}"))
        return struct.unpack("<f", struct.pack("<I", v & 0xFFFFFFFF))[0]

    def wreg(self, n):
        return self.mu.reg_read(getattr(sys.modules[__name__], f"UC_ARM64_REG_W{n}")) & 0xFFFFFFFF


# ---------------- 재구현 ----------------
def re_permille(pts, d):
    """pts = [Alpha, Bravo, Charlie] PaintPoint, d = PaintPtMax. 반환 [(pt, permille)]*3"""
    D = f32(max(f32(float(d)), 1.0))
    r = [f32(f32(float(p)) / D) for p in pts]
    order = sorted(range(3), key=lambda i: -r[i])  # 같은 값의 순서는 원본 정렬 규칙 미확정
    a, b = order[0], order[1]
    if rnd_half_away(f32(r[a] * 1000.0)) == rnd_half_away(f32(r[b] * 1000.0)):
        r[a] = f32(float(rnd_half_away(f32(r[a] * 1000.0)) + 1) / 1000.0)
    return [(rnd_half_away(f32(D * r[i])), rnd_half_away(f32(r[i] * 1000.0))) for i in range(3)]


def re_gauge_add(frac, texels, rate, auto, ten, extra, g4):
    acc = f32(frac + f32(rate * f32(float(texels))))
    acc = f32(acc + auto)
    acc = f32(f32(acc + ten) + extra)
    n = int(acc)                      # fcvtzs (0 방향 절삭)
    if acc < 0 and acc != n:          # 음수 비정수면 -1 → floor
        n -= 1
    return f32(acc - f32(float(n))), (g4 + (n & 0xFFFFFFFF)) & 0xFFFFFFFF


def re_full(req):
    return int(f32(req * f32(211.2)))


def re_ratio(g4, full):
    if full < 1:
        return 1.0
    q = f32(f32(float(g4)) / f32(float(full)))
    return 0.0 if q < 0 else min(q, 1.0)


def re_net_pct(ratio):
    if ratio >= 1.0:
        return 100
    v = f32(ratio * 100.0)
    u = 0 if v <= 0 or v != v else int(v)
    return min(u, 99)


def main():
    E = Emu()
    out = []
    rng = random.Random(1)
    G = HEAP + 0x1000          # 게이지 구조체 (본체+0xbd4)
    PP = HEAP + 0x3000         # PlayerParam
    BODY = G - 0xBD4

    # A. PaintPermille
    n_ok = n_all = 0
    cases = [([100, 100, 0], 1000), ([333, 333, 0], 1000), ([0, 0, 0], 0), ([1, 0, 0], 1),
             ([12345, 12000, 0], 30000), ([500, 499, 0], 1000), ([2, 1, 1], 3)]
    for _ in range(300):
        d = rng.randint(1, 40000)
        a = rng.randint(0, d)
        b = rng.randint(0, d - a)
        cases.append(([a, b, rng.choice([0, 0, rng.randint(0, d - a - b)])], d))
    for pts, d in cases:
        E.clear()
        obj = HEAP + 0x10000
        ring = HEAP + 0x20000
        E.w(obj + 0x128, "<Q", ring)
        E.w(ring + 0x10D0, "<Q", ring + 0x2000)
        E.w(ring + 0x10D8, "<iii", 3, 0, 3)
        for i, p in enumerate(pts):
            E.w(ring + 0x2000 + i * 0x80 + 0x70, "<ii", p, 0)
        darg = HEAP + 0x30000
        E.w(darg, "<i", d)
        E.run(0x710303BD80, CODE + 0x100, regs={"x0": obj, "x1": darg})
        got = [E.r(ring + 0x2000 + i * 0x80 + 0x70, "<ii") for i in range(3)]
        exp = re_permille(pts, d)
        n_all += 1
        same = [tuple(g) for g in got] == exp
        n_ok += same
        if not same or (pts, d) in cases[:7]:
            out.append(f"A permille pts={pts} D={d} -> 원본 {got} 재구현 {exp} {'OK' if same else 'DIFF'}")
    out.append(f"A 요약: {n_ok}/{n_all} 일치")

    # B. 게이지 누적
    n_ok = n_all = 0
    for k in range(400):
        E.clear()
        frac = f32(rng.random() * 0.999)
        tex = rng.choice([0, 1, 7, 64, 211, 1000, rng.randint(0, 5000)])
        rate = f32(rng.choice([1.0, 1.15, 1.3, rng.uniform(1.0, 1.3)]))
        ten = f32(rng.choice([0.0, 0.0, 2 / 60 * 211.2 * rng.choice([1, 2, 3])]))
        extra = f32(rng.choice([0.0, 0.0, rng.uniform(0, 5)]))
        auto = f32(rng.choice([0.0, rng.uniform(0, 3)])) if k % 2 else 0.0
        g4 = rng.randint(0, 50000)
        E.w(G + 4, "<Ifff", g4, frac, extra, 0.0)
        E.w(PP + 0xE8, "<f", rate)
        E.w(PP + 0x17C, "<f", ten)
        if auto:
            rule = HEAP + 0x40000
            vt = HEAP + 0x41000
            E.w(RULE_GLOBAL, "<Q", rule)
            E.w(rule, "<Q", vt)
            E.w(rule + 8, "<f", auto)
            E.w(vt + 0x48, "<Q", CODE)
            pobj = HEAP + 0x42000
            E.w(BODY + 8, "<Q", pobj)
            E.w(pobj + 0x668, "<i", 0)
        E.run(0x7102488D68, 0x7102488E1C, regs={"x24": PP, "x21": G, "x22": BODY, "w23": tex})
        g4o, fro = E.r(G + 4, "<If")
        fre, g4e = re_gauge_add(frac, tex, rate, auto, ten, extra, g4)
        n_all += 1
        same = (g4o == g4e and struct.pack("<f", fro) == struct.pack("<f", fre))
        n_ok += same
        if not same or k < 4:
            out.append(f"B add tex={tex} rate={rate:.6g} auto={auto:.6g} ten={ten:.6g} extra={extra:.6g} frac={frac:.6g} g4={g4}"
                       f" -> 원본 (G+4 {g4o}, G+8 {fro:.9g}) 재구현 ({g4e}, {fre:.9g}) {'OK' if same else 'DIFF'}")
    out.append(f"B 요약: {n_ok}/{n_all} 일치")

    # C. 비율, D. 필요 텍셀
    n_ok = n_all = 0
    for req in (180.0, 190.0, 200.0, 0.0, 0.001):
        E.clear()
        E.w(BODY + 0xBE8, "<f", req)
        E.run(0x7102485508, 0x7102485524, regs={"x22": BODY, "x21": G})
        full = E.wreg(8)
        exp = re_full(req)
        n_all += 1
        n_ok += full == exp
        out.append(f"D full req={req} -> 원본 {full} 재구현 {exp}")
        for g4 in (0, 1, full // 2, full - 1, full, full + 999, 0xFFFFFFFF):
            if full < 0:
                continue
            E.w(G + 4, "<I", g4 & 0xFFFFFFFF)
            E.run(0x71024855E0, 0x7102485618, regs={"x21": G, "w8": full})
            got = E.r(G + 0x10, "<f")[0]
            exp = f32(re_ratio(g4, full))
            n_all += 1
            n_ok += struct.pack("<f", got) == struct.pack("<f", exp)
            if struct.pack("<f", got) != struct.pack("<f", exp) or g4 in (full // 2, full):
                out.append(f"C ratio G+4={g4} full={full} -> 원본 {got:.9g} 재구현 {exp:.9g}")
    out.append(f"C/D 요약: {n_ok}/{n_all} 일치")

    # E. 넷 %
    n_ok = n_all = 0
    for ratio in [0.0, 0.004, 0.005, 0.0099, 0.01, 0.5, 0.989, 0.99, 0.995, 0.9999, 1.0, 1.5, -0.1] + [rng.random() for _ in range(200)]:
        E.clear()
        ratio = f32(ratio)
        E.w(BODY + 0xBE4, "<f", ratio)
        E.run(0x71024876E4, 0x7102487714, regs={"x28": BODY})
        got = E.wreg(9)
        exp = re_net_pct(ratio)
        n_all += 1
        n_ok += got == exp
        if got != exp or n_all <= 13:
            out.append(f"E net% ratio={ratio:.6g} -> 원본 {got} 재구현 {exp}")
    out.append(f"E 요약: {n_ok}/{n_all} 일치")

    # F. 스페셜 사용 중 비율(G+0x1c 남은, G+0x20 전체)
    for rem, tot in ((300, 600), (600, 600), (1, 600), (700, 600), (5, 0), (5, -1), (-3, -1)):
        E.clear()
        E.w(G + 0x1C, "<ii", rem, tot)
        stop = E.run(0x71024854D8, [0x7102485844, 0x7102485508], regs={"x21": G, "x22": BODY})
        out.append(f"F active rem={rem} tot={tot} -> 원본 s1={E.sreg(1):.6g} (정지 {hex(stop) if stop else None})")

    txt = "\n".join(out)
    print(txt)
    (ROOT / "analysis" / "gauge").mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis" / "gauge" / "gauge_emu_out.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
