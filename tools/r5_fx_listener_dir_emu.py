"""r5 fx: Alto 리스너 지향성 거리 배율(음원별 기록 +0x90) 원본 실행 대조.

0x710384922c(P = listener+0x68, pos) 와 그 안의 원뿔 각 0x71038612b0 을 그대로 실행하고, 독립 재구현과 비트 비교한다.
  P+0x08 u8   사용(IsUseDirectivity)          P+0x24/+0x34/+0x44  지향 행렬 위치(listener+0x8c/+0x9c/+0xac)
  P+0x48..50  지향 축(listener+0xb0..b8)        P+0x54/+0x58/+0x5c  inner/outer 각(rad)·차
  P+0x60/+0x64/+0x68 inner/outer 반경·차        P+0x6c/+0x70/+0x74  inner/outer DistRate·차
스텁: atan2f(PLT 0x7103e9c1e0) 한 개만 파이썬 f32 atan2 로 대체(libm). 그 밖 외부 호출 없음.
"""
import json, math, random, struct
from pathlib import Path
from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_LR, UC_ARM64_REG_PC
from unicorn import UC_HOOK_CODE
from network_uc import UC

ROOT = Path(__file__).resolve().parents[2]
f = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
ATAN2F = 0x7103e9c1e0


def rs(mu, r):
    return struct.unpack('<f', struct.pack('<I', mu.reg_read(r) & 0xffffffff))[0]


def ws(mu, r, v):
    mu.reg_write(r, struct.unpack('<I', struct.pack('<f', v))[0])


def cone(axis, inner, outer, diff, rel):
    if axis == [0.0, 0.0, 0.0] or rel == [0.0, 0.0, 0.0]:
        a = 0.0
    else:
        ax, ay, az = axis; x, y, z = rel
        c0 = f(f(z * ay) - f(y * az)); c1 = f(f(x * az) - f(ax * z)); c2 = f(f(ax * y) - f(x * ay))
        s = f(f(f(c0 * c0) + f(c1 * c1)) + f(c2 * c2))
        cr = f(math.sqrt(s))
        dot = f(f(f(ax * x) + f(y * ay)) + f(z * az))
        a = f(math.atan2(cr, dot))
    if a <= inner: return 0.0
    if a <= outer: return f(f(a - inner) / diff)
    return 1.0


def expect(P, pos):
    if not P['on']: return 1.0
    rel = [f(pos[i] - P['L'][i]) for i in range(3)]
    if rel == [0.0, 0.0, 0.0]: return P['rin']
    s = f(f(f(rel[0] * rel[0]) + f(rel[1] * rel[1])) + f(rel[2] * rel[2]))
    r = f(math.sqrt(s))
    if not (P['Rin'] < r): return P['rin']
    if r <= P['Rout']:
        t = f(f(r - P['Rin']) / P['Rd'])
        if t == 0.0: return P['rin']
    else:
        t = 1.0
    a = cone(P['axis'], P['ain'], P['aout'], P['ad'], rel)
    if a == 0.0: return P['rin']
    if a <= t: t = a
    if t == 1.0: return P['rout']
    return f(P['rin'] + f(t * P['rd']))


def main():
    u = UC(); m = u.mu
    def hook(mu, addr, size, ud):
        y = rs(mu, UC_ARM64_REG_S0); x = rs(mu, UC_ARM64_REG_S1)
        ws(mu, UC_ARM64_REG_S0, f(math.atan2(y, x)))
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    m.hook_add(UC_HOOK_CODE, hook, begin=ATAN2F, end=ATAN2F)
    rng = random.Random(0x710384922c)
    P_ = u.alloc(0x100); pos_ = u.alloc(0x10)
    n = 0; hist = {}
    for k in range(2048):
        ain = f(math.radians(40)); aout = f(math.radians(90))
        Rin, Rout = f(3.0), f(6.0)
        rin, rout = f(1.0), f(2.5)
        if k % 2:
            ain = f(rng.uniform(0, 1.5)); aout = f(rng.uniform(float(ain), 3.1)); Rin = f(rng.uniform(0, 5)); Rout = f(rng.uniform(float(Rin) + 0.01, 12))
            rin = f(rng.uniform(0.5, 2)); rout = f(rng.uniform(0.5, 4))
        yaw = rng.uniform(-math.pi, math.pi)
        axis = [f(math.sin(yaw)), f(0.0), f(math.cos(yaw))]
        L = [f(rng.uniform(-50, 50)) for _ in range(3)]
        P = {'on': k % 17 != 0, 'L': L, 'axis': axis, 'ain': ain, 'aout': aout, 'ad': f(aout - ain), 'Rin': Rin, 'Rout': Rout,
             'Rd': f(Rout - Rin), 'rin': rin, 'rout': rout, 'rd': f(rout - rin)}
        d = rng.choice([0.0, 1.0, 2.9, 3.0, 4.5, 6.0, 7.0, rng.uniform(0, 15)])
        dirv = [rng.uniform(-1, 1) for _ in range(3)]; l = math.sqrt(sum(x * x for x in dirv)) or 1
        pos = [f(L[i] + dirv[i] / l * d) for i in range(3)]
        m.mem_write(P_, b'\0' * 0x100)
        m.mem_write(P_ + 8, bytes([1 if P['on'] else 0]))
        u.f32(P_ + 0x24, L[0]); u.f32(P_ + 0x34, L[1]); u.f32(P_ + 0x44, L[2])
        m.mem_write(P_ + 0x48, struct.pack('<3f', *axis))
        m.mem_write(P_ + 0x54, struct.pack('<9f', ain, aout, P['ad'], Rin, Rout, P['Rd'], rin, rout, P['rd']))
        m.mem_write(pos_, struct.pack('<3f', *pos))
        u.call(0x710384922c, P_, pos_)
        got = rs(m, UC_ARM64_REG_S0)
        exp = expect(P, pos)
        assert struct.pack('<f', got) == struct.pack('<f', exp), (k, got, exp, P, pos)
        key = 'in' if got == rin else ('out' if got == rout else 'mid'); hist[key] = hist.get(key, 0) + 1
        n += 1
    out = {'bit_matches': n, 'cases': hist, 'stubs': ['atan2f PLT 0x7103e9c1e0 -> python f32(atan2)'],
           'functions': ['0x710384922c', '0x71038612b0'],
           'limits': ['지향 행렬(listener+0x80..) 공급 경로(게임 0x7103147020 / 0x710383b534)는 실행 안 함',
                      '호출 조건(0x7103863ab4: 감쇠 세트 존재 && (음원 플래그 bit5 || 세트+0x90))은 판독만']}
    (ROOT / 'analysis/completion/r5').mkdir(parents=True, exist_ok=True)
    (ROOT / 'analysis/completion/r5/fx_listener_dir_emu.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
