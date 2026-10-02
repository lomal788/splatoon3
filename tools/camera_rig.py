"""플레이어 3인칭 카메라 리그 재구현 (spl:PlayerCamera, vtable 0x7105633960, 객체 0x1978 B).

근거 (analysis/decomp/camera/batch1.c):
  0x71024d63f0  상수 블록 초기화 (this+0x179c~0x1864)
  0x71024d6598  리셋: FOV/near/far, 감도 → 회전 속도
  0x71024d6e84  피치 정규값 p(-1..1) → 주시점/카메라 위치 (기본 경로만 재현)
  0x71024e64f0  피치 각(도) → p 매핑 (스틱/자이로 공용)
  0x71024e0178  입력 → 속도 (yaw +0x14f8, pitch +0x1504) 일부

사용:
  camera_rig.py selftest
  camera_rig.py table          # p 별 리그 값 표
  camera_rig.py sens           # 감도 설정(-5..+5) 별 회전 속도
"""
import sys, math, argparse
import numpy as np

f32 = np.float32


def consts(alt=False):
    """0x71024d63f0. alt = (*0x7105791bd0 != 0 && [..]+0x143d0 != 0) 분기 [미확정: 의미]"""
    c = {
        0x179c: 55.0, 0x17a0: 7.2, 0x17a4: 6.8, 0x17a8: 4.0, 0x17ac: 2.25, 0x17b0: 2.25, 0x17b4: 2.75,
        0x17b8: 1.0, 0x17bc: 0.5, 0x17c0: 0.0, 0x17c4: 0.0, 0x17c8: 0.0, 0x17cc: 0.0,
        0x17d0: 60.0, 0x17d4: -7.5, 0x17d8: -75.0, 0x17dc: 0.2, 0x17e0: 60.0, 0x17e4: 7.2, 0x17e8: 6.8,
        0x17ec: 5.2, 0x17f0: 1.45, 0x17f4: 1.45, 0x17f8: 2.35, 0x17fc: 0.0, 0x1800: 0.5, 0x1804: 0.5,
        0x1808: 0.0, 0x180c: 0.0, 0x1810: 0.0, 0x1814: 20.0, 0x1818: 0.0, 0x181c: -60.0, 0x1820: 0.5,
        0x1824: 45.0, 0x1828: 0.1, 0x182c: 0.01, 0x1830: 0.1,
        0x184c: 0.0, 0x1850: 0.0, 0x1854: 0.0, 0x1858: 30.0, 0x185c: 0.0, 0x1864: 0.5,
    }
    if not alt:
        c.update({0x1834: 0.8, 0x1838: 0.65, 0x183c: 0.65, 0x1840: -1.25, 0x1844: -1.25, 0x1848: -1.0, 0x1860: -27.0})
    else:
        c.update({0x1834: 0.4, 0x1838: 0.25, 0x183c: 0.25, 0x1840: 0.25, 0x1844: 0.25, 0x1848: 0.5, 0x1860: -20.0})
    return {k: f32(v) for k, v in c.items()}


def bez3(p, down, mid, up, k):
    """0x71024d6e84 의 반복 패턴: p>0 → P0=mid, P1=mid+k(up-down), P2=P3=up
                                  p<=0 → s=-p, P0=mid, P1=mid-k(up-down), P2=P3=down"""
    p = f32(p)
    tan = f32(f32(up - down) * k)
    if p <= 0:
        s = f32(-p); a = f32(1 + p)
        b1 = f32(f32(p * f32(-3.0)) * a)          # 3s(1-s)
        return f32(f32(f32(p * p) * s) * down + f32(b1 * s) * down + f32(a * a * a) * mid + f32(a * b1) * f32(mid - tan))
    a = f32(1 - p)
    b1 = f32(f32(p * f32(3.0)) * a)
    return f32(f32(p * p * p) * up + f32(b1 * p) * up + f32(a * a * a) * mid + f32(a * b1) * f32(mid + tan))


def rig_values(p, C, mode=0):
    """기본 경로 (this+0x1764 == 0, 특수 블렌드 가중치 0x152c/0x15b8/0x1538/0x1544/0x15a0/0x15ac/0x15cc 모두 0).
    반환 H(주시점 높이), F(주시점 전방), D(카메라 거리), S(시선수직 위 오프셋)"""
    if mode == 1:
        if p <= 0:
            a = 1 + p; b = p * -3 * a; c3 = -p * p * p; d = b * -p; e = a * a * a; g = a * b
            return 0.0, 4.0, 15.0, c3 * 24 + d * 24 + e * 22 + g * 24
        a = 1 - p; b = p * 3 * a
        return 0.0, 4.0, 15.0, p ** 3 * 20 + b * p * 20 + a ** 3 * 22 + a * b * 20
    k = C[0x17dc]
    H = bez3(p, C[0x17ac], C[0x17b0], C[0x17b4], k)
    F = bez3(p, C[0x17b8], C[0x17bc], C[0x17c0], k)
    D = bez3(p, C[0x17a0], C[0x17a4], C[0x17a8], k)
    S = bez3(p, C[0x17c4], C[0x17c8], C[0x17cc], k)
    return float(H), float(F), float(D), float(S)


def elevation_deg(p, C, mode=0, blend1680=0.0, v1688=0.0):
    """0x71024d6e84 끝부분: 회전각 = A + |p|(B-A), 실제 회전은 -그 값 (카메라가 위로 = +)
    A=this+0x15e0(=0x17d4 -7.5), B=p>0 ? this+0x15e4(=0x17d0 60) : this+0x15dc(=0x17d8 -75)"""
    if mode == 1:
        A = 0.0; B = 20.0 if p > 0 else -25.0
    else:
        A = float(C[0x17d4]); Bu = float(C[0x17d0]); Bd = float(C[0x17d8])
        if blend1680 > 0:
            A = A + blend1680 * (-(v1688 + 30.0) - A)
            Bu = Bu + blend1680 * (-15.0 - Bu)
            Bd = Bd + blend1680 * (-75.0 - Bd)
        B = Bu if p > 0 else Bd
    return A + abs(p) * (B - A)


def camera_pose(player_pos, yaw_dir, p, C, extra_h=0.0, mode=0):
    """player_pos = this+0x120 (플레이어 위치), yaw_dir = this+0x1a4 (수평 시선, 단위벡터)
    extra_h = player+0xcf0 (형태별 추가 높이) [미확정 의미]"""
    H, F, D, S = rig_values(p, C, mode)
    H += extra_h
    dx, dy, dz = yaw_dir
    px, py, pz = player_pos
    tgt = np.array([F * dx + px, F * dy + H + py, F * dz + pz])
    cam = tgt - D * np.array([dx, dy, dz])
    # S: 시선 수직 위방향 dir×(up×dir) 성분
    cam = cam + S * np.array([-dx * dy, dx * dx + dz * dz, -dy * dz])
    v = cam - tgt
    ax = np.array([-v[2], 0.0, v[0]])
    n = np.linalg.norm(ax)
    if n > 0:
        ax /= n
        th = math.radians(-elevation_deg(p, C, mode))
        # Rodrigues
        v = v * math.cos(th) + np.cross(ax, v) * math.sin(th) + ax * np.dot(ax, v) * (1 - math.cos(th))
        cam = tgt + v
    return tgt, cam


def pitch_angle_to_p(angle, gk=0.0, handheld_flag=False, off_a=0.0, off_b=0.0, stick=True):
    """0x71024e64f0(param_1=gk, param_2=angle, param_3=off_a, param_4=off_b, param_5=!flag, param_6=stick, out)
    반환 (p, 보정량 out). angle 은 this+0x150c + (-75 [+10 if flag])"""
    a = max(angle, -180.0)
    f7 = (3.0 if gk >= 0 else 11.0) * gk - 103.0
    f8 = (0.0) * gk - 75.0
    f11 = (-6.0 if gk >= 0 else -18.0) * gk - 31.0
    if handheld_flag:
        f7 += 10; f8 += 10; f11 += 10
    out = 0.0
    if a >= -165.0:
        lo = f7 + off_a - off_b
        if a < lo:
            out = (lo - a) if (lo - 165.0) * 0.5 <= a else (a + 165.0)
            return -1.0, out
        mid = f8 - off_b
        if a < mid:
            f4 = 0.0 if gk >= 0 else -6.0
            f11b = -2.0 if gk >= 0 else -4.0
            f5 = f11b
            f6 = -gk if gk >= 0 else gk * -3.0
            span = mid - lo
            f9 = f11b * gk + 10.0
            f11c = f4 * gk + 0.0
            if stick:
                f9 = f6 + 7.0
                f11c = f5 * gk + 10.0
            t = (a - lo) / span if span != 0 else 0.0
            P0, P1, P2, P3 = -1.0, f11c / span - 1.0, -f9 / span, 0.0
        else:
            hi = f11 + off_a - off_b
            if a < hi:
                f7b = (-4.0 if gk >= 0 else -8.0) * gk + 26.0
                f11d = (-4.0 if gk >= 0 else -6.0)
                f10 = 0.0
                f11e = f10 * gk
                if stick:
                    f7b = f11d * gk + 18.0
                    f11e = 8.0 - (gk + gk)
                span = hi - mid
                t = (a - mid) / span if span != 0 else 0.0
                P0, P1, P2, P3 = 0.0, f7b / span, 1.0 - f11e / span, 1.0
            elif a < 60.0:
                out = (hi - a) if not ((hi + 60.0) * 0.5 <= a) else (a - 60.0)
                return 1.0, out
            else:
                t = (a - 60.0) / 135.0
                P0, P1, P2, P3 = 1.0, 1.0, -1.0, -1.0
    else:
        t = (a + 300.0) / 135.0
        P0, P1, P2, P3 = 1.0, 1.0, -1.0, -1.0
    u = 1 - t
    return P3 * t ** 3 + P2 * 3 * t * t * u + P1 * 3 * t * u * u + P0 * u ** 3, out


def sens_speeds(setting_int):
    """세이브값(0..20, 기본 10) → k=clamp((v-10)/10,-1,1) [판독 0x71024d6598]
    yaw 기본 속도 = 4 + k*(k>=0?3.0:1.6) 도/프레임, pitch = 1.8 + (k>=0?k:0.8k) 도/프레임"""
    k = max(-1.0, min(1.0, (setting_int - 10) / 10.0))
    yaw = 4.0 + k * (3.0 if k >= 0 else 1.6)
    yaw_slow = 2.4 + k * (1.8 if k >= 0 else 0.96)
    pitch = 1.8 + (k if k >= 0 else k * 0.8)
    return k, yaw, yaw_slow, pitch


def stick_response(m, gyro_on):
    """0x71024e0178: 크기 m(0..1) → bias(m, 0.8 or 0.4) = m^(-log2 b)"""
    b = 0.4 if gyro_on else 0.8
    if m < 0.001:
        return 0.0
    return math.exp(math.log(m) * math.log(b) * -1.442695)


def cmd_table():
    C = consts()
    print("| p | H 주시점높이 | F 주시점전방 | D 거리 | S 위오프셋 | 고각(도) | 카메라 높이(플레이어 기준) | 수평거리 |")
    print("|---|---|---|---|---|---|---|---|")
    for p in [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]:
        H, F, D, S = rig_values(p, C)
        tgt, cam = camera_pose((0, 0, 0), (0, 0, 1), p, C)
        print(f"| {p:+.2f} | {H:.4f} | {F:.4f} | {D:.4f} | {S:.4f} | {-elevation_deg(p, C):+.2f} | {cam[1]:.4f} | {-cam[2]:.4f} |")


def cmd_sens():
    print("| 설정(UI 추정) | 세이브값 | k | yaw 도/프레임 | yaw(느린 블렌드 끝) | pitch 도/프레임 |")
    print("|---|---|---|---|---|---|")
    for v in range(0, 21, 2):
        k, y, ys, pt = sens_speeds(v)
        print(f"| {(v - 10) / 2:+.1f} | {v} | {k:+.1f} | {y:.3f} | {ys:.3f} | {pt:.3f} |")


# 대체 리그 가중치(0x71024d9ae8 2594~3060행): 켜진 쪽 비율 누산기 r_on += inc(상한 cap), 꺼진 쪽 누산기는 0.
# 가중치 w += r*(목표 - w). 목표 1(켜짐) / 0(꺼짐). (inc, cap) 은 켜짐·꺼짐에 각각 따로.
ALT_RIG = {
    # 이름: (켜짐 inc, 켜짐 cap, 꺼짐 inc, 꺼짐 cap)
    "+0x152c NiceBall 들기": (0.2, 0.2, 0.2, 0.2),
    "+0x1538 Jetpack": (0.2, 0.2, 0.2, 0.2),
    "+0x1544 IkuraShoot": (0.2, 0.2, 0.2, 0.2),
    "+0x15a0 다운(+0xe0c>=1)": (0.2, 0.005, 0.2, 0.005),
    "+0x15ac (this+0x1918)": (0.044, 0.065, 0.044, 0.065),
    "+0x15cc Pipeline": (0.044, 0.065, 0.044, 0.065),
    "+0x15b8 GrindRail(지연 카운터 0 가정)": (0.2, 0.2, 0.005, 0.2),
    "+0x1764 오징어(접지)": (0.025, 0.2, 0.025, 0.2),
    "+0x1764 오징어(공중 4f+)": (0.001, 0.2, 0.001, 0.2),
}


def alt_rig_frames(inc, cap, thr=0.9, w0=0.0, target=1.0, max_frames=5000):
    r = 0.0; w = w0
    for f in range(1, max_frames + 1):
        r = min(r + inc, cap)
        w = w + r * (target - w)
        if abs(target - w) <= abs(target - w0) * (1 - thr):
            return f, w
    return None, w


def cmd_altrig():
    print("| 가중치 | 켜짐 0→0.9 프레임 | 꺼짐 1→0.1 프레임 |")
    print("|---|---|---|")
    for k, (i1, c1, i0, c0) in ALT_RIG.items():
        f1, _ = alt_rig_frames(i1, c1)
        f0, _ = alt_rig_frames(i0, c0, w0=1.0, target=0.0)
        print(f"| {k} | {f1} | {f0} |")


def cmd_selftest():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    C = consts()
    chk("p=0 거리 6.8", abs(rig_values(0, C)[2] - 6.8) < 1e-6)
    chk("p=-1 거리 7.2", abs(rig_values(-1, C)[2] - 7.2) < 1e-5)
    chk("p=+1 거리 4.0", abs(rig_values(1, C)[2] - 4.0) < 1e-5)
    chk("p=0 높이 2.25", abs(rig_values(0, C)[0] - 2.25) < 1e-6)
    # C1 연속: p=0 좌우 미분 동일
    e = 1e-3   # f32 반올림 때문에 너무 작은 e 는 쓰지 않는다
    for i, nm in enumerate("HFDS"):
        dl = (rig_values(0, C)[i] - rig_values(-e, C)[i]) / e
        dr = (rig_values(e, C)[i] - rig_values(0, C)[i]) / e
        chk(f"{nm} p=0 기울기 연속 ({dl:.4f} vs {dr:.4f})", abs(dl - dr) < 3e-2)
    # 끝점 기울기 0
    d1 = (rig_values(1, C)[2] - rig_values(1 - e, C)[2]) / e
    chk(f"D p=1 끝 기울기 0 ({d1:.5f})", abs(d1) < 1e-2)
    # 고각
    chk("p=0 고각 +7.5", abs(-elevation_deg(0, C) - 7.5) < 1e-9)
    chk("p=1 고각 -60", abs(-elevation_deg(1, C) + 60) < 1e-9)
    chk("p=-1 고각 +75", abs(-elevation_deg(-1, C) - 75) < 1e-9)
    tgt, cam = camera_pose((0, 0, 0), (0, 0, 1), 0.0, C)
    chk("p=0 카메라-주시점 거리 = D", abs(np.linalg.norm(cam - tgt) - 6.8) < 1e-4)
    chk("p=0 카메라가 주시점보다 위", cam[1] > tgt[1])
    # 피치각→p (스틱, gk=0): 상대각 s=-28→-1, 0→0, +44→+1, 단조 증가
    vals = [pitch_angle_to_p(s - 75.0)[0] for s in np.linspace(-28, 44, 145)]
    chk("s=-28→-1", abs(pitch_angle_to_p(-103.0)[0] + 1) < 1e-9)
    chk("s=0→0", abs(pitch_angle_to_p(-75.0)[0]) < 1e-9)
    chk("s=+44→1", abs(pitch_angle_to_p(-31.0 + 1e-9)[0] - 1) < 1e-6 or pitch_angle_to_p(-31.0)[0] == 1.0)
    chk("단조 증가", all(b >= a - 1e-9 for a, b in zip(vals, vals[1:])))
    chk("범위 밖 보정량(s=-40 → +12)", abs(pitch_angle_to_p(-115.0)[1] - 12.0) < 1e-9)
    chk("감도 0 → yaw 4, pitch 1.8", sens_speeds(10)[1:] == (4.0, 2.4, 1.8))
    chk("감도 +5 → yaw 7, pitch 2.8", sens_speeds(20)[1] == 7.0 and abs(sens_speeds(20)[3] - 2.8) < 1e-9)
    chk("감도 -5 → yaw 2.4, pitch 1.0", abs(sens_speeds(0)[1] - 2.4) < 1e-9 and abs(sens_speeds(0)[3] - 1.0) < 1e-9)
    chk("스틱 응답 m=0.5 (자이로 off) = 0.5^0.3219", abs(stick_response(0.5, False) - 0.5 ** 0.321928) < 1e-5)
    chk("대체 리그 rate 0.2 고정: 0→0.9 11프레임", alt_rig_frames(0.2, 0.2)[0] == 11)
    chk("다운 리그 rate 0.005: 0→0.9 460프레임", alt_rig_frames(0.2, 0.005)[0] == 460)
    print("ALL PASS" if ok else "SOME FAIL")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["selftest", "table", "sens", "altrig"])
    a = ap.parse_args()
    {"selftest": cmd_selftest, "table": cmd_table, "sens": cmd_sens, "altrig": cmd_altrig}[a.cmd]()
