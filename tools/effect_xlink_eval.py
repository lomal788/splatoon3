"""XLink2 키 → 재생할 에셋 목록 평가기(웹 디스패처의 참조 구현, 합성 검증용).

원본 실행이 아니다. 데이터(effect_xlink.py dump 결과)와 공개 xlink2 디컴파일(Splatoon 2 기반)의 컨테이너 규칙으로
"키 하나를 방출하면 어떤 에셋이 어떤 파라미터로 나오는가"를 계산한다.

규칙(근거는 web/docs/effect_sound/xlink_format.md §4, 주소는 이 게임 main):
  Switch   : 자식을 childStart→childEnd 순서로 보고, 조건이 없거나 '속성값 OP 조건값' 이 참인 첫 자식.   [판독 0x71038978bc]
  Random   : 자식 조건 weight 합 W, r = W*rand, 누적 weight 가 r 보다 커지는 첫 자식(r < 누적).          [판독 0x71038925a0]
  Random2  : Random 과 같되 직전에 고른 자식(인스턴스별 기억)을 후보에서 뺀다. 자식이 1개면 빼지 않음.   [판독 0x7103892874]
  Blend    : 모든 자식을 재생(+1 바이트 0 인 경우. 값 범위 블렌드는 데이터에 없음).                      [판독 0x710388f59c]
  Sequence : 자식을 순서대로 하나씩(앞 자식이 끝나면 다음, 시작 실패한 자식은 건너뜀).                    [판독 0x7103897644]
  Grid     : 두 속성 값의 2차원 표에서 자식 하나(-1 이면 없음).                                         [판독 0x71038909a4]
  duration : 컨테이너 자식이 끝날 때 duration>0 이면 1 감소, 0 이 아니면 다시 start(-1 = 무한 반복).   [판독 0x710389250c]
값 해석 (0x7103888b04, 난수 = sead xorshift128 의 (u>>9|0x3f800000)-1):
  Random(min,max)          = min<=max 이면 min + rand*(max-min), 아니면 min
  RandomNPow(min,max)      = min + r + sign(u)*|u|^N * r,  r=|max-min|/2, u=2*rand-1
  RandomNPowWeightMin      = min + |max-min| * rand^N ;  WeightMax = min + |max-min| * (1 - rand^N)
  Curve (curveType 0)      = 첫 점보다 작으면 첫 y, 점 x 와 같으면 그 y(다음 점 x 도 같으면 다음 y = 계단),
                             두 점 사이 선형, 마지막 점 이상이면 마지막 y. curveType != 0 은 마지막 y.
                             정수형 속성(Enum/S32/참조형)은 float 로 바꿔 넣는다.
  웹 구현에서 난수열 순서는 원본과 맞추지 않는다(연출값).

사용:
  PY web/tools/effect_xlink_eval.py <users.json> <UserName> <key> [prop=value ...] [--seed N]
  PY web/tools/effect_xlink_eval.py --selftest
"""
import json
import random
import sys

CMP = {
    'Equal': lambda a, b: a == b, 'NotEqual': lambda a, b: a != b,
    'GreaterThan': lambda a, b: a > b, 'GreaterThanOrEqual': lambda a, b: a >= b,
    'LessThan': lambda a, b: a < b, 'LessThanOrEqual': lambda a, b: a <= b,
}


def cond_ok(cond, props):
    if cond is None:
        return True
    if cond['parent'] != 'Switch':
        return True
    v = props.get(cond.get('_prop'))
    if v is None:
        return False
    return CMP[cond['compare']](v, cond['value'])


def curve_value(c, x):
    pts = c['points']
    if not pts:
        return 0.0
    if c.get('curveType', 0) != 0:
        return pts[-1][1]
    for k, (px, py) in enumerate(pts):
        if x == px:
            if k + 1 < len(pts) and pts[k + 1][0] == px:
                return pts[k + 1][1]
            return py
        if x < px:
            if k == 0:
                return py
            x0, y0 = pts[k - 1]
            return y0 + (x - x0) * ((py - y0) / (px - x0))
    return pts[-1][1]


def value(v, props, rng):
    if isinstance(v, dict):
        if 'curve' in v:
            c = v['curve']
            return curve_value(c, props.get(c['prop'], 0.0))
        for k, (lo, hi) in ((k, x) for k, x in v.items() if isinstance(x, list)):
            if k == 'Random':
                return lo + rng.random() * (hi - lo) if lo <= hi else lo
            n = None
            for nm, nv in (('2', 2.0), ('3', 3.0), ('4', 4.0), ('1Point5', 1.5)):
                if k.startswith('Random' + nm + 'Pow'):
                    n = nv
            if n is not None and k.endswith('Pow'):
                r = abs(hi - lo) / 2
                u = rng.random() * 2 - 1
                p = abs(u) ** n * r
                return lo + r + (p if u >= 0 else -p)
            if n is not None and k.endswith('WeightMin'):
                return lo + abs(hi - lo) * rng.random() ** n
            if n is not None and k.endswith('WeightMax'):
                return lo + abs(hi - lo) * (1.0 - rng.random() ** n)
        return v
    return v


def evaluate(user, key, props, rng=None, defaults=None, memo=None):
    rng = rng or random.Random(0)
    memo = {} if memo is None else memo  # Random2 직전 선택(사용자 인스턴스별)
    cts = user['callTables']
    roots = [c for c in cts if c['key'] == key and c['parent'] == -1]
    if not roots:
        return []
    out = []

    def attach_prop(parent_ct, child_ct):
        cond = child_ct.get('condition')
        if cond and cond['parent'] == 'Switch':
            cond['_prop'] = parent_ct['container']['watchProperty']
        return cond

    def run(ct, path):
        k = ct.get('container')
        if k is None:
            params = {}
            for name, v in (ct.get('params') or {}).items():
                params[name] = value(v, props, rng)
            out.append({'path': path + [ct['key']], 'asset': params.get('RuntimeAssetName', ''), 'params': params})
            return
        a, b = k['children']
        kids = [cts[i] for i in range(a, b + 1)]
        t = k['type']
        if t == 'Switch':
            for c in kids:
                if cond_ok(attach_prop(ct, c), props):
                    run(c, path + [ct['key']])
                    return
        elif t in ('Random', 'Random2'):
            last = memo.get(ct['i']) if (t == 'Random2' and len(kids) > 1) else None
            cand = [c for c in kids if c['i'] != last]
            ws = [(c.get('condition') or {}).get('weight', 0.0) for c in cand]
            tot = sum(ws)
            if tot > 0:
                r = rng.random() * tot
                acc = 0.0
                for c, w in zip(cand, ws):
                    acc += w
                    if r < acc:
                        if t == 'Random2':
                            memo[ct['i']] = c['i']
                        run(c, path + [ct['key']])
                        return
        elif t == 'Grid':
            v1 = props.get(k['props'][0])
            v2 = props.get(k['props'][1])
            if v1 in k['values1'] and v2 in k['values2']:
                ci = k['table'][k['values1'].index(v1)][k['values2'].index(v2)]
                if ci >= 0:
                    run(cts[ci], path + [ct['key']])
        elif t in ('Blend', 'Sequence'):
            for c in kids:
                run(c, path + [ct['key']])
    run(roots[0], [])
    return out


def selftest():
    U = json.load(open('C:/dev/splatoon3/analysis/effect_sound/slink2_users.json', encoding='utf-8'))
    E = json.load(open('C:/dev/splatoon3/analysis/effect_sound/elink2_users.json', encoding='utf-8'))
    s = U['WeaponShooterNormal']
    e = E['WeaponShooterNormal']
    ok = True

    def check(label, got, exp):
        nonlocal ok
        res = got == exp
        ok &= res
        print(('OK  ' if res else 'FAIL'), label, got, '' if res else '(expected %s)' % exp)

    for st, exp in (('Focused', 'Wp_ShooterNormal_Shot_00'), ('Enemy', 'Wp_NormalShot_02'),
                    ('Friend', 'Wp_NormalShot_Blurred_02')):
        r = evaluate(s, 'Fire', {'SubjectiveType': st})
        check('SLink Fire SubjectiveType=%s' % st, [x['asset'] for x in r], [exp])
    check('SLink Fire SubjectiveType 미설정', evaluate(s, 'Fire', {}), [])
    check('SLink OnAttach Focused', [x['asset'] for x in evaluate(s, 'OnAttach', {'SubjectiveType': 'Focused'})],
          ['Wp_Shooter_Attach_00'])
    check('SLink OnAttach Enemy (조건 불일치 → 무음)', evaluate(s, 'OnAttach', {'SubjectiveType': 'Enemy'}), [])
    # 볼륨/피치 난수 범위
    rng = random.Random(1)
    vols, pits = [], []
    for _ in range(20000):
        r = evaluate(s, 'Fire', {'SubjectiveType': 'Focused'}, rng)[0]['params']
        vols.append(r['Volume'])
        pits.append(r['Pitch'])
    check('Fire_Focused Volume 범위 [0.9,1.1]', (round(min(vols), 2) >= 0.9, round(max(vols), 2) <= 1.1), (True, True))
    check('Fire_Focused Pitch Random2Pow 범위 [0.7,1.25]', (min(pits) >= 0.7, max(pits) <= 1.25), (True, True))
    mid = sum(1 for p in pits if abs(p - 0.975) < 0.0275) / len(pits)
    print('    Random2Pow 중앙 10%% 구간 비율 %.3f (균등이면 0.100, N=2 이면 sqrt(0.1)=0.316)' % mid)
    check('Random2Pow 중앙 집중', 0.28 < mid < 0.35, True)
    # ELink 머즐 플래시 Delay 커브
    mz = [c for c in e['callTables'] if c['key'] == 'マズルフラッシュ'][0]
    for dot, exp in ((1.0, 0.0), (0.75, 2.0), (0.875, 1.0), (0.5, 2.0)):
        got = round(curve_value(mz['params']['Delay']['curve'], dot), 4)
        check('Muzzle Delay(MuzzleShotDirXZDot=%s)' % dot, got, exp)
    # ELink InkDive 스위치(StandAloneType)
    for sa, exp in (('DieInWater', ['GearWaterSplash']), ('Die', ['GearInkDive']), ('None', [])):
        check('ELink InkDive StandAloneType=%s' % sa,
              [x['asset'] for x in evaluate(e, 'InkDive', {'StandAloneType': sa})], exp)
    for sm, exp in (('Versus', ['GearWaterRipple']), ('Coop', ['GearWaterRippleCoop'])):
        check('ELink WaterRipple SpecMode=%s' % sm,
              [x['asset'] for x in evaluate(e, 'WaterRipple', {'SpecMode': sm})], exp)
    # Grid(2차원 표) 컨테이너: BulletPointSensor OnActivate = SpecMode(전역) x SubjectiveType [판독 규칙 + 데이터]
    g = U['BulletPointSensor']
    for sm, st, exp in (('Versus', 'Focused', ['Wp_MarkingFly_00']), ('Versus', 'Friend', []),
                        ('Coop', 'Friend', ['Wp_MarkingFly_00']), ('Mission', 'Enemy', ['Wp_MarkingFly_00'])):
        r = evaluate(g, 'OnActivate', {'SpecMode': sm, 'SubjectiveType': st})
        check('Grid BulletPointSensor OnActivate %s/%s' % (sm, st), [x['asset'] for x in r], exp)
    # Random2: 같은 인스턴스(memo 공유)에서 연속 두 번 같은 자식이 나오지 않음 (HitEffect 水没 8종)
    h = U['HitEffect']
    memo, prev, rep = {}, None, 0
    rr = random.Random(7)
    for _ in range(2000):
        a = [x['asset'] for x in evaluate(h, '水没', {}, rr, memo=memo)]
        if a and a == prev:
            rep += 1
        prev = a
    check('Random2 水没 연속 중복 0회 (2000회)', rep, 0)
    # Curve 계단(같은 x 연속 점) 규칙 — 합성 커브
    cv = {'curveType': 0, 'points': [[0.0, 1.0], [0.5, 1.0], [0.5, 3.0], [1.0, 5.0]]}
    check('Curve x=0.5 (같은 x 두 점 → 뒤 점 y)', curve_value(cv, 0.5), 3.0)
    check('Curve x=0.75 (선형)', curve_value(cv, 0.75), 4.0)
    check('Curve x=-1 / 2 (끝값)', (curve_value(cv, -1.0), curve_value(cv, 2.0)), (1.0, 5.0))
    # 데이터 전수: Switch 컨테이너의 무조건 자식이 마지막에만 있는지(기본값 규칙의 데이터 근거)
    bad = tot = 0
    for D in (U, E):
        for u in D.values():
            cts = u['callTables']
            for c in cts:
                k = c.get('container')
                if k and k['type'] == 'Switch':
                    a, b = k['children']
                    kids = cts[a:b + 1]
                    tot += 1
                    nc = [i for i, x in enumerate(kids) if 'condition' not in x]
                    if any(i != len(kids) - 1 for i in nc):
                        bad += 1
    print('    Switch 컨테이너 %d개 중 무조건 자식이 마지막이 아닌 것 %d개' % (tot, bad))
    print('SELFTEST', 'PASS' if ok else 'FAIL')


def main():
    if sys.argv[1] == '--selftest':
        selftest()
        return
    U = json.load(open(sys.argv[1], encoding='utf-8'))
    user = U[sys.argv[2]]
    props = {}
    seed = 0
    args = sys.argv[4:]
    if '--seed' in args:
        seed = int(args[args.index('--seed') + 1])
    for a in args:
        if '=' in a:
            k, v = a.split('=', 1)
            try:
                v = float(v)
            except ValueError:
                pass
            props[k] = v
    print(json.dumps(evaluate(user, sys.argv[3], props, random.Random(seed)), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
