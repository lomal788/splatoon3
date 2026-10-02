"""대전 미니맵(슈퍼점프 맵) 카메라 데이터와 정사영 범위 재구현.

근거(판독): spl::MiniMap 슬롯8 초기화 0x7102263214
  - 스테이지 SceneComponent/VersusCamera/<stage>.spl__VersusCameraParam.MiniMapCamera
    → game__CameraPoserFixedParam (없으면 Bootup 의 Gyml/VersusMiniMapDefault)
  - CameraPoserFixedParam(리플렉션 0x710100d3f0): +0x38 Far 10000, +0x3c FovY 45, +0x40 Near 0.1,
    +0x44 Pos, +0x50 Rot, +0x5c IsDofEnabled
  - k = Pos.Y * tan(FovY) / halfH   (tan 은 sead 사인표 0x7104aa5b5c 의 sin/cos 비; FovY 전체 각)
    정사영: top = Pos.Z + halfH*k, bottom = Pos.Z - halfH*k, left = Pos.X - halfW*k, right = Pos.X + halfW*k,
            near = Near - 100, far = Far
    xlink 전역 속성 MiniMapScale = 0.24 / k
  - halfW/halfH = 렌더 레이어 5(MiniMap) 뷰포트 (x1-x0)/2, (y1-y0)/2  ← 실행 시 값, 여기서는 인자로 받음 [미확정]

사용:
  ui_minimap.py table [--half 960 540]     # Vss_* 스테이지별 미니맵 카메라와 범위
  ui_minimap.py selftest
  ui_minimap.py cam [--rot 25 30] [--posy 70] [--g 0 0] [--flip]   # 맵 카메라 기저(0x7102264240 698~930행 재구현)
"""
import sys, math, glob, os, json, struct, argparse
from pathlib import Path

ROOT = Path(r"C:/dev/splatoon3")
sys.path.insert(0, str(ROOT / "web/tools"))
import spl_data as S  # noqa: E402

DEFAULTS = dict(Far=10000.0, FovY=45.0, Near=0.1, Pos=(0.0, 0.0, 0.0), Rot=(0.0, 0.0, 0.0))


def sead_tan_deg(deg):
    """0x7102263214 의 tan: u = deg * 11930465 (2^32/360), 표 0x7104aa5b5c 항목 (sin, dsin, cos, dcos) 선형 보간 비."""
    img = (ROOT / "extracted/exefs/main.img").read_bytes()
    t = 0x7104aa5b5c - 0x7100000000
    u = int(deg * 11930465.0) & 0xFFFFFFFF
    i = (u >> 24) & 0xFF
    fr = (u & 0xFFFFFF) * 5.9604645e-08
    a, b, c, d = struct.unpack_from("<4f", img, t + i * 16)
    return (a + b * fr) / (c + fr * d)


def cat(pack, inner):
    import subprocess
    out = subprocess.run([sys.executable, str(ROOT / "web/tools/spl_data.py"), "cat", pack, inner],
                         capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip().startswith("{") else None


def poser_values(d):
    v = dict(DEFAULTS)
    if d:
        for k in ("Far", "FovY", "Near"):
            if k in d:
                v[k] = float(d[k])
        for k in ("Pos", "Rot"):
            if k in d:
                v[k] = tuple(float(d[k].get(a, 0.0)) for a in "XYZ")
    return v


def extents(v, half_w, half_h):
    k = v["Pos"][1] * sead_tan_deg(v["FovY"]) / half_h
    return dict(k=k, top=v["Pos"][2] + half_h * k, bottom=v["Pos"][2] - half_h * k,
                left=v["Pos"][0] - half_w * k, right=v["Pos"][0] + half_w * k,
                near=v["Near"] - 100.0, far=v["Far"], MiniMapScale=0.24 / k)


def stage_rows():
    rows = []
    default = cat(str(ROOT / "extracted/romfs/Pack/Bootup.Nin_NX_NVN.pack.zs"),
                  "Gyml/VersusMiniMapDefault.game__CameraPoserFixedParam.bgyml")
    for p in sorted(glob.glob(str(ROOT / "extracted/romfs/Pack/Scene/Vss_*.pack.zs"))):
        st = os.path.basename(p).split(".")[0]
        names = S.sarc(S.load(p))
        vc = f"SceneComponent/VersusCamera/{st}.spl__VersusCameraParam.bgyml"
        src, d = "default", default
        if vc in names:
            c = cat(p, vc)
            ref = (c or {}).get("MiniMapCamera", "")
            if ref:
                inner = ref.replace("Work/", "").replace(".gyml", ".bgyml")
                if inner in names:
                    d, src = cat(p, inner), inner
        rows.append((st, src, poser_values(d)))
    return rows


def cmd_table(a):
    hw, hh = a.half
    print(f"뷰포트 반폭/반높이 가정 = {hw}, {hh} (원본 실행 값 미확정)")
    print("| 스테이지 | 출처 | Pos | Rot(X 기울기, Y 방향) | FovY | 반높이(월드) | 반폭(월드) | MiniMapScale |")
    print("|---|---|---|---|---|---|---|---|")
    for st, src, v in stage_rows():
        e = extents(v, hw, hh)
        print(f"| {st} | {os.path.basename(src)} | {v['Pos']} | {v['Rot'][:2]} | {v['FovY']} | "
              f"{(e['top'] - e['bottom']) / 2:.2f} | {(e['right'] - e['left']) / 2:.2f} | {e['MiniMapScale']:.5f} |")


def sead_sincos_deg(deg):
    """각(도) → (sin, cos): 32비트 각 단위 u = rad*6.8356525e8, 표 0x7104aa5b5c (sin, dsin, cos, dcos) 선형 보간."""
    img = (ROOT / "extracted/exefs/main.img").read_bytes()
    t = 0x7104aa5b5c - 0x7100000000
    u = int(math.radians(deg) * 6.8356525e+08) & 0xFFFFFFFF
    i = (u >> 24) & 0xFF
    fr = (u & 0xFFFFFF) * 5.9604645e-08
    a, b, c, d = struct.unpack_from("<4f", img, t + i * 16)
    return a + b * fr, c + fr * d


def map_camera(rot_x, rot_y, pos_y, g1=0.0, g2=0.0, flip=False, base=(0.0, -1.0, 0.0)):
    """spl::MiniMap 갱신 0x7102264240 698~930행 식을 그대로 옮김(평활 전 목표값).
    base = +0xbb0..+0xbb8 (생성자 0x7102262994 가 (0, -1, 0)으로 두고 다른 writer 없음).
    g1 = PlayerCamera+0x16f4, g2 = +0x1704 (자이로 꺼짐·관전이면 0). 반환: pos(+0xb48), up(+0xb54), at(+0xb60)."""
    X, Y, Z = base
    cl = lambda v: max(-70.0, min(70.0, v))
    tA = cl(g2 * -180.0 * 0.07)
    tB = cl(g1 * -180.0 * -0.07)
    yaw = math.radians(rot_y) + (math.pi if flip else 0.0)
    c, s = math.cos(yaw), math.sin(yaw)
    S1, C1 = sead_sincos_deg(tA - rot_x)
    S2, C2 = sead_sincos_deg(tB)
    f80 = -c; f61 = -s
    f89x = g1 * 12.0 + X
    f60 = f80; f65 = 0.0
    f82z = g2 * 5.0 + Z
    f75 = -f61
    f81 = f61 * f82z + f89x * f60
    f84 = -f61 * f89x + f80 * f82z
    f86 = f81
    f85 = (f61 * f60) - f61 * f80
    f94 = Y
    f92 = f84
    f90 = pos_y + f94
    f88 = (f60 * f86 + f65 * f90) - f61 * f92
    f91, f79 = S1, C1
    f93 = (f61 * f75 - f80 * f60) * f91 + (f65 * f85 - f65 * f85 * f79)
    f78 = f91 * (f86 * f75 - f60 * f92) + f65 * f88 + f79 * (f90 - f65 * f88)
    f83 = f91 * (f65 * f92 + f61 * f90) + f60 * f88 + f79 * (f86 - f60 * f88)
    f87 = (f80 * f65) * f91 + f60 * f85 + (f61 - f60 * f85) * f79
    f82 = f91 * (f60 * f90 - f65 * f86) + f88 * f75 + f79 * (f92 - f88 * f75)
    f92b = (-f61 * f65) * f91 + f85 * f75 + (f80 - f85 * f75) * f79
    f95, f89 = S2, C2
    g75 = f80 * f82 + f61 * f83
    g85 = f80 * f92b + f61 * f87
    p_y = f95 * (f80 * f83 - f61 * f82) + f89 * f78
    p_z = f95 * (f61 * f78) + f80 * g75 + f89 * (f82 - f80 * g75)
    u_x = f95 * (-f80 * f93) + f61 * g85 + f89 * (f87 - f61 * g85)
    p_x = f95 * (-f80 * f78) + f61 * g75 + f89 * (f83 - f61 * g75)
    u_y = f95 * (f80 * f87 - f61 * f92b) + f89 * f93
    u_z = f95 * (f61 * f93) + f80 * g85 + f89 * (f92b - f80 * g85)
    n = math.sqrt(u_x * u_x + u_y * u_y + u_z * u_z)
    return (p_x, p_y, p_z), (u_x / n, u_y / n, u_z / n), (f81, f94, f84)


def cmd_cam(a):
    pos, up, at = map_camera(a.rot[0], a.rot[1], a.posy, a.g[0], a.g[1], a.flip)
    v = [p - q for p, q in zip(pos, at)]
    L = math.sqrt(sum(x * x for x in v))
    look = [-x / L for x in v]
    elev = math.degrees(math.asin(-look[1]))
    head = math.degrees(math.atan2(look[0], look[2]))
    print(f"pos={tuple(round(x, 4) for x in pos)} at={tuple(round(x, 4) for x in at)} up={tuple(round(x, 4) for x in up)}")
    print(f"|pos-at|={L:.4f} 시선={tuple(round(x, 4) for x in look)} 내려다봄={elev:.3f}° 시선 방위(atan2(x,z))={head:.3f}°")


def cmd_selftest(a):
    ok = True

    def chk(n, c):
        nonlocal ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    chk("sead tan(45) = 1", abs(sead_tan_deg(45.0) - 1.0) < 1e-6)
    chk("sead tan(30) ≈ math", abs(sead_tan_deg(30.0) - math.tan(math.radians(30))) < 1e-6)
    v = poser_values({"Pos": {"X": 0, "Y": 70, "Z": 5}, "Rot": {"X": 25, "Y": 30, "Z": 0}, "FovY": 45})
    e = extents(v, 960, 540)
    chk("VersusMiniMapDefault 반높이 = 70·tan45 = 70", abs((e["top"] - e["bottom"]) / 2 - 70.0) < 1e-3)
    chk("반폭 = 70·960/540", abs((e["right"] - e["left"]) / 2 - 70 * 960 / 540) < 1e-3)
    chk("MiniMapScale = 0.24/(70/540)", abs(e["MiniMapScale"] - 0.24 / (70 / 540)) < 1e-6)
    chk("near = 0.1 - 100", abs(e["near"] + 99.9) < 1e-6)
    pos, up, at = map_camera(25.0, 30.0, 70.0)
    L = math.sqrt(sum(x * x for x in pos))
    chk("맵 카메라 위치는 원점 기준 회전: |pos| = Pos.Y + base.y = 69", abs(L - 69.0) < 0.02)
    chk("원점에서 본 pos 고각 = 90 - Rot.X", abs(math.degrees(math.asin(pos[1] / L)) - 65.0) < 1e-2)
    chk("up ⟂ pos(원점 기준)", abs(sum(p * q for p, q in zip(up, pos))) / L < 1e-4)
    chk("주시점 = (0, -1, 0) (기울임 0)", max(abs(at[0]), abs(at[1] + 1), abs(at[2])) < 1e-6)
    chk("Rot.Y=0 이면 카메라는 +Z 쪽에서 -Z 쪽을 봄, 화면 위 = -Z", map_camera(25, 0, 70)[0][2] > 0 and map_camera(25, 0, 70)[1][2] < 0)
    p2, u2, a2 = map_camera(25.0, 30.0, 70.0, flip=True)
    chk("팀 반전 = 위치·주시점 Y축 180° 회전", abs(p2[0] + pos[0]) < 1e-3 and abs(p2[2] + pos[2]) < 1e-3)
    print("ALL PASS" if ok else "SOME FAIL")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["table", "selftest", "cam"])
    ap.add_argument("--half", nargs=2, type=float, default=[960.0, 540.0])
    ap.add_argument("--rot", nargs=2, type=float, default=[25.0, 30.0])
    ap.add_argument("--posy", type=float, default=70.0)
    ap.add_argument("--g", nargs=2, type=float, default=[0.0, 0.0])
    ap.add_argument("--flip", action="store_true")
    a = ap.parse_args()
    {"table": cmd_table, "selftest": cmd_selftest, "cam": cmd_cam}[a.cmd](a)
