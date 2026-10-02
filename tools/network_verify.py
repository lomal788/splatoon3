"""넷 직렬화 검증 (원본 함수 unicorn 실행 + 파이썬 재구현 비교 + 지연 추정기 재구현).

1) 전 타입 비트 합계: 각 이벤트/상태를 원본 생성자로 만들고 원본 write 를 실행해 기록된 비트 수 합 = 등록 비트 수(max) 인지.
2) 양자화 재구현 대조: 위치17·속력16/12·가속12·방향21/25 를 무작위 입력으로 원본 실행 결과와 비교.
3) 왕복: 원본 write → 원본 read 결과 = 파이썬 decode(encode(x)).
4) PlayerNetState 546비트 고정 + 변형(variant) 인덱스별 패딩 확인.
5) PlayerNetControl 지연 추정기(0.992/0.03/2~5프레임) 재구현 시뮬레이션 표.
결과: analysis/network/verify_result.json
"""
import csv
import json
import math
import random
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC

ROOT = Path(__file__).resolve().parents[2]
F = np.float32


def f(x):
    return F(x)


def q_pos17(v):
    a = f(abs(f(v)))
    u = int(f(f(a * f(0.00390625)) * f(65535.0))) if a * 0.00390625 * 65535 < 2**32 else 0xFFFFFFFF
    u = min(u, 0xFFFF)
    return u | (0x10000 if f(v) < 0 else 0)


def dq_pos17(u):
    m = f(f(u & 0xFFFEFFFF) / f(65535.0))
    return float(f(m * f(-256.0)) if u & 0x10000 else f(m * f(256.0)))


def q_speed(vx, vy, vz, mul, rng, nbits):
    """속도 헬퍼의 크기 부분(원본: |v*mul| -> /mul*mul -> /rng*(2^n-1))"""
    x, y, z = f(f(vx) * f(mul)), f(f(vy) * f(mul)), f(f(vz) * f(mul))
    L = f(math.sqrt(float(f(f(f(x * x) + f(y * y)) + f(z * z)))))
    if L <= 0.0001:
        L = f(0.0)
    inv = f(1.0 / mul) if mul == 60 else f(0.00027777778)
    s = f(f(L * (f(0.016666668) if mul == 60 else f(0.00027777778))) * f(mul))
    maxq = (1 << nbits) - 1
    u = int(f(f(s * f(1.0 / rng)) * f(maxq)))
    return min(u, maxq)


def main():
    rows = list(csv.DictReader(open(ROOT / "analysis/network/nettypes.tsv", encoding="utf-8"), delimiter="\t"))
    u = UC()
    res = {}

    # 1) 전 타입 비트 합계
    tot = []
    for r in rows:
        if not r["ctor"] or not r["write"] or r["ctor"] == "None":
            continue
        size = int(r["obj_size"])
        obj = u.alloc(size + 0x40)
        try:
            u.call(int(r["ctor"], 16), obj)
            u.unknown = []
            log = u.write(int(r["write"], 16), obj)
            bits = sum(n for k, n, v in log)
            want = r["bits_max"]
            tot.append(dict(name=r["name"], bits=bits, reg_min=r["bits_min"], reg_max=want,
                            ok=str(bits) == want or str(bits) == r["bits_min"], unknown=sorted(set(u.unknown))))
        except Exception as e:
            tot.append(dict(name=r["name"], error=str(e)[:80]))
    okc = sum(1 for t in tot if t.get("ok"))
    res["all_types_default_write"] = dict(total=len(tot), ok=okc, items=tot)
    print(f"[1] 기본 생성 객체 write 비트 합 = 등록 비트(min 또는 max): {okc}/{len(tot)}")
    for t in tot:
        if not t.get("ok"):
            print("    ", t)

    # 2) 위치 17bit 재구현 대조 + 3) BulletShooter 왕복
    random.seed(1)
    obj = u.alloc(0x48)
    o2 = u.alloc(0x48)
    mism = {"pos": 0, "speed": 0}
    maxerr = {"pos": 0.0, "dir_dot_min": 1.0}
    N = 3000
    dir_diff = []
    for i in range(N):
        u.call(0x71023E0AF0, obj)
        p = [random.uniform(-300, 300) for _ in range(3)]
        if i % 50 == 0:
            p = [random.choice([0.0, 255.999, -255.999, 256.0, 1e-6, -1e-6, 0.00390625])] * 3
        v = [random.uniform(-1.5, 1.5) for _ in range(3)]
        if i % 37 == 0:
            v = [0.0, 0.0, 0.0]
        for k in range(3):
            u.f32(obj + 0x20 + 4 * k, p[k])
            u.f32(obj + 0x2C + 4 * k, v[k])
        u.f32(obj + 0x38, random.uniform(0, 7.99))
        u.u32(obj + 0x3C, random.randrange(16))
        log = u.write(0x71023E0C28, obj)
        vals = [x[2] for x in log]
        for k in range(3):
            if vals[k] != q_pos17(p[k]):
                mism["pos"] += 1
        sp = q_speed(*v, 60, 2048.0, 16)
        if vals[5] != sp:
            mism["speed"] += 1
        u.call(0x71023E0AF0, o2)
        u.read(0x71023E0FA8, o2, log)
        for k in range(3):
            d = u.rf32(o2 + 0x20 + 4 * k)
            if d != dq_pos17(vals[k]):
                mism["pos"] += 1
            if abs(p[k]) < 256:
                maxerr["pos"] = max(maxerr["pos"], abs(d - p[k]))
        dv = [u.rf32(o2 + 0x2C + 4 * k) for k in range(3)]
        Lv = math.sqrt(sum(x * x for x in v))
        Ld = math.sqrt(sum(x * x for x in dv))
        if Lv > 1e-3 and Ld > 0:
            dot = sum(a * b for a, b in zip(v, dv)) / (Lv * Ld)
            maxerr["dir_dot_min"] = min(maxerr["dir_dot_min"], dot)
            # 방향 파이썬 근사(atan2/asin) 대비 LSB 차
            nx, ny, nz = [x / Lv for x in v]
            pitch = math.asin(max(-1, min(1, ny)))
            yaw = math.atan2(nx, nz)
            qp = min(int(abs(pitch) / (math.pi / 2) * 2047), 2047)
            qy = min(int(abs(yaw) / math.pi * 4095), 4095)
            dir_diff.append((abs((vals[3] & 0x7FF) - qp), abs((vals[4] & 0xFFF) - qy)))
    res["bullet_shooter_roundtrip"] = dict(N=N, mismatch=mism, maxerr=maxerr,
                                           dir_python_vs_orig_max_lsb=[max(d[0] for d in dir_diff), max(d[1] for d in dir_diff)],
                                           dir_python_vs_orig_exact_rate=sum(1 for d in dir_diff if d == (0, 0)) / len(dir_diff))
    print(f"[2,3] BulletShooter 왕복 {N}회: 재구현 불일치 {mism}, 위치 최대오차 {maxerr['pos']:.6f}, 속도방향 최소 cos {maxerr['dir_dot_min']:.6f}")
    print(f"      방향 파이썬 atan2/asin 근사 vs 원본 표 기반: 최대 LSB 차(pitch,yaw)={res['bullet_shooter_roundtrip']['dir_python_vs_orig_max_lsb']}, 완전일치율 {res['bullet_shooter_roundtrip']['dir_python_vs_orig_exact_rate']:.3f}")

    # 4) PlayerNetState
    ps = next(r for r in rows if r["name"] == "spl::PlayerNetState")
    obj = u.alloc(0x1D0 + 0x40)
    u.call(int(ps["ctor"], 16), obj)
    idx = (u.ru32(obj + 0xE0), u.ru32(obj + 0x128), u.ru32(obj + 0x160))
    log = u.write(int(ps["write"], 16), obj)
    pbits = sum(n for k, n, v in log)
    kinds = {}
    for k, n, v in log:
        kinds[k] = kinds.get(k, 0) + 1
    res["player_net_state_default"] = dict(variant_index=idx, bits=pbits, items=len(log), kinds=kinds)
    print(f"[4] PlayerNetState 기본 객체: variant 인덱스(+0xe0,+0x128,+0x160)={idx}, 비트 합 {pbits}, 항목 {kinds}")

    # 4b) variant 인덱스 -> 하위 상태 타입 (원본 read 에 인덱스 값을 공급, 생성된 vtable 로 판정)
    vt2name = {int(r["vtable"], 16): r["name"].replace("spl::PlayerNetState_", "") for r in rows if r["vtable"] not in ("", "None")}
    vmap = {}
    for slot, pos, stor, rng in (("v1(+0xe0)", 32, 0xB0, 2), ("v2(+0x128)", 36, 0xE8, 4), ("v3(+0x160)", None, 0x130, 16)):
        vmap[slot] = {}
        for val in range(rng):
            o = u.alloc(0x210)
            u.call(int(ps["ctor"], 16), o)
            if pos is None:
                # v1=Squid(3bit) 기본, v2=Jump 기본일 때 v3 인덱스 읽기 위치 = 46
                u.feed_fn = lambda i, n, val=val: val if i == 46 else 0
            else:
                u.feed_fn = lambda i, n, val=val, pos=pos: val if i == pos else 0
            u.rlog = []
            u.call(int(ps["read"], 16), o, u.S)
            u.feed_fn = None
            vt = struct.unpack("<Q", u.mu.mem_read(o + stor, 8))[0]
            vmap[slot][val] = vt2name.get(vt, hex(vt))
    res["player_net_state_variants"] = vmap
    print("[4b] variant 인덱스 -> 타입:", vmap)

    # 5) 지연 추정기 재구현
    def sim(latency, period=4, frames=600, jitter=0):
        D = 0.0
        w = 1.0
        S = 0.0
        out = []
        rnd = random.Random(7)
        for t in range(frames):
            recv = (t % period == 0)
            if not recv:
                w *= 0.992
            else:
                lat = latency + (rnd.randint(-jitter, jitter) if jitter else 0)
                delta = float(lat)
                D = D + (1.0 - w) * (delta - D)
                w = 1.0
            if D > 5.0:
                T = D - 5.0
            elif D < 2.0:
                T = D - 2.0
            else:
                T = 0.0
            S = S + (T - S) * 0.03
            if t in (0, 4, 60, 120, 300, 599):
                out.append(dict(frame=t, D=round(D, 4), S=round(S, 4)))
        return out
    res["delay_estimator_sim"] = {f"lat{l}_period4": sim(l) for l in (1, 3, 8)}
    res["delay_estimator_sim"]["lat8_period1"] = sim(8, period=1)
    print("[5] 지연 추정기(재구현) lat=8프레임, 4프레임 주기:", res["delay_estimator_sim"]["lat8_period4"])
    print("    lat=8, 매 프레임 수신(주기1):", res["delay_estimator_sim"]["lat8_period1"])
    (ROOT / "analysis/network/verify_result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
