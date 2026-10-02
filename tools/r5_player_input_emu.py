"""r5 player: 이동 입력 구조체(본체+0x474) 원본 실행 대조.

A. 스틱 기록·데드존 재매핑 구간(입력 함수 0x710249f494 안 명령 구간 0x71024a0850 ~ 0x71024a0940)
   본체+0x474/+0x478 = 스틱, +0x47c = 데드존 재매핑 크기, +0x480 = 내려갈 때만 0.2 비율로 따라가는 크기.
   구간 실행: x28 = 합성 본체, s3/s2 = 스틱 x/y. NaN(sqrtf) 분기와 구간 뒤 호출은 실행하지 않는다.
B. 0x71024a7100(입력 구조체, 바닥 법선 N=본체+0x180, 입력 구조체, 전방 축 D=본체+0xd40, 카메라 기저 Y=[PlayerCamera+0x68]+0xc)
   → 구조체 +0x10(본체+0x484), +0x14(본체+0x488 = 벽 미끄럼 계수의 x) 전체 함수 실행. 스텁 없음(순수 계산).
bss 상수는 정적 초기화 에뮬 결과 analysis/player/bss_consts_58bb000.json 값을 써 넣는다.
결과: analysis/completion/r5_player_input_emu.json
"""
import json, random, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC
from unicorn.arm64_const import UC_ARM64_REG_X28, UC_ARM64_REG_S2, UC_ARM64_REG_S3, UC_ARM64_REG_SP

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
C = json.loads((ROOT / 'analysis/player/bss_consts_58bb000.json').read_text(encoding='utf-8'))


def cf(addr):
    return np.frombuffer(struct.pack('<I', C[hex(addr)]['u32']), F)[0]


DZ = cf(0x71058bbbe4)        # 0.1
FALL = cf(0x71058bbcd0)      # 0.2
FLOOR = cf(0x71058bbb60)     # 0.64144969
DECAY = cf(0x71058bbcd8)     # 0.03
LO = cf(0x71058bbcdc)        # 0.35
HI = cf(0x71058bbce0)        # 0.2


def bits(x):
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]


def fb(u):
    return np.frombuffer(struct.pack('<I', u), F)[0]


def deadzone(sx, sy, prev480):
    sx, sy = F(sx), F(sy)
    ln = F(np.sqrt(F(F(sy * sy) + F(sx * sx))))
    one = F(1)
    assert DZ <= one  # DZ > 1 분기(0x71024a0894~)는 상수 0.1 에서 도달 불가
    if True:
        if ln <= DZ:
            m = F(0)
        elif ln >= one:
            m = one
        else:
            d = F(one - DZ)
            m = F(0) if d == 0 else F(F(ln - DZ) / d)
    p = F(prev480)
    n480 = F(p + F(F(m - p) * FALL)) if p > m else m
    return m, n480


def sign1(v):
    return F(1) if v >= 0 else F(-1)


def wall_input(prev10, prev14, n, d, c, sx, sy):
    nx, ny, nz = map(F, n); dx, dy, dz = map(F, d); cx, cy, cz = map(F, c); sx, sy = F(sx), F(sy)
    one = F(1); half = F(0.5); mhalf = F(-0.5); zero = F(0)
    ax_ = abs(sx); sgx = sign1(sx)
    wx = F(F(ny * dz) - F(nz * dy))
    wy = F(F(nz * dx) - F(dz * nx))
    wz = F(F(dy * nx) - F(ny * dx))
    e = F(F(F(wx * cx) + F(wy * cy)) + F(wz * cz))
    f = F(F(F(dx * cx) + F(dy * cy)) + F(dz * cz))
    ay_ = abs(sy); ae = abs(e); sge = sign1(e); af = abs(f)
    if not (ny < FLOOR):
        o10 = F(prev10 + F(-1)); o10 = zero if o10 <= 0 else o10
        o14 = F(prev14 - DECAY); o14 = zero if o14 <= 0 else o14
        return o10, o14
    w = min(F(one - ny), one)
    a = F(F(F(sgx * half) * sge) + half)
    t1 = F(w * F(ax_ * F(F(ae * a) + mhalf)))
    sgf = sign1(f)
    s16 = sgf if sy >= 0 else F(-sgf)
    t2 = F(w * F(ay_ * F(F(af * F(half - s16)) + mhalf)))
    s20 = F(t1 + t2)
    o10 = F(-1) if s20 < F(-1) else min(s20, one)
    if f < 0:
        g = af
    else:
        if LO >= 0:
            if ae <= 0:
                r = zero
            elif LO <= ae:
                r = one
            elif LO == 0:
                r = zero
            else:
                r = F(ae / LO)
        else:
            raise AssertionError('LO<0 경로는 상수상 도달 불가')
        k = F(HI + F(F(one - HI) * r))
        if k >= 0:
            if af <= 0:
                g = zero
            elif k <= af:
                g = one
            elif k == 0:
                g = zero
            else:
                g = F(af / k)
        else:
            raise AssertionError('k<0 경로는 상수상 도달 불가')
    p = F(F(max(F(sge * F(-sgx)), zero) + mhalf))
    s2 = F(ax_ * F(F(ae * p) + half))
    q = F(F(F(max(s16, zero) + mhalf) * g) + half)
    s1 = F(s2 + F(ay_ * q))
    o14 = zero if s1 < 0 else min(s1, one)
    return o10, o14


def run_a(e, body, rng):
    for k in (0x71058bbbe4, 0x71058bbcd0):
        e.u32(k, C[hex(k)]['u32'])
    rows = []; mis = 0
    sticks = [(0, 0), (0.1, 0), (0.0999, 0), (0.1001, 0), (1, 0), (0.6, 0.8), (0.70710677, 0.70710677), (-1, 0), (0.05, 0.05)]
    sticks += [(F(rng.uniform(-1, 1)), F(rng.uniform(-1, 1))) for _ in range(3000)]
    prev = F(0)
    for sx, sy in sticks:
        prev = F(rng.choice([0.0, 0.3, 1.0, float(prev)]))
        e.mu.mem_write(body, b'\0' * 0x1000)
        e.f32(body + 0x480, float(prev))
        e.mu.reg_write(UC_ARM64_REG_X28, body)
        e.mu.reg_write(UC_ARM64_REG_S3, bits(sx)); e.mu.reg_write(UC_ARM64_REG_S2, bits(sy))
        e.mu.reg_write(UC_ARM64_REG_SP, 0x10000000 + 0xF0000)
        e.mu.emu_start(0x71024a0850, 0x71024a0940, count=200)
        got = [e.ru32(body + o) for o in (0x474, 0x478, 0x47c, 0x480)]
        m, n480 = deadzone(sx, sy, prev)
        exp = [bits(sx), bits(sy), bits(m), bits(n480)]
        if got != exp:
            mis += 1
        if len(rows) < 200:
            rows.append(dict(stick=[float(sx), float(sy)], prev480=float(prev), got=[hex(x) for x in got], expected=[hex(x) for x in exp]))
    return dict(range='0x71024a0850..0x71024a0940', cases=len(sticks), mismatches=mis, deadzone=float(DZ), fall_rate=float(FALL), rows_head=rows)


def run_b(e, rng):
    for k in (0x71058bbb60, 0x71058bbcd8, 0x71058bbcdc, 0x71058bbce0):
        e.u32(k, C[hex(k)]['u32'])
    st = e.alloc(0x40); pn = e.alloc(16); pd = e.alloc(16); pc = e.alloc(16)
    unit = lambda: (lambda v: [F(x / np.linalg.norm(v)) for x in v])(np.array([rng.gauss(0, 1) for _ in range(3)]))
    rows = []; mis = 0; cases = 0; onwall = 0
    for i in range(6000):
        if i % 5 == 0:
            n = [F(0), F(1), F(0)]
        elif i % 5 == 1:
            yy = F(rng.uniform(-0.3, 0.64))
            h = float(np.sqrt(max(0.0, 1 - float(yy) ** 2))); ang = rng.uniform(0, 6.283)
            n = [F(h * np.cos(ang)), yy, F(h * np.sin(ang))]
        else:
            n = unit()
        d = unit(); c = unit()
        if i % 7 == 0:
            c = [F(0), F(1), F(0)]
        sx = F(rng.uniform(-1, 1)); sy = F(rng.uniform(-1, 1))
        if i % 11 == 0:
            sx = F(0)
        if i % 13 == 0:
            sy = F(0)
        p10 = F(rng.uniform(-1, 1.5)); p14 = F(rng.uniform(0, 1))
        e.mu.mem_write(st, struct.pack('<6f', float(sx), float(sy), 0, 0, float(p10), float(p14)))
        e.mu.mem_write(pn, struct.pack('<3f', *map(float, n)))
        e.mu.mem_write(pd, struct.pack('<3f', *map(float, d)))
        e.mu.mem_write(pc, struct.pack('<3f', *map(float, c)))
        e.call(0x71024a7100, st, pn, st, pd, pc)
        got = [e.ru32(st + 0x10), e.ru32(st + 0x14)]
        o10, o14 = wall_input(p10, p14, n, d, c, sx, sy)
        exp = [bits(o10), bits(o14)]
        cases += 1; onwall += n[1] < FLOOR
        if got != exp:
            mis += 1
            if mis < 5:
                print('B mismatch', n, d, c, sx, sy, [hex(x) for x in got], [hex(x) for x in exp])
        if len(rows) < 300:
            rows.append(dict(n=[float(x) for x in n], d=[float(x) for x in d], c=[float(x) for x in c], stick=[float(sx), float(sy)], prev=[float(p10), float(p14)], got=[hex(x) for x in got], expected=[hex(x) for x in exp]))
    return dict(function='0x71024a7100', cases=cases, wall_cases=int(onwall), mismatches=mis,
                consts=dict(floor=float(FLOOR), decay=float(DECAY), lo=float(LO), hi=float(HI)), rows_head=rows)


def main():
    e = UC(); body = e.alloc(0x1000)
    rng = random.Random(20261003)
    a = run_a(e, body, rng)
    b = run_b(e, rng)
    res = dict(stubs='없음(A는 명령 구간 실행, NaN sqrtf 분기 미도달; B는 순수 함수)', deadzone_range=a, wall_input=b)
    (ROOT / 'analysis/completion/r5_player_input_emu.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('A deadzone', a['cases'], 'mismatch', a['mismatches'])
    print('B 0x71024a7100', b['cases'], 'wall', b['wall_cases'], 'mismatch', b['mismatches'])


if __name__ == '__main__':
    main()
