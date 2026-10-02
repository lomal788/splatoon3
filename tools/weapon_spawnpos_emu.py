"""슈터 탄 생성 위치(0x7102552170)를 원본 그대로 unicorn 으로 실행하고, 파이썬 f32 재구현과 비트 대조한다.

구조체 S(호출자 0x7102583008 이 스택에 구성, float 배열):
  S[0..2]  본체+0x58..+0x60 (위치)          S[3..5] 본체+0x54c..+0x554 (리그 수평 시선 L)
  S[6]     본체+0x558 (카메라 피치 p, -1..1)  S[7..9] *0x71058bdeb8.. (오프셋 옆/위/앞)
  S+0x28 PitchDegMin, +0x2c PitchDegHorizon, +0x30 PitchDegMax,
  S+0x34 BezierKMin, +0x38 BezierKHor, +0x3c BezierKMax  (0x7102552710 이 spl__BulletShotDirParam 에서 복사)
  byte S+0x40 (y + 1.1), S+0x41 (p<0 일 때 위 오프셋을 0.6 쪽으로)

실행 순서: 정적 초기화 0x710257ff00(0x71058bdeb0 기본값 객체 채움) → 0x7102552710(S, param) → 0x7102552170(S).
param = 0(null)이면 전역 기본값(*0x710579ded0 = 0x71058bdeb0), 아니면 플래그 +0x48..+0x4d 를 모두 켠 가짜 파라미터 객체.

사용: PY web/tools/weapon_spawnpos_emu.py [--json 출력.json]
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn.arm64_const import (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_S0, UC_ARM64_REG_S1,
                                 UC_ARM64_REG_S2, UC_ARM64_REG_CPACR_EL1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from player_initemu import Emu, STACK  # noqa: E402
from xref import BASE, load_img  # noqa: E402

f32 = np.float32
INIT_FN = 0x710257FF00
COPY_FN = 0x7102552710
POS_FN = 0x7102552170
DEF_OBJ = 0x71058BDEB0
TBL_ADDR = 0x7104AA5B5C
S_ADDR = STACK + 0x1000
PARAM_ADDR = STACK + 0x2000

_TBL = struct.unpack_from("<1024f", load_img(), TBL_ADDR - BASE)


def bits(x):
    return struct.unpack("<I", struct.pack("<f", float(x)))[0]


def fb(u):
    return f32(struct.unpack("<f", struct.pack("<I", u))[0])


def sincos(theta):
    v = int(f32(theta * fb(0x4E22F983)))
    i = (v >> 24) & 0xFF
    fr = f32(f32(v & 0xFFFFFF) * fb(0x33800000))
    s = f32(f32(_TBL[4 * i]) + f32(f32(_TBL[4 * i + 1]) * fr))
    c = f32(f32(_TBL[4 * i + 2]) + f32(f32(_TBL[4 * i + 3]) * fr))
    return s, c


def spawn_pos(P, L, p, off, prm, b40=1, b41=1):
    """0x7102552170 의 f32 재구현(연산 순서 그대로). prm = (DegMin, DegHor, DegMax, KMin, KHor, KMax)"""
    Px, Py, Pz = (f32(v) for v in P)
    Lx, Ly, Lz = (f32(v) for v in L)
    p = f32(p)
    ox, oy, oz = (f32(v) for v in off)
    aMin, aHor, aMax, kMin, kHor, kMax = (f32(v) for v in prm)
    z = f32(0.0)
    if p < 0 and b41:
        oy = f32(oy - f32(f32(fb(0x3F19999A) - oy) * p))
    t1 = f32(Ly * z)
    t2 = f32(Lx * z)
    Rx = f32(Lz - t1)
    Ry = f32(t2 - f32(Lz * z))
    Rz = f32(t1 - Lx)
    ln = np.sqrt(f32(f32(Rz * Rz) + f32(f32(Rx * Rx) + f32(Ry * Ry))), dtype=f32)
    if ln > 0:
        inv = f32(f32(1.0) / ln)
        Rx, Ry, Rz = f32(Rx * inv), f32(inv * Ry), f32(Rz * inv)
    a = f32(Rx * z)
    c = f32(Ry * z)
    Fy = f32(f32(Rz * z) - a)
    Fx = f32(c - Rz)
    Fz = f32(Rx - c)
    b1k = f32(f32(aMax - aMin) * kHor)
    if p > 0:
        t = f32(f32(1.0) - p)
        m = f32(f32(p * f32(3.0)) * t)
        E = f32(f32(aMax - aHor) * kMax)
        B2 = f32(aMax - f32(E + E))
        B1 = f32(aHor + b1k)
        c0 = f32(t * f32(t * t))
        c1 = f32(t * m)
        c2 = f32(p * m)
        p3 = f32(p * f32(p * p))
        end = aMax
    else:
        r = f32(p + f32(1.0))
        m = f32(f32(p * f32(-3.0)) * r)
        E = f32(f32(aHor - aMin) * kMin)
        B2 = f32(aMin + f32(E + E))
        B1 = f32(aHor - b1k)
        c0 = f32(r * f32(r * r))
        c1 = f32(r * m)
        c2 = f32(m * f32(-p))
        p3 = f32(f32(p * p) * f32(-p))
        end = aMin
    deg = f32(f32(end * p3) + f32(f32(f32(aHor * c0) + f32(B1 * c1)) + f32(c2 * B2)))
    theta = f32(deg * fb(0xBC8EFA35))
    sn, cs = sincos(theta)
    Ux = f32(f32(Fx * sn) + f32(cs * z))
    Uy = f32(cs + f32(Fy * sn))
    Uz = f32(f32(Fz * sn) + f32(cs * z))
    Wx = f32(f32(Fx * cs) - f32(sn * z))
    Wy = f32(f32(Fy * cs) - sn)
    Wz = f32(f32(Fz * cs) - f32(sn * z))
    y0 = f32(Py + fb(0x3F8CCCCD)) if b40 else Py
    X = f32(Px + f32(f32(oz * Wx) + f32(f32(ox * Rx) + f32(oy * Ux))))
    Y = f32(y0 + f32(f32(oz * Wy) + f32(f32(ox * Ry) + f32(oy * Uy))))
    Z = f32(Pz + f32(f32(oz * Wz) + f32(f32(ox * Rz) + f32(oy * Uz))))
    return (X, Y, Z), deg


class SpawnEmu:
    def __init__(self):
        self.e = Emu()
        self.e.uc.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        r = self.e.run(INIT_FN)
        if r is not True:
            raise RuntimeError(f"init 실패: {r}")
        raw = bytes(self.e.uc.mem_read(DEF_OBJ, 0x2c))
        self.defobj = struct.unpack_from("<Q9f", raw)

    def call(self, fn, x0, x1=0):
        uc = self.e.uc
        uc.reg_write(UC_ARM64_REG_X0, x0)
        uc.reg_write(UC_ARM64_REG_X1, x1)
        r = self.e.run(fn)
        if r is not True:
            raise RuntimeError(f"{hex(fn)} 실패: {r}")

    def run(self, P, L, p, b40=1, b41=1, param=None):
        uc = self.e.uc
        off = struct.unpack("<3f", bytes(uc.mem_read(DEF_OBJ + 8, 12)))
        s = struct.pack("<10f", *P, *L, p, *off) + b"\0" * 0x18 + bytes([b40, b41]) + b"\0" * 6
        uc.mem_write(S_ADDR, s)
        pa = 0
        if param is not None:
            obj = bytearray(0x50)
            dMin, dHor, dMax, kMin, kHor, kMax = param
            struct.pack_into("<6f", obj, 0x30, kHor, kMax, kMin, dHor, dMax, dMin)
            for fl in range(0x48, 0x4E):
                obj[fl] = 1
            uc.mem_write(PARAM_ADDR, bytes(obj))
            pa = PARAM_ADDR
        self.call(COPY_FN, S_ADDR, pa)
        copied = struct.unpack("<6f", bytes(uc.mem_read(S_ADDR + 0x28, 0x18)))
        self.call(POS_FN, S_ADDR)
        out = [uc.reg_read(r) & 0xFFFFFFFF for r in (UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2)]
        return out, off, copied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    emu = SpawnEmu()
    d = emu.defobj
    print("기본값 객체 0x71058bdeb0: vtable=%#x  off=(%s)  DegMax/Hor/Min=(%s)  KMax/Hor/Min=(%s)" % (
        d[0], ", ".join("%g" % v for v in d[1:4]), ", ".join("%g" % v for v in d[4:7]),
        ", ".join("%g" % v for v in d[7:10])))
    P = (1.0, 2.0, 3.0)
    cases = []
    for L in [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.6, 0.0, 0.8)]:
        for p in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            cases.append(("default", P, L, p, None))
    charger = (-65.0, 0.0, 60.0, 0.185, 0.165, 0.148)
    for p in [-0.5, 0.5]:
        cases.append(("charger", P, (0.6, 0.0, 0.8), p, charger))
    rows = []
    bad = 0
    for tag, P_, L, p, prm in cases:
        out, off, copied = emu.run(P_, L, p, param=prm)
        ref, deg = spawn_pos(P_, L, p, off, copied)
        rb = [bits(v) for v in ref]
        ok = rb == out
        bad += not ok
        rows.append({"tag": tag, "P": P_, "L": L, "p": p, "param": copied, "offset": off,
                     "deg": float(deg), "emu_bits": ["%08x" % v for v in out],
                     "emu": [float(fb(v)) for v in out], "py_bits": ["%08x" % v for v in rb], "match": ok})
        print("%-7s L=(%g,%g,%g) p=%5g deg=%-11.7g emu=(%s) [%s] %s" % (
            tag, *L, p, deg, ", ".join("%.9g" % fb(v) for v in out), " ".join("%08x" % v for v in out),
            "OK" if ok else "MISMATCH py=" + " ".join("%08x" % v for v in rb)))
    print("불일치 %d / %d" % (bad, len(rows)))
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
