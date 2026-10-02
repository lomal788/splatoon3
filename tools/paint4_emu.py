"""ColPaint 아틀라스 원본 함수를 unicorn으로 실행해 paint4_colpaint.py 재구현과 비교한다.

대상(원본 함수 단독 실행):
  classify   0x7102bd7918  법선 → 방향 클래스
  basis      0x7102bd7b2c  방향 클래스 → 기저 3축
  slab       0x7102c0638c  프리즘 깊이 슬랩 비트
  touch      0x7102c05444  정점 공유 판정
  tricb      0x7102c0725c  메시 삼각형 콜백(실제 Fld_Yagara 충돌 삼각형 전부) → 프리즘(방향·슬랩)
  packer     0x7102c105bc  기요틴 패킹(+ 0x7102c104f8 빈칸 정렬 삽입)
  reproject  0x7102bf9850  패널 매핑 AABB 재투영
  horiz      0x7102bfda20  수평 묶음 픽셀 영역 크기·배치
스텁: PLT 는 x0=0 반환(player_initemu.Emu), atan2f/cosf/sinf/sqrtf 는 파이썬 math(double) → f32.
       malloc(0x710083d2f0)·free 는 범프 할당기 훅. 재구현도 같은 math 를 쓰므로 libm 1ulp 차이는 검증 범위 밖.
사용: PY web/tools/paint4_emu.py [--n 5000] [--out analysis/paint4/emu_out.txt]
"""
import argparse
import math
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_S0, UC_ARM64_REG_S1,
                                 UC_ARM64_REG_W0, UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2,
                                 UC_ARM64_REG_X3)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from player_initemu import Emu
import paint4_colpaint as cp

f32 = np.float32
HEAP = 0x7E00000000
HEAP_SIZE = 0x4000000
MATH = {0x7103E9C1E0: "atan2f", 0x7103E9BB50: "sqrtf", 0x7103E9BE30: "cosf", 0x7103E9BE40: "sinf"}
MALLOC, FREE = 0x710083D2F0, 0x710083D340


def fb(x):
    return struct.pack("<f", float(f32(x)))


def bits(x):
    return struct.unpack("<I", struct.pack("<f", float(f32(x))))[0]


def rdf(b, off=0):
    return f32(struct.unpack_from("<f", b, off)[0])


class PEmu(Emu):
    def __init__(self):
        super().__init__()
        self.uc.mem_map(HEAP, HEAP_SIZE)
        self.top = HEAP + 0x100000
        self.uc.hook_add(UC_HOOK_CODE, self._math, begin=0x7103E9B000, end=0x7103E9D000)
        self.uc.hook_add(UC_HOOK_CODE, self._alloc, begin=MALLOC, end=MALLOC)
        self.uc.hook_add(UC_HOOK_CODE, self._free, begin=FREE, end=FREE)

    def _math(self, uc, addr, size, ud):
        name = MATH.get(addr)
        if name is None:
            return
        s0 = float(struct.unpack("<f", struct.pack("<I", uc.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0])
        s1 = float(struct.unpack("<f", struct.pack("<I", uc.reg_read(UC_ARM64_REG_S1) & 0xFFFFFFFF))[0])
        if name == "atan2f":
            r = math.atan2(s0, s1)
        elif name == "cosf":
            r = math.cos(s0)
        elif name == "sinf":
            r = math.sin(s0)
        else:
            r = math.sqrt(s0) if s0 >= 0 else float("nan")
        uc.reg_write(UC_ARM64_REG_S0, bits(r))
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def _alloc(self, uc, addr, size, ud):
        n = uc.reg_read(UC_ARM64_REG_X0)
        a = self.alloc(max(n, 8))
        uc.reg_write(UC_ARM64_REG_X0, a)
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def _free(self, uc, addr, size, ud):
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_LR))

    def alloc(self, n, zero=True):
        a = (self.top + 0xF) & ~0xF
        self.top = a + n
        if self.top > HEAP + HEAP_SIZE:
            raise MemoryError
        if zero:
            self.uc.mem_write(a, b"\0" * n)
        return a

    def call(self, func, *args):
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3]
        for r, v in zip(regs, args):
            self.uc.reg_write(r, v)
        res = self.run(func, count=0)
        if res is not True:
            raise RuntimeError(f"{hex(func)}: {res}")
        return self.uc.reg_read(UC_ARM64_REG_X0)

    def w(self, a, b):
        self.uc.mem_write(a, b)

    def r(self, a, n):
        return bytes(self.uc.mem_read(a, n))


def rand_normal(rng):
    k = rng.random()
    if k < 0.15:  # 축·경계 근처
        ax = rng.choice([(0, 1, 0), (0, -1, 0), (1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 0, -1)])
        return tuple(a + rng.uniform(-0.02, 0.02) for a in ax)
    if k < 0.35:  # 클래스 경계 각도 근처
        el = rng.choice([22.5, 45.0, 67.5, 112.5, 157.5]) + rng.uniform(-0.3, 0.3)
        az = rng.choice([22.5 + 45 * i for i in range(8)]) + rng.uniform(-0.3, 0.3)
        e, a = math.radians(el), math.radians(az)
        return (math.sin(e) * math.sin(a), math.cos(e), math.sin(e) * math.cos(a))
    v = [rng.gauss(0, 1) for _ in range(3)]
    s = rng.uniform(0.2, 30.0)  # 정규화 전 길이
    return tuple(x * s for x in v)


def test_classify(e, rng, n, log):
    buf = e.alloc(32)
    bad = 0
    for i in range(n):
        v = rand_normal(rng)
        e.w(buf + 16, fb(v[0]) + fb(v[1]) + fb(v[2]))
        e.call(0x7102BD7918, buf, buf + 16)
        got = e.r(buf, 1)[0]
        exp = cp.classify(v)
        if got != exp:
            bad += 1
            if bad <= 5:
                log(f"  classify 불일치 n={v} 원본={got:#x} 재구현={exp:#x}")
    log(f"classify 0x7102bd7918: {n - bad}/{n} 일치")
    return bad


def test_basis(e, log):
    buf = e.alloc(64)
    bad = 0
    for d in list(range(0x2A)) + [0x2A, 0x30, 0xFF]:
        e.w(buf, bytes([d]))
        e.call(0x7102BD7B2C, buf, buf + 16, buf + 32, buf + 48)
        got = [e.r(buf + 16 + 16 * k, 12) for k in range(3)]
        exp = cp.basis(d)
        ok = all(got[k] == b"".join(fb(x) for x in exp[k]) for k in range(3))
        if not ok:
            bad += 1
            log(f"  basis 불일치 d={d:#x} 원본={[struct.unpack('<3f', g) for g in got]} 재구현={exp}")
    log(f"basis 0x7102bd7b2c: {45 - bad}/45 일치")
    return bad


def rand_tri(rng, span=180.0):
    c = [rng.uniform(-span, span) for _ in range(3)]
    s = rng.choice([0.05, 1.0, 5.0, 20.0])
    return [tuple(c[i] + rng.uniform(-s, s) for i in range(3)) for _ in range(3)]


def test_slab(e, rng, n, log):
    pr = e.alloc(0x60)
    db = e.alloc(16)
    bad = 0
    for i in range(n):
        t = rand_tri(rng, 260.0)
        d = rng.choice(list(range(0x2A)))
        e.w(pr, b"\0" * 0x60)
        e.w(pr + 8, b"".join(fb(x) for v in t for x in v))
        e.w(db, bytes([d]))
        e.call(0x7102C0638C, pr, db)
        got = struct.unpack("<I", e.r(pr + 0x2C, 4))[0]
        exp = cp.slab_mask(t, d)
        if got != exp:
            bad += 1
            if bad <= 5:
                log(f"  slab 불일치 d={d:#x} tri={t} 원본={got:#x} 재구현={exp:#x}")
    log(f"slab 0x7102c0638c: {n - bad}/{n} 일치")
    return bad


def test_touch(e, rng, n, log):
    a = e.alloc(0x60)
    b = e.alloc(0x60)
    bad = 0
    for i in range(n):
        t1 = rand_tri(rng, 5.0)
        t2 = rand_tri(rng, 5.0)
        if rng.random() < 0.5:
            k = rng.randrange(3)
            j = rng.randrange(3)
            jit = rng.choice([0.0, 0.0005, 0.0009, 0.0011, 0.002])
            t2[j] = tuple(x + jit for x in t1[k])
        e.w(a + 8, b"".join(fb(x) for v in t1 for x in v))
        e.w(b + 8, b"".join(fb(x) for v in t2 for x in v))
        got = e.call(0x7102C05444, a, b) & 1
        exp = 1 if cp.touch(t1, t2) else 0
        if got != exp:
            bad += 1
            if bad <= 5:
                log(f"  touch 불일치 원본={got} 재구현={exp}")
    log(f"touch 0x7102c05444: {n - bad}/{n} 일치")
    return bad


def test_tricb(e, log, stage="Yagara"):
    """0x7102c0725c(cbobj, triinfo): 실제 충돌 삼각형마다 원본 콜백 → 프리즘 방향·슬랩 비교."""
    m, ph = cp.load_mesh(Path(__file__).resolve().parents[2] / f"extracted/romfs/Pack/Actor/Fld_{stage}.pack.zs")
    pos, tri, tag = m["pos"], m["tri"], m["tag"]
    ntri = len(tri)
    pool = e.alloc(0x20)
    nodes = e.alloc(0x60 * (ntri + 1))
    ptrs = e.alloc(8 * (ntri + 1))
    for i in range(ntri):  # 자유 목록
        e.w(nodes + 0x60 * i, struct.pack("<Q", nodes + 0x60 * (i + 1)))
    e.w(pool, struct.pack("<iiQQ", 0, ntri + 1, ptrs, nodes))
    dbuf = e.alloc(42 * 0xFA10)
    for d in range(42):
        base = dbuf + d * 0xFA10
        e.w(base, struct.pack("<iiQ", 0, 8000, base + 0x10))
    mtx = e.alloc(48)
    e.w(mtx, struct.pack("<12f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0))
    ctx = e.alloc(0x20)
    e.w(ctx, struct.pack("<QQQQ", pool, dbuf, 0x1234, mtx))
    cb = e.alloc(0x20)
    e.w(cb + 0x10, struct.pack("<Q", ctx))
    ti = e.alloc(0x100)
    vtx = e.alloc(0x40)
    vptr = e.alloc(0x18)
    e.w(vptr, struct.pack("<QQQ", vtx, vtx + 0x10, vtx + 0x20))
    mat = e.alloc(0x10)
    bad = 0
    made = 0
    prev_count = 0
    for i, (a, b, c) in enumerate(tri.tolist()):
        t = int(tag[i])
        mi, _, mask = ph["materials"][t]
        v = (tuple(pos[a]), tuple(pos[b]), tuple(pos[c]))
        for k in range(3):
            e.w(vtx + 0x10 * k, b"".join(fb(x) for x in v[k]))
        e.w(mat, struct.pack("<IIQ", mi, 0, mask))
        e.w(ti + 8, struct.pack("<Q", vptr))
        e.w(ti + 0x80, struct.pack("<I", i))
        e.w(ti + 0x88, struct.pack("<Q", mat))
        e.call(0x7102C0725C, cb, ti)
        cnt = struct.unpack("<i", e.r(pool, 4))[0]
        exp_d = cp.tri_filter(mi, mask, *v)
        if cnt == prev_count:
            got = None
        else:
            p = struct.unpack("<Q", e.r(ptrs + 8 * (cnt - 1), 8))[0]
            got = (None, struct.unpack("<I", e.r(p + 0x2C, 4))[0])
            # 방향: 어느 방향 버퍼에 들어갔는지
            for d in range(42):
                base = dbuf + d * 0xFA10
                dc = struct.unpack("<i", e.r(base, 4))[0]
                if dc and struct.unpack("<Q", e.r(base + 0x10 + 8 * (dc - 1), 8))[0] == p:
                    got = (d, got[1])
                    break
            made += 1
        prev_count = cnt
        exp = None if exp_d is None else (exp_d, cp.slab_mask(v, exp_d))
        if got != exp:
            bad += 1
            if bad <= 5:
                log(f"  tricb 불일치 tri={i} 원본={got} 재구현={exp}")
    log(f"tricb 0x7102c0725c (Fld_{stage} 충돌 삼각형 {ntri}개, 프리즘 {made}개): {ntri - bad}/{ntri} 일치")
    return bad


def test_panels(e, log, stage="Yagara"):
    """0x7102c0725c(전 삼각형) → 0x7102bf7ce8 aggregatePrismInFace_ → 0x7102bf88d0 mergeInsidePanel_ 을
    원본 그대로 이어 실행하고, 프리즘 +0x40(소속 패널) 분할을 재구현(extract_panels+merge_panels)과 비교."""
    m, ph = cp.load_mesh(Path(__file__).resolve().parents[2] / f"extracted/romfs/Pack/Actor/Fld_{stage}.pack.zs")
    pos, tri, tag = m["pos"], m["tri"], m["tag"]
    ntri = len(tri)
    pool = e.alloc(0x20)
    nodes = e.alloc(0x60 * (ntri + 1))
    ptrs = e.alloc(8 * (ntri + 1))
    for i in range(ntri):
        e.w(nodes + 0x60 * i, struct.pack("<Q", nodes + 0x60 * (i + 1)))
    e.w(pool, struct.pack("<iiQQ", 0, ntri + 1, ptrs, nodes))
    dbuf = e.alloc(42 * 0xFA10)
    for d in range(42):
        base = dbuf + d * 0xFA10
        e.w(base, struct.pack("<iiQ", 0, 8000, base + 0x10))
    mtx = e.alloc(48)
    e.w(mtx, struct.pack("<12f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0))
    ctx = e.alloc(0x20)
    e.w(ctx, struct.pack("<QQQQ", pool, dbuf, 0x1234, mtx))
    cb = e.alloc(0x20)
    e.w(cb + 0x10, struct.pack("<Q", ctx))
    ti = e.alloc(0x100)
    vtx = e.alloc(0x40)
    vptr = e.alloc(0x18)
    e.w(vptr, struct.pack("<QQQ", vtx, vtx + 0x10, vtx + 0x20))
    mat = e.alloc(0x10)
    pr_tri = []
    prev = 0
    py_prisms = []
    for i, (a, b, c) in enumerate(tri.tolist()):
        mi, _, mask = ph["materials"][int(tag[i])]
        v = (tuple(pos[a]), tuple(pos[b]), tuple(pos[c]))
        for k in range(3):
            e.w(vtx + 0x10 * k, b"".join(fb(x) for x in v[k]))
        e.w(mat, struct.pack("<IIQ", mi, 0, mask))
        e.w(ti + 8, struct.pack("<Q", vptr))
        e.w(ti + 0x80, struct.pack("<I", i))
        e.w(ti + 0x88, struct.pack("<Q", mat))
        e.call(0x7102C0725C, cb, ti)
        cnt = struct.unpack("<i", e.r(pool, 4))[0]
        if cnt != prev:
            pr_tri.append(i)
            d = cp.tri_filter(mi, mask, *v)
            py_prisms.append((d, v, cp.slab_mask(v, d)))
        prev = cnt
    prism_addr = [struct.unpack("<Q", e.r(ptrs + 8 * k, 8))[0] for k in range(len(pr_tri))]
    # 패널 버퍼 42 × 0xa010, 추출기 객체(+8 → 패널 목록, 목록 링크 오프셋 0x1e0)
    pbuf = e.alloc(42 * 0xA010)
    for d in range(42):
        base = pbuf + d * 0xA010
        e.w(base, struct.pack("<iiQ", 0, 5120, base + 0x10))
    plist = e.alloc(0x20)
    e.w(plist, struct.pack("<QQQii", 0, 0, 0, 0, 0x1E0))
    ext = e.alloc(0x20)
    e.w(ext + 8, struct.pack("<Q", plist))
    e.call(0x7102BF7CE8, ext, pbuf, dbuf, 0)
    n_before = sum(struct.unpack("<i", e.r(pbuf + d * 0xA010, 4))[0] for d in range(42))
    e.call(0x7102BF88D0, ext, pbuf, 0, 0)
    n_after = sum(struct.unpack("<i", e.r(pbuf + d * 0xA010, 4))[0] for d in range(42))
    owner = [struct.unpack("<Q", e.r(p + 0x40, 8))[0] for p in prism_addr]
    if globals().get("_dbg"):
        import collections
        z = collections.Counter(py_prisms[k][0] for k, o in enumerate(owner) if o == 0)
        t = collections.Counter(p[0] for p in py_prisms)
        print("owner0 by dir", {hex(d): (z[d], t[d]) for d in sorted(t)})
    groups = {}
    for k, o in enumerate(owner):
        groups.setdefault(o, set()).add(k)
    emu_parts = sorted(tuple(sorted(g)) for g in groups.values())
    py_ext = cp.extract_panels(py_prisms)
    py_mrg = cp.merge_panels(py_ext)
    py_parts = sorted(tuple(sorted(p["prisms"])) for p in py_mrg)
    same = emu_parts == py_parts
    # 패널 AABB(+0x20..+0x34) 비교
    aabb_bad = 0
    pan_by_set = {}
    for d in range(42):
        base = pbuf + d * 0xA010
        cnt = struct.unpack("<i", e.r(base, 4))[0]
        for j in range(cnt):
            pa = struct.unpack("<Q", e.r(base + 0x10 + 8 * j, 8))[0]
            lohi = struct.unpack("<6f", e.r(pa + 0x20, 24))
            members = tuple(sorted(k for k, o in enumerate(owner) if o == pa))
            pan_by_set[members] = (e.r(pa + 0x38, 1)[0], lohi)
    for p in py_mrg:
        key = tuple(sorted(p["prisms"]))
        if key in pan_by_set:
            dd, lohi = pan_by_set[key]
            exp = tuple(float(x) for x in list(p["lo"]) + list(p["hi"]))
            if dd != p["dir"] or tuple(float(x) for x in lohi) != exp:
                aabb_bad += 1
    log(f"panels 0x7102bf7ce8+0x7102bf88d0 (Fld_{stage} 프리즘 {len(pr_tri)}개): 원본 패널 {n_before}→병합 후 {n_after}, "
        f"재구현 {len(py_ext)}→{len(py_mrg)}, 분할 일치={same}, 패널 방향·AABB 불일치 {aabb_bad}")
    if globals().get("_dbg"):
        globals()["_parts"] = (emu_parts, py_parts, py_prisms, [cp.extract_panels(py_prisms)])
        # 병합 전 원본 분할도 따로 구함: 병합 전에 소유 패널을 읽어야 하므로 별도 실행 필요
    if not same:
        a, b = set(emu_parts), set(py_parts)
        log(f"  원본에만 {len(a - b)}개, 재구현에만 {len(b - a)}개 예: {sorted(a - b)[:3]} / {sorted(b - a)[:3]}")
    return 0 if same and not aabb_bad else 1


def test_packer(e, rng, n_seq, log):
    """0x7102c105bc: 패커 객체 {vt, 빈칸 목록 루트*, 풀*}. 풀 = {목록 루트(+0..+0x14), 자유 노드(+0x18), 최대(+0x28)}."""
    vt = 0x710567E290  # 원본 vtable 그대로(+0x18 삽입 0x7102c104f8, +0x20 목록 0x7102c11918)
    bad = 0
    total = 0
    for s in range(n_seq):
        # 풀: 노드 0x30 B, 목록 링크 +0x10(오프셋 0x10), 풀 링크 +0x20
        cap = 4000
        pool = e.alloc(0x40)
        nodes = e.alloc(0x30 * cap)
        for i in range(cap - 1):
            e.w(nodes + 0x30 * i, struct.pack("<Q", nodes + 0x30 * (i + 1)))
        e.w(pool, struct.pack("<QQiiQQi", 0, 0, 0, 0, nodes, 0, cap))
        root = e.alloc(0x18)
        e.w(root, struct.pack("<QQii", root, root, 0, 0x10))
        pk = e.alloc(0x20)
        e.w(pk, struct.pack("<QQQ", vt, root, pool))
        # 초기 빈칸 1개 (0,0,3200,3200) — 0x7102c0ec20 와 같은 노드 구성
        nd = nodes + 0x30 * (cap - 1)
        e.w(nd, struct.pack("<4f", 0, 0, 3200, 3200))
        e.w(nd + 0x10, struct.pack("<QQ", root, root))
        e.w(root, struct.pack("<QQi", nd + 0x10, nd + 0x10, 1))
        ref = cp.Packer(400, 1)
        sz = e.alloc(8)
        out = e.alloc(16)
        for k in range(rng.randint(5, 60)):
            w = rng.choice([rng.randint(1, 40), rng.randint(20, 400), rng.randint(300, 1800)])
            h = rng.choice([rng.randint(1, 40), rng.randint(20, 400), rng.randint(300, 1800)])
            w, h = float(w) + rng.choice([0, 0, 0.5]), float(h)
            e.w(sz, fb(w) + fb(h))
            e.w(out, struct.pack("<4f", 3.4e38, 3.4e38, -3.4e38, -3.4e38))
            ok = e.call(0x7102C105BC, pk, sz, out) & 1
            got = struct.unpack("<4f", e.r(out, 16)) if ok else None
            r = ref.place(w, h)
            exp = tuple(float(x) for x in r[0]) if r else None
            total += 1
            if got != exp:
                bad += 1
                if bad <= 5:
                    log(f"  packer 불일치 seq={s} k={k} w,h={w},{h} 원본={got} 재구현={exp}")
                break
    log(f"packer 0x7102c105bc: {total - bad}/{total} 배치 일치 ({n_seq} 순서열)")
    return bad


def test_reproject(e, rng, n, log):
    buf = e.alloc(0x40)
    db = e.alloc(8)
    bad = 0
    for i in range(n):
        d0 = rng.randrange(0x2A)
        d1 = rng.choice([0x28, rng.randrange(0x2A)])
        lo = [rng.uniform(-100, 100) for _ in range(3)]
        hi = [x + rng.uniform(0, 30) for x in lo]
        vals = lo + hi
        e.w(buf, b"".join(fb(x) for x in vals) + bytes([d0, 0, 0, 0]) + b"".join(fb(x) for x in vals) + bytes([0xFF, 0, 0, 0]))
        e.w(db, bytes([d1]))
        e.call(0x7102BF9850, buf, db)
        got = struct.unpack("<6f", e.r(buf + 0x1C, 24)), e.r(buf + 0x34, 1)[0]
        er = cp.reproject([f32(x) for x in lo], [f32(x) for x in hi], d0, [f32(x) for x in lo], [f32(x) for x in hi], d1)
        exp = tuple(float(x) for x in er[0]), er[1]
        if got != exp:
            bad += 1
            if bad <= 5:
                log(f"  reproject 불일치 d0={d0:#x} d1={d1:#x} 원본={got} 재구현={exp}")
    log(f"reproject 0x7102bf9850: {n - bad}/{n} 일치")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out")
    ap.add_argument("--only")
    a = ap.parse_args()
    lines = []

    def log(s):
        print(s)
        lines.append(s)
    rng = random.Random(a.seed)
    e = PEmu()
    tests = {
        "classify": lambda: test_classify(e, rng, a.n * 4, log),
        "basis": lambda: test_basis(e, log),
        "slab": lambda: test_slab(e, rng, a.n, log),
        "touch": lambda: test_touch(e, rng, a.n, log),
        "reproject": lambda: test_reproject(e, rng, a.n, log),
        "packer": lambda: test_packer(e, rng, 60, log),
        "tricb": lambda: test_tricb(e, log),
        "panels": lambda: test_panels(e, log),
    }
    for k, f in tests.items():
        if a.only and k not in a.only.split(","):
            continue
        f()
    if a.out:
        Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()


def debug_panels():
    import collections
    e = PEmu()
    logs = []
    globals()["_dbg"] = True
    test_panels(e, lambda s: logs.append(s[:300]))
    print("\n".join(logs))
