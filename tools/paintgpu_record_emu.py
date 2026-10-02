"""도색 네트워크 레코드 N(0x60 B) → GPU 그리기 레코드 D 변환 함수 0x7102c11f80 원본 실행 검증.

원본 실행(unicorn) 결과와 재구현(re_convert)을 무작위 입력으로 비교한다.
- 대상 종류 N+0x38 = 1(Floor) 로 고정: 0x7102c4a6bc 가 위치를 그대로 돌려주는 경로(전역 대상 표 불필요).
- InkTexInfo 런타임 표(*0x71058eeae8, 행 0xd0 B × 50, 표+0x40 부터)는 analysis/paint/InkTexInfo.json 을
  InkTexType 열거 순서로 채운 가짜 표. 행 필드 배치: +0x00 텍스처 수, +0x08 텍스처 배열(0xf8 B 간격),
  +0x10 PatternNum(나눗수), +0x14 AnimationFrame, +0x18 AnimationStep, +0xb8 HeightRangeType,
  +0xbc/+0xc0 높이 (max,min), +0xc4 HeightRangeRate, +0xc8 DisableSlopeScale.
  (+0x14/+0x18/+0xb8/+0xc8 는 소비 코드와 이름이 맞고, 나머지 이름 대응은 추정)
- 스텁: nn::os::GetSystemTick(0x7103e9a3d0) → 0 반환(결과에 쓰이지 않음).
- 온라인 플래그 *(*0x71057908b8)+0x195 는 입력으로 바꿔 가며 확인.
사용: PY web/tools/paintgpu_record_emu.py [건수]
"""
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK, HEAP, CODE = 0x10000000, 0x20000000, 0x30000000
FN = 0x7102C11F80
TICK = 0x7103E9A3D0
G_NET = 0x7105825FD0          # *0x71057908b8 가 가리키는 GameNet 포인터 변수
G_TABLE = 0x71058EEAE8        # InkTexInfo 런타임 표 포인터 변수
TEX_BASE = 0x40000000
INKTEX = ("Shot00 Shot01 Shot02 Shot03 Shot04 RlrSplash00 RlrSplash01 RlrSplash02 ChgrSplash00 ChgrSplash01 "
          "Bomb00 WallDrip00 WallDrip01 Roller00 PaintLift00 PaintLift01 Disk Rectangle InkRutStart InkRutMove "
          "QuadDonut Rain00_0 Rain00_1 Rain00_2 SprBall00 StampKingFace Common WallDrip00_0 WallDrip00_1 "
          "WallDrip00_2 WallDrip00_3 WallDrip00_4 WallDrip01_0 WallDrip01_1 WallDrip01_2 WallDrip01_3 "
          "WallDrip01_4 SpStamp00 Death00 SprLanding00 Manta GachihokoCross00 BombLineMarker Slosher00 Chgr00 "
          "Bomb00Height3pnt4 Bomb00ForBombFlower TripleTornado DiskHD AllPaint").split()
HTYPE = {"MinEdge": 0, "MaxEdge": 1, "Static": 2, "None": 3}


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def load_rows():
    rows = {}
    for r in json.load(open(ROOT / "analysis" / "paint" / "InkTexInfo.json", encoding="utf-8")):
        name = r["__RowId"].split("/")[-1].split(".")[0]
        rows[name] = r
    out = []
    for i, n in enumerate(INKTEX):
        r = rows[n]
        out.append(dict(count=r["PatternNum"], div=r["PatternNum"], af=r["AnimationFrame"], st=r["AnimationStep"],
                        htype=HTYPE[r["HeightRangeType"]], hmax=r["StaticHeightRangeMax"], hmin=r["StaticHeightRangeMin"],
                        rate=r["HeightRangeRate"], disable=1 if r["DisableSlopeScale"] else 0,
                        tex=TEX_BASE + i * 0x10000))
    return out


def table_bytes(rows):
    t = bytearray(0x40 + 0xd0 * 0x32)
    for i, r in enumerate(rows):
        o = 0x40 + i * 0xd0
        struct.pack_into("<I", t, o + 0x00, r["count"])
        struct.pack_into("<Q", t, o + 0x08, r["tex"])
        struct.pack_into("<IIi", t, o + 0x10, r["div"], r["af"], r["st"])
        struct.pack_into("<iffff", t, o + 0xb8, r["htype"], r["hmax"], r["hmin"], r["rate"], 0.0)
        t[o + 0xc8] = r["disable"]
    return bytes(t)


def sead_first(seed):
    M = 0x6C078965
    s0 = ((seed ^ (seed >> 30)) * M + 1) & 0xFFFFFFFF
    s1 = ((s0 ^ (s0 >> 30)) * M + 2) & 0xFFFFFFFF
    s2 = ((s1 ^ (s1 >> 30)) * M + 3) & 0xFFFFFFFF
    s3 = ((s2 ^ (s2 >> 30)) * M + 4) & 0xFFFFFFFF
    t = (s0 ^ (s0 << 11)) & 0xFFFFFFFF
    return (t ^ (t >> 8) ^ s3 ^ (s3 >> 19)) & 0xFFFFFFFF


def fcvtzs(x):
    if x != x:
        return 0
    v = int(x)
    return max(-2**31, min(2**31 - 1, v))


def re_convert(N, rows, online):
    """재구현: N(bytes 0x60) → D 필드 dict"""
    u8 = lambda o: N[o]
    u16 = lambda o: struct.unpack_from("<H", N, o)[0]
    u32 = lambda o: struct.unpack_from("<I", N, o)[0]
    i32 = lambda o: struct.unpack_from("<i", N, o)[0]
    fl = lambda o: struct.unpack_from("<f", N, o)[0]
    D = {}
    D[0x52] = u16(0x3e)
    D[0x08] = u8(0)
    n4 = u32(4)
    if not online:
        v = (n4 * 11) & 0xFFFFFFFF
    elif n4 == 0x1745D1:
        v = 0xFFFFFB
    else:
        v = (n4 * 11 + u8(0)) & 0xFFFFFFFF
    D[0x0c] = f32(f32(float(v)) * 0.0625)
    D[0x10] = u32(0x34)
    D[0x14] = (fl(8), fl(0xc), fl(0x10))
    typ = i32(0x40)
    row = rows[typ] if 0 <= typ < 0x32 else None
    nrm = (fl(0x1c), fl(0x20), fl(0x24))
    if row is not None and row["disable"]:
        nrm = (0.0, 0.0, 0.0)
    D[0x30] = nrm
    D[0x28] = (fl(0x14), fl(0x18))
    D[0x4c] = u32(0x38)
    D[0x68] = u32(0x40)
    W, L = fl(0x14), fl(0x18)
    if u8(0x4b):
        D[0x20] = (fl(0x4c), fl(0x50))
    else:
        ht = row["htype"]
        if ht == 2:
            D[0x20] = (f32(row["hmax"]), f32(row["hmin"]))
        elif ht in (0, 1):
            e = (W if W > L else L) if ht == 1 else (W if W < L else L)   # MaxEdge: fcsel gt / MinEdge: fcsel mi
            h = f32(e * 0.5)
            D[0x20] = (f32(f32(row["rate"]) * h), -f32(f32(row["rate"]) * h))
        else:
            D[0x20] = (20000.0, -20000.0)
    D[0x6e] = 1 if (u8(0x49) != 0 and (u16(0x3e) >> 10) > 4) else 0
    D[0x49] = row["af"] & 0xFF
    D[0x4a] = row["st"] & 0xFF
    if u8(0x54):
        seed = u32(0x58)
    else:
        x, y, z = fl(8), fl(0xc), fl(0x10)     # Floor: 0x7102c4a6bc 는 위치 그대로
        s = f32(f32(z + f32(x + y)) * 100.0)
        seed = (abs(fcvtzs(s)) + n4) & 0xFFFFFFFF
    D[0x54] = seed
    r = sead_first(seed)
    div = row["div"]
    idx = r if div == 0 else r % div
    D[0x60] = row["tex"] + idx * 0xF8 if idx < row["count"] else row["tex"]
    D[0x3c] = (fl(0x28), fl(0x2c), fl(0x30))
    a = u8(0x48)
    D[0x6d] = 0
    if i32(0x44) == 3:
        q = f32(f32(f32(a / 255.0) * float(row["af"] & 0xFF)))
        q = min(q, 1.0)
        a = fcvtzs(f32(q * 255.0)) & 0xFF
        if n4 == 0x1745D1:
            D[0x6d] = 1
    D[0x58] = a
    D[0x6c] = 1 if i32(0x44) != 1 else 0
    return D


class Emu:
    def __init__(self, rows):
        img = IMG.read_bytes()
        self.mu = mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x100000)
        mu.mem_map(CODE, 0x1000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        mu.mem_write(CODE, struct.pack("<I", 0xD65F03C0) * 0x400)
        self.T = HEAP + 0x10000
        mu.mem_write(self.T, table_bytes(rows))
        mu.mem_write(G_TABLE, struct.pack("<Q", self.T))
        self.GN = HEAP + 0x8000
        mu.mem_write(G_NET, struct.pack("<Q", self.GN))
        self.N = HEAP + 0x1000
        self.D = HEAP + 0x2000

        def hook(m, addr, size, user):
            if addr == TICK:
                m.reg_write(UC_ARM64_REG_X0, 0)
                m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_X30))
        mu.hook_add(UC_HOOK_CODE, hook, begin=TICK, end=TICK + 4)

    def run(self, N, online):
        mu = self.mu
        mu.mem_write(self.GN + 0x195, bytes([1 if online else 0]))
        mu.mem_write(self.N, N)
        mu.mem_write(self.D, b"\xAA" * 0x90)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
        mu.reg_write(UC_ARM64_REG_X0, self.D)
        mu.reg_write(UC_ARM64_REG_X1, self.N)
        mu.reg_write(UC_ARM64_REG_X30, CODE + 0x100)
        mu.emu_start(FN, CODE + 0x100, count=100000)
        return bytes(mu.mem_read(self.D, 0x90))


def read_D(b):
    fl = lambda o: struct.unpack_from("<f", b, o)[0]
    u32 = lambda o: struct.unpack_from("<I", b, o)[0]
    return {0x52: struct.unpack_from("<H", b, 0x52)[0], 0x08: b[8], 0x0c: fl(0xc), 0x10: u32(0x10),
            0x14: (fl(0x14), fl(0x18), fl(0x1c)), 0x30: (fl(0x30), fl(0x34), fl(0x38)), 0x28: (fl(0x28), fl(0x2c)),
            0x4c: u32(0x4c), 0x68: u32(0x68), 0x20: (fl(0x20), fl(0x24)), 0x6e: b[0x6e], 0x49: b[0x49], 0x4a: b[0x4a],
            0x54: u32(0x54), 0x60: struct.unpack_from("<Q", b, 0x60)[0], 0x3c: (fl(0x3c), fl(0x40), fl(0x44)),
            0x58: b[0x58], 0x6c: b[0x6c], 0x6d: b[0x6d] if b[0x6d] == 1 else 0}


def rand_N(rng):
    N = bytearray(0x60)
    N[0] = rng.choice([0, 1, 3, 7, 8, 9, 10])
    struct.pack_into("<I", N, 4, rng.choice([0, 1, 12345, 0x1745D1, rng.randrange(0, 1 << 24)]))
    for o in (8, 0xc, 0x10):
        struct.pack_into("<f", N, o, f32(rng.uniform(-300, 300)))
    struct.pack_into("<ff", N, 0x14, f32(rng.uniform(0.1, 8)), f32(rng.uniform(0.1, 8)))
    for o in range(0x1c, 0x34, 4):
        struct.pack_into("<f", N, o, f32(rng.uniform(-1, 1)))
    struct.pack_into("<I", N, 0x34, rng.randrange(0, 3))
    struct.pack_into("<I", N, 0x38, 1)
    N[0x3c] = rng.randrange(0, 64)
    struct.pack_into("<H", N, 0x3e, rng.choice([0, 3, 0x1000, 0x1400, 0x2c00]))
    struct.pack_into("<i", N, 0x40, rng.randrange(0, 50))
    struct.pack_into("<i", N, 0x44, rng.randrange(0, 4))
    N[0x48] = rng.choice([0xff, 0x80, 0x40, 0x10, rng.randrange(256)])
    N[0x49] = rng.randrange(0, 2)
    N[0x4b] = 1 if rng.random() < 0.15 else 0
    struct.pack_into("<ff", N, 0x4c, f32(rng.uniform(0, 10)), f32(rng.uniform(-10, 0)))
    N[0x54] = 1 if rng.random() < 0.2 else 0
    struct.pack_into("<I", N, 0x58, rng.randrange(0, 1 << 32))
    return bytes(N)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    rows = load_rows()
    emu = Emu(rows)
    rng = random.Random(20261002)
    ok = 0
    bad = []
    hist = {}
    for k in range(n):
        N = rand_N(rng)
        online = rng.random() < 0.5
        got = read_D(emu.run(N, online))
        exp = re_convert(N, rows, online)
        diff = [hex(o) for o in exp if got[o] != exp[o]]
        if diff:
            bad.append((k, diff, {d: (got[int(d, 16)], exp[int(d, 16)]) for d in diff}))
        else:
            ok += 1
        typ = struct.unpack_from("<i", N, 0x40)[0]
        if typ == 0:
            idx = (got[0x60] - rows[0]["tex"]) // 0xF8
            hist[idx] = hist.get(idx, 0) + 1
    print(f"0x7102c11f80 원본 실행 vs 재구현: {ok}/{n} 일치")
    for b in bad[:10]:
        print("  불일치", b)
    print("Shot00 변형 번호 분포(원본 실행):", dict(sorted(hist.items())))
    # 고정 예: Shot00, 시드 직접 지정
    for seed in (0, 1, 12345, 0xFFFFFFFF):
        r = sead_first(seed)
        print(f"  seed {seed:#x}: 첫 난수 {r:#010x} → Shot00 변형 {r % 12}")


if __name__ == "__main__":
    main()
