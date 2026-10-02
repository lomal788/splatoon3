"""r5 player: 이동 코드가 부르는 SDK 수학 함수(powf/logf/expf/cosf)를 원본 SDK 모듈로 실행해
웹 근사(Math.pow/log/exp/cos 배정밀 → f32 반올림)와 비트 대조한다.

- 원본: extracted/exefs/sdk.img(SDK NSO 해제본). 동적 심볼표(MOD0 → DT_SYMTAB/DT_STRTAB)에서 함수 위치를 찾는다.
  main 의 PLT(0x7103e9c2a0 logf 등)가 가리키는 대상이 이 심볼이라는 연결은 이름 기준이다.
- 스텁 없음: 각 함수는 SDK 안에서 끝난다(분기 대상이 SDK 범위를 벗어나면 실패로 기록).
- 입력: 이동 코드가 실제로 쓰는 범위 — powf(len, 4.0)(입력 크기 m, 0x710245b2b4), b(x,s) 곡선의
  logf(|x|)·logf(s)·expf(·) (가속·기어, 0x710245b2b4/기어 함수), cosf(60·0.017453292)(롤 판정).
결과: analysis/completion/r5_player_libm_emu.json
"""
import json, math, random, struct
from pathlib import Path
import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UcError
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / 'extracted/exefs/sdk.img'
BASE = 0x7400000000
STACK = 0x10000000
END = 0x30000000
F = np.float32


def symbols(d):
    mod0 = struct.unpack_from('<I', d, 4)[0]
    dyn = mod0 + struct.unpack_from('<i', d, mod0 + 4)[0]
    tags = {}
    i = dyn
    while True:
        t, v = struct.unpack_from('<qQ', d, i); i += 16
        if t == 0:
            break
        tags.setdefault(t, v)
    symtab, strtab = tags[6], tags[5]
    out = {}
    for k in range((strtab - symtab) // 24):
        no, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', d, symtab + k * 24)
        nm = d[strtab + no:d.index(b'\0', strtab + no)].decode()
        if value:
            out[nm] = (value, size)
    return out


class Sdk:
    def __init__(self):
        d = SDK.read_bytes()
        self.sym = symbols(d)
        self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        size = (len(d) + 0xFFFF) & ~0xFFFF
        self.mu.mem_map(BASE, size); self.mu.mem_write(BASE, d)
        self.size = size
        self.mu.mem_map(STACK, 0x100000)
        self.mu.mem_map(END, 0x1000); self.mu.mem_write(END, struct.pack('<I', 0xD65F03C0))
        self.mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)

    def call(self, name, *fargs):
        addr = BASE + self.sym[name][0]
        for r, v in zip((UC_ARM64_REG_S0, UC_ARM64_REG_S1), fargs):
            self.mu.reg_write(r, struct.unpack('<I', struct.pack('<f', float(v)))[0])
        self.mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        self.mu.reg_write(UC_ARM64_REG_LR, END)
        self.mu.emu_start(addr, END, count=100000)
        return self.mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff


def bits(x):
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]


def web(name, *a):
    a = [float(F(x)) for x in a]
    try:
        v = {'powf': lambda x, y: math.pow(x, y), 'logf': math.log, 'expf': math.exp, 'cosf': math.cos}[name](*a)
    except (ValueError, OverflowError):
        return None
    return bits(F(v))


def main():
    s = Sdk()
    rng = random.Random(20261003)
    res = {}
    plans = {
        'powf': [(F(rng.uniform(0, 1.5)), F(4.0)) for _ in range(20000)] + [(F(x), F(4.0)) for x in (0, 1e-6, 0.1, 0.5, 0.9999999, 1, 1.4142135)],
        'logf': [(F(rng.uniform(1e-3, 1)),) for _ in range(20000)] + [(F(x),) for x in (0.8, 0.5, 0.4, 0.001, 0.999, 1.0, 0.70710677)],
        'expf': [(F(rng.uniform(-12, 0)),) for _ in range(20000)] + [(F(x),) for x in (0, -1, -0.5, -6.9077554)],
        'cosf': [(F(F(60) * F(0.017453292)),)] + [(F(rng.uniform(0, 3.1415927)),) for _ in range(5000)],
    }
    for name, inputs in plans.items():
        mis = []; n = 0
        for a in inputs:
            got = s.call(name, *a)
            w = web(name, *a)
            n += 1
            if got != w:
                gi = struct.unpack('<i', struct.pack('<I', got))[0]; wi = struct.unpack('<i', struct.pack('<I', w))[0] if w is not None else 0
                mis.append(dict(args=[float(x) for x in a], sdk=hex(got), web=None if w is None else hex(w), ulp=abs(gi - wi)))
        res[name] = dict(sdk_offset=hex(s.sym[name][0]), cases=n, mismatches=len(mis), max_ulp=max([m['ulp'] for m in mis], default=0), examples=mis[:20])
        print(name, 'cases', n, 'mismatch', len(mis), 'max ulp', res[name]['max_ulp'])
    # 가속·기어 곡선 b(x, s) = expf(logf(|x|) * (logf(s) * -1.442695)) 전체: SDK 연결 vs 웹 근사
    K = np.frombuffer(struct.pack('<I', 0xbfb8aa3b), F)[0]
    mis = 0; n = 0; ex = []
    for sv in (F(0.8), F(0.4), F(0.7), F(0.6), F(0.5) + F(0.002)):
        ls_sdk = np.frombuffer(struct.pack('<I', s.call('logf', sv)), F)[0]
        ls_web = F(math.log(float(sv)))
        for _ in range(4000):
            x = F(rng.uniform(0.001, 1))
            lx = np.frombuffer(struct.pack('<I', s.call('logf', x)), F)[0]
            got = s.call('expf', F(lx * F(ls_sdk * K)))
            w = bits(F(math.exp(float(F(F(math.log(float(x))) * F(ls_web * K))))))
            n += 1
            if got != w:
                mis += 1
                if len(ex) < 10:
                    ex.append(dict(s=float(sv), x=float(x), sdk=hex(got), web=hex(w)))
    res['curve_b'] = dict(cases=n, mismatches=mis, examples=ex)
    print('curve b cases', n, 'mismatch', mis)
    # 기어 표(gear_skills.md §4.3) 전 행 × AP 0..57: logf/expf 를 SDK 로 바꾼 gear_lerp 와 파이썬 math 판의 대조
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import player_gear as pg
    rows = [(0.096, 0.12, 0.144), (0.088, 0.116, 0.144), (0.104, 0.124, 0.144), (1.0, 1.125, 1.25),
            (0.192, 0.216, 0.24), (0.1728, 0.216, 0.24), (0.2016, 0.2208, 0.24),
            (0.08, 0.098, 0.11), (0.024, 0.05568, 0.0768), (0.012, 0.033, 0.042), (0.5, 0.75, 1.0),
            (0.003, 0.00225, 0.0015), (0.4, 0.3, 0.2), (0.0, 26.0, 39.0), (0.85, 0.925, 1.0)]
    sdk_log = lambda v: float(np.frombuffer(struct.pack('<I', s.call('logf', F(v))), F)[0])
    sdk_exp = lambda v: float(np.frombuffer(struct.pack('<I', s.call('expf', F(v))), F)[0])
    gm = 0; gn = 0; gex = []
    for low, mid, high in rows:
        for ap in range(58):
            for ninja in (False, True):
                rate = pg.ap_to_rate(ap, ninja)
                a = pg.gear_lerp(low, mid, high, rate)
                ml, me = pg.math.log, pg.math.exp
                pg.math.log, pg.math.exp = sdk_log, sdk_exp
                try:
                    b = pg.gear_lerp(low, mid, high, rate)
                finally:
                    pg.math.log, pg.math.exp = ml, me
                gn += 1
                if bits(a) != bits(b):
                    gm += 1
                    if len(gex) < 10:
                        gex.append(dict(row=[low, mid, high], ap=ap, ninja=ninja, python=hex(bits(a)), sdk=hex(bits(b))))
    res['gear_table'] = dict(cases=gn, mismatches=gm, examples=gex)
    print('gear table cases', gn, 'mismatch', gm)
    res['stubs'] = '없음(SDK 함수 단독 실행). main PLT ↔ SDK 심볼 연결은 이름 기준'
    (ROOT / 'analysis/completion/r5_player_libm_emu.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
