"""[network] GameFrame(*0x710580e758 +0x148) 갱신 델리게이트를 unicorn으로 실행해 재구현과 비교한다.

원본 델리게이트(NetUtilFrameStarter 0x710126c02c 가 GameFrame +0x108/+0x128 에 설치):
  0x710126d2ac  시작 전: *frame = INT_MIN(0x80000000), starter+0x4c += delta
  0x710126d1fc  공유 시계 → 프레임: base(+0x10) + (s32)((float)(s32)(clock - start(+8)) / 1000 * 60)
  0x710126d040  로컬 시작용: frame == INT_MIN 이면 frame = base(델리게이트 +0x10), 아니면 frame = (s32)((float)frame + delta)
  (0x710126d0ec 는 0x710126d1fc 와 같은 식을 넷 관리자 시계 vt+0x20 값으로 계산, 시계 무효면 INT_MIN)
사용: PY web/tools/network_clock.py [--json analysis/network/clock_result.json]
"""
import argparse
import json
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_W0

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F_CLOCK2FRAME = 0x710126D1FC
F_PRESTART = 0x710126D2AC
F_LOCAL = 0x710126D040
INT_MIN = 0x80000000


def f32(x):
    return float(np.float32(x))


def s32(x):
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


def trunc_s32(f):
    # fcvtzs: 0 방향 절삭, 범위 밖 포화
    if f != f:
        return 0
    if f >= 2147483647.0:
        return 0x7FFFFFFF
    if f <= -2147483648.0:
        return -0x80000000
    return int(f)


def re_clock2frame(start, base, clock):
    d = s32(clock - start)
    t = f32(f32(f32(d) / f32(1000.0)) * f32(60.0))
    return s32(base + trunc_s32(t))


def re_local(frame, delta, base):
    if frame & 0xFFFFFFFF == INT_MIN:
        return base & 0xFFFFFFFF
    return trunc_s32(f32(f32(s32(frame)) + f32(delta))) & 0xFFFFFFFF


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--json", default=str(ROOT / "analysis/network/clock_result.json"))
    a = ap.parse_args()
    u = UC()
    rnd = random.Random(7)
    dg = u.alloc(0x20)
    bad = 0
    samples = []
    for i in range(a.n):
        start = rnd.getrandbits(32)
        base = rnd.choice([0, 0, rnd.randint(-1000, 1000)])
        off = rnd.choice([rnd.randint(-5000, 600000), rnd.randint(-100, 100), rnd.randint(0, 86400000)])
        clock = (start + off) & 0xFFFFFFFF
        u.mu.mem_write(dg + 8, struct.pack("<Q", start))
        u.mu.mem_write(dg + 0x10, struct.pack("<i", base))
        u.call(F_CLOCK2FRAME, dg, clock)
        got = s32(u.mu.reg_read(UC_ARM64_REG_W0))
        exp = re_clock2frame(start, base, clock)
        if got != exp:
            bad += 1
        if i < 6:
            samples.append({"clock_minus_start_ms": off, "base": base, "frame": got})
    # 시작 전 델리게이트
    st = u.alloc(0x60)
    fr = u.alloc(8)
    u.u32(fr, 1234)
    u.f32(st + 0x4C, 0.0)
    obj = u.alloc(0x10)
    u.mu.mem_write(obj + 8, struct.pack("<Q", st))
    for _ in range(10):
        u.call(F_PRESTART, obj, fr, fargs=(1.0,))
    pre = {"frame_after": hex(u.ru32(fr)), "starter_0x4c": u.rf32(st + 0x4C)}
    # 로컬 델리게이트
    bad_local = 0
    for _ in range(a.n // 3):
        v = rnd.choice([INT_MIN, rnd.randint(0, 1 << 22), rnd.randint(-200, 200) & 0xFFFFFFFF])
        d = rnd.choice([1.0, 0.0, 0.5, 2.0])
        base = rnd.randint(-300, 300)
        u.u32(fr, v)
        u.mu.mem_write(dg + 0x10, struct.pack("<i", base))
        u.call(F_LOCAL, dg, fr, fargs=(d,))
        if u.ru32(fr) != re_local(v, d, base):
            bad_local += 1
    res = {"clock2frame_mismatch": bad, "trials": a.n, "samples": samples,
           "prestart_10calls_delta1": pre, "local_delegate_mismatch": bad_local}
    print(json.dumps(res, indent=1))
    Path(a.json).write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
