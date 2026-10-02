"""슈터·스플래시 탄 도색 모양 재구현 (원본 판독 기반).

근거 함수 (main, 0x7100000000 기준)
  0x7101751c08  BulletShooterBase 슬롯84: 폭(WidthHalf) 거리 보간 + DepthScale(각도/BreakFree 낙하)
  0x7101811b44  BulletSplashShooter 슬롯84: 폭(WidthHalf/Nearest) + DepthScale(낙하 높이)
  0x7101765fd8  공용: (WidthHalf, DepthScale) -> 사각 크기 (W, L) + 중심 이동
  0x7101765b50  공용: 패턴 1..7일 때 중심을 진행 방향으로 (L-W)/2 이동

사용:
  python web/tools/paint_shape.py table   # 모든 무기 표 요약 -> analysis/paint/shooter_paint_table.json
  python web/tools/paint_shape.py check   # 경계·연속성 자체 검사
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GPT = ROOT / "extracted/params/Component/GameParameterTable"
REFL = ROOT / "analysis/param_reflect"
OUT = ROOT / "analysis/paint"


def defaults(type_name):
    d = json.loads((REFL / f"{type_name}.json").read_text(encoding="utf-8"))
    return dict(d["classes"][0]["defaults"])


def load_table(name):
    p = GPT / f"{name}.game__GameParameterTable.bgyml.json"
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_param(table_name, key, type_name):
    """$parent 체인: 필드별로 자식에 값이 있으면 자식, 없으면 부모, 끝까지 없으면 생성자 기본값."""
    chain = []
    name = table_name
    while name:
        t = load_table(name)
        chain.append(t.get("GameParameters", {}).get(key, {}))
        par = t.get("$parent")
        name = par.split("/")[-1].split(".")[0] if par else None
    out = defaults(type_name)
    src = {k: "default" for k in out}
    for obj in reversed(chain):
        for k, v in obj.items():
            if k.startswith("$"):
                continue
            out[k] = v
            src[k] = "data"
    return out, src


def clamp_lerp(x, x0, y0, x1, y1):
    """0x7101751c08 안에 인라인된 두 점 보간. x0>x1 이어도 정렬해서 같은 식으로 동작."""
    if x1 < x0:
        x0, y0, x1, y1 = x1, y1, x0, y0
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    d = x1 - x0
    t = 0.0 if d == 0.0 else (x - x0) / d
    return y0 + (y1 - y0) * t


def shooter_width_half(p, dist):
    """dist = 탄+0x1200 누적 이동거리. DistanceMiddle 기준으로 near/far 구간 선택."""
    if dist < p["DistanceMiddle"]:
        return clamp_lerp(dist, p["DistanceNear"], p["WidthHalfNear"], p["DistanceMiddle"], p["WidthHalfMiddle"])
    return clamp_lerp(dist, p["DistanceMiddle"], p["WidthHalfMiddle"], p["DistanceFar"], p["WidthHalfFar"])


def lerp_t(a, b, t):
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    return a + t * (b - a)


def shooter_depth_scale(p, spawn_pos, pos, in_free_state, max_y_in_state):
    dx = pos[0] - spawn_pos[0]
    dz = pos[2] - spawn_pos[2]
    hdist = math.sqrt(dx * dx + dz * dz)
    if hdist > 0.0:
        deg = math.atan(abs(pos[1] - spawn_pos[1]) / hdist) * 57.295776
        t = (deg - p["DegreeUseDepthScaleMax"]) / (p["DegreeUseDepthScaleMin"] - p["DegreeUseDepthScaleMax"])
    else:
        t = 1.0
    ds = lerp_t(p["DepthScaleMax"], p["DepthScaleMin"], t)
    if in_free_state:
        h = max_y_in_state - pos[1]
        t2 = (h - p["HeightUseDepthScaleMaxBreakFree"]) / (
            p["HeightUseDepthScaleMinBreakFree"] - p["HeightUseDepthScaleMaxBreakFree"])
        ds_bf = lerp_t(p["DepthScaleMaxBreakFree"], p["DepthScaleMinBreakFree"], t2)
        ds = ds if ds < ds_bf else ds_bf
    if ds < 1.0:
        return 1.0
    return min(ds, 5.0)


def splash_paint(p, nearest, spawn_y, y):
    w = p["WidthHalfNearest"] if nearest else p["WidthHalf"]
    drop = spawn_y - y
    t = (drop - p["DepthMaxDropHeight"]) / (p["DepthMinDropHeight"] - p["DepthMaxDropHeight"])
    ds = lerp_t(p["DepthScaleMax"], p["DepthScaleMin"], t)
    return w, max(ds, 1.0)


def rect_size(width_half, depth_scale):
    """0x7101765fd8: W = 2w*ds^-1/4 (진행 직교), L = 2w*ds^3/4 (진행 방향). L/W = ds, W*L = 4w^2*sqrt(ds)."""
    s = math.sqrt(depth_scale)
    q = math.sqrt(abs(s))
    length = (width_half + width_half) * s * q
    width = ((width_half + width_half) / s) * q
    return width, length


def center_shift(width, length, pattern):
    """0x7101765b50: 패턴 1..7 이면 진행 방향(표면 평면 투영)으로 (L-W)/2 앞으로. 그 외 0."""
    if not (1 <= pattern <= 7):
        return 0.0
    r = length / width
    return length * ((r - 1.0) / (r + r))


def build_table():
    rows = []
    for p in sorted(GPT.glob("*.bgyml.json")):
        name = p.name.split(".")[0]
        t = json.loads(p.read_text(encoding="utf-8"))
        gp = t.get("GameParameters", {})
        ent = {"table": name}
        for key, v in gp.items():
            ty = v.get("$type") if isinstance(v, dict) else None
            if ty == "spl__BulletShooterPaintParam":
                ent["shooter_key"] = key
                ent["shooter"], ent["shooter_src"] = resolve_param(name, key, ty)
            elif ty == "spl__BulletSplashShooterPaintParam":
                ent["splash_key"] = key
                ent["splash"], ent["splash_src"] = resolve_param(name, key, ty)
            elif ty == "spl__BulletWallDropCollisionPaintParam":
                ent["walldrop_key"] = key
                ent["walldrop"], _ = resolve_param(name, key, ty)
        if len(ent) > 1:
            if "shooter" in ent:
                sp = ent["shooter"]
                ent["width_half_by_dist"] = {str(d): round(shooter_width_half(sp, d), 6)
                                             for d in (0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)}
                flat = shooter_depth_scale(sp, (0, 0, 0), (10, 0, 0), False, 0)
                steep = shooter_depth_scale(sp, (0, 0, 0), (1, -5, 0), False, 0)
                ent["depth_scale_flat"] = round(flat, 6)
                ent["depth_scale_steep"] = round(steep, 6)
                W, L = rect_size(shooter_width_half(sp, 20.0), flat)
                ent["rect_dist20_flat_WxL"] = [round(W, 4), round(L, 4)]
            if "splash" in ent:
                w, ds = splash_paint(ent["splash"], False, 0.0, -1.0)
                W, L = rect_size(w, ds)
                ent["splash_drop1_WxL"] = [round(W, 4), round(L, 4)]
            rows.append(ent)
    return rows


def check():
    p = defaults("spl__BulletShooterPaintParam")
    assert shooter_width_half(p, 0.0) == p["WidthHalfNear"]
    assert abs(shooter_width_half(p, 100.0) - p["WidthHalfFar"]) < 1e-9
    W, L = rect_size(1.0, 1.0)
    assert abs(W - 2.0) < 1e-6 and abs(L - 2.0) < 1e-6
    W, L = rect_size(1.0, 4.0)
    assert abs(L / W - 4.0) < 1e-6 and abs(W * L - 4.0 * 2.0) < 1e-5
    assert center_shift(2.0, 2.0, 1) == 0.0
    assert abs(center_shift(1.0, 3.0, 1) - 1.0) < 1e-6
    assert center_shift(1.0, 3.0, 0) == 0.0
    assert shooter_depth_scale(p, (0, 0, 0), (0, 0, 0), False, 0) == p["DepthScaleMin"]
    assert shooter_depth_scale(p, (0, 0, 0), (10, 0, 0), False, 0) == p["DepthScaleMax"]
    assert shooter_depth_scale(p, (0, 0, 0), (1, -5, 0), False, 0) == p["DepthScaleMin"]
    sn = resolve_param("WeaponShooterNormal", "PaintParam", "spl__BulletShooterPaintParam")[0]
    prev = None
    for i in range(0, 301):
        w = shooter_width_half(sn, i * 0.1)
        if prev is not None:
            assert abs(w - prev) < 0.05, (i, w, prev)
        prev = w
    print("check ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "table"
    if cmd == "check":
        check()
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        rows = build_table()
        (OUT / "shooter_paint_table.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        for r in rows:
            if "shooter" in r:
                s = r["shooter"]
                print(f'{r["table"]:36s} W n/m/f={s["WidthHalfNear"]:.3f}/{s["WidthHalfMiddle"]:.3f}/{s["WidthHalfFar"]:.3f} '
                      f'D n/m/f={s["DistanceNear"]:.2f}/{s["DistanceMiddle"]:.2f}/{s["DistanceFar"]:.2f} '
                      f'ds flat/steep={r["depth_scale_flat"]:.3f}/{r["depth_scale_steep"]:.3f} WxL(d20,flat)={r["rect_dist20_flat_WxL"]}')
        print(len(rows), "tables ->", OUT / "shooter_paint_table.json")
