"""피격·데미지 계산 재구현 (combat 영역).

원본 판독 근거는 web/docs/combat/damage_hit.md.

  PY web/tools/combat_damage.py falloff [무기GPT이름...]   # 슈터 거리(프레임) 감쇠 표
  PY web/tools/combat_damage.py rate <Row> <Col>            # DamageRateInfo 배율 조회
  PY web/tools/combat_damage.py weapon <WeaponInfoMain RowId>  # 무기 → 배율 행, 감쇠 표
  PY web/tools/combat_damage.py selftest                    # 경계 조건 검사

f32 재현: numpy.float32로 원본 명령(scvtf/fdiv/fmin/fcsel/fsub/fmul/fadd/fcvtzs) 순서를 그대로 따른다.
"""
import json
import os
import sys

import numpy as np

R = 'C:/dev/splatoon3'
GPT = R + '/extracted/params/Component/GameParameterTable'
RATE = R + '/analysis/combat/DamageRateInfoConfig.json'
WIM = R + '/analysis/combat/rsdb/WeaponInfoMain.json'
f32 = np.float32

# spl::BulletShooterDamageParam 생성자 기본값 (0x7101521104) [판독]
SHOOTER_DMG_DEFAULT = {'ValueMax': 180, 'ValueMin': 120, 'ReduceStartFrame': 8, 'ReduceEndFrame': 24}


def shooter_damage(frame, vmax, vmin, rstart, rend):
    """0x71017506d0 재구현. frame = 탄 객체 +0x134 (경과 프레임 카운터)."""
    denom = rend - rstart
    if denom == 0:  # subs/cinc eq
        denom = 1
    num = frame - rstart + 1
    t = f32(num) / f32(denom)
    t1 = min(t, f32(1.0))  # fmin s1, s0, 1.0
    if t < f32(0.0):  # fcmp s0,#0 ; fcsel mi → 0
        t1 = f32(0.0)
    vmax_f = f32(vmax)
    d = (f32(vmin) - vmax_f) * t1 + vmax_f
    return int(np.trunc(d))  # fcvtzs: 0 방향 절삭


def _load(name):
    p = f'{GPT}/{name}.game__GameParameterTable.bgyml.json'
    return json.load(open(p, encoding='utf-8'))


def resolve_gpt(name):
    """$parent 를 따라 GameParameters 를 항목(키) 단위·필드 단위로 덮어쓴다.

    병합 규칙은 [추정]: 코드에서는 '설정됨 플래그'가 선 필드만 자식 값을 쓰고 아니면 부모를 탄다
    (0x71017506d0 의 부모 체인 순회 판독). 그래서 필드 단위 덮어쓰기로 구현한다.
    """
    d = _load(name)
    chain = [d]
    while '$parent' in chain[-1]:
        par = chain[-1]['$parent'].split('/')[-1].replace('.game__GameParameterTable.gyml', '')
        chain.append(_load(par))
    out = {}
    for node in reversed(chain):
        for k, v in node.get('GameParameters', {}).items():
            out.setdefault(k, {}).update(v)
    return out


def shooter_param(name):
    g = resolve_gpt(name)
    for v in g.values():
        if v.get('$type') == 'spl__BulletShooterDamageParam':
            p = dict(SHOOTER_DMG_DEFAULT)
            p.update({k: v[k] for k in SHOOTER_DMG_DEFAULT if k in v})
            return p
    return None


def falloff_table(p, frames=range(0, 60)):
    return [(f, shooter_damage(f, p['ValueMax'], p['ValueMin'], p['ReduceStartFrame'], p['ReduceEndFrame'])) for f in frames]


_rate = None


def damage_rate(row, col, default=1.0):
    """DamageRateInfoConfig 셀 조회. DamageRate 키가 없는 셀은 기본값(default) [미확정: 기본값 1.0은 데이터 패턴 추정]."""
    global _rate
    if _rate is None:
        _rate = json.load(open(RATE, encoding='utf-8'))['CellList']
    c = _rate.get(f'{row}___{col}')
    if c is None:
        return None
    return c.get('DamageRate', default)


def weapon(row_id):
    rows = json.load(open(WIM, encoding='utf-8'))
    r = [x for x in rows if x['__RowId'] == row_id][0]
    spec = r['SpecActor'].split('/')[-1].replace('.engine__actor__ActorParam.gyml', '')
    return r, spec


def cmd_falloff(names):
    if not names:
        names = sorted(f.split('.')[0] for f in os.listdir(GPT) if f.endswith('.json')
                       and 'spl__BulletShooterDamageParam' in open(f'{GPT}/{f}', encoding='utf-8').read())
    for n in names:
        p = shooter_param(n)
        if p is None:
            continue
        t = falloff_table(p, range(0, max(p['ReduceEndFrame'] + 2, 12)))
        first_drop = next((f for f, d in t if d < p['ValueMax']), None)
        first_min = next((f for f, d in t if d == p['ValueMin']), None)
        print(f"{n:34s} max {p['ValueMax']:4d} min {p['ValueMin']:4d} start {p['ReduceStartFrame']:3d} end {p['ReduceEndFrame']:3d}"
              f" | 처음 감소 프레임 {first_drop} 최소 도달 {first_min}")


def selftest():
    ok = True
    def chk(a, b, msg):
        nonlocal ok
        if a != b:
            ok = False
            print('FAIL', msg, a, b)
    # 스플래시슈터 360/180/8/40
    chk(shooter_damage(0, 360, 180, 8, 40), 360, 'frame0')
    chk(shooter_damage(6, 360, 180, 8, 40), 360, 'frame6 (num<0)')
    chk(shooter_damage(7, 360, 180, 8, 40), 360, 'frame7 (num=0)')
    chk(shooter_damage(8, 360, 180, 8, 40), 354, 'frame8 t=1/32 → 360-5.625=354.375 → 354')
    chk(shooter_damage(39, 360, 180, 8, 40), 180, 'frame39 t=1')
    chk(shooter_damage(100, 360, 180, 8, 40), 180, 'clamp')
    # 분모 0 → 1
    chk(shooter_damage(5, 300, 100, 5, 5), 100, 'denom0 frame5 t=1')
    chk(shooter_damage(4, 300, 100, 5, 5), 300, 'denom0 frame4 t=0')
    # 증가형(min>max)도 같은 식
    chk(shooter_damage(8, 100, 200, 8, 10), 150, 'min>max')
    print('selftest', 'OK' if ok else 'FAIL')
    return ok


def main():
    a = sys.argv[1:]
    if not a or a[0] == 'falloff':
        cmd_falloff(a[1:])
    elif a[0] == 'rate':
        print(damage_rate(a[1], a[2]))
    elif a[0] == 'weapon':
        r, spec = weapon(a[1])
        print('SpecActor GPT', spec, 'DefaultDamageRateInfoRow', r['DefaultDamageRateInfoRow'],
              'Extra', r['ExtraDamageRateInfoRowSet'], 'HitEffector', r['DefaultHitEffectorType'])
        p = shooter_param(spec)
        if p:
            print(p)
            for f, d in falloff_table(p, range(0, p['ReduceEndFrame'] + 2)):
                print(f'  frame {f:3d}  {d:4d}  ({d / 10:.1f})')
    elif a[0] == 'selftest':
        sys.exit(0 if selftest() else 1)


if __name__ == '__main__':
    main()


# ---- 수신 측(DamageReceiver 0x7101a86ec0) 재구현 ----
EPS = f32(1e-05)


def apply_rate(damage, rate):
    """dmg' = fcvtzs((rate + 1e-5) * float(dmg))  (0x7101a870dc~0x7101a870fc)"""
    return int(np.trunc((f32(rate) + EPS) * f32(damage)))


def apply_rate_no_eps(damage, rate):
    """ObjectEffect_Up 보정(0x7101a87aa0)은 엡실론 없이 (int)(rate*float(dmg))"""
    return int(np.trunc(f32(rate) * f32(damage)))


def receive(damage, row, col, extra_rate=None, object_effect_up=False):
    d = damage
    if extra_rate is not None:  # receiver+0x1cc 켜짐 → +0x1c4 배율 먼저
        d = apply_rate(d, extra_rate)
    r = damage_rate(row, col)
    d = apply_rate(d, 1.0 if r is None else r)
    if d == 0:
        return 0
    if object_effect_up:
        r2 = damage_rate('ObjectEffect_Up', col)
        d = apply_rate_no_eps(d, 1.0 if r2 is None else r2)
    if d > 99999:
        d = 99998
    return d


# ---- 탄 넉백 (0x7101e66c4c, 인자 표 0x7101763368) ----
KNOCKBACK_SHOOTER = (95.0, 300, 280.0, 2000, 0.0)  # {+0 f32, +4 s32, +8 f32, +0xc s32, +0x10 f32}


def knockback(damage, vel, up=(0.0, 1.0, 0.0), p=KNOCKBACK_SHOOTER):
    v = np.array(vel, dtype=np.float32)
    n = np.float32(np.sqrt(np.float32(v @ v)))
    if n > 0:
        v = v * (np.float32(1.0) / n)
    lo, a, hi, b, blend = p
    t = f32(1.0)
    if b - a != 0:
        t = f32(damage - a) / f32(b - a)
    tc = min(t, f32(1.0))
    if t < 0:
        tc = f32(0.0)
    mag = f32(lo) + (f32(hi) - f32(lo)) * tc
    n = np.float32(np.sqrt(np.float32(v @ v)))
    if n > 0:
        v = v * (mag / n)
    u = np.array(up, dtype=np.float32)
    if u.any():
        dot = np.float32(u @ v)
        if dot != 0:
            v = v - u * dot
            # blend(+0x10) > 0 이면 크기 복원 — 슈터는 0이라 생략
    return v, float(mag), float(tc)
