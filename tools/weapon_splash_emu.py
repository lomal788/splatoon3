"""스플래시 일정·생성을 원본 함수로 실행(unicorn)해 weapon_splash_sim.py 재구현과 비트 비교.

실행하는 원본: 슬롯15 0x710174efc0(BulletSimple 시작 0x7101762f68 호출만 건너뜀),
             슬롯56 0x71017512bc → 0x7101751304 → 0x71017540ec → 0x71012500d4 (실제 코드).
스텁(파이썬 훅):
  0x710164434c  탄 위치(바디 +0x94) → s0..s2 = 재구현이 적분한 위치
  0x71038a94fc  파라미터 배열 개수 → ForceSpawnNearestAddNumArray 길이
  0x7103e99ef0  __cxa_guard_acquire → 0 (정적 형식 변수 초기화 생략; 형식 검사 스텁이 값을 보지 않음)
  0x71016e3af4  탄 관리자 생성 요청 → 요청 구조체(x2) 0xe0 B 기록 후 0 반환(실제 생성 안 함)
  파라미터 객체 vtable[0](형식 검사) → 1, 배열 vtable[0x78](i) → &arr[i], 탄 vtable 은 0x188(getVelocity)=원본 0x7101762d00, 나머지 0 반환
가정: 탄 이동(위치·속도·상태)은 재구현값을 매 프레임 탄 객체에 써 넣음(이동 자체는 이 도구의 검증 범위 밖).
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bullet_shooter_sim as bs  # noqa: E402
import weapon_splash_sim as ws  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000
STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000
END = STUB + 0xF00
S_RET0, S_RET1, S_ARR = STUB + 0x0, STUB + 0x10, STUB + 0x20
F = np.float32


def fb(x):
    return struct.pack("<f", float(F(x)))


class Emu:
    def __init__(self):
        img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x100000)
        mu.mem_map(STUB, 0x1000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        mu.mem_write(STUB, struct.pack("<I", 0xD65F03C0) * 0x400)
        self.hnext = HEAP
        self.pos = (F(0), F(0), F(0))
        self.arr = []
        self.reqs = []
        self.handlers = {
            0x7101762f68: self._ret0, 0x710164434c: self._pos, 0x71038a94fc: self._cnt,
            0x7103e99ef0: self._ret0, 0x71016e3af4: self._req,
            S_RET0: self._ret0, S_RET1: self._ret1, S_ARR: self._arrget,
        }
        for a in self.handlers:
            mu.hook_add(UC_HOOK_CODE, self._hook, begin=a, end=a)

    def alloc(self, n):
        a = self.hnext
        self.hnext += (n + 0xF) & ~0xF
        self.mu.mem_write(a, b"\0" * n)
        return a

    def _hook(self, mu, addr, size, user):
        h = self.handlers.get(addr)
        if h is None:
            return
        h()
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def _ret0(self):
        self.mu.reg_write(UC_ARM64_REG_X0, 0)

    def _ret1(self):
        self.mu.reg_write(UC_ARM64_REG_X0, 1)

    def _pos(self):
        for r, v in zip((UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2), self.pos):
            self.mu.reg_write(r, struct.unpack("<I", fb(v))[0])

    def _cnt(self):
        self.mu.reg_write(UC_ARM64_REG_X0, len(self.arr))

    def _arrget(self):
        i = self.mu.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF
        self.mu.reg_write(UC_ARM64_REG_X0, self.arr_base + 4 * i)

    def _req(self):
        x2 = self.mu.reg_read(UC_ARM64_REG_X2)
        self.reqs.append(bytes(self.mu.mem_read(x2, 0xe0)))
        self.mu.reg_write(UC_ARM64_REG_X0, 0)

    def call(self, fn, x0, x1=0):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_X0, x0)
        mu.reg_write(UC_ARM64_REG_X1, x1)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(fn, END, count=5_000_000)

    def rf(self, a):
        return F(struct.unpack("<f", self.mu.mem_read(a, 4))[0])

    def ru(self, a, n=4):
        return int.from_bytes(self.mu.mem_read(a, n), "little")

    def setup(self, sp, idx, gseed, frame, dir0, speed, pos0):
        mu = self.mu
        self.arr = [int(v) for v in sp["ForceSpawnNearestAddNumArray"]]
        self.arr_base = self.alloc(4 * max(1, len(self.arr)))
        mu.mem_write(self.arr_base, b"".join(struct.pack("<i", v) for v in self.arr) or b"\0" * 4)
        pv = self.alloc(0x400)
        for off in range(0, 0x400, 8):
            mu.mem_write(pv + off, struct.pack("<Q", S_RET1))
        av = self.alloc(0x100)
        for off in range(0, 0x100, 8):
            mu.mem_write(av + off, struct.pack("<Q", S_RET0))
        mu.mem_write(av + 0x78, struct.pack("<Q", S_ARR))
        P = self.alloc(0x100)
        mu.mem_write(P, struct.pack("<Q", pv))
        mu.mem_write(P + 0x30, struct.pack("<Q", av))
        mu.mem_write(P + 0x58, fb(sp["RandomSpawnVelXMax"]) + fb(sp["RandomSpawnVelYMax"]) + fb(sp["RandomSpawnVelZMax"])
                     + fb(sp["RandomSpawnVelZMin"]) + fb(sp["SpawnBetweenLength"]) + fb(sp["SpawnNearestLength"])
                     + fb(sp["SpawnNum"]) + struct.pack("<i", int(sp["SplitNum"])))
        mu.mem_write(P + 0x78, b"\1" * 9)
        H = self.alloc(0x20)
        mu.mem_write(H, struct.pack("<Q", P))
        mu.mem_write(H + 0xc, struct.pack("<I", 7))
        I = self.I = self.alloc(0x200)
        buf = self.alloc(0x40)
        mu.mem_write(buf, b"BulletSplashShooter\0")
        mu.mem_write(I + 0x2c, struct.pack("<i", 0))
        mu.mem_write(I + 0x30, fb(pos0[0]) + fb(pos0[1]) + fb(pos0[2]) + fb(dir0[0]) + fb(dir0[1]) + fb(dir0[2]) + fb(speed))
        mu.mem_write(I + 0x64, struct.pack("<i", frame))
        mu.mem_write(I + 0x6d, b"\1")
        mu.mem_write(I + 0x90, bytes([idx]))
        mu.mem_write(I + 0xa8, struct.pack("<Q", buf))
        mu.mem_write(I + 0xb0, struct.pack("<i", 0x40))
        mu.mem_write(I + 0xf0, struct.pack("<Q", H))
        mu.mem_write(I + 0xf8, struct.pack("<I", 7))
        bv = self.alloc(0x400)
        for off in range(0, 0x400, 8):
            mu.mem_write(bv + off, struct.pack("<Q", S_RET0))
        mu.mem_write(bv + 0x188, struct.pack("<Q", 0x7101762d00))
        B = self.B = self.alloc(0x1300)
        mu.mem_write(B, struct.pack("<Q", bv))
        mu.mem_write(B + 0x108, struct.pack("<Q", I))
        M = self.alloc(0x200)
        mu.mem_write(M + 0x120, struct.pack("<i", gseed))
        mu.mem_write(0x7105850620, struct.pack("<Q", M))

    def bullet_fields(self):
        B = self.B
        r = {k: float(self.rf(B + o)) for k, o in (("f11f4", 0x11f4), ("f11f8", 0x11f8), ("f1200", 0x1200), ("f1204", 0x1204),
                                                    ("f1208", 0x1208), ("f120c", 0x120c))}
        r["hex"] = {k: "0x%08x" % self.ru(B + o) for k, o in (("f11f4", 0x11f4), ("f11f8", 0x11f8), ("f1208", 0x1208), ("f120c", 0x120c))}
        r["isLast"], r["forced"], r["f11fc"] = self.ru(B + 0x11ed, 1), self.ru(B + 0x11ee, 1), self.ru(B + 0x11fc)
        r["tailVel"] = [float(self.rf(B + 0x11e0 + 4 * i)) for i in range(3)]
        r["tailPos"] = [float(self.rf(B + 0x11c8 + 4 * i)) for i in range(3)]
        return r


def parse_req(q):
    f = lambda o: F(struct.unpack_from("<f", q, o)[0])
    h = lambda o: "0x%08x" % struct.unpack_from("<I", q, o)[0]
    return {"pos": [float(f(0x30 + 4 * i)) for i in range(3)], "pos_hex": [h(0x30 + 4 * i) for i in range(3)],
            "dir": [float(f(0x3c + 4 * i)) for i in range(3)], "dir_hex": [h(0x3c + 4 * i) for i in range(3)],
            "speed": float(f(0x48)), "speed_hex": h(0x48), "isNearest": q[0x90], "frame64": struct.unpack_from("<i", q, 0x64)[0],
            "team2c": struct.unpack_from("<i", q, 0x2c)[0], "local6d": q[0x6d], "paintDir94_98": [float(f(0x94)), float(f(0x98))],
            "vt": "0x%x" % struct.unpack_from("<Q", q, 0)[0], "f68": h(0x68), "f6c": q[0x6c], "f1c": h(0x1c), "f28": h(0x28)}


def run_one(table, idx, gseed, frame, frames=200, dir_in=(0.0, 0.0, 1.0)):
    p = bs.load_move_param(table)
    sp = ws.load_spawn_param(table)
    speed = F(p["SpawnSpeed"])
    dir0 = tuple(F(c) for c in dir_in)
    pos0 = (F(0), F(0), F(0))
    e = Emu()
    e.setup(sp, idx, gseed, frame, dir0, speed, pos0)
    e.call(0x710174efc0, e.B, 0)
    start = e.bullet_fields()
    ref = ws.run(table, idx, gseed, frame, frames, dir0=dir0)
    B = e.B
    vel = (F(dir0[0] * speed), F(speed * dir0[1]), F(speed * dir0[2]))
    pos, age, state, sframe = pos0, -1, bs.initial_state(p), 0
    mis, emu_sp = [], []
    for k in range(frames):
        prev = pos if age >= 0 else pos0
        if age >= 0:
            prev = pos
        age += 1
        v = np.array(vel, F)
        if age == 1:
            l = ws.len3(*v)
            if l > F(0):
                kk = F(speed / l)
                v = np.array([F(v[0] * kk), F(v[1] * kk), F(v[2] * kk)], F)
        o, done = bs.STEPS[state](p, v, sframe)
        state, sframe = (state + 1, 0) if done else (state, sframe + 1)
        if age != 0:
            vel = tuple(F(c) for c in o)
        pos = tuple(F(F(ws.DT * F(vel[i] * ws.SIXTY)) + pos[i]) for i in range(3))
        e.mu.mem_write(B + 0x110, b"".join(fb(c) for c in prev))
        e.mu.mem_write(B + 0x1118, b"".join(fb(c) for c in vel))
        e.mu.mem_write(B + 0x198, struct.pack("<I", state))
        e.pos = pos
        n0 = len(e.reqs)
        e.call(0x71017512bc, B)
        for q in e.reqs[n0:]:
            r = parse_req(q)
            r["age"] = age
            emu_sp.append(r)
        if pos[1] < F(-10.0):
            break
    for a, b in zip(emu_sp, ref["spawns"]):
        for key in ("pos_hex", "dir_hex", "speed_hex"):
            if a[key] != b[key]:
                mis.append((a["age"], key, a[key], b[key]))
        if a["age"] != b["frame_age"] or bool(a["isNearest"]) != b["isNearest"]:
            mis.append((a["age"], "age/near", a["isNearest"], b["frame_age"]))
    if len(emu_sp) != len(ref["spawns"]):
        mis.append(("count", len(emu_sp), len(ref["spawns"])))
    s = ref["schedule"]
    for key in ("f11f4", "f11f8", "f1208", "f120c"):
        if s[key] is not None and start["hex"][key] != s[key]["hex"]:
            mis.append(("start", key, start["hex"][key], s[key]["hex"]))
    for key in ("isLast", "forced", "f11fc"):
        if int(start[key]) != int(s[key]):
            mis.append(("start", key, start[key], s[key]))
    end = e.bullet_fields()
    return {"idx": idx, "start": start, "end": end, "spawns": emu_sp, "mismatch": mis}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table", nargs="?", default="WeaponShooterNormal")
    ap.add_argument("--global-seed", type=int, default=10)
    ap.add_argument("--frame", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=0, help="추가로 무작위 (전역, 프레임) 쌍 N개 비교")
    ap.add_argument("--dir", type=float, nargs=3, default=(0.0, 0.0, 1.0), help="생성정보 발사 방향(그대로 f32로 씀)")
    ap.add_argument("--json")
    a = ap.parse_args()
    sp = ws.load_spawn_param(a.table)
    pairs = [(a.global_seed, a.frame)]
    rng = np.random.default_rng(7)
    pairs += [(int(rng.integers(0, 2**31)), int(rng.integers(0, 100000))) for _ in range(a.seeds)]
    out, total = [], 0
    for gs, fr in pairs:
        for idx in range(int(sp["SplitNum"]) or 1):
            r = run_one(a.table, idx, gs, fr, dir_in=tuple(a.dir))
            total += len(r["mismatch"])
            if gs == a.global_seed and fr == a.frame:
                out.append(r)
                print(f"idx {idx}: start={r['start']['hex']} 11fc={r['start']['f11fc']} last={r['start']['isLast']} forced={r['start']['forced']} "
                      f"spawns={len(r['spawns'])} mismatch={r['mismatch']}")
                for q in r["spawns"]:
                    print(f"   age {q['age']} near={q['isNearest']} pos={q['pos_hex']} dir={q['dir_hex']} spd={q['speed_hex']} "
                          f"f64={q['frame64']} 6d={q['local6d']} 94/98={q['paintDir94_98']} vt={q['vt']} 68={q['f68']} 6c={q['f6c']}")
            elif r["mismatch"]:
                print("MISMATCH", gs, fr, idx, r["mismatch"][:3])
    print(f"pairs={len(pairs)} 총 불일치 {total}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
