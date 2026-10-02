"""MeterAction 사용자 셰이더(SuperGaugeTV_00 bgsh/MeterAction.glsl) 재구현 + 검증.

원본 GLSL 소스를 그대로 옮긴 식이다(analysis/shader 문서 참조).
  F0,F1,F2 = __CUS_Float_0..2 (nwExUserDataFloat_0..2)
  p = uv*2-1 ; t = 1 - (atan2(p.x, p.y) + pi) / (2 pi)
  arc   = 1 - smoothstep(mix(-0.005, 1, F0), mix(-0.005, 1, F0) + 0.005, t)
  d     = distance(uv, (0.5,0.5))
  outer = smoothstep(F2 + 0.005, F2, d)
  rin   = F2 - mix(0, F2, F1) ; inner = smoothstep(rin, rin + 0.005, d)
  a     = arc * tex.a * outer * inner
  out   = mix(black, white, vec4(tex.rgb, a)) * vertexColor

사용: .venv/Scripts/python web/tools/shader_meteraction.py   (표 출력 + analysis/shader/meteraction_*.png)
"""
import math
import os

import numpy as np
from PIL import Image

ROOT = r'C:/dev/splatoon3'


def smoothstep(e0, e1, x):
    # GLSL smoothstep: e0 > e1 도 정의대로 계산(분모 음수)
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def meter_alpha(u, v, f0, f1=1.0, f2=1.0, tex_a=1.0):
    px, py = u * 2.0 - 1.0, v * 2.0 - 1.0
    t = 1.0 - (np.arctan2(px, py) + math.pi) / (2.0 * math.pi)
    e0 = (1.0 - f0) * -0.005 + f0 * 1.0
    arc = 1.0 - smoothstep(e0, e0 + 0.005, t)
    d = np.hypot(u - 0.5, v - 0.5)
    outer = smoothstep(f2 + 0.005, f2, d)
    rin = f2 - f2 * f1
    inner = smoothstep(rin, rin + 0.005, d)
    return arc * tex_a * outer * inner


def clock_of(u, v):
    """화면 좌표(v 아래로 증가)에서 시계 방향 각도(12시=0도)."""
    return (math.degrees(math.atan2(u - 0.5, -(v - 0.5))) + 360.0) % 360.0


def main():
    print('표 1. 시계 위치(반지름 0.4)별 표시 여부 (F1=F2=1)')
    pts = {'12시': (0.5, 0.1), '1시반': (0.5 + 0.283, 0.5 - 0.283), '3시': (0.9, 0.5), '6시': (0.5, 0.9),
           '9시': (0.1, 0.5), '10시반': (0.5 - 0.283, 0.5 - 0.283)}
    for f0 in (0.0, 0.125, 0.25, 0.5, 0.75, 1.0):
        row = []
        for k, (u, v) in pts.items():
            a = float(meter_alpha(np.float64(u), np.float64(v), f0))
            row.append(f'{k}={a:.2f}')
        print(f'  F0={f0:<5}', ' '.join(row))
    # 경계 각도: F0 마다 alpha 0.5 가 되는 시계 각도
    print('표 2. F0 → 드러난 호의 끝 각도(12시 기준 시계 방향, 반지름 0.4)')
    angs = np.linspace(0, 360, 36001)[:-1]
    us = 0.5 + 0.4 * np.sin(np.radians(angs))
    vs = 0.5 - 0.4 * np.cos(np.radians(angs))
    for f0 in (0.1, 0.25, 0.5, 0.75):
        a = meter_alpha(us, vs, f0)
        vis = angs[a > 0.5]
        print(f'  F0={f0}: 보이는 각도 {vis.min():.2f}..{vis.max():.2f}도 (기대 0..{f0 * 360:.1f})')
    print('표 3. F1/F2 (반지름 방향 마스크, 12시 방향 v 변화)')
    for f1, f2 in ((1.0, 1.0), (0.5, 0.5), (0.2, 0.45)):
        vs2 = np.linspace(0.5, 0.0, 501)
        a = meter_alpha(np.full_like(vs2, 0.5), vs2, 1.0, f1, f2)
        d = 0.5 - vs2
        vis = d[a > 0.5]
        print(f'  F1={f1} F2={f2}: 보이는 반지름 {vis.min():.3f}..{vis.max():.3f} (기대 {f2 * (1 - f1):.3f}..{min(f2, 0.5):.3f})')
    # 렌더(GaugeSp_00^s 텍스처 사용)
    src = ROOT + '/analysis/ui/tex/SuperGaugeTV_00/GaugeSp_00^s.png'
    if os.path.exists(src):
        img = np.asarray(Image.open(src).convert('RGBA')).astype(np.float64) / 255.0
        h, w = img.shape[:2]
        vv, uu = np.mgrid[0:h, 0:w]
        uu = (uu + 0.5) / w
        vv = (vv + 0.5) / h
        # BC4(^s) 단일 채널: 레이아웃 재질 흑/백 보간의 입력. 알파 채널이 없으면 R을 알파로 본다.
        tex_a = img[..., 3] if img[..., 3].min() < 1.0 else img[..., 0]
        tiles = []
        for f0 in (0.1875, 0.375, 0.5625, 0.75):
            a = meter_alpha(uu, vv, f0, tex_a=tex_a)
            rgb = np.zeros((h, w, 3))
            rgb[...] = (1.0, 0x5d / 255.0, 0.0)
            tile = np.dstack([rgb, a])
            tiles.append((tile * 255).astype(np.uint8))
        out = ROOT + '/analysis/shader/meteraction_gauge.png'
        Image.fromarray(np.concatenate(tiles, axis=1), 'RGBA').save(out)
        print('렌더:', out, '(F0 = 0.1875, 0.375, 0.5625, 0.75 = 게이지 25/50/75/100%)')


if __name__ == '__main__':
    main()
