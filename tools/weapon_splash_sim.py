"""스플래시슈터 탄(spl::BulletShooterBase)이 떨어뜨리는 스플래시 탄(BulletSplashShooter) 생성 재구현 (f32, asm 연산 순서 그대로).

원본 근거(main NSO, 0x7100000000 기준):
  슬롯15 0x710174efc0 : 탄별 sead::Random, 스플래시 일정(+0x11ed/+0x11ee/+0x11f4/+0x11f8/+0x11fc/+0x1208/+0x120c)
  0x710174fe94        : nearest = SpawnNearestLength>0 ? 그것 : SpawnBetweenLength/split
  슬롯56 0x71017512bc : 이동 상태!=0 이면 +0x1204=max(+0x1204,y) 후 0x7101751304(누적·생성 루프·강제 생성)
  0x71017540ec        : 스플래시 하나 생성(위치 보간, 시드=전역+0x120+생성정보+0x64+남은 수, 기준축, 난수 X→Y→Z, 요청 구성)
  0x71012500d4        : side = normalize(up × normalize(fwd)), up = fwd × side
  0x7101645590        : 탄 시작 공통(age=-1, prevPos=pos, vel=dir*(speed+info+0x68))
  0x7101763a10        : 이동(age==1 재정규화 k=speed/|v|, age==0 은 SM 진행·속도 유지)
  바디 적분 0x7103b0a2bc : p = fl(fl(dt*fl(60v)) + p), dt=0x3c888889

사용: PY web/tools/weapon_splash_sim.py [--global-seed 10] [--frame 100] [--json out.json]
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bullet_shooter_sim as bs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
DT = np.frombuffer(np.uint32(0x3c888889).tobytes(), F)[0]
SIXTY = F(60.0)
TWO_PI = np.frombuffer(np.uint32(0x40c90fdb).tobytes(), F)[0]
EPS_H = np.frombuffer(np.uint32(0x38d1b717).tobytes(), F)[0]   # 1e-4 (0x71017542ac)
EPS_D2 = np.frombuffer(np.uint32(0x322bcc76).tobytes(), F)[0]  # 1e-8 (0x71017548e4)
UP_Y = (F(0), F(1), F(0))   # *0x7105791978 -> 0x7104a985b8
UP_X = (F(1), F(0), F(0))   # *0x71057919a0 -> 0x7104a985c4
PERM_ADDR = 0x4a9b0a1

SPAWN_DEFAULTS = {"SpawnNum": 0.0, "SpawnBetweenLength": 0.0, "SplitNum": 1, "SpawnNearestLength": 0.0,
                  "RandomSpawnVelXMax": 0.055, "RandomSpawnVelYMax": 0.015,
                  "RandomSpawnVelZMin": 0.01, "RandomSpawnVelZMax": 0.02, "ForceSpawnNearestAddNumArray": []}


def hx(x):
    return "0x%08x" % struct.unpack("<I", struct.pack("<f", float(x)))[0]


def sqrt32(x):
    return F(np.sqrt(F(x)))


def len3(x, y, z):
    return sqrt32(F(F(F(x * x) + F(y * y)) + F(z * z)))


class SeadRandom:
    def __init__(self, seed):
        s = seed & 0xFFFFFFFF
        st = []
        for i in range(1, 5):
            s = (((s ^ (s >> 30)) * 0x6c078965) + i) & 0xFFFFFFFF
            st.append(s)
        self.s = st

    def u32(self):
        x, y, z, w = self.s
        t = (x ^ (x << 11)) & 0xFFFFFFFF
        n = (t ^ (t >> 8) ^ w ^ (w >> 19)) & 0xFFFFFFFF
        self.s = [y, z, w, n]
        return n

    def f01(self):
        b = (self.u32() >> 9) | 0x3f800000
        return F(np.frombuffer(np.uint32(b).tobytes(), F)[0] + F(-1.0))


def load_perm():
    img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
    return [list(img[PERM_ADDR + 16 * n: PERM_ADDR + 16 * n + 16]) for n in range(16)]


def load_spawn_param(table):
    p = json.loads((ROOT / "extracted/params/Component/GameParameterTable" / f"{table}.game__GameParameterTable.bgyml.json").read_text(encoding="utf-8"))
    sp = dict(SPAWN_DEFAULTS)
    sp.update({k: v for k, v in p["GameParameters"]["SplashSpawnParam"].items() if k != "$type"})
    return sp


def nearest_len(sp, split):
    """0x710174fe94"""
    n = F(sp["SpawnNearestLength"])
    if n > F(0):
        return n
    return F(F(sp["SpawnBetweenLength"]) / F(split))


def schedule(sp, idx, gseed, frame, perm):
    """슬롯15 0x710174efc0 의 스플래시 일정 부분. 반환: 탄 필드 dict, 난수 기록"""
    split = int(sp["SplitNum"]) or 1
    rng = SeadRandom(gseed + frame)
    between = F(F(sp["SpawnBetweenLength"]) / F(split))           # s12 = fdiv(+0x68, scvtf(split))
    near = nearest_len(sp, split)                                 # s8
    bmn = F(between - near)                                       # s13 = fsub s12, s8
    s11 = F(split - 1)                                            # scvtf(split-1)
    is_last = (split - 1) == idx                                  # +0x11ed
    forced = False                                                # +0x11ee
    row = perm[split] if split < 16 else perm[0]
    for v in sp["ForceSpawnNearestAddNumArray"]:
        if v < 1:
            continue
        r = v - int(v / split) * split
        if (row[r] if r < 16 else row[0]) == idx:
            forced = True
            break
    out = {"isLast": is_last, "forced": forced, "rand": []}
    if forced:
        r1 = rng.f01()
        out["rand"].append(("+0x1208", float(r1)))
        out["f1208"] = F(bmn + F(F(between * s11) + F(r1 * near)))
    else:
        out["f1208"] = None
    r2 = rng.f01()
    out["rand"].append(("+0x11f4", float(r2)))
    s0 = F((near if is_last else between) * r2)
    out["f11f8"] = F(s0 / near) if (is_last or forced) else None
    out["f11f4"] = F(bmn + F(F(between * F(idx)) + s0))
    num = F(sp["SpawnNum"])
    n = int(np.trunc(num))
    if num < 0 and F(n) != num:
        n -= 1
    cond = F(s11 - F(F(F(num - F(n)) * F(split)) + F(-1.0))) <= F(idx)
    out["f11fc"] = n + (1 if cond else 0)
    r3 = rng.f01()
    out["rand"].append(("+0x120c", float(r3)))
    out["f120c"] = F(r3 * TWO_PI)
    out["between"], out["near"] = between, near
    return out


def frame_vec(fwd, up):
    """0x71012500d4: M={a(side),b(up),c(fwd)} — c 정규화, a=b×c 정규화, b=c×a. 반환 (a, b, c, ok)"""
    cx, cy, cz = fwd
    lc = len3(cx, cy, cz)
    if lc > F(0):
        k = F(F(1) / lc)
        cx, cy, cz = F(k * cx), F(k * cy), F(k * cz)
    bx, by, bz = up
    ax = F(F(cz * by) - F(cy * bz))
    ay = F(F(cx * bz) - F(cz * bx))
    az = F(F(cy * bx) - F(cx * by))
    la = sqrt32(F(az * az + F(F(ax * ax) + F(ay * ay))))
    if la > F(0):
        k = F(F(1) / la)
        ax, ay, az = F(k * ax), F(k * ay), F(k * az)
    nbx = F(F(az * cy) - F(ay * cz))
    nby = F(F(ax * cz) - F(az * cx))
    nbz = F(F(ay * cx) - F(ax * cy))
    return (ax, ay, az), (nbx, nby, nbz), (cx, cy, cz), bool(lc > F(0) and la > F(0))


def scale_to(v, val):
    l = len3(*v)
    if l > F(0):
        k = F(val / l)
        return tuple(F(k * c) for c in v)
    return v


def spawn_one(sp, b, acc, h, is_nearest, gseed):
    """0x71017540ec(bullet, acc=s0, h=s1, isNearest=w1)"""
    sbl = F(sp["SpawnBetweenLength"])
    prev, pos = b["prev"], b["pos"]
    if (F(-h) if h < F(0) else h) >= EPS_H:
        f = F(F(1) - F(F(acc - sbl) / h))
        sx = F(prev[0] + F(f * F(pos[0] - prev[0])))
        sy = F(prev[1] + F(f * F(pos[1] - prev[1])))
        sz = F(prev[2] + F(f * F(pos[2] - prev[2])))
    else:
        f = None
        sx, sy, sz = prev
    seed = (gseed + b["frame"] + b["remain"]) & 0xFFFFFFFF
    rng = SeadRandom(seed)
    X, Y = F(sp["RandomSpawnVelXMax"]), F(sp["RandomSpawnVelYMax"])
    zmin, zmax = F(sp["RandomSpawnVelZMin"]), F(sp["RandomSpawnVelZMax"])
    dx, dy, dz = F(pos[0] - prev[0]), F(pos[1] - prev[1]), F(pos[2] - prev[2])
    d2 = F(F(F(dx * dx) + F(dy * dy)) + F(dz * dz))
    if d2 < EPS_D2:
        s = F(1) if dy > F(0) else F(-1)
        z0 = F(s * F(0))
        dx, dy, dz = z0, s, z0
        hz2 = F(F(z0 * z0) + F(z0 * z0))
    else:
        hz2 = F(F(dz * dz) + F(dx * dx))
    up = UP_Y if hz2 >= EPS_D2 else UP_X
    side, upv, fwd, _ = frame_vec((dx, dy, dz), up)
    rnd = []
    if X >= F(-X):
        r = rng.f01(); rnd.append(float(r))
        vx = F(F(r * F(X + X)) - X)
    else:
        vx = F(-X)
    side = scale_to(side, vx)
    if Y >= F(-Y):
        r = rng.f01(); rnd.append(float(r))
        vy = F(F(F(Y + Y) * r) - Y)
    else:
        vy = F(-Y)
    upv = scale_to(upv, vy)
    if zmax >= zmin:
        r = rng.f01(); rnd.append(float(r))
        vz = F(zmin + F(F(zmax - zmin) * r))
    else:
        vz = zmin
    fwd = scale_to(fwd, vz)
    sumv = tuple(F(fwd[i] + F(side[i] + upv[i])) for i in range(3))
    spd = len3(*sumv)
    if spd > F(0):
        k = F(F(1) / spd)
        dirv = tuple(F(c * k) for c in sumv)
    else:
        dirv = sumv
    return {"frame_age": b["age"], "isNearest": bool(is_nearest), "seed": seed, "remainAtSpawn": b["remain"],
            "acc": float(acc), "h": float(h), "f": None if f is None else float(f),
            "pos": [float(sx), float(sy), float(sz)], "dir": [float(c) for c in dirv], "speed": float(spd),
            "pos_hex": [hx(sx), hx(sy), hx(sz)], "dir_hex": [hx(c) for c in dirv], "speed_hex": hx(spd),
            "paintDir_vel_xz": [float(b["vel"][0]), float(b["vel"][2])], "spawnY": float(sy), "rand": rnd,
            "randVel": [float(vx), float(vy), float(vz)]}


def post_move(sp, b, gseed, out):
    """슬롯56 0x71017512bc + 0x7101751304"""
    pos, prev, vel = b["pos"], b["prev"], b["vel"]
    if b["state"] != 0:
        b["f1204"] = b["f1204"] if b["f1204"] > pos[1] else pos[1]
    dx, dy, dz = F(pos[0] - prev[0]), F(pos[1] - prev[1]), F(pos[2] - prev[2])
    dot = F(F(dz * vel[2]) + F(F(dx * vel[0]) + F(dy * vel[1])))
    if dot < F(0):
        return
    if vel[2] == F(0) and vel[0] == F(0) and vel[1] == F(0):
        return
    dx2, dz2 = F(dx * dx), F(dz * dz)
    b["f1200"] = F(sqrt32(F(F(dx2 + F(dy * dy)) + dz2)) + b["f1200"])
    h = sqrt32(F(dx2 + dz2))
    sbl = F(sp["SpawnBetweenLength"])
    if b["remain"] >= 1:
        b["f11f4"] = F(h + b["f11f4"])
        acc = b["f11f4"]
        while acc >= sbl:
            out.append(spawn_one(sp, b, acc, h, b["isLast"], gseed))
            b["f11f4"] = F(b["f11f4"] - sbl)
            acc = b["f11f4"]
            if b["isLast"]:
                split = int(sp["SplitNum"]) or 1
                between = F(sbl / F(split))
                b["f11f4"] = F(b["f11f4"] + F(F(between - nearest_len(sp, split)) * b["f11f8"]))
                acc = b["f11f4"]
                b["isLast"] = False
            b["remain"] -= 1
            if b["remain"] <= 0:
                break
    if b["forced"]:
        b["f1208"] = F(h + b["f1208"])
        if not (b["f1208"] < sbl):
            out.append(spawn_one(sp, b, b["f1208"], h, True, gseed))
            b["forced"] = False


def run(table, idx, gseed, frame, frames=200, dir0=(0.0, 0.0, 1.0), pos0=(0.0, 0.0, 0.0), perm=None):
    p = bs.load_move_param(table)
    sp = load_spawn_param(table)
    perm = perm or load_perm()
    sc = schedule(sp, idx, gseed, frame, perm)
    speed = F(p["SpawnSpeed"])
    d = tuple(F(c) for c in dir0)
    vel = (F(d[0] * speed), F(speed * d[1]), F(speed * d[2]))  # 0x71016458a4~b4: s=+0x48(+0x68=0)
    b = {"age": -1, "pos": tuple(F(c) for c in pos0), "prev": tuple(F(c) for c in pos0), "vel": vel,
         "state": bs.initial_state(p), "sframe": 0, "frame": frame, "remain": sc["f11fc"],
         "f11f4": sc["f11f4"], "f11f8": sc["f11f8"], "f1208": sc["f1208"], "isLast": sc["isLast"],
         "forced": sc["forced"], "f1200": F(0), "f1204": F(-1000000.0)}
    spawns, trace = [], []
    for _ in range(frames):
        if b["age"] >= 0:
            b["prev"] = b["pos"]
        b["age"] += 1
        v = np.array(b["vel"], F)
        if b["age"] == 1:
            l = len3(*v)
            if l > F(0):
                k = F(speed / l)
                v = np.array([F(v[0] * k), F(v[1] * k), F(v[2] * k)], F)
        o, done = bs.STEPS[b["state"]](p, v, b["sframe"])
        if done:
            b["state"], b["sframe"] = b["state"] + 1, 0
        else:
            b["sframe"] += 1
        if b["age"] != 0:
            b["vel"] = tuple(F(c) for c in o)
        b["pos"] = tuple(F(F(DT * F(b["vel"][i] * SIXTY)) + b["pos"][i]) for i in range(3))
        n0 = len(spawns)
        post_move(sp, b, gseed, spawns)
        trace.append({"age": b["age"], "pos": [float(c) for c in b["pos"]], "vel": [float(c) for c in b["vel"]],
                      "acc": float(b["f11f4"]), "remain": b["remain"], "spawned": len(spawns) - n0})
        if b["pos"][1] < F(-10.0):  # 슬롯21 시작: y < -10 이면 슬롯66(소멸 요청). 같은 슬롯21의 슬롯56 까지는 실행
            break
    sched = {k: (v if not isinstance(v, np.floating) else {"f": float(v), "hex": hx(v)}) for k, v in sc.items()}
    return {"idx": idx, "schedule": sched, "spawns": spawns, "lastAge": b["age"], "trace": trace}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table", nargs="?", default="WeaponShooterNormal")
    ap.add_argument("--global-seed", type=int, default=10, help="탄관리자+0x120 (원천 없으면 13+118+213+388=... 아닌 10)")
    ap.add_argument("--frame", type=int, default=100, help="생성정보+0x64 (발사 GameFrame)")
    ap.add_argument("--frames", type=int, default=200)
    ap.add_argument("--json")
    a = ap.parse_args()
    perm = load_perm()
    sp = load_spawn_param(a.table)
    res = []
    for idx in range(int(sp["SplitNum"]) or 1):
        r = run(a.table, idx, a.global_seed, a.frame, a.frames, perm=perm)
        res.append(r)
        s = r["schedule"]
        f1208 = s["f1208"]["f"] if s["f1208"] else None
        print(f"idx {idx}: isLast={s['isLast']} forced={s['forced']} 11f4={s['f11f4']['f']:.6f}({s['f11f4']['hex']}) "
              f"11fc={s['f11fc']} 1208={f1208} 120c={s['f120c']['hex']}  (마지막 age {r['lastAge']})")
        for sv in r["spawns"]:
            print(f"   age {sv['frame_age']:2d} near={int(sv['isNearest'])} seed={sv['seed']} pos=({sv['pos'][0]:.6f},{sv['pos'][1]:.6f},{sv['pos'][2]:.6f}) "
                  f"dir=({sv['dir'][0]:+.6f},{sv['dir'][1]:+.6f},{sv['dir'][2]:+.6f}) spd={sv['speed']:.7f}")
            print(f"          hex pos={sv['pos_hex']} dir={sv['dir_hex']} spd={sv['speed_hex']}")
    if a.json:
        Path(a.json).write_text(json.dumps({"table": a.table, "globalSeed": a.global_seed, "frame": a.frame, "bullets": res},
                                           indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
