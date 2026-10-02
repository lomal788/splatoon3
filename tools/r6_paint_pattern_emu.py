"""r6 paint: ColPaintPanelPatternRecognizer::recognizeIndependentPattern(0x7102bfb8b8) 원본 실행 대조.

1) 실제 데이터: paint4_emu 와 같은 원본 파이프라인(0x7102c0725c 삼각형 콜백 → 0x7102bf7ce8 → 0x7102bf88d0)으로
   Fld_<stage> 패널을 만든 뒤, 원본 0x7102bfb8b8 을 그 패널 배열에 실행하고 패턴(+0x9c)·매핑 AABB(+0x3c..+0x50)를
   재구현(ref_pattern)과 비교한다.
2) 합성: 무작위 패널(경계값 0.3/1/2/4·0.2·0.5 주변, 매핑 AABB 정상/뒤집힘, 방향 0..0x29) N 개.
스텁: player_initemu.Emu 규칙(PLT → x0=0; GetSystemTick 포함), 수학 PLT 는 paint4_emu 와 같음, 할당기 범프.
      프로파일러(0x710103c888/0x710103c9b4, 이름 표 vt+0x18)는 원본 그대로 실행한다(되돌림 값 무시).
결과: analysis/paint/r6_pattern_emu_out.json
"""
import json
import random
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paint4_emu as pe
import paint4_colpaint as cp

ROOT = Path(__file__).resolve().parents[2]
F = np.float32


def gt(a, b):
    return (not np.isnan(a)) and (not np.isnan(b)) and a > b


def ref_pattern(p):
    """p: dict(lo, hi, mlo, mhi, d, a1d8) -> (pattern, 새 매핑 lo, 새 매핑 hi)."""
    du = F(p["hi"][0] - p["lo"][0])
    dv = F(p["hi"][1] - p["lo"][1])
    mdu = F(p["mhi"][0] - p["mlo"][0])
    mdv = F(p["mhi"][1] - p["mlo"][1])
    T = F(0.3)
    mlo, mhi = p["mlo"], p["mhi"]
    if gt(du, T) and gt(dv, T) and gt(mdu, T) and gt(mdv, T):
        d = p["d"]
        if d <= 0x17 and (d & 0xFE) != 0x28:
            area = F(du * dv)
            big = gt(dv, F(1)) and gt(du, F(1)) and not (area < F(4)) and gt(mdu, F(1)) and gt(mdv, F(1))
            if not big:
                return 14, mlo, mhi
        if gt(du, F(2)) and gt(F(abs(F(du - mdu)) / du), F(0.2)):
            return 17, mlo, mhi
        if gt(dv, F(2)) and gt(F(abs(F(dv - mdv)) / dv), F(0.2)):
            return 17, mlo, mhi
        return 0, mlo, mhi
    if not gt(mlo[0], mhi[0]) and not gt(mlo[1], mhi[1]) and not gt(mlo[2], mhi[2]):
        return 11, mlo, mhi
    d = p["d"]
    if d == 0x29 or (d != 0x28 and d > 0x1F):
        return 12, mlo, mhi
    area = F(du * F(p["hi"][1] - p["lo"][1]))
    if gt(area, F(1)) and gt(F(F(p["a1d8"]) / area), F(0.5)):
        return 13, p["lo"], p["hi"]
    return 12, mlo, mhi


def rdp(e, pa):
    b = e.r(pa, 0x1e0)

    def f(o):
        return F(struct.unpack_from("<f", b, o)[0])
    return dict(lo=(f(0x20), f(0x24), f(0x28)), hi=(f(0x2c), f(0x30), f(0x34)), d=b[0x38],
                mlo=(f(0x3c), f(0x40), f(0x44)), mhi=(f(0x48), f(0x4c), f(0x50)), a1d8=f(0x1d8))


def run_array(e, panels):
    arr = e.alloc(8 * max(1, len(panels)))
    for i, p in enumerate(panels):
        e.w(arr + 8 * i, struct.pack("<Q", p))
    hdr = e.alloc(0x10)
    e.w(hdr, struct.pack("<iiQ", len(panels), len(panels), arr))
    e.call(0x7102BFB8B8, 0, hdr)


def compare(e, panels, before):
    bad = []
    pats = Counter()
    for pa, p in zip(panels, before):
        exp, elo, ehi = ref_pattern(p)
        got = struct.unpack("<i", e.r(pa + 0x9c, 4))[0]
        q = rdp(e, pa)
        pats[got] += 1
        same_box = all(F(q["mlo"][k]).tobytes() == F(elo[k]).tobytes() and F(q["mhi"][k]).tobytes() == F(ehi[k]).tobytes()
                       for k in range(3))
        if got != exp or not same_box:
            bad.append(dict(panel=hex(pa), got=got, exp=exp, d=p["d"]))
    return bad, pats


def real(e, stage):
    """paint4_emu.test_panels 와 같은 원본 파이프라인(복사본). 패널 포인터를 원본 build 순서로 돌려준다."""
    m, ph = cp.load_mesh(ROOT / f"extracted/romfs/Pack/Actor/Fld_{stage}.pack.zs")
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
    for i, (a, b, c) in enumerate(tri.tolist()):
        mi, _, mask = ph["materials"][int(tag[i])]
        v = (tuple(pos[a]), tuple(pos[b]), tuple(pos[c]))
        for k in range(3):
            e.w(vtx + 0x10 * k, b"".join(pe.fb(x) for x in v[k]))
        e.w(mat, struct.pack("<IIQ", mi, 0, mask))
        e.w(ti + 8, struct.pack("<Q", vptr))
        e.w(ti + 0x80, struct.pack("<I", i))
        e.w(ti + 0x88, struct.pack("<Q", mat))
        e.call(0x7102C0725C, cb, ti)
    pbuf = e.alloc(42 * 0xA010)
    for d in range(42):
        base = pbuf + d * 0xA010
        e.w(base, struct.pack("<iiQ", 0, 5120, base + 0x10))
    plist = e.alloc(0x20)
    e.w(plist, struct.pack("<QQQii", 0, 0, 0, 0, 0x1E0))
    ext = e.alloc(0x20)
    e.w(ext + 8, struct.pack("<Q", plist))
    e.call(0x7102BF7CE8, ext, pbuf, dbuf, 0)
    e.call(0x7102BF88D0, ext, pbuf, 0, 0)
    panels = []
    for d in range(42):  # 원본 build 처럼 방향 버퍼 0..41 을 차례로 이어 붙임(colpaint_r0.c 7866행 근처)
        base = pbuf + d * 0xA010
        cnt = struct.unpack("<i", e.r(base, 4))[0]
        panels += [struct.unpack("<Q", e.r(base + 0x10 + 8 * j, 8))[0] for j in range(cnt)]
    return panels


def synth(e, rng, n):
    panels, before = [], []
    vals = [0.29, 0.3, 0.31, 0.5, 0.99, 1.0, 1.01, 1.9, 2.0, 2.01, 2.5, 3.99, 4.0, 5, 10, 40]
    for _ in range(n):
        pa = e.alloc(0x1f0)
        lo = [F(rng.uniform(-50, 50)) for _ in range(3)]
        sz = [F(rng.choice(vals) if rng.random() < 0.6 else rng.uniform(0, 12)) for _ in range(3)]
        hi = [F(lo[k] + sz[k]) for k in range(3)]
        if rng.random() < 0.6:
            mlo = [F(lo[k] + F(rng.uniform(-0.5, 0.5))) for k in range(3)]
            msz = [F(sz[k] * F(rng.choice([1.0, 0.9, 0.79, 0.81, 1.2, 1.21, 0.5]))) for k in range(3)]
            mhi = [F(mlo[k] + msz[k]) for k in range(3)]
        else:
            mlo = [F(3.4028235e38)] * 3
            mhi = [F(-3.4028235e38)] * 3
            if rng.random() < 0.3:
                k = rng.randrange(3)
                mlo = list(mlo)
                mhi = list(mhi)
                mlo[k], mhi[k] = F(0), F(1)
        d = rng.choice(list(range(0x2A)))
        a1d8 = F(rng.uniform(0, 1.2) * float(sz[0] * sz[1]))
        b = bytearray(0x1f0)
        struct.pack_into("<6f", b, 0x20, *[float(x) for x in lo + hi])
        b[0x38] = d
        struct.pack_into("<6f", b, 0x3c, *[float(x) for x in mlo + mhi])
        b[0x54] = 0xff
        struct.pack_into("<f", b, 0x1d8, float(a1d8))
        struct.pack_into("<i", b, 0x9c, -7)
        e.w(pa, bytes(b))
        panels.append(pa)
        before.append(rdp(e, pa))
    return panels, before


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}
    for stage in ("Yagara",):
        e = pe.PEmu()
        panels = real(e, stage)
        before = [rdp(e, p) for p in panels]
        run_array(e, panels)
        bad, pats = compare(e, panels, before)
        a1 = [float(b["a1d8"]) for b in before]
        mvalid = sum(1 for b in before if not gt(b["mlo"][0], b["mhi"][0]))
        out[f"real_{stage}"] = dict(panels=len(panels), mismatch=len(bad), patterns=dict(sorted(pats.items())),
                                    a1d8_min=min(a1), a1d8_max=max(a1), mapping_valid=mvalid, bad=bad[:10])
        print(stage, len(panels), "mismatch", len(bad), dict(sorted(pats.items())), "a1d8", min(a1), max(a1), "mvalid", mvalid)
    e = pe.PEmu()
    rng = random.Random(61003)
    panels, before = synth(e, rng, 6000)
    run_array(e, panels)
    bad, pats = compare(e, panels, before)
    out["synthetic"] = dict(panels=len(panels), mismatch=len(bad), patterns=dict(sorted(pats.items())), bad=bad[:10])
    print("synthetic", len(panels), "mismatch", len(bad), dict(sorted(pats.items())))
    (ROOT / "analysis/paint/r6_pattern_emu_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
