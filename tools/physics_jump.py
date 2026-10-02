import argparse
import json
import sys
from pathlib import Path

import numpy as np

F = np.float32
ROOT = Path(__file__).resolve().parents[2]

G_BASE = F(0.008)
DECAY = F(0.98)
AIR_FRAMES_FOR_GRAVITY = 3
JUMP_V0 = F(0.115)
PHIVE_G0 = F(9.8)


def gravity_scale(g):
    return F(F(F(F(g) * F(60.0)) * F(60.0)) / PHIVE_G0)


def step(v, g, gravity_on):
    v = F(DECAY * v)
    if gravity_on:
        v = F(v - g)
    return v


def arc(v0, g, frames, gravity_from):
    v = F(v0)
    y = F(0.0)
    rows = []
    for n in range(1, frames + 1):
        v = step(v, g, n >= gravity_from)
        y = F(y + v)
        rows.append((n, float(v), float(y)))
    return rows


def solver_height(v0, g):
    v = F(v0)
    s = F(0.0)
    while v > F(0.0):
        v = F(DECAY * v)
        v = F(v - g)
        s = F(s + v)
    return s


def solver_v0(h, g):
    h = abs(F(h))
    hi = F(0.5)
    lo = F(0.0)
    mid = F(0.0)
    while True:
        mid = F(F(hi + lo) * F(0.5))
        s = solver_height(mid, g)
        d = F(s - h)
        if -0.01 <= d < 0.01 or not (lo <= hi):
            break
        if h <= s:
            hi = F(mid - F(0.001))
        else:
            lo = F(mid + F(0.001))
        if not (lo <= hi):
            break
    return mid


def summarize(rows):
    apex = max(rows, key=lambda r: r[2])
    land = next((r for r in rows if r[0] > apex[0] and r[2] <= 0.0), None)
    return {"apex_frame": apex[0], "apex_height": apex[2], "land_frame": land[0] if land else None}


def main():
    ap = argparse.ArgumentParser(description="플레이어 수직 속도 재구현(본체+0x73c: v=0.98v-g) 계산")
    ap.add_argument("--v0", type=float, default=float(JUMP_V0))
    ap.add_argument("--g", type=float, default=float(G_BASE))
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--json", type=str, default="")
    a = ap.parse_args()
    g = F(a.g)
    out = {
        "g": float(g),
        "gravity_scale_phive": float(gravity_scale(g)),
        "terminal_velocity": float(F(-g / F(1.0 - DECAY))),
        "variants": {},
    }
    for name, start in (("gravity_from_frame1", 1), ("gravity_from_frame3", AIR_FRAMES_FOR_GRAVITY)):
        rows = arc(a.v0, g, a.frames, start)
        out["variants"][name] = {"summary": summarize(rows), "rows": rows[:60]}
    h = solver_height(F(a.v0), g)
    out["solver"] = {"height_for_v0": float(h), "v0_back": float(solver_v0(h, g))}
    fall = arc(F(0.0), g, 300, 1)
    v90 = next(r for r in fall if r[1] <= 0.9 * float(out["terminal_velocity"]))
    out["fall_from_rest"] = {"frames_to_90pct_terminal": v90[0], "rows_head": fall[:10]}
    print(f"g={out['g']:.9g} u/frame^2, Phive GravityScale={out['gravity_scale_phive']:.9g}, terminal={out['terminal_velocity']:.9g} u/frame")
    for name, v in out["variants"].items():
        s = v["summary"]
        print(f"{name}: apex frame {s['apex_frame']} height {s['apex_height']:.6f}, back to y<=0 at frame {s['land_frame']}")
    print(f"solver(0x71024c0b38 model): height(v0={a.v0})={out['solver']['height_for_v0']:.6f}, inverse v0={out['solver']['v0_back']:.6f}")
    print(f"fall from rest: 90% terminal at frame {out['fall_from_rest']['frames_to_90pct_terminal']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
