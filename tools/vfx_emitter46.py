"""VFXB v46 이미터(EmitterData 0xEF0 B) 원시 덤프·필드표 판독 도구.

사용:
  PY web/tools/vfx_emitter46.py raw  <x.vfxb> <이미터셋> [이미터명]          # 4B 단위 u32/f32 표(0이 아닌 칸)
  PY web/tools/vfx_emitter46.py stat <x.vfxb> <오프셋16진...>                  # 전 이미터의 해당 오프셋 값 분포
  PY web/tools/vfx_emitter46.py fields <x.vfxb> <이미터셋...> [--json out]      # 판독된 v46 필드표로 해석
  PY web/tools/vfx_emitter46.py sim <fields.json> <이미터셋/이미터> [프레임수]       # GPU_TIME 파티클 식 재구현 표
  PY web/tools/vfx_emitter46.py selftest                                         # 재구현 식 합성 검사
"""
import collections
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import effect_vfxb as V  # noqa: E402

SIZE = 0xEF0


def emitters(v, want=None):
    for e in v.esets:
        nm = v.eset_name(e)
        if want and nm not in want:
            continue

        def walk(em, depth, parent):
            bo = em.data_off()
            name = v.d[bo + 0x10:bo + 0x70].split(b'\0')[0].decode('utf-8', 'replace')
            yield nm, name, depth, parent, bo, em
            for c in em.children:
                yield from walk(c, depth + 1, name)
        for em in e.children:
            yield from walk(em, 0, None)


def f32(d, o):
    return struct.unpack_from('<f', d, o)[0]


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def cmd_raw(v, eset, ename=None):
    for es, name, depth, parent, bo, em in emitters(v, [eset]):
        if ename and name != ename:
            continue
        print(f'== {es}/{name} depth={depth} parent={parent} off={bo:#x} attrs={[a.magic for a in em.attrs]}')
        d = v.d
        for o in range(0, SIZE, 4):
            u = u32(d, bo + o)
            if u == 0:
                continue
            fv = f32(d, bo + o)
            fs = f'{fv:.6g}' if 1e-6 < abs(fv) < 1e7 else '-'
            print(f'  +{o:#05x} u32={u:#010x} i32={struct.unpack_from("<i", d, bo + o)[0]:<11d} f32={fs}')


def cmd_stat(v, offs):
    acc = {o: collections.Counter() for o in offs}
    n = 0
    for es, name, depth, parent, bo, em in emitters(v):
        n += 1
        for o in offs:
            acc[o][u32(v.d, bo + o)] += 1
    print('emitters', n)
    for o in offs:
        top = acc[o].most_common(8)
        print(f'+{o:#05x}', ', '.join(f'{k:#x}({struct.unpack("<f", struct.pack("<I", k))[0]:.4g})x{c}' for k, c in top))


# ---------------------------------------------------------------- v46 필드표 (판독 결과는 FIELDS 에 누적)
FIELDS = [
    # (오프셋, 형, 웹 권장 이름, 근거). 근거: 판독=코드/셰이더 판독, 셰이더옵션=bfsha 프로그램 옵션과 데이터 일치, 추정=v53 순서 정렬
    # --- 정적 블록: GPU UBO sysEmitterStaticUniformBlock = ResEmitter[0:0xA90], data[k] = +16k (UBO 크기 2704 B)
    (0x070, 'u32', 'staticFlags1', '판독: 셰이더 data[7].x bit28/29/30 = 회전 X/Y/Z 무작위 반전'),
    (0x080, 'u32', 'numColor0Keys', '셰이더옵션 COLOR_0_ANIM_n_KEY'),
    (0x084, 'u32', 'numAlpha0Keys', '셰이더옵션 ALPHA_0_ANIM_n_KEY'),
    (0x088, 'u32', 'numColor1Keys', '셰이더옵션 COLOR_1_ANIM_n_KEY'),
    (0x08c, 'u32', 'numAlpha1Keys', '셰이더옵션 ALPHA_1_ANIM_n_KEY'),
    (0x090, 'u32', 'numScaleKeys', '셰이더옵션 SCALE_ANIM_n_KEY'),
    (0x0a0, 'f32x5', 'loopRate_c0_a0_c1_a1_scale', '판독: data[10].y(alpha0) data[11].x(scale), >0 이면 반복 주기(프레임)'),
    (0x0b4, 'f32x5', 'loopRandom_c0_a0_c1_a1_scale', '판독: data[11].z data[12].y = 시작 위상 난수 배율'),
    (0x0d0, 'f32x3', 'gravityDir', '판독: data[13].xyz'),
    (0x0dc, 'f32', 'gravityScale', '판독: data[13].w'),
    (0x0e0, 'f32', 'airRegist', '판독: data[14].x, CPU 0x7100826cb0'),
    (0x0e4, 'f32', 'unknownE4', '판독(용도 미확정): data[14].y'),
    (0x0f0, 'f32x3', 'pivotOffset', '판독: data[15], 정점 = (pos + 0.5*값) * scale'),
    (0x670, 'f32', 'colorScale', '판독: data[103].x, CPU 정적+0x600'),
    (0x680, 'key8', 'color0Keys', '판독: data[104..] {r,g,b,t}'),
    (0x700, 'key8', 'alpha0Keys', '판독: data[112..] .x 값 .w 시각'),
    (0x780, 'key8', 'color1Keys', '판독: data[120]'),
    (0x800, 'key8', 'alpha1Keys', '추정(color1 다음, 같은 배치)'),
    (0x8c0, 'key8', 'scaleKeys', '판독: data[140..] {sx,sy,sz,t}'),
    (0xa00, 'f32x3', 'rotateInit', '추정(v53 순서)'),
    (0xa10, 'f32x3', 'rotateInitRand', '판독: data[161] * (rand-0.5)'),
    (0xa20, 'f32x3', 'rotateAdd', '판독: data[162].xyz'),
    (0xa2c, 'f32', 'rotateRegist', '판독: data[162].w, (1-r^t)/(1-r)'),
    (0xa30, 'f32x3', 'rotateAddRand', '판독: data[163]'),
    # --- EmitterInfo (CPU)
    (0xa92, 'u8', 'calcType', '판독+셰이더옵션: 0 CPU, 1 GPU_TIME, 2 GPU_SO'),
    (0xa93, 'u8', 'followType', '셰이더옵션: 0 ALL, 1 NONE (2 POS 추정)'),
    (0xa94, 'u8', 'randomSeedType', '판독 0x710080ca78: 0 전역 난수, 1 이미터셋 시드, 2 고정'),
    (0xa95, 'u8', 'updateMatrixByEmit', '판독 0x710080e9a4 -> 0x710080e4cc'),
    (0xa99, 'u8', 'fadeInCurve', '판독 0x710080ec48: 0 끔 1 선형 2 제곱 3 4제곱'),
    (0xa9b, 'u8', 'fadeOutCurve', '판독 0x710080ecac'),
    (0xaa0, 'i32', 'randomSeed', '판독'),
    (0xaa4, 'i32', 'drawPath', '판독 0x710080eb7c, 셰이더옵션 DRAW_PATH_n'),
    (0xaa8, 'i32', 'fadeOutFrames', '판독 0x710081c0b8'),
    (0xaac, 'i32', 'fadeInFrames', '판독 0x710081c0b8'),
    (0xab0, 'f32x3', 'emitterTrans', '판독(0x710080e4cc 가 15 float 읽음, 순서 추정)'),
    (0xabc, 'f32x3', 'emitterTransRand', '추정'),
    (0xac8, 'f32x3', 'emitterRotate', '추정'),
    (0xad4, 'f32x3', 'emitterRotateRand', '추정'),
    (0xae0, 'f32x3', 'emitterScale', '추정'),
    (0xb18, 'f32', 'fadeInMin', '판독 0x710080ed10'),
    (0xb1c, 'f32', 'fadeOutMin', '판독 0x710080ed10'),
    # --- Emission
    (0xb38, 'u8', 'hasEmitEnd', '판독 0x710081c0b8: 0 무한 방출, 1 start+duration 까지'),
    (0xb39, 'u8', 'isWorldGravity', '셰이더옵션 WORLD_GRAVITY'),
    (0xb3a, 'u8', 'isEmitDistEnabled', '판독 0x710081b784'),
    (0xb3b, 'u8', 'isWorldOrientedVelocity', '판독 0x710081e3e4'),
    (0xb3c, 'u32', 'emitStart', '판독(프레임)'),
    (0xb40, 'u32', 'emitTiming', '판독(자식: 부모 수명 %)'),
    (0xb44, 'u32', 'emitDuration', '판독(프레임)'),
    (0xb48, 'f32', 'emitRate', '판독'),
    (0xb4c, 'i32', 'emitRateRandom', '판독(%)'),
    (0xb50, 'i32', 'emitInterval', '판독: 간격 = interval+1+floor(u*intervalRandom)'),
    (0xb54, 'i32', 'emitIntervalRandom', '판독'),
    (0xb58, 'f32', 'positionRandom', '판독 0x710081e3e4'),
    (0xb5c, 'f32', 'emissionGravityScale', '데이터(정적 0xdc 와 같은 값), 소비 미확인'),
    (0xb6c, 'f32', 'emitDistUnit', '판독'),
    (0xb70, 'f32', 'emitDistMin', '판독'),
    (0xb74, 'f32', 'emitDistMax', '판독'),
    (0xb78, 'f32', 'emitDistMargin', '판독'),
    # --- Shape
    (0xb80, 'u8', 'volumeType', '판독: 점프표 0x710540fea8'),
    (0xb88, 'f32', 'sweepLongitude', '판독-부분(형상 함수가 읽음)'),
    (0xb8c, 'f32', 'sweepLatitude', '판독-부분'),
    (0xb90, 'f32', 'sweepStart', '판독-부분'),
    (0xb98, 'f32', 'caliberRatio', '판독-부분'),
    (0xba4, 'f32x3', 'volumeRadius', '판독-부분'),
    (0xbb0, 'f32x3', 'volumeFormScale', '판독 0x710081c0b8 -> 이미터+0x7f0'),
    # --- Particle
    (0xbe8, 'u8', 'infiniteLife', '판독 0x710081e3e4'),
    (0xbea, 'u8', 'billboardType', '셰이더옵션: 3 POLYGON_XY, 4 POLYGON_XZ'),
    (0xbeb, 'u8', 'rotType', '셰이더옵션: 4 YZX, 6 ZXY'),
    (0xbf8, 'i32', 'life', '판독(프레임)'),
    (0xbfc, 'i32', 'lifeRandom', '판독(%)'),
    (0xc00, 'f32', 'momentumRandom', '판독: m = 1 + r - 2*r*u'),
    (0xc4c, 'i32', 'shaderIndex', '데이터+셰이더옵션 일치'),
    # --- Velocity
    (0xcf4, 'f32', 'allDirectionVel', '판독 0x710081c0b8 -> 이미터+0x7cc'),
    (0xcf8, 'f32', 'designatedDirScale', '추정(이미터+0x7d8)'),
    (0xcfc, 'f32x3', 'designatedDir', '판독 0x710081e3e4'),
    (0xd08, 'f32', 'diffusionDirAngle', '판독: cos 균일 [1-a/90, 1]'),
    (0xd0c, 'f32', 'xzDiffusion', '판독'),
    (0xd10, 'f32x3', 'diffusionVel', '판독: + 난수표 벡터 * 값'),
    (0xd1c, 'f32', 'velRandom', '판독(%)'),
    (0xd20, 'f32', 'emitterVelInherit', '판독'),
    (0xd24, 'f32', 'emitterVelInheritMax', '판독: 상속 속도 길이 상한'),
    # --- Color / Scale
    (0xd3c, 'u8', 'color0Type', '셰이더옵션: 0 FIXED 1 RANDOM 2 ANIM'),
    (0xd3d, 'u8', 'color1Type', '셰이더옵션'),
    (0xd3e, 'u8', 'alpha0Type', '셰이더옵션'),
    (0xd3f, 'u8', 'alpha1Type', '셰이더옵션'),
    (0xd60, 'f32x3', 'particleScale', '추정(v53 순서, 무작위 % 바로 앞)'),
    (0xd6c, 'f32x3', 'particleScaleRandom', '판독(%): s*(1-r/100*u), 세 값이 같으면 같은 u'),
]


def read_field(d, bo, off, t):
    if t == 'f32':
        return f32(d, bo + off)
    if t == 'u32':
        return u32(d, bo + off)
    if t == 'i32':
        return struct.unpack_from('<i', d, bo + off)[0]
    if t == 'u8':
        return d[bo + off]
    if t == 'u16':
        return struct.unpack_from('<H', d, bo + off)[0]
    if t.startswith('f32x'):
        n = int(t[4:])
        return list(struct.unpack_from(f'<{n}f', d, bo + off))
    if t == 'key8':
        return [list(struct.unpack_from('<4f', d, bo + off + 16 * i)) for i in range(8)]
    raise ValueError(t)


def cmd_fields(v, want, out=None):
    res = {}
    for es, name, depth, parent, bo, em in emitters(v, want):
        rec = {'eset': es, 'depth': depth, 'parent': parent, 'off': hex(bo)}
        for off, t, fname, _why in FIELDS:
            val = read_field(v.d, bo, off, t)
            rec[fname] = [round(x, 6) if isinstance(x, float) else x for x in val] if isinstance(val, list) and val and not isinstance(val[0], list) else val
        res[f'{es}/{name}'] = rec
        print(f'== {es}/{name}')
        for off, t, fname, _why in FIELDS:
            print(f'  +{off:#05x} {fname:32s} {rec[fname]}')
    if out:
        json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- 재구현 (셰이더 판독 식, analysis/vfx/shader/p1940.vert)
def key_lerp(keys, n, t):
    """판독: 셰이더 키 보간. t < k0.t 이면 k0, 마지막 키 이후는 마지막 값, 그 사이 선형. 키 = [x, y, z, time]."""
    ks = keys[:max(n, 1)]
    if t < ks[0][3] or len(ks) == 1:
        return ks[0][:3]
    for a, b in zip(ks, ks[1:]):
        if a[3] <= t < b[3]:
            u = (t - a[3]) / (b[3] - a[3])
            return [a[i] + (b[i] - a[i]) * u for i in range(3)]
    return ks[-1][:3]


def motion_terms(t, air):
    """판독: 속도항 f(t), 중력항 g(t). air==1 이면 t, t^2/2."""
    import math
    if air == 1.0:
        return t, 0.5 * t * t
    at = air ** t
    f = (1.0 - at) / (1.0 - air)
    g = (t - (at - 1.0) / math.log(air)) / (1.0 - air)
    return f, g


def particle_pos(p0, v0, t, air, gdir, gscale, momentum=1.0):
    """로컬 위치(WORLD_GRAVITY 의 축 변환·이미터 행렬은 생략, 이미터 행렬이 항등일 때)."""
    f, g = motion_terms(t, air)
    return [p0[i] + momentum * (v0[i] * f + gdir[i] * gscale * g) for i in range(3)]


def rot_terms(t, regist):
    """판독: 회전 누적항. regist==1 이면 t, 0 이면 1(첫 프레임 값만), 그 밖 (1-r^t)/(1-r)."""
    if regist == 1.0:
        return t
    if regist == 0.0:
        return 1.0
    return (1.0 - regist ** t) / (1.0 - regist)


def cmd_sim(path, key, frames=None):
    e = json.load(open(path, encoding='utf-8'))[key]
    life = e['life']
    frames = frames or life
    v0 = [e['designatedDirScale'] * x for x in e['designatedDir']]
    print(f'# {key} life={life} lifeRandom={e["lifeRandom"]}% v0(local)={v0} gravity={e["gravityScale"]}*{e["gravityDir"]} air={e["airRegist"]}')
    print('frame  t/life  pos(x,y,z)                 scale(x,y,z)*particleScale       alpha0')
    for fr in range(frames + 1):
        tn = fr / life
        pos = particle_pos([0, 0, 0], v0, fr, e['airRegist'], e['gravityDir'], e['gravityScale'])
        sc = key_lerp(e['scaleKeys'], e['numScaleKeys'], tn) if e['numScaleKeys'] else [1, 1, 1]
        sc = [sc[i] * e['particleScale'][i] for i in range(3)]
        al = key_lerp(e['alpha0Keys'], e['numAlpha0Keys'], tn)[0] if e['alpha0Type'] == 2 else e['alpha0Keys'][0][0]
        print(f'{fr:5d}  {tn:6.3f}  ' + ' '.join(f'{x:8.4f}' for x in pos) + '   ' + ' '.join(f'{x:7.4f}' for x in sc) + f'   {al:7.4f}')


def cmd_selftest():
    ok = True

    def chk(label, got, exp, tol=1e-5):
        nonlocal ok
        r = abs(got - exp) <= tol
        ok &= r
        print(('OK  ' if r else 'FAIL'), label, round(got, 6), '' if r else f'(expected {exp})')
    f, g = motion_terms(10.0, 1.0)
    chk('air=1 속도항 = t', f, 10.0)
    chk('air=1 중력항 = t^2/2', g, 50.0)
    f2, g2 = motion_terms(10.0, 0.999999)
    chk('air->1 극한 연속(속도항)', f2, 10.0, 1e-3)
    chk('air->1 극한 연속(중력항)', g2, 50.0, 2e-2)
    f3, _ = motion_terms(3.0, 0.5)
    chk('air=0.5 t=3 속도항 = 1+0.5+0.25', f3, 1.75)
    keys = [[0.75, 1, 0.75, 0], [0.9185, 1.28, 0.9185, 0.11], [1.05, 1.45, 1.05, 0.33], [1.1, 0.9185, 1.1, 0.66], [1.1, 0, 1.1, 1.0]]
    chk('키 보간 시작 이전 = k0', key_lerp(keys, 5, -0.1)[1], 1.0)
    chk('키 보간 0.22 = k1..k2 중간', key_lerp(keys, 5, 0.22)[1], (1.28 + 1.45) / 2, 1e-4)
    chk('키 보간 끝 이후 = 마지막', key_lerp(keys, 5, 1.5)[1], 0.0)
    p = particle_pos([0, 0, 0], [0, 0.02, 0], 4, 1.0, [0, -1, 0], 0.005)
    chk('Splash y(t=4) = 0.02*4 - 0.005*8', p[1], 0.04)
    chk('rotateRegist 0.99 t=10', rot_terms(10, 0.99), (1 - 0.99 ** 10) / 0.01, 1e-4)
    # 수명 난수: L*(1 - floor(u*lr)/100), 정수로 자름
    L, lr = 14, 25
    lives = sorted({int(L * (1 - k / 100)) for k in range(lr)})
    chk('Splash 수명 최소(k=24) = int(14*0.76)', lives[0], 10)
    chk('Splash 수명 최대 = 14', lives[-1], 14)
    print('SELFTEST', 'PASS' if ok else 'FAIL')


def main():
    cmd = sys.argv[1]
    if cmd == 'selftest':
        cmd_selftest()
        return
    if cmd == 'sim':
        cmd_sim(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else None)
        return
    path = sys.argv[2]
    v = V.Vfxb(path)
    if cmd == 'raw':
        cmd_raw(v, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == 'stat':
        cmd_stat(v, [int(x, 16) for x in sys.argv[3:]])
    elif cmd == 'fields':
        args = [a for a in sys.argv[3:] if not a.startswith('--')]
        out = None
        if '--json' in sys.argv:
            out = sys.argv[sys.argv.index('--json') + 1]
            args = [a for a in args if a != out]
        cmd_fields(v, args, out)


if __name__ == '__main__':
    main()
