"""탄 바디 위치 적분 재구현과 pos+=vel 근사의 f32 차이 측정.

원본 판독(phive_controller.md §6):
  setVelocity 0x71016cb0a0 : body+0xc4 = fmul(v, 60.0f)
  바디 스텝   0x7103b0a2bc : p1 = fadd(fmul(dt, body+0xc4), p0)  (FMA 아님, dt = 월드+0x24)
  월드 dt     0x7103db385c : 0x3c888889 (=1/60 f32), 월드 생성 0x7103ac71c8 에서 min(dt, 0.99899)
  충돌 시     p = p0 + f*(p1-p0) (fsub→fmul→fadd), body+0xc4 = 0
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bullet_shooter_sim as bs  # noqa: E402

F = np.float32
DT = np.frombuffer(np.uint32(0x3c888889).tobytes(), F)[0]
SIXTY = F(60.0)


def body_step(p0, v):
    vb = (v * SIXTY).astype(F)
    return (DT * vb).astype(F) + p0


def body_step_hit(p0, p1, f):
    f = F(f)
    return (p0 + (f * (p1 - p0).astype(F)).astype(F)).astype(F)


def simulate_both(p, v0, frames):
    spawn_speed = F(p["SpawnSpeed"])
    state, sframe = bs.initial_state(p), 0
    v = np.array(v0, F)
    pa = np.zeros(3, F)
    pb = np.zeros(3, F)
    worst = 0.0
    rows = []
    for age in range(1, frames + 1):
        if age == 1:
            l = bs.sqrt32(F(v @ v))
            if F(0) < l:
                v = (v * F(spawn_speed / l)).astype(F)
        out, done = bs.STEPS[state](p, v, sframe)
        if done:
            state, sframe = state + 1, 0
        else:
            sframe += 1
        v = out
        pa = (pa + v).astype(F)
        pb = body_step(pb, v).astype(F)
        d = float(np.max(np.abs(pa.astype(np.float64) - pb.astype(np.float64))))
        worst = max(worst, d)
        rows.append({"age": age, "posAdd": [float(c) for c in pa], "posBody": [float(c) for c in pb], "diff": d})
    return rows, worst


def ulp_stats(n, seed):
    rng = np.random.default_rng(seed)
    v = rng.uniform(-3.0, 3.0, n).astype(F)
    back = (DT * (v * SIXTY).astype(F)).astype(F)
    diff = back != v
    return {"samples": n, "v*60*dt != v": int(diff.sum()), "ratio": float(diff.mean())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", type=int, default=40)
    ap.add_argument("--json")
    a = ap.parse_args()
    tables = ["WeaponShooterNormal", "WeaponShooterShort", "WeaponShooterLong", "WeaponShooterPrecision",
              "WeaponShooterBlaze", "WeaponShooterGravity"]
    out = {"dt_hex": "0x3c888889", "dt": float(DT), "ulp": ulp_stats(200000, 1), "tables": {}}
    print("dt =", repr(float(DT)), " 60*dt(f64) =", 60.0 * float(DT))
    print("ulp:", out["ulp"])
    for t in tables:
        p = bs.load_move_param(t)
        for pitch in (0.0, 30.0, -20.0):
            r = np.radians(pitch)
            rows, worst = simulate_both(p, (0.0, float(np.sin(r)), float(np.cos(r))), a.frames)
            key = f"{t}@{pitch:+.0f}"
            last = rows[-1]
            out["tables"][key] = {"maxDiff": worst, "last": last}
            print(f"{key:32s} maxDiff={worst:.3e}  z(add)={last['posAdd'][2]:.6f} z(body)={last['posBody'][2]:.6f}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
