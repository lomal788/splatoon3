"""Alto 사운드 설정 판독: Attenuation 아카이브(.baatarc = SARC{baatn, baroc, baudc, baadr, baacl}).

필드 의미는 이 도구에서 정하지 않는다. 헤더(magic, BOM, version)와 본문을 u32/f32 로 나란히 보여 주고,
AATN 은 문자열 영역의 하위 커브 이름 참조를 풀어 준다.
사용:
  PY web/tools/sound_alto.py ls   [이름 부분...]
  PY web/tools/sound_alto.py set  <DistanceParamSetName>     # AATN 과 그 하위 파일을 한 번에
  PY web/tools/sound_alto.py aroc [이름...]                  # AROC 롤오프 모델 해석 + 거리별 이득 표
  PY web/tools/sound_alto.py audc [이름...]                  # AUDC(우선순위 거리 커브) 해석 + 거리별 값
  PY web/tools/sound_alto.py selftest                        # AROC/AUDC/AADR 재구현 합성 검사

AROC (거리 롤오프 커브) [판독: 파서 0x7103852e2c, 평가 0x7103852da4, 모델 vtable 0x7105735030/078/0c0]:
  +0x08 u32 type : 1=Rational(역거리), 2=Linear, 3=Power, 그 밖=모델 없음(항상 D 반환)
  +0x0C f32 A    : 기준(최소) 거리. >0 일 때만 반영(기본 1.0)
  +0x10 f32 B    : 최대 거리. 0 이면 FLT_MAX(제한 없음)
  +0x14 f32 C    : 모델 계수 (Rational/Linear: 감쇠량, Power: 지수)
  +0x18 f32 D    : 0..1 일 때만 반영. 결과 혼합 비율
  +0x1C u32 flag : 0 이면 out = g*D, 아니면 out = 1-(1-g)*D
  +0x20 f32 E    : v2 만(v1 은 0). 이 평가 함수에서는 쓰지 않음
  g(d) = d <= A ? 1 : 모델(min(d, B)), |g| < 2^-15 근처는 0 으로 스냅, 최종 out 은 [0,1] 로 자름
    Rational : A / (C*d + (1-C)*A)
    Linear   : 1 - (d - A) * C / (B - A)
    Power    : (A / d) ** C
  d 의 단위: Alto 계산부 0x7103863fe8 이 (음원 거리 [+0x8c]) / (전역 단위 [*0x710599a3f8 → +0x10 → +0x20]) * [+0x90] 로 만든다.
  [+0x90] 에 SLink DistCoef 가 들어가는지는 미확정.

AUDC (거리 우선순위 커브) [판독: 파서 0x710385b234, 평가 vtable 0x7105735168 슬롯 6 = 0x710385b148]:
  +0x08 u32 type(0 지수, 1 선형) +0x0C A(0..1, 가까울 때 값) +0x10 B(0..1, 먼 쪽 수렴값) +0x14 C(>=0, 시작 거리)
  +0x18 D(>0, 감쇠 거리 단위) +0x1C E(0..1, D 마다 곱해지는 비율) +0x20 (>=0, 평가에서 안 씀)
  v(x) = x<=C ? A : (x>cut ? 0 : (E==1 ? A : (E==0 ? B : B + (A-B)*t)))
    t = type0: E^((x-C)/D),  type1: max(1-(1-E)(x-C)/D, 0),  |v|<2^-15 -> 0
  cut = (A<B or B>0) ? FLT_MAX : (A<=0 ? 0 : (E==0 ? C : C + D*(type0: ln(t0)/ln(E), type1: (1-t0)/(1-E)))),
        t0 = max(-B/(A-B), 3.0517578e-5)
AADR (음원 지향성) [판독: 파서 0x710384eaac 안 0x71038515b0, 설정 0x7103863788, 평가 0x7103863fe8]:
  +0x08 inner(도, 0..180) +0x0C outer(도, 0..180) +0x10 outerGain(0..1) +0x14 outerFilter(0..1)
  각도 = atan2(|z x v|, z . v) (z = 음원 행렬 3열, v = 청자 위치 - 음원 위치, 0x710386119c), 라디안 비교
  inner_r = clamp(inner*pi/180, 0, outer_r), outer_r = clamp(outer*pi/180, 0, pi)
  t = clamp((각도-inner_r)/(outer_r-inner_r), 0, 1): volume *= 1 - t*(1-outerGain), filter += t*outerFilter
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import spl_data as S  # noqa: E402

ARC = 'C:/dev/splatoon3/extracted/romfs/Sound/Attenuation/Attenuation.Product.100.baatarc.zs'


def files():
    return S.sarc(S.unzs(open(ARC, 'rb').read()))


def words(d, start):
    out = []
    for o in range(start, len(d) - 3, 4):
        u, = struct.unpack_from('<I', d, o)
        f, = struct.unpack_from('<f', d, o)
        out.append('%08x(%s)' % (u, ('%.6g' % f) if 1e-6 < abs(f) < 1e7 or u == 0 else 'u%d' % u))
    return out


def aatn(d):
    """AATN v1: +8 u32 문자열 영역 오프셋, +0xC 부터 고정 배치(데이터 3종에서 일관) [데이터]:
    (vol 이름, u32), (farFx 이름, u32), (filter 이름, u32), (? 이름, u32), (priority 이름, u32),
    directivity 이름, culling 이름, u32, u32. u32 는 0(이름 커브 사용)/2(이름 없음) 로 보임 [추정]."""
    so, = struct.unpack_from('<I', d, 8)

    def name(off):
        p = so + off
        return d[p:d.index(b'\0', p)].decode()
    w = struct.unpack_from('<14I', d, 0xc)
    slots = ['volume', 'farFx', 'filter', 'unknown3', 'priority']
    out = {}
    for i, k in enumerate(slots):
        out[k] = (name(w[2 * i]), w[2 * i + 1])
    out['directivity'] = name(w[10])
    out['culling'] = name(w[11])
    out['tail'] = [w[12], w[13]]
    return out


FLT_MAX = 3.4028234663852886e+38


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def aroc_parse(d):
    ver, = struct.unpack_from('<H', d, 6)
    typ, A, B, C, D, flag = struct.unpack_from('<IffffI', d, 8)
    E = struct.unpack_from('<f', d, 0x20)[0] if ver != 1 else 0.0
    return {'type': typ, 'A': A, 'B': B, 'C': C, 'D': D, 'flag': flag, 'E': E, 'ver': ver}


def _snap(g):
    return g if (g >= 3.051851e-05 or g <= -3.0517578e-05) else 0.0


def aroc_gain(c, dist):
    """0x7103852da4 재구현 (f32 반올림은 단계별로 흉내). 반환 0..1."""
    A = c['A'] if c['A'] > 0 else 1.0
    B = c['B'] if c['B'] >= 0 else 0.0
    C = c['C'] if c['C'] >= 0 else 1.0
    D = c['D'] if 0.0 <= c['D'] <= 1.0 else 1.0
    t = c['type']
    if t not in (1, 2, 3):
        return D
    mx = FLT_MAX if B == 0.0 else B
    if t == 1:
        coef = f32((1.0 - C) * A)
    elif t == 2:
        coef = f32(C / (mx - A)) if mx != A else 0.0
    else:
        coef = f32((1.0 / A) ** (-C))
    if not dist > A:
        g = 1.0
    else:
        x = mx if dist >= mx else dist
        if t == 1:
            g = _snap(f32(A / f32(x * C + coef)))
        elif t == 2:
            g = _snap(f32(1.0 - f32((x - A) * coef)))
        else:
            g = _snap(f32(f32(x ** (-C)) * coef))
    out = g * D if c['flag'] == 0 else 1.0 - g * (1.0 - D)
    out = min(out, 1.0)
    return 0.0 if out < 0 else out


def audc_parse(d):
    typ, A, B, C, D, E, F = struct.unpack_from('<Iffffff', d, 8)
    return {'type': typ, 'A': A, 'B': B, 'C': C, 'D': D, 'E': E, 'F': F}


def audc_cut(c):
    """0x710385b234 의 +0x74 (값이 0 이 되는 거리) 재구현."""
    A, B, C, D, E = c['A'], c['B'], c['C'], c['D'], c['E']
    if A < B or B > 0.0:
        return FLT_MAX
    if A <= 0.0:
        return 0.0
    if E == 0.0:
        return C
    t0 = max(f32((0.0 - B) / (A - B)), 3.0517578e-05)
    if c['type'] == 1:
        f = (1.0 - t0) / (1.0 - E) * D
    elif c['type'] == 0:
        import math
        f = math.log(t0) / math.log(E) * D
    else:
        f = 0.0
    return C + f


def audc_value(c, x):
    """0x710385b148 재구현."""
    A, B, C, D, E = c['A'], c['B'], c['C'], c['D'], c['E']
    if not C < x:
        return A
    if not audc_cut(c) >= x:
        return 0.0
    if E == 1.0:
        return A
    if E == 0.0:
        return B
    dx = x - C
    if c['type'] == 1:
        t = max(1.0 - (1.0 - E) * (dx / D), 0.0)
    elif c['type'] == 0:
        t = E ** (dx / D)
    else:
        t = 0.0
    v = B + t * (A - B)
    return 0.0 if -3.0517578e-05 < v < 3.0517578e-05 else v


def aadr_gain(inner_deg, outer_deg, outer_gain, angle_rad):
    """0x7103863788(설정) + 0x7103863fe8(평가) 재구현. 반환 (볼륨 배율, t)."""
    import math
    k = 0.017453292
    o = min(max(outer_deg * k, 0.0), math.pi)
    i = max(inner_deg * k, 0.0)
    i = o if i > o else i
    if angle_rad <= i:
        return 1.0, 0.0
    if angle_rad <= o:
        t = (angle_rad - i) / (o - i)
        return (1.0 - t * (1.0 - outer_gain)) if t < 1.0 else outer_gain, t
    return outer_gain, 1.0


def cmd_audc(fs, names):
    for n, d in sorted(fs.items()):
        if not n.endswith('.baudc'):
            continue
        base = n.split('/')[-1][:-6]
        if names and base not in names:
            continue
        c = audc_parse(d)
        tab = ' '.join('%g:%.4f' % (x, audc_value(c, x)) for x in (0, 1, 2, 4, 8, 16, 32))
        print('%-20s type=%d A=%g B=%g C=%g D=%g E=%g cut=%.4g | %s' % (base, c['type'], c['A'], c['B'], c['C'], c['D'], c['E'], audc_cut(c), tab))


def cmd_aroc(fs, names):
    for n, d in sorted(fs.items()):
        if not n.endswith('.baroc'):
            continue
        base = n.split('/')[-1][:-6]
        if names and base not in names:
            continue
        c = aroc_parse(d)
        tab = ' '.join('%g:%.4f' % (x, aroc_gain(c, x)) for x in (0.5, 1, 2, 4, 8, 16, 32, 64))
        print('%-28s type=%d A=%g B=%g C=%g D=%g flag=%d | %s' % (base, c['type'], c['A'], c['B'], c['C'], c['D'], c['flag'], tab))


def cmd_selftest():
    ok = True

    def chk(label, got, exp, tol=1e-5):
        nonlocal ok
        r = abs(got - exp) <= tol
        ok &= r
        print(('OK  ' if r else 'FAIL'), label, round(got, 6), '' if r else '(expected %s)' % exp)
    rat = {'type': 1, 'A': 1.0, 'B': 0.0, 'C': 1.0, 'D': 1.0, 'flag': 0}
    chk('Rational A=1 C=1 d=4 -> 1/4', aroc_gain(rat, 4.0), 0.25)
    chk('Rational d<=A -> 1', aroc_gain(rat, 0.5), 1.0)
    pw = {'type': 3, 'A': 1.0, 'B': 0.0, 'C': 0.70794, 'D': 1.0, 'flag': 0}
    chk('Power A=1 C=0.70794 d=10 -> 10^-0.70794', aroc_gain(pw, 10.0), 10 ** -0.70794, 1e-4)
    lin = {'type': 2, 'A': 2.0, 'B': 10.0, 'C': 0.8, 'D': 1.0, 'flag': 0}
    chk('Linear A=2 B=10 C=0.8 d=6 -> 0.6', aroc_gain(lin, 6.0), 0.6)
    chk('Linear d>=B 고정 -> 1-C', aroc_gain(lin, 50.0), 0.2)
    mix = dict(lin, D=0.5, flag=1)
    chk('flag=1 D=0.5 d=6 -> 1-(1-0.6)*... = 1-0.6*0.5', aroc_gain(mix, 6.0), 1 - 0.6 * 0.5)
    none = {'type': 0, 'A': 1.0, 'B': 0.0, 'C': 1.0, 'D': 0.7, 'flag': 0}
    chk('모델 없음 -> D', aroc_gain(none, 100.0), 0.7)
    lo = {'type': 0, 'A': 0.4, 'B': 0.0, 'C': 0.0, 'D': 3.0, 'E': 0.1, 'F': 0.0}
    hi = {'type': 0, 'A': 0.9, 'B': 0.41, 'C': 0.0, 'D': 3.0, 'E': 0.1, 'F': 0.0}
    chk('AUDC CmnPrio_Low d=0 -> A', audc_value(lo, 0.0), 0.4)
    chk('AUDC CmnPrio_Low d=3 -> 0.4*0.1', audc_value(lo, 3.0), 0.04)
    chk('AUDC CmnPrio_Low cut = 3*ln(2^-15)/ln(0.1)', audc_cut(lo), 3.0 * 4.515450, 1e-3)
    chk('AUDC CmnPrio_Low d=14 (cut 너머) -> 0', audc_value(lo, 14.0), 0.0)
    chk('AUDC CmnPrio_High d=3 -> 0.41+0.49*0.1', audc_value(hi, 3.0), 0.41 + 0.049)
    lin = {'type': 1, 'A': 1.0, 'B': 0.0, 'C': 2.0, 'D': 4.0, 'E': 0.5, 'F': 0.0}
    chk('AUDC 선형 d=6 -> 1-(0.5)(4/4)=0.5', audc_value(lin, 6.0), 0.5)
    import math
    chk('AADR WeaponMuzzle 60도 -> 1', aadr_gain(80, 140, 0.8, math.radians(60))[0], 1.0)
    chk('AADR WeaponMuzzle 110도 -> 1-0.5*0.2', aadr_gain(80, 140, 0.8, math.radians(110))[0], 0.9, 1e-4)
    chk('AADR WeaponMuzzle 170도 -> 0.8', aadr_gain(80, 140, 0.8, math.radians(170))[0], 0.8)
    print('SELFTEST', 'PASS' if ok else 'FAIL')


def main():
    if sys.argv[1] == 'selftest':
        cmd_selftest()
        return
    fs = files()
    if sys.argv[1] == 'aroc':
        cmd_aroc(fs, set(sys.argv[2:]))
        return
    if sys.argv[1] == 'audc':
        cmd_audc(fs, set(sys.argv[2:]))
        return
    if sys.argv[1] == 'ls':
        for n, d in sorted(fs.items()):
            if len(sys.argv) > 2 and not any(k in n for k in sys.argv[2:]):
                continue
            ver, = struct.unpack_from('<H', d, 6)
            print(n, d[:4].decode(), 'v%d' % ver, len(d))
            if d[:4] == b'AATN':
                print('   refs', aatn(d))
            else:
                print('   ', ' '.join(words(d, 8)))
    elif sys.argv[1] == 'set':
        name = sys.argv[2]
        d = fs['Attenuation/%s.baatn' % name]
        refs = aatn(d)
        print(name, 'AATN refs', refs)
        for nm in [v[0] if isinstance(v, tuple) else v for k, v in refs.items() if k != 'tail']:
            if not nm:
                continue
            for ext in ('baroc', 'baudc', 'baadr', 'baacl'):
                k = 'Attenuation/%s.%s' % (nm, ext)
                if k in fs:
                    x = fs[k]
                    print('  ', nm, ext, x[:4].decode(), ' '.join(words(x, 8)))


if __name__ == '__main__':
    main()
