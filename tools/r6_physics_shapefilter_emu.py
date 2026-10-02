"""[r6 physics] 형상(shapeTag) 필터 행 + 공통 쌍 필터 결합 0x7103c5e244 원본 실행.

0x7103c5e244(A, B, keyA, keyB) (호출: TtCollectManifoldModifier 0x7103c5df04/0x7103c5e33c, 같은 꼴 0x7103c5cda0·0x7103c584f0):
  if (F(A)+8 bit28 || F(B)+8 bit28):
      0x7103c34b7c(L(A), S(A), keyB, B) == 1 && 0x7103c34b7c(L(B), S(B), keyA, A) == 1  아니면 0
  af44e8(A,B) && (F(A)+0x18 >> L(B)) & 1 && (F(A)+0x1c >> S(B)) & 1 && af44e8(B,A) && 같은 마스크(B,A)
0x7103c34b7c(Lo, So, key, X): F(X)+8 bit28 이 꺼져 있으면 1.
   형상(X+0x28)이 복합(IsA 0x7105553a08)이면 lo/hi = 형상+0xb8/+0xbc,
   아니면 0x7103ad658c → 0x7103ad6a70 로 shapeTag 행(lo = Layer 마스크, hi = SubLayer 마스크)을 찾고, 못 찾으면 lo = hi = 0xffffffff.
   결과 = (lo >> Lo) & 1 && (hi >> So) & 1
실행: 원본 0x7103c5e244, 0x7103c34b7c, 0x7103ad658c, 0x7103ad6a70, 0x7103af44e8 를 그대로 실행.
스텁: 형상 vt slot0(IsA) = 사례별 0/1, vt+0x10(형식) = 1, vt+0x70 → 객체 P, P vt+0x10 → hknp 형상 H,
      Havok 잎 디스패치(type8 slot+0xc0) = 키별 합성 shapeTag 를 결과+0xbf8 에 씀, 공통 표 vt+0x8 형 조회 = 1,
      PLT(LockMutex/UnlockMutex/__cxa_guard_*) = 0 반환.
결과: analysis/completion/r6/physics_shapefilter_emu.json
"""
import json
import random
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X3, UC_ARM64_REG_LR, UC_ARM64_REG_PC  # noqa: E402
from r5_gfx_char_uc import GUC  # noqa: E402
from network_uc import BASE, STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FN = 0x7103c5e244


def run(cases=4096, seed=20261003):
    h = GUC()
    mu = h.mu
    q = h.wq

    def u32(a, v):
        mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    ret_map = {}
    leaf_tag = {}
    LEAF = STUB + 0xA00

    def stub_fn(addr, val):
        mu.mem_write(addr, struct.pack("<I", 0xD65F03C0))
        ret_map[addr] = val
        return addr

    def hook(m, a, s, d):
        if a == LEAF:
            key = struct.unpack("<i", bytes(m.mem_read(m.reg_read(UC_ARM64_REG_X1), 4)))[0]
            m.mem_write(m.reg_read(UC_ARM64_REG_X3) + 0xbf8, struct.pack("<H", leaf_tag.get(key, 0)))
            m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
        elif a in ret_map:
            v = ret_map[a]
            m.reg_write(UC_ARM64_REG_X0, v() if callable(v) else v)
            m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
    mu.hook_add(UC_HOOK_CODE, hook, begin=STUB + 0x900, end=STUB + 0xB00)
    mu.mem_write(LEAF, struct.pack("<I", 0xD65F03C0))
    # 공통 표 (0x7103af44e8)
    module = h.alloc(0x200); world = h.alloc(0x500); provider = h.alloc(0x80); table = h.alloc(0x400); tvt = h.alloc(0x20)
    q(BASE + 0x599dfa8, module); q(module + 0xe8, world); q(world + 0xb8, provider); q(provider + 0x28, table)
    q(table, tvt); q(tvt + 8, stub_fn(STUB + 0x900, 1))
    mu.mem_write(BASE + 0x599f7e0, b"\1")
    dispatch = h.alloc(16 * 0x200)
    q(BASE + 0x57dd738, dispatch); q(dispatch + 8 * 0x200 + 0xc0, LEAF)
    bodies = {}
    for nm, base_off in (("A", 0x910), ("B", 0x940)):
        body = h.alloc(0x200); F = h.alloc(0x40); shp = h.alloc(0x100); svt = h.alloc(0x80)
        P = h.alloc(0x20); pvt = h.alloc(0x20); H = h.alloc(0x40); info = h.alloc(0x40); mesh = h.alloc(0x40)
        rows = h.alloc(64 * 8)
        q(body + 0x180, F); q(body + 0x28, shp); q(shp, svt)
        isa_addr = STUB + base_off
        mu.mem_write(isa_addr, struct.pack("<I", 0xD65F03C0)); ret_map[isa_addr] = 0
        q(svt + 0, isa_addr)
        q(svt + 0x10, stub_fn(STUB + base_off + 0x8, 1))
        q(svt + 0x70, stub_fn(STUB + base_off + 0x10, P))
        q(P, pvt); q(pvt + 0x10, stub_fn(STUB + base_off + 0x18, H))
        mu.mem_write(H + 0x18, b"\x08"); q(H + 0x28, info); q(info + 0x10, rows); q(info + 0x28, mesh)
        mu.mem_write(mesh + 0x18, b"\x08")
        bodies[nm] = dict(body=body, F=F, shp=shp, isa=isa_addr, info=info, rows=rows)
    rng = random.Random(seed)
    mism, samples = [], []
    stats = {"shape_check_applied": 0, "rejected_by_shape": 0, "passed_total": 0}
    for ci in range(cases):
        st = {}
        for nm in ("A", "B"):
            b = bodies[nm]
            L = rng.randrange(29); S = rng.randrange(27)
            bit28 = rng.random() < 0.6
            fw = L | (S << 6) | ((1 << 28) if bit28 else 0)
            m18 = 0xFFFFFFFF if rng.random() < 0.7 else rng.getrandbits(32)
            m1c = 0xFFFFFFFF if rng.random() < 0.7 else rng.getrandbits(32)
            u32(b["F"] + 8, fw); u32(b["F"] + 0x18, m18); u32(b["F"] + 0x1c, m1c)
            mu.mem_write(b["F"] + 0x30, struct.pack("<H", 0))
            compound = rng.random() < 0.2
            ret_map[b["isa"]] = 1 if compound else 0
            cb8 = rng.getrandbits(32); cbc = rng.getrandbits(32)
            u32(b["shp"] + 0xb8, cb8); u32(b["shp"] + 0xbc, cbc)
            q(b["body"] + 0x88, rng.choice([0, 0x20]))
            count = rng.choice([0, 4, 28, 64])
            u32(b["info"] + 8, count)
            rowv = [(rng.choice([0x1ffffffe, 0x62, 0xe2, 0x1fffff9e, 0x1f0cbc7e, 0x1bffffc6, rng.getrandbits(32)]),
                     rng.choice([0xffffffff, 0x03fff5ff, 0x03ff75cf, 0x03bffa07, rng.getrandbits(32)])) for _ in range(64)]
            mu.mem_write(b["rows"], b"".join(struct.pack("<II", *r) for r in rowv))
            key = rng.choice([-1, rng.randrange(1 << 20)])
            tag = rng.choice([rng.randrange(64), rng.randrange(1 << 16)])
            st[nm] = dict(L=L, S=S, bit28=bit28, m18=m18, m1c=m1c, compound=compound, cb8=cb8, cbc=cbc,
                          count=count, rows=rowv, key=key, tag=tag)
        if st["A"]["key"] == st["B"]["key"] and st["A"]["key"] != -1:
            st["B"]["key"] = st["A"]["key"] ^ 1
        leaf_tag.clear()
        for nm in ("A", "B"):
            leaf_tag[st[nm]["key"]] = st[nm]["tag"]
        tbl = [[rng.getrandbits(32) | (0xFFFFFFFF if rng.random() < 0.5 else 0) for _ in range(32)] for _ in range(3)]
        for blk, off in zip(tbl, [0x190, 0x210, 0x290]):
            mu.mem_write(table + off, struct.pack("<32I", *blk))

        def bit(w, n):
            return (w >> (n & 31)) & 1

        def shape_ok(X, other):
            x = st[X]; o = st[other]
            if not x["bit28"]:
                return 1
            if x["compound"]:
                lo, hi = x["cb8"], x["cbc"]
                return bit(lo, o["L"]) & bit(hi, o["S"])
            if x["key"] != -1 and (x["tag"] & 0x1fff) < x["count"]:
                lo, hi = x["rows"][x["tag"] & 0x1fff]
                return bit(lo, o["L"]) & bit(hi, o["S"])
            return 1
        a, b_ = st["A"], st["B"]
        pair = (bit(tbl[0][a["L"]], b_["L"]) & bit(a["m18"], b_["L"]) & bit(a["m1c"], b_["S"])
                & bit(tbl[0][b_["L"]], a["L"]) & bit(b_["m18"], a["L"]) & bit(b_["m1c"], a["S"]))
        shape = 1
        if a["bit28"] or b_["bit28"]:
            stats["shape_check_applied"] += 1
            shape = shape_ok("B", "A") & shape_ok("A", "B")
            if not shape:
                stats["rejected_by_shape"] += 1
        exp = shape & pair
        got = h.call(FN, bodies["A"]["body"], bodies["B"]["body"], a["key"] & 0xFFFFFFFF, b_["key"] & 0xFFFFFFFF) & 1
        stats["passed_total"] += got
        row = {"case": ci, "A": {k: a[k] for k in ("L", "S", "bit28", "compound", "count", "key", "tag")},
               "B": {k: b_[k] for k in ("L", "S", "bit28", "compound", "count", "key", "tag")},
               "shape": shape, "pair": pair, "expected": exp, "original": got}
        if ci < 6:
            samples.append(row)
        if got != exp:
            mism.append(row)
    out = {"function": hex(FN), "callees_executed": ["0x7103c34b7c", "0x7103ad658c", "0x7103ad6a70", "0x7103af44e8"],
           "cases": cases, "passed": cases - len(mism), "stats": stats, "mismatches": mism[:10], "samples": samples,
           "plt_stubbed": sorted(set(h.plt_stubbed)),
           "stubs": ["형상 vt slot0 IsA(사례별 0/1), vt+0x10 형식=1, vt+0x70/P vt+0x10 → hknp 형상",
                     "Havok 잎 디스패치 → 키별 합성 shapeTag", "공통 표 vt+0x8 = 1", "PLT 0 반환"],
           "unverified": ["실제 bphsh 행 배열 부착(정보 객체 writer)", "복합 형상 type 0xf 경로 0x7103ad677c",
                          "매니폴드 수정자에서 이 결과로 접촉을 끄는 후속 처리(0x7103c5cda0 의 +0x2c |= 0x20)"]}
    p = ROOT / "analysis/completion/r6/physics_shapefilter_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"shape filter combine: {out['passed']}/{cases} 일치 {stats} -> {p}")
    return out


if __name__ == "__main__":
    run()
