"""r5 player: 방향 보간 0x7101252ff0(+ acos 0x7101252780) 원본 실행 대조.

원본 함수를 unicorn으로 실행하고, 명령 판독으로 따로 짠 f32 재구현 두 가지와 비교한다.
  A. 표 재구현: sead 사인 표(0x7104aa5b5c, 16 B × 257)·아탄 표(0x7104aa6b6c, 8 B × 129)를
     이미지에서 읽어 원본 명령 순서대로 계산 (기대: 원본과 비트 일치)
  B. 웹 근사: Math.acos/Math.sin 에 해당하는 libm 배정밀 계산 + 연산마다 f32 반올림
     (impl/physics.md §2.2 의 현재 근사, 불일치 건수만 기록)
스텁 없음: 두 함수는 순수 계산이다. sqrtf PLT(0x7103e9bb50)는 NaN 입력에서만 불리며 이번 입력에는 NaN 이 없다.
결과: analysis/completion/r5_player_lerpdir_emu.json
"""
import json, math, random, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC
from xref import load_img, BASE
from unicorn.arm64_const import UC_ARM64_REG_S0

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
IMG = load_img()


def rd(a, fmt):
    n = struct.calcsize(fmt)
    return struct.unpack(fmt, bytes(IMG[a - BASE:a - BASE + n]))


SIN = [rd(0x7104aa5b5c + i * 16, '<4f') for i in range(257)]
ATAN = [rd(0x7104aa6b6c + i * 8, '<If') for i in range(129)]
K = np.frombuffer(struct.pack('<I', 0x4e22f983), F)[0]
HALF_PI = np.frombuffer(struct.pack('<I', 0x3fc90fdb), F)[0]
IDX2RAD = np.frombuffer(struct.pack('<I', 0x30c90fdb), F)[0]
EPS_HI = np.frombuffer(struct.pack('<I', 0x3f7fffef), F)[0]
EPS_LO = np.frombuffer(struct.pack('<I', 0xbf7fffef), F)[0]
R2 = np.frombuffer(struct.pack('<I', 0x3f3504f3), F)[0]
TWO_M24 = np.frombuffer(struct.pack('<I', 0x33800000), F)[0]


def bits(x):
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]


def fcvtzu32(x):
    x = float(x)
    if x != x or x <= 0:
        return 0
    return min(int(x), 0xffffffff)


def fcvtzs64(x):
    return int(float(x))


def ucvtf(w):
    return F(w & 0xffffffff)


def atan_lookup(r128_exact_int, r128_f):
    base, slope = ATAN[r128_exact_int]
    frac = F(r128_f - F(r128_exact_int))
    return (base + fcvtzu32(F(frac * F(slope)))) & 0xffffffff


def acos_tbl(x):
    x = F(x)
    one = F(1)
    if x < F(-1):
        a = 0x80000000
    elif x > one:
        a = 0
    elif x >= 0:
        s = F(np.sqrt(F(one - F(x * x))))
        if x > R2:
            r = F(s / x)
            a = atan_lookup(int(float(r) * 128), F(r * F(128)))
        else:
            r = F(x / s)
            a = (0x40000000 - atan_lookup(int(float(r) * 128), F(r * F(128)))) & 0xffffffff
    else:
        s = F(np.sqrt(F(one - F(x * x))))
        if x < -R2:
            r = F(F(s / x) * F(-128))
            i = int(float(r))
            base, slope = ATAN[i]
            frac = F(r - F(i))
            a = (0x80000000 - ((base + fcvtzu32(F(F(slope) * frac))) & 0xffffffff)) & 0xffffffff
        else:
            r = F(F(-x) / s)
            i = int(float(r) * 128)
            r128 = F(r * F(128))
            base, slope = ATAN[i]
            frac = F(r128 - F(i))
            a = ((base + fcvtzu32(F(F(slope) * frac))) + 0x40000000) & 0xffffffff
    return F(ucvtf(a) * IDX2RAD)


def sin_lookup(v):
    x8 = fcvtzs64(v)
    idx = (x8 >> 24) & 0xff
    frac = ucvtf(x8 & 0xffffff)
    base, slope = SIN[idx][0], SIN[idx][1]
    return F(F(base) + F(F(F(slope) * frac) * TWO_M24))


def normalize(v):
    x, y, z = map(F, v)
    ln = F(np.sqrt(F(F(F(x * x) + F(y * y)) + F(z * z))))
    if ln > 0:
        inv = F(F(1) / ln)
        x, y, z = F(x * inv), F(y * inv), F(z * inv)
    if ln == 0:
        x = y = z = F(0)
    return ln, (x, y, z)


def lerp_dir(t, a, b, axis, web=False):
    t = F(t)
    if t <= 0:
        return tuple(map(F, a))
    if t >= 1:
        return tuple(map(F, b))
    la, (ax, ay, az) = normalize(a)
    lb, (bx, by, bz) = normalize(b)
    omt = F(F(1) - t)
    d = F(F(F(ax * bx) + F(ay * by)) + F(az * bz))
    w0, w1 = omt, t
    if d > EPS_HI:
        pass
    elif d >= EPS_LO:
        if web:
            th = F(math.acos(float(d)))
            st = F(math.sin(float(th)))
            w0 = F(F(math.sin(float(F(omt * th)))) / st)
            w1 = F(F(math.sin(float(F(th * t)))) / st)
        else:
            th = acos_tbl(d)
            st = sin_lookup(F(th * K))
            w0 = F(sin_lookup(F(F(omt * th) * K)) / st)
            w1 = F(sin_lookup(F(F(th * t) * K)) / st)
    elif axis is not None:
        cx, cy, cz = map(F, axis)
        px = F(F(az * cy) - F(ay * cz))
        py = F(F(ax * cz) - F(az * cx))
        pz = F(F(ay * cx) - F(ax * cy))
        ln = F(np.sqrt(F(F(F(px * px) + F(py * py)) + F(pz * pz))))
        if ln > 0:
            inv = F(F(1) / ln)
            px, py, pz = F(px * inv), F(inv * py), F(inv * pz)
        if ln != 0:
            if t > F(0.5):
                t = F(t + F(-0.5))
                ax, ay, az = px, py, pz
            else:
                bx, by, bz = px, py, pz
            t = F(t + t)
            omt = F(F(1) - t)
            if web:
                w0 = F(math.sin(float(F(omt * HALF_PI))))
                w1 = F(math.sin(float(F(t * HALF_PI))))
            else:
                w0 = sin_lookup(F(F(omt * HALF_PI) * K))
                w1 = sin_lookup(F(F(t * HALF_PI) * K))
    ln = F(F(la * omt) + F(lb * t))
    return (F(F(F(bx * w1) + F(ax * w0)) * ln), F(F(F(by * w1) + F(ay * w0)) * ln), F(F(F(bz * w1) + F(az * w0)) * ln))


def cases(rng):
    out = []
    unit = lambda: normalize([F(rng.gauss(0, 1)) for _ in range(3)])[1]
    for t in (0.0, 1.0, -0.5, 1.5, 0.5, 1e-7, 0.9999999):
        out.append((t, unit(), unit(), None))
    for _ in range(6000):
        a = [F(rng.uniform(-2, 2)) for _ in range(3)]
        b = [F(rng.uniform(-2, 2)) for _ in range(3)]
        out.append((F(rng.random()), a, b, None))
    for _ in range(3000):
        a = unit(); b = unit()
        out.append((F(rng.random()), a, b, None))
    for _ in range(1500):
        a = unit()
        jitter = [F(x + rng.gauss(0, 1e-3)) for x in a]
        out.append((F(rng.random()), a, jitter, None))
    for _ in range(1500):
        a = unit()
        opp = [F(-x + rng.gauss(0, 3e-4)) for x in a]
        out.append((F(rng.random()), a, opp, unit() if rng.random() < 0.8 else None))
    for _ in range(1000):
        out.append((F(rng.choice([0.003, 0.006, 0.5, 0.25, 0.75, 0.997])), unit(), unit(), None))
    for _ in range(300):
        a = unit()
        out.append((F(rng.random()), a, [F(-x) for x in a], unit()))
    for _ in range(200):
        out.append((F(rng.random()), [0, 0, 0], unit(), None))
        out.append((F(rng.random()), unit(), [0, 0, 0], None))
    return out


def main():
    e = UC()
    out = e.alloc(16); pa = e.alloc(16); pb = e.alloc(16); pc = e.alloc(16)
    rng = random.Random(20261003)
    rows = []; mis_tbl = 0; mis_web = 0; web_maxulp = 0
    acos_rows = 0; acos_mis = 0
    for x in [F(-1.5), F(-1), F(-0.9999), F(-0.7071068), F(-0.70710677), F(-0.5), F(-1e-8), F(0), F(1e-8), F(0.3), F(0.70710677), F(0.7071068), F(0.9999), F(1), F(1.5)] + [F(rng.uniform(-1, 1)) for _ in range(20000)]:
        e.call(0x7101252780, fargs=(float(x),))
        got = e.mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff
        exp = bits(acos_tbl(x)); acos_rows += 1
        if got != exp:
            acos_mis += 1
            if acos_mis < 5:
                print('acos mismatch', float(x), hex(got), hex(exp))
    for t, a, b, axis in cases(rng):
        e.mu.mem_write(pa, struct.pack('<3f', *map(float, a)))
        e.mu.mem_write(pb, struct.pack('<3f', *map(float, b)))
        if axis is not None:
            e.mu.mem_write(pc, struct.pack('<3f', *map(float, axis)))
        e.mu.mem_write(out, b'\0' * 12)
        e.call(0x7101252ff0, out, pa, pb, pc if axis is not None else 0, fargs=(float(t),))
        got = struct.unpack('<3I', bytes(e.mu.mem_read(out, 12)))
        tbl = tuple(bits(v) for v in lerp_dir(t, a, b, axis))
        web = tuple(bits(v) for v in lerp_dir(t, a, b, axis, web=True))
        ok = got == tbl
        mis_tbl += not ok
        if got != web:
            mis_web += 1
            for g, w in zip(got, web):
                gi = struct.unpack('<i', struct.pack('<I', g))[0]; wi = struct.unpack('<i', struct.pack('<I', w))[0]
                if (gi < 0) == (wi < 0):
                    web_maxulp = max(web_maxulp, abs(gi - wi))
        if not ok and mis_tbl < 5:
            print('table mismatch', float(t), a, b, axis, [hex(x) for x in got], [hex(x) for x in tbl])
        if len(rows) < 400:
            rows.append(dict(t=float(t), a=[float(x) for x in a], b=[float(x) for x in b], axis=None if axis is None else [float(x) for x in axis], got=[hex(x) for x in got], table=[hex(x) for x in tbl], web=[hex(x) for x in web]))
    n = len(cases(random.Random(20261003)))
    res = dict(
        functions={'0x7101252780': 'acos (sead 아탄 표, u32 각도 → ×2π/2^32)', '0x7101252ff0': '방향 slerp(크기는 선형)'},
        acos_cases=acos_rows, acos_mismatch_table=acos_mis,
        lerp_cases=n, lerp_mismatch_table=mis_tbl, lerp_mismatch_web_libm=mis_web, web_max_ulp=web_maxulp,
        stubs='없음(순수 함수, sqrtf PLT 는 NaN 에서만 호출, 이번 입력 미도달)',
        rows_head=rows)
    p = ROOT / 'analysis/completion/r5_player_lerpdir_emu.json'
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('acos', acos_rows, 'mismatch(table)', acos_mis)
    print('lerp', n, 'mismatch(table)', mis_tbl, 'mismatch(web libm)', mis_web, 'max ulp', web_maxulp)


if __name__ == '__main__':
    main()
