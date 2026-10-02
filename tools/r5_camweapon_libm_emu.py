"""r5 camweapon: 카메라·조준 식이 쓰는 bias 곡선 bias(u, b) = ±expf(logf(|u|) * (logf(b) * -1.442695))를
원본 SDK libm(extracted/exefs/sdk.img, r5_player_libm_emu.Sdk 재사용)으로 실행해 웹 근사(Math.log/exp 배정밀 → f32)와 비트 대조한다.

명령 순서(원본 asm 0x7102583b54~0x7102583b80, 흔들림): t = f32(logf(b) * K), K = 0xbfb8aa3b(-1.442695);
e = f32(logf(|u|) * t); p = expf(e); u < 0 이면 -p. 스틱 응답(0x71024e0fd4~0x71024e1004)도 같은 순서.
입력 범위(실제로 쓰는 값):
  - 흔들림: u = 2r-1, r = sead getF32 격자(u32>>9 | 0x3f800000) - 1. b = max(서기 누적 bias, 점프 bias) — 스플래시슈터
    Stand Min .01 / Kf .01 / Max .25 / Decrease .015 로 40단계 안에 도달하는 f32 값(BFS), 점프 bias = Min + t(.4 - Min), t = min(cnt/45, 1).
    최종 각 ang = f32(rad * u'), rad = f32(swerve * 0.017453292).
  - 스틱 응답 b = 0.8(자이로 꺼짐)·0.4(켜짐), 피치 기울기 b = 0.45(t, t+0.001), 자이로 억제 b = 0.2.
스텁: 없음(SDK 함수 단독 실행). main PLT 0x7103e9c2a0(logf)/0x7103e9be20(expf) ↔ SDK 심볼 연결은 이름 기준.
결과: analysis/completion/r5/camweapon_libm_emu.json
"""
import json, math, random, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import Sdk, bits  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
K = np.frombuffer(struct.pack('<I', 0xbfb8aa3b), F)[0]


def f(b):
    return np.frombuffer(struct.pack('<I', b), F)[0]


def sdk_bias(s, u, b, cache):
    if b not in cache:
        cache[b] = F(f(s.call('logf', b)) * K)
    t = cache[b]
    e = F(f(s.call('logf', F(abs(u)))) * t)
    p = f(s.call('expf', e))
    return F(-p) if u < 0 else p


def web_bias(u, b):
    t = F(F(math.log(float(b))) * K)
    e = F(F(math.log(abs(float(u)))) * t)
    p = F(math.exp(float(e)))
    return F(-p) if u < 0 else p


def reachable_bias():
    mn, kf, mx, dec = F(0.01), F(0.01), F(0.25), F(0.015)
    seen = {F(0.0), mn}
    frontier = list(seen)
    depth = 0
    while frontier and depth < 40:          # 연속 40번 발사/감쇠까지(도달 값이 반올림 경로로 계속 늘어 상한을 둠)
        depth += 1
        nxt = []
        for v in frontier:
            for w in (F(min(F(v + kf), mx)), F(max(F(v - dec), mn)), F(max(v, mn))):
                if w not in seen:
                    seen.add(w); nxt.append(w)
        frontier = nxt
    return sorted(seen)


def main():
    s = Sdk()
    rng = random.Random(71025839)
    cache = {}
    stand = reachable_bias()
    jump = sorted({F(F(0.01) + F(F(min(F(c) / F(45), F(1))) * F(F(0.4) - F(0.01)))) for c in range(1, 71)})
    bvals = sorted(set(stand) | set(jump))   # b = max(서기, 점프) 는 두 집합 중 하나의 값
    bvals = [b for b in bvals if b >= F(0.001) and abs(float(b) - 0.5) > 0.001]
    res = {'bias_values': len(bvals)}
    # 흔들림
    n = mis = amis = 0; ex = []; maxulp = 0
    rads = [F(F(x) * F(0.017453292)) for x in (6.0, 12.0, 9.0)]
    for i in range(30000):
        r = F(f(0x3f800000 | (rng.getrandbits(32) >> 9)) - F(1))
        u = F(F(r + r) + F(-1))
        if abs(float(u)) < 0.001 or abs(float(u)) >= 1:
            continue
        b = bvals[i % len(bvals)]
        a, w = sdk_bias(s, u, b, cache), web_bias(u, b)
        n += 1
        if bits(a) != bits(w):
            mis += 1
            ul = abs(int(bits(abs(a))) - int(bits(abs(w))))
            maxulp = max(maxulp, ul)
            if len(ex) < 10: ex.append(dict(u=float(u), b=float(b), sdk=hex(bits(a)), web=hex(bits(w)), ulp=ul))
        rad = rads[i % 3]
        if bits(F(rad * a)) != bits(F(rad * w)):
            amis += 1
    res['swerve'] = dict(cases=n, bias_mismatch=mis, max_ulp=maxulp, angle_mismatch=amis, examples=ex)
    print('swerve', res['swerve']['cases'], 'bias mismatch', mis, 'max ulp', maxulp, 'angle mismatch', amis)
    # 스틱·피치·자이로
    for name, b, gen in [('stick_0.8', F(0.8), lambda: F(rng.uniform(0.0011, 1.0))),
                         ('stick_gyro_0.4', F(0.4), lambda: F(rng.uniform(0.0011, 1.0))),
                         ('pitch_slope_0.45', F(0.45), lambda: F(rng.uniform(0.0011, 1.001))),
                         ('gyro_suppress_0.2', F(0.2), lambda: F(rng.uniform(0.0011, 1.0)))]:
        n = mis = 0; maxulp = 0; ex = []
        for _ in range(10000):
            u = gen()
            a, w = sdk_bias(s, u, b, cache), web_bias(u, b)
            n += 1
            if bits(a) != bits(w):
                mis += 1
                ul = abs(int(bits(a)) - int(bits(w))); maxulp = max(maxulp, ul)
                if len(ex) < 5: ex.append(dict(u=float(u), sdk=hex(bits(a)), web=hex(bits(w)), ulp=ul))
        res[name] = dict(cases=n, mismatch=mis, max_ulp=maxulp, examples=ex)
        print(name, n, 'mismatch', mis, 'max ulp', maxulp)
    res['logf_b'] = {f'{float(b):.9g}': dict(sdk=hex(bits(f(s.call('logf', b)))), web=hex(bits(F(math.log(float(b))))))
                     for b in [F(0.8), F(0.4), F(0.45), F(0.2)] + bvals[:5]}
    res['sdk_offsets'] = {k: hex(s.sym[k][0]) for k in ('logf', 'expf')}
    res['stubs'] = '없음(SDK 함수 단독 실행)'
    p = ROOT / 'analysis/completion/r5/camweapon_libm_emu.json'
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
