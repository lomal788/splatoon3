import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
F = np.float32

MOVE_DEFAULTS = {
    "SpawnSpeed": 2.0, "GoStraightToBrakeStateFrame": 10, "GoStraightStateEndMaxSpeed": 10.0,
    "BrakeGravity": 0.07, "BrakeAirResist": 0.36, "BrakeToFreeVelocityY": -0.15,
    "BrakeToFreeVelocityXZ": 0.2355, "BrakeToFreeStateFrame": 4, "FreeGravity": 0.016, "FreeAirResist": 0.02,
}
GO_STRAIGHT, BRAKE, FREE = 0, 1, 2


def load_move_param(table):
    p = json.loads((ROOT / "extracted/params/Component/GameParameterTable" / f"{table}.game__GameParameterTable.bgyml.json").read_text(encoding="utf-8"))
    mp = dict(MOVE_DEFAULTS)
    mp.update({k: v for k, v in p["GameParameters"]["MoveParam"].items() if k != "$type"})
    return mp


def sqrt32(x):
    return F(np.sqrt(F(x)))


def step_go_straight(p, v, frame):
    return v.copy(), frame >= p["GoStraightToBrakeStateFrame"] - 1


def step_brake(p, v, frame):
    x, y, z = (F(c) for c in v)
    if frame == 0:
        mx = F(p["GoStraightStateEndMaxSpeed"])
        l2 = F(x * x + y * y + z * z)
        if F(mx * mx) < l2:
            l = sqrt32(l2)
            if F(0) < l:
                s = F(mx / l)
                x, y, z = F(x * s), F(y * s), F(z * s)
    r, g = F(p["BrakeAirResist"]), F(p["BrakeGravity"])
    bx = F(x - F(x * r))
    by = F(y + F(F(y * -r) - g))
    bz = F(z - F(z * r))
    vy_th, vxz_th, n = F(p["BrakeToFreeVelocityY"]), F(p["BrakeToFreeVelocityXZ"]), p["BrakeToFreeStateFrame"]
    if vy_th <= by:
        return np.array([bx, by, bz], F), False
    h2 = F(bx * bx + bz * bz)
    if F(vxz_th * vxz_th) <= h2 and frame < n:
        return np.array([bx, by, bz], F), False
    t1 = F(0)
    if vy_th <= y:
        t1 = min(F((vy_th - y) / (by - y)), F(1))
    hpre = sqrt32(F(x * x + z * z))
    t2 = F(0)
    if vxz_th <= hpre:
        hnew = sqrt32(h2)
        if F(hnew - hpre) != 0:
            t2 = min(F((vxz_th - hpre) / (hnew - hpre)), F(1))
    t3 = F(1) if frame <= n else F(0)
    t2 = min(t2, t3)
    t = max(t1, t2)
    fr, fg = F(p["FreeAirResist"]), F(p["FreeGravity"])
    ix, iy, iz = F(x + F((bx - x) * t)), F(y + F((by - y) * t)), F(z + F((bz - z) * t))
    s = F(F(1) - t)
    ox = F(ix + F(s * F(F(ix - F(ix * fr)) - ix)))
    oy = F(iy + F(s * F(F(iy + F(F(iy * -fr) - fg)) - iy)))
    oz = F(iz + F(s * F(F(iz - F(iz * fr)) - iz)))
    return np.array([ox, oy, oz], F), True


def step_free(p, v, frame):
    x, y, z = (F(c) for c in v)
    fr, fg = F(p["FreeAirResist"]), F(p["FreeGravity"])
    return np.array([F(x - F(x * fr)), F(y + F(F(y * -fr) - fg)), F(z - F(z * fr))], F), False


STEPS = (step_go_straight, step_brake, step_free)


ADD_DEFAULTS = {"XRate": 0.4, "YMax": 100.0, "YMinusRate": 0.0, "YPlusRate": 1.0, "ZRate": 2.0, "GuideYMinusZero": False}


def initial_velocity(speed, d, pvel, axis, add, guide=False):
    """0x71026beed0 판독식. d=조준 방향(단위), pvel=플레이어 속도, axis=조준 기준 축."""
    a = dict(ADD_DEFAULTS)
    a.update(add or {})
    speed = F(speed)
    t = F(F(pvel[0] * axis[0]) + F(F(pvel[1] * F(0)) + F(pvel[2] * axis[2])))
    pa = [F(c * t) for c in axis]
    if pvel[1] > 0:
        yr = F(a["YPlusRate"])
    elif guide and a["GuideYMinusZero"]:
        yr = F(0)
    else:
        yr = F(a["YMinusRate"])
    vy = min(F(pvel[1] * yr), F(a["YMax"]))
    xr, zr = F(a["XRate"]), F(a["ZRate"])
    vx = F(F(F(d[0] * speed) + F(F(pvel[0] - pa[0]) * xr)) + F(pa[0] * zr))
    vyy = F(F(F(F(d[1] * speed) + F(F(F(0) - pa[1]) * xr)) + F(pa[1] * zr)) + vy)
    vz = F(F(F(d[2] * speed) + F(F(pvel[2] - pa[2]) * xr)) + F(pa[2] * zr))
    return np.array([vx, vyy, vz], F)


def initial_state(p):
    return FREE if p["GoStraightToBrakeStateFrame"] == 0 else GO_STRAIGHT


def simulate(p, v0, frames, spawn_speed=None, pos0=(0, 0, 0)):
    spawn_speed = F(p["SpawnSpeed"] if spawn_speed is None else spawn_speed)
    state, sframe = initial_state(p), 0
    v = np.array(v0, F)
    pos = np.array(pos0, F)
    rows = []
    for age in range(1, frames + 1):
        if age == 1:
            l = sqrt32(F(v @ v))
            if F(0) < l:
                v = (v * F(spawn_speed / l)).astype(F)
        out, done = STEPS[state](p, v, sframe)
        if done:
            state, sframe = state + 1, 0
        else:
            sframe += 1
        v = out
        pos = (pos + v).astype(F)
        rows.append({"age": age, "state": ["GoStraight", "Brake", "Free"][state], "stateFrame": sframe,
                     "vel": [float(c) for c in v], "pos": [float(c) for c in pos]})
    return rows


def main():
    ap = argparse.ArgumentParser(description="슈터 탄 속도 상태 머신 재구현 (판독식 float32). 위치 적분 pos+=vel은 추정")
    ap.add_argument("table", nargs="?", default="WeaponShooterNormal")
    ap.add_argument("--frames", type=int, default=40)
    ap.add_argument("--pitch", type=float, default=0.0, help="수평 기준 발사 각도(도), 위가 +")
    ap.add_argument("--json")
    a = ap.parse_args()
    p = load_move_param(a.table)
    rad = np.radians(a.pitch)
    v0 = (0.0, float(np.sin(rad)), float(np.cos(rad)))
    rows = simulate(p, v0, a.frames)
    print(json.dumps({k: p[k] for k in MOVE_DEFAULTS}))
    for r in rows:
        print(f"{r['age']:3d} {r['state']:<10} sf={r['stateFrame']:2d} v=({r['vel'][1]:+.5f},{r['vel'][2]:.5f}) pos=(y {r['pos'][1]:+8.4f}, z {r['pos'][2]:8.4f})")
    if a.json:
        Path(a.json).write_text(json.dumps({"table": a.table, "param": p, "pitch": a.pitch, "rows": rows}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
