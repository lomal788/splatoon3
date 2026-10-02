"""도색 스탬프 픽셀 셰이더(Hoian_Proc.sharcb PaintOverpaint) 재구현 + 합성 테스트.

근거: analysis/shader/hoian_proc/PaintOverpaint__*.pixel.glsl (Ryujinx 역번역),
      CPU 상수 0x7102c188b4 (cTeamAlphaTestThreshold=0.3, cConvex=0.99, cColor=팀 원-핫, cTeam=팀 번호,
      cAlpha=요청 바이트/255), 변형 선택 idx = MASK | ALPHA_TEST<<1 | ERASE<<2 | WRITE_NORMAL<<3.

텍셀 dst = (R,G,B,A) — R/G/B = 팀 0/1/2(Alpha/Bravo/Charlie) 잉크량, A = cColor.w(=0) 로 덮이는 별도 채널.
사용: .venv/Scripts/python web/tools/shader_paint_overpaint.py
"""
import numpy as np

F32 = np.float32
TH = F32(0.3)          # 0x3e99999a
CONVEX = F32(0.99)     # 0x3f7d70a4
K105 = F32(1.04999995)


def color_of(team):
    c = np.zeros(4, F32)
    if 0 <= team < 3:
        c[team] = 1.0
    return c


def mode_variant(mode, has_height_tex=False):
    """0x7102c188b4: 표 0x7104aa2b78 = [2,2,2,0,2,2,2,2,0,0,0,2] (모드 0..11, 그 외 0)."""
    tbl = [2, 2, 2, 0, 2, 2, 2, 2, 0, 0, 0, 2]
    alpha = (tbl[mode] if 0 <= mode < 12 else 0) != 0
    erase = (mode & ~1) == 10
    normal = mode == 8
    return dict(mask=has_height_tex, alpha_test=alpha, erase=erase, write_normal=normal)


def overpaint(dst, ink_raw, c_alpha, team, alpha_test=True, erase=False, write_normal=False,
              height=None, height_range=None):
    """한 텍셀. 반환: 새 값(4) 또는 None(discard = 기존 값 유지)."""
    dst = np.asarray(dst, F32)
    col = color_of(team)
    if height is not None and (height < height_range[0] or height > height_range[1]):
        return None
    ink = F32(ink_raw) * F32(c_alpha)
    if ink <= 0:
        return None
    if erase:
        out = np.clip(dst - ink, 0, 1).astype(F32)
        if alpha_test and (out[:3] >= TH).any():
            return None
        return out
    if write_normal:
        m = dst[:3].max()
        if m < TH + F32(0.3):
            return None
        if not (0 <= team < 3) or dst[team] < m:
            # 원본: cTeam 이 0/1/2 가 아니면 세 검사를 모두 통과(쓰기 허용). 여기서는 0..2 만 다룸.
            if 0 <= team < 3:
                return None
        out = np.maximum(F32(ink_raw) * ink * col + dst * (1 - ink), TH * col * K105).astype(F32)
        return out
    s = np.clip(dst - TH, 0, 1)
    dec = s * (1 - CONVEX)                       # fma(s, -convex, s)
    d2 = dst * (1 - dec * col)                   # fma(d, -(dec*c), d)
    new = d2 + ink * (col - d2)                  # mix(d2, c, ink)
    keep = (new[:3] < TH * K105).all()
    rgb = new[:3].copy()
    for ch in range(3):
        if dst[ch] > TH and keep:
            rgb[ch] = dst[ch]
    out = np.array([rgb[0], rgb[1], rgb[2], new[3]], F32)
    if alpha_test:
        mx = out[:3].max()
        if 0 <= team < 3 and (out[team] < TH or out[team] < mx):
            return None
    return out


def owner(t):
    """표시·판정용 소유 팀: 채널 >= 0.3 이면서 최대인 팀(셰이더 알파 테스트와 같은 조건) — 판정 규칙의 CPU 대응은 [추정]."""
    m = t[:3].max()
    if m < TH:
        return -1
    return int(np.argmax(t[:3]))


def show(name, v):
    print(f'  {name:<46} ->', 'discard' if v is None else np.round(v, 4).tolist(), '' if v is None else f'owner={owner(v)}')


def main():
    z = np.zeros(4, F32)
    print('A. 빈 텍셀에 팀0 스탬프 (알파 테스트 켬, 모드 0)')
    for ink in (1.0, 0.5, 0.31, 0.3, 0.29, 0.1):
        show(f'ink={ink}', overpaint(z, ink, 1.0, 0))
    print('B. 팀0이 1.0 칠한 텍셀에 팀1 덧칠')
    full0 = np.array([1, 0, 0, 0], F32)
    for ink in (1.0, 0.6, 0.4, 0.2):
        show(f'ink={ink}', overpaint(full0, ink, 1.0, 1))
    print('C. 약하게 칠해진 텍셀(팀0 0.35)에 팀1 약한 잉크 0.2 (keep 규칙)')
    show('team1 ink 0.2', overpaint(np.array([0.35, 0, 0, 0], F32), 0.2, 1.0, 1))
    show('team1 ink 0.2 (알파 테스트 끔)', overpaint(np.array([0.35, 0, 0, 0], F32), 0.2, 1.0, 1, alpha_test=False))
    print('D. 같은 팀 반복(감쇠: s*(1-convex) 만큼 자기 채널 소폭 감소 후 보간)')
    t = np.array([0.8, 0, 0, 0], F32)
    show('team0 ink 0.05 on 0.8', overpaint(t, 0.05, 1.0, 0))
    print('E. 지우기(모드 10: 알파 테스트 없음 / 11: 있음)')
    show('erase 0.5 on (1,0,0) mode10', overpaint(full0, 0.5, 1.0, 0, alpha_test=False, erase=True))
    show('erase 0.5 on (1,0,0) mode11', overpaint(full0, 0.5, 1.0, 0, alpha_test=True, erase=True))
    show('erase 0.8 on (1,0,0) mode11', overpaint(full0, 0.8, 1.0, 0, alpha_test=True, erase=True))
    print('F. 모드 → 변형')
    for m in range(13):
        print('  mode', m, mode_variant(m))
    # 자기 검사
    assert overpaint(z, 0.29, 1.0, 0) is None
    assert owner(overpaint(z, 0.31, 1.0, 0)) == 0
    assert owner(overpaint(full0, 0.6, 1.0, 1)) == 1
    assert overpaint(full0, 0.4, 1.0, 1) is None
    print('assert OK')


if __name__ == '__main__':
    main()
