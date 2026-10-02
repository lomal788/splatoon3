import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[2]
F = np.float32
GPT = ROOT / "extracted/params/Component/GameParameterTable"

SINCOS_TABLE_ADDR = 0x7104AA5B5C

MOVE_DEFAULTS = {
    "FreeGravityType": "value_0_008", "FallPeriodFirstTargetSpeed": 0.06, "FallPeriodFirstFrameMin": 10,
    "FallPeriodFirstFrameMax": 30, "FallPeriodSecondTargetSpeed": 0.06, "FallPeriodSecondFrame": 10,
    "FallPeriodLastFrameMin": 15, "FallPeriodLastFrameMax": 20,
}
PAINT_DEFAULTS = {"PaintRadiusShock": 1.3, "PaintRadiusFall": 0.65, "PaintRadiusGround": 0.6,
                  "FallPeriodFirstSecondTargetAlp": 1.0}
COMMON_DEFAULTS = {"InitVelocityRateYPlus": 0.015, "InitVelocityRateYMinus": 0.035, "PaintWallSpanMinFrame": 2,
                   "PaintWallSpanMaxFrame": 4, "PaintWallDropDistance": 0.0}
GRAVITY = {"value_0_008": 0x3C03126F, "value_0_015": 0x3C75C28F}
R_SPHERE = F(0.2)


def bits(x):
    return struct.unpack("<I", struct.pack("<f", float(F(x))))[0]


def fb(u):
    return F(struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0])



def fcvtzs(x):
    return int(np.trunc(np.float64(F(x))))


class SeadRandom:
    def __init__(self, seed):
        k = 0x6C078965
        s = seed & 0xFFFFFFFF
        self.x = (k * (s ^ (s >> 30)) + 1) & 0xFFFFFFFF
        self.y = (k * (self.x ^ (self.x >> 30)) + 2) & 0xFFFFFFFF
        self.z = (k * (self.y ^ (self.y >> 30)) + 3) & 0xFFFFFFFF
        self.w = (k * (self.z ^ (self.z >> 30)) + 4) & 0xFFFFFFFF

    def next(self):
        t = (self.x ^ (self.x << 11)) & 0xFFFFFFFF
        self.x, self.y, self.z = self.y, self.z, self.w
        self.w = (self.w ^ (self.w >> 19) ^ t ^ (t >> 8)) & 0xFFFFFFFF
        return self.w

    def get_u32(self, n):
        return (self.next() * (n & 0xFFFFFFFF)) >> 32


def load_table(name, key, defaults):
    p = GPT / f"{name}.game__GameParameterTable.bgyml.json"
    d = dict(defaults)
    if p.exists():
        g = json.loads(p.read_text(encoding="utf-8"))["GameParameters"].get(key, {})
        d.update({k: v for k, v in g.items() if k != "$type"})
    return d


def load_sincos():
    from xref import BASE, load_img
    m = load_img()
    o = SINCOS_TABLE_ADDR - BASE
    return np.frombuffer(bytes(m[o:o + 257 * 16]), dtype="<f4").reshape(257, 4).copy()


def norm3(v):
    x, y, z = (F(c) for c in v)
    l2 = F(F(F(x * x) + F(y * y)) + F(z * z))
    ln = F(np.sqrt(l2))
    if ln > F(0):
        inv = F(F(1) / ln)
        return [F(x * inv), F(y * inv), F(z * inv)], ln
    return [x, y, z], ln


def quantize(move, paint, seed61):
    q = {}
    q["shock"] = fcvtzs(F(F(F(paint["PaintRadiusShock"]) / F(0.05)) + F(0.001)))
    q["fall"] = fcvtzs(F(F(F(paint["PaintRadiusFall"]) / F(0.05)) + F(0.001)))
    q["ground"] = fcvtzs(F(F(F(paint["PaintRadiusGround"]) / F(0.05)) + F(0.001)))
    q["alp"] = F(fcvtzs(F(F(F(paint["FallPeriodFirstSecondTargetAlp"]) / F(0.1)) + F(0.0001))))
    q["gravity_type"] = move["FreeGravityType"]
    q["t1"] = fcvtzs(F(F(F(move["FallPeriodFirstTargetSpeed"]) / F(0.005)) + F(0.0001)))
    rnd = SeadRandom((seed61 * 0x3F3 + 0x7D5) & 0xFFFFFFFF)
    lo, hi = int(move["FallPeriodFirstFrameMin"]), int(move["FallPeriodFirstFrameMax"])
    q["n0"] = lo + rnd.get_u32(hi - lo) if lo <= hi else lo
    q["t2"] = fcvtzs(F(F(F(move["FallPeriodSecondTargetSpeed"]) / F(0.005)) + F(0.0001)))
    q["n1"] = int(move["FallPeriodSecondFrame"])
    lo, hi = int(move["FallPeriodLastFrameMin"]), int(move["FallPeriodLastFrameMax"])
    q["n2"] = lo + rnd.get_u32(hi - lo) if lo <= hi else lo
    q["pat"] = rnd.get_u32(5)
    if q["shock"] <= 0 and q["fall"] <= 0 and q["ground"] <= 0:
        q["skip"] = True
    return q


def spawn_velocity(vb, n, common):
    d, sp = norm3(vb)
    vy_in = F(d[1] * sp)
    nx, ny, nz = (F(c) for c in n)
    k = F(0.005)
    v0 = [F(F(0) - F(nx * k)), F(vy_in - F(ny * k)), F(F(0) - F(nz * k))]
    d0, s0 = norm3(v0)
    vy0 = F(s0 * d0[1])
    rate = F(common["InitVelocityRateYPlus"]) if vy0 > F(0) else F(common["InitVelocityRateYMinus"])
    v1 = [F(F(0) - F(nx * k)), F(F(vy0 * rate) - F(ny * k)), F(F(0) - F(nz * k))]
    d1, s1 = norm3(v1)
    s = F(s1 + F(0))
    return [F(d1[0] * s), F(s * d1[1]), F(s * d1[2])], {"dir_in": d, "speed_in": sp, "vy_in": vy_in, "rate": rate}


def phase_alpha(st, q):
    ph, cnt = st["phase"], st["cnt"]
    if ph == 2:
        t = F(F(cnt) / F(st["n2"]))
        if t > F(0.9):
            k = F(F(F(F(t + F(-0.9)) / fb(0x3DCCCCD0)) * F(0.9)) + F(0.1))
        else:
            k = F(F(1) - F(F(t / F(0.9)) * F(0.9)))
        base = 0x20
    elif ph == 1:
        k = F(F(fcvtzs(q["alp"])) * F(0.1))
        base = 0x20
    elif ph == 0:
        k = F(F(F(F(cnt) / F(st["n0"])) * F(F(F(fcvtzs(q["alp"])) * F(0.1)) + F(-1))) + F(1))
        base = 0x1B
    else:
        return F(1), 0
    pat = 0 if st["c"] < 0 else base + q["pat"]
    return k, pat


def wall_contact(st, q, common, cpos, cnorm, frame, events):
    span_max = np.int8(int(common["PaintWallSpanMaxFrame"]) & 0xFF)
    span_min = np.int8(int(common["PaintWallSpanMinFrame"]) & 0xFF)
    c = int(st["c"])
    if c <= int(span_max) - int(span_min):
        ok = True
        if c > 0:
            dd = F(common["PaintWallDropDistance"])
            dx, dy, dz = (F(cpos[i] - st["last_paint"][i]) for i in range(3))
            d2 = F(F(F(dx * dx) + F(dy * dy)) + F(dz * dz))
            if d2 < F(dd * dd):
                ok = False
        if ok:
            st["last_paint"] = list(cpos)
            ri = q["shock"] if (st["info6e"] <= 0 and c < 0) else q["fall"]
            r = F(F(ri) * F(0.05))
            size = F(r + r)
            k, pat = phase_alpha(st, q)
            s0 = F(k * F(int(span_max) - (c if c > 0 else 0)))
            a = F(0) if s0 < F(0) else min(s0, F(1))
            alpha = fcvtzs(F(a * F(255)))
            events.append({"frame": frame, "kind": "wall", "pos": [float(x) for x in cpos],
                           "normal": [float(x) for x in cnorm], "dir": [0.0, 1.0, 0.0], "size": float(size),
                           "pattern": pat, "alpha": alpha, "radius_q": ri})
            st["painted"] = True
    st["on_wall"] = True
    st["normal"] = list(cnorm)
    st["body"] = 1


def ground_contact(st, q, seed_ground, table, cpos, cnorm, frame, events):
    rnd = SeadRandom(seed_ground)
    r = rnd.next()
    row = table[r >> 24]
    f = F(F(r & 0xFFFFFF) * fb(0x33800000))
    s = F(F(row[0]) + F(F(row[1]) * f))
    co = F(F(row[2]) + F(F(row[3]) * f))
    size = F(F(F(q["ground"]) * F(0.05)))
    size = F(size + size)
    events.append({"frame": frame, "kind": "ground", "pos": [float(x) for x in cpos],
                   "normal": [float(x) for x in cnorm], "dir": [float(s), 0.0, float(co)], "size": float(size),
                   "pattern": 0, "alpha": 255, "rand": r})
    st["dead"] = True


def simulate(args):
    move = load_table(args.weapon, "WallDropMoveParam", MOVE_DEFAULTS)
    paint = load_table(args.weapon, "WallDropCollisionPaintParam", PAINT_DEFAULTS)
    common = load_table("BulletWallDrop", "CommonParam", COMMON_DEFAULTS)
    q = quantize(move, paint, args.seed61)
    table = load_sincos()
    n = [F(1), F(0), F(0)]
    hit = [F(x) for x in args.hit]
    pos = [F(hit[i] + F(n[i] * F(0.05))) for i in range(3)]
    v, info = spawn_velocity([F(x) for x in args.vb], n, common)
    g = fb(GRAVITY.get(q["gravity_type"], GRAVITY["value_0_008"]))
    st = {"phase": 0, "cnt": 0, "n0": q["n0"], "n2": q["n2"], "falling": False, "on_wall": True,
          "normal": list(n), "c": -1, "info6e": 0, "last_paint": [F(0)] * 3, "painted": False,
          "body": 1, "left_body": 0, "dead": False, "vel": v}
    st["accel"] = F(F(F(F(q["t1"]) * fb(0xBBA3D70A)) - v[1]) / F(q["n0"]))
    rows = []
    events = []
    rows.append({"frame": 0, "phase": 0, "cnt": 0, "on_wall": 1, "falling": 0, "pos": list(pos), "vel": list(v),
                 "accel": st["accel"], "c": -1, "note": "spawn(slot15)"})
    for frame in range(1, args.frames + 1):
        if st["dead"]:
            break
        st["painted"] = False
        v = list(st["vel"])
        raw_vy = v[1]
        note = ""
        if st["on_wall"]:
            nx, ny, nz = st["normal"]
            d = F(F(F(v[0] * nx) + F(v[1] * ny)) + F(v[2] * nz))
            v = [F(v[0] - F(nx * d)), F(v[1] - F(ny * d)), F(v[2] - F(nz * d))]
            if st["falling"]:
                st["falling"] = False
                if st["left_body"] == st["body"] and st["body"] != 0:
                    note = "reattach same body -> destroy"
                    st["dead"] = True
                else:
                    st["phase"] = 0
                    st["accel"] = F(F(F(F(q["t1"]) * fb(0xBBA3D70A)) - raw_vy) / F(st["n0"]))
                    st["cnt"] = 0
            v[1] = F(v[1] + st["accel"])
            st["cnt"] = int(np.int16(st["cnt"] + 1))
            cnt = st["cnt"]
            if st["phase"] == 2:
                if cnt >= st["n2"]:
                    note = "phase2 end -> destroy"
                    st["dead"] = True
            elif st["phase"] == 1:
                if q["n1"] <= cnt:
                    st["phase"] = 2
                    st["accel"] = F(F(F(0) - v[1]) / F(st["n2"]))
                    st["cnt"] = 0
            elif st["phase"] == 0:
                if cnt < st["n0"]:
                    st["accel"] = F(F(F(F(q["t1"]) * fb(0xBBA3D70A)) - v[1]) / F(st["n0"] - cnt))
                else:
                    st["phase"] = 1
                    st["accel"] = F(F(F(F(q["t2"]) * fb(0xBBA3D70A)) - v[1]) / F(q["n1"]))
                    st["cnt"] = 0
        else:
            if not st["falling"]:
                st["falling"] = True
                if not (raw_vy > F(0)):
                    st["left_body"] = st["body"]
            if st["phase"] == 0:
                st["cnt"] = int(np.int16(st["cnt"] + 1))
            m0 = F(-0.0)
            v = [F(v[0] + F(v[0] * m0)), F(v[1] + F(F(v[1] * m0) - g)), F(v[2] + F(v[2] * m0))]
        st["vel"] = v
        st["on_wall"] = False
        for i in range(3):
            pos[i] = F(pos[i] + v[i])
        cpos = None
        if args.floor_y is not None and pos[1] - R_SPHERE < F(args.floor_y):
            cpos = [pos[0], F(args.floor_y), pos[2]]
            ground_contact(st, q, args.ground_seed, table, cpos, [F(0), F(1), F(0)], frame, events)
            note = (note + " ground paint -> destroy").strip()
        elif pos[0] < R_SPHERE and F(args.wall_bottom) <= pos[1] <= F(args.wall_top):
            cpos = [F(0), pos[1], pos[2]]
            wall_contact(st, q, common, cpos, [F(1), F(0), F(0)], frame, events)
        if st["painted"]:
            st["c"] = int(np.int8((int(common["PaintWallSpanMaxFrame"]) - 1) & 0xFF))
        elif st["c"] >= 1:
            st["c"] -= 1
        if st["falling"]:
            st["c"] = 0
        rows.append({"frame": frame, "phase": st["phase"], "cnt": st["cnt"], "on_wall": int(st["on_wall"]),
                     "falling": int(st["falling"]), "pos": list(pos), "vel": list(v), "accel": st["accel"],
                     "c": st["c"], "note": note})
    return q, info, rows, events


def main():
    ap = argparse.ArgumentParser(description="BulletWallDrop 이동·벽 도색 재구현 (vtable 0x71055b77d0)")
    ap.add_argument("--weapon", default="WeaponShooterNormal")
    ap.add_argument("--vb", type=float, nargs=3, default=[-2.2, -0.3, 0.0], help="부모 탄 속도(탄+0x1118)")
    ap.add_argument("--hit", type=float, nargs=3, default=[0.0, 0.0, 0.0], help="벽 접점(법선 (1,0,0) 평면 x=0)")
    ap.add_argument("--seed61", type=lambda s: int(s, 0), default=0, help="(G+0x120)+부모 생성정보+0x64")
    ap.add_argument("--ground-seed", type=lambda s: int(s, 0), default=0, help="(G+0x120)+자식 생성정보+0x64")
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--floor-y", type=float, default=None)
    ap.add_argument("--wall-top", type=float, default=1e9)
    ap.add_argument("--wall-bottom", type=float, default=-1e9)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dump-sincos", action="store_true")
    a = ap.parse_args()
    if a.dump_sincos:
        t = load_sincos()
        print(json.dumps([[f"{bits(x):08x}" for x in r] for r in t]))
        return
    q, info, rows, events = simulate(a)
    if a.json:
        conv = lambda o: float(o) if isinstance(o, np.floating) else o
        print(json.dumps({"quant": {k: conv(v) for k, v in q.items()},
                          "rows": [{k: ([conv(x) for x in v] if isinstance(v, list) else conv(v)) for k, v in r.items()}
                                   for r in rows], "events": events}, ensure_ascii=False, indent=1))
        return
    print(f"quant: shock={q['shock']} fall={q['fall']} ground={q['ground']} alpQ={float(q['alp'])} "
          f"t1={q['t1']} t2={q['t2']} N0={q['n0']} N1={q['n1']} N2={q['n2']} pat={q['pat']} grav={q['gravity_type']}")
    print(f"in: vy_in={float(info['vy_in']):.9g} rate={float(info['rate']):.9g}")
    print("f  ph cnt w fl c   pos.x        pos.y          vel.x        vel.y (hex)            accel          note")
    for r in rows:
        p, v = r["pos"], r["vel"]
        print(f"{r['frame']:<3d}{r['phase']:<3d}{r['cnt']:<4d}{r['on_wall']:<2d}{r['falling']:<3d}{r['c']:<4d}"
              f"{float(p[0]):<13.9g}{float(p[1]):<15.9g}{float(v[0]):<13.9g}{float(v[1]):<13.9g}({bits(v[1]):08x}) "
              f"{float(r['accel']):<15.9g}{r['note']}")
    for e in events:
        print("paint", json.dumps(e, ensure_ascii=False))


if __name__ == "__main__":
    main()
