"""r6 combat: 탄 바디 비교 그룹(F+0x30)과 탄↔강체 막는 접촉 판정 원본 실행(unicorn).

A. 탄 행동 슬롯12 0x71016444ec(생성정보 → 액터+0x668 팀) → BulletBodyComponent 슬롯9 0x71013405e0
   (유닛 바디마다 F = 바디.vt+0x38 = 바디+0x138, F+0x30 == 0 이면 팀→그룹) 연결 실행.
B. 탄 바디↔강체 접촉 필터 0x7103c55ed8 → 0x7103c34e14 → 0x7103c34ce8(원본 그대로) 실행.
   표는 PhiveConfig LayerEntityParamTableSet(Default/Same/Other)의 값 2 비트(mask1)를 백엔드 +0x190/+0x210/+0x290 에 넣음.

스텁: 형 검사(IsA) 가상 호출은 1 반환 코드, 행동 vt+0x1a8 은 1, this+0x170 vt+0x78 은 0, 뮤텍스 PLT(0x7103e99fd0/ff0)는 바로 반환.
      월드 추가(유닛+0x90=0)·공간 격자(*0x710580b8b0=0) 경로는 끔. 형상 필터는 F+8 bit28 = 0 이라 원본이 1을 돌려주는 경로.
사용: PY web/tools/r6_combat_filter_emu.py
"""
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_LR, UC_ARM64_REG_PC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, BASE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RET1 = struct.pack("<II", 0xD2800020, 0xD65F03C0)
RET0 = struct.pack("<II", 0xD2800000, 0xD65F03C0)


def setup():
    h = UC()
    mu = h.mu
    mu.mem_map(0x40000000, 0x4000000)
    h.heap_next = 0x40000000
    code = h.alloc(0x40)
    mu.mem_write(code, RET1)
    mu.mem_write(code + 0x10, RET0)
    h.ret1, h.ret0 = code, code + 0x10

    def plt_ret(m, a, s, d):
        m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
    for a in (0x7103e99fd0, 0x7103e99ff0):
        mu.hook_add(UC_HOOK_CODE, plt_ret, begin=a, end=a)
    for g in (0x7105812578, 0x7105850590, 0x710580b9f8, 0x7105828210, 0x710599f7e0):
        mu.mem_write(g, b"\1")
    return h


def q(h, a, v):
    h.mu.mem_write(a, struct.pack("<Q", v))


def fakevt(h, slots):
    vt = h.alloc(0x400)
    for i in range(0x80):
        q(h, vt + i * 8, h.ret0)
    for off, fn in slots.items():
        q(h, vt + off, fn)
    return vt


def ref_group(team):
    return 0 if team in (-1, 3) else (team + 1) & 0xFFFF


def run_a(h, rng):
    mu = h.mu
    q(h, BASE + 0x580B8B0, 0)
    actor_vt = fakevt(h, {0x0: h.ret1, 0x78: 0x7100F78650})
    beh_vt = fakevt(h, {0x1A8: h.ret1})
    info_vt = fakevt(h, {0x0: h.ret1})
    obj170_vt = fakevt(h, {0x78: h.ret0})
    rows, bad = [], []
    teams = [-1, 0, 1, 2, 3, 4, 7, -2, 0x7FFF, 0xFFFF]
    for i in range(600):
        team = teams[i % len(teams)] if i < 200 else rng.randrange(-3, 70000)
        st4d0 = 2 if i % 13 == 5 else rng.choice([0, 1, 3])
        old668 = rng.randrange(-1, 4)
        actor = h.alloc(0x800)
        q(h, actor, actor_vt)
        h.u32(actor + 0x4D0, st4d0)
        h.u32(actor + 0x668, old668)
        info = h.alloc(0x100)
        q(h, info, info_vt)
        h.u32(info + 0x1C, 0xC0000000 | i)
        h.u32(info + 0x2C, team)
        o170 = h.alloc(0x20)
        q(h, o170, obj170_vt)
        beh = h.alloc(0x200)
        q(h, beh, beh_vt)
        q(h, beh + 0x10, actor)
        q(h, beh + 0x170, o170)
        r12 = h.call(0x71016444EC, beh, info) & 0xFFFFFFFF
        n = rng.randrange(1, 4)
        units, fs, init = [], [], []
        for k in range(n):
            f = h.alloc(0x40)
            g0 = 0 if (i + k) % 5 else rng.randrange(1, 6)
            mu.mem_write(f + 0x30, struct.pack("<H", g0))
            body = h.alloc(0x198)
            q(h, body, 0x7105749990)
            q(h, body + 0x138, f)
            unit = h.alloc(0x98)
            q(h, unit + 0x38, body)
            mu.mem_write(unit + 0x90, b"\0")
            units.append(unit)
            fs.append(f)
            init.append(g0)
        arr = h.alloc(8 * n)
        for k, u in enumerate(units):
            q(h, arr + 8 * k, u)
        E = h.alloc(0x50)
        h.u32(E + 8, n)
        q(h, E + 0x10, arr)
        comp = h.alloc(0x60)
        q(h, comp + 0x20, actor)
        q(h, comp + 0x30, E)
        h.call(0x71013405E0, comp)
        t668 = struct.unpack("<i", mu.mem_read(actor + 0x668, 4))[0]
        exp668 = old668 if st4d0 == 2 else struct.unpack("<i", struct.pack("<I", team & 0xFFFFFFFF))[0]
        got = [struct.unpack("<H", mu.mem_read(f + 0x30, 2))[0] for f in fs]
        exp = [g0 if g0 else ref_group(exp668) for g0 in init]
        ok = (t668 == exp668) and got == exp and r12 == 1
        row = {"team": team, "actor4d0": st4d0, "actor668": t668, "init": init, "group": got, "expected": exp}
        if i < 12:
            rows.append(row)
        if not ok:
            bad.append(row)
    return {"functions": ["0x71016444ec", "0x71013405e0", "0x7103b0b350"], "cases": 600, "mismatches": bad, "sample": rows}


def load_tables():
    d = json.load(open(ROOT / "analysis/gimmick/PhiveConfig.json", encoding="utf-8"))
    names = d["LayerEntityCollection"]
    out = []
    for t in ("LayerEntityParamTableSet", "LayerEntityParamTableSetSame", "LayerEntityParamTableSetOther"):
        T = d[t]["Default"]["LayerEntityFilterTable"]
        rows = []
        for r in range(32):
            w = 0
            if r < len(T):
                for c, v in enumerate(T[r]):
                    if v == 2:
                        w |= 1 << c
            rows.append(w)
        out.append(rows)
    return names, out


def run_b(h, rng):
    mu = h.mu
    names, tables = load_tables()
    module = h.alloc(0x200)
    world = h.alloc(0x200)
    prov = h.alloc(0x80)
    table = h.alloc(0x400)
    tvt = fakevt(h, {0x8: h.ret1})
    q(h, BASE + 0x599DFA8, module)
    q(h, module + 0xE8, world)
    q(h, world + 0xB8, prov)
    q(h, prov + 0x28, table)
    q(h, table, tvt)
    for rows, off in zip(tables, (0x190, 0x210, 0x290)):
        mu.mem_write(table + off, struct.pack("<32I", *rows))
    bvt = fakevt(h, {0x0: h.ret1, 0x38: 0x7103B0B350})
    rvt = fakevt(h, {0x28: h.ret1})
    fa = h.alloc(0x40)
    fb = h.alloc(0x40)
    bb = h.alloc(0x198)
    q(h, bb, bvt)
    q(h, bb + 0x138, fa)
    q(h, bb + 0xF8, h.alloc(0x40))
    rb = h.alloc(0x300)
    q(h, rb, rvt)
    q(h, rb + 0x180, fb)
    q(h, rb + 0x28, h.alloc(0x40))
    q(h, rb + 0x88, 0)
    contact = h.alloc(0x80)

    def bit(w, n):
        return (w >> (n & 31)) & 1

    def ref(la, sa, ga, ma, na, lb, sb, gb, mb, nb):
        ti = 0 if (ga == 0 or gb == 0) else (1 if ga == gb else 2)
        T = tables[ti]
        return bit(T[la], lb) & bit(ma, lb) & bit(na, sb) & bit(T[lb], la) & bit(mb, la) & bit(nb, sa)

    bad, sample = [], []
    cases = 0

    def one(la, sa, ga, ma, na, lb, sb, gb, mb, nb, flag0):
        nonlocal cases
        cases += 1
        h.u32(fa + 8, la | (sa << 6))
        h.u32(fb + 8, lb | (sb << 6))
        h.u32(fa + 0x18, ma)
        h.u32(fa + 0x1C, na)
        h.u32(fb + 0x18, mb)
        h.u32(fb + 0x1C, nb)
        mu.mem_write(fa + 0x30, struct.pack("<H", ga))
        mu.mem_write(fb + 0x30, struct.pack("<H", gb))
        mu.mem_write(contact + 0x68, struct.pack("<H", flag0))
        h.call(0x7103C55ED8, contact, bb, 0, rb, 0)
        got = struct.unpack("<H", mu.mem_read(contact + 0x68, 2))[0]
        exp = flag0 | (2 if ref(la, sa, ga, ma, na, lb, sb, gb, mb, nb) else 0)
        return got, exp

    for i in range(4000):
        la = rng.choice([8, 9, rng.randrange(29)])
        lb = rng.choice([5, 3, 16, 21, rng.randrange(29)])
        sa, sb = rng.randrange(27), rng.randrange(27)
        ga, gb = rng.choice([(0, 0), (0, 2), (1, 1), (2, 2), (1, 2), (2, 1), (3, 0), (65535, 65535)])
        allones = i % 3 == 0
        ma = 0xFFFFFFFF if allones else rng.getrandbits(32)
        na = 0xFFFFFFFF if allones else rng.getrandbits(32)
        mb = 0xFFFFFFFF if allones else rng.getrandbits(32)
        nb = 0xFFFFFFFF if allones else rng.getrandbits(32)
        flag0 = rng.choice([0, 1, 4, 0x20])
        got, exp = one(la, sa, ga, ma, na, lb, sb, gb, mb, nb, flag0)
        if got != exp:
            bad.append({"la": la, "lb": lb, "ga": ga, "gb": gb, "got": got, "exp": exp})
    scen = []
    P = names.index("SplPlayer")
    for lname in ("SplInkBullet", "SplInkBullet_FriendThrough"):
        L = names.index(lname)
        for desc, ga, gb in (("bullet 그룹 0(미설정)", 0, 1), ("같은 팀(1,1)", 1, 1), ("다른 팀(1,2)", 1, 2)):
            got, exp = one(L, 0, ga, 0xFFFFFFFF, 0xFFFFFFFF, P, 0, gb, 0xFFFFFFFF, 0xFFFFFFFF, 0)
            scen.append({"bullet_layer": lname, "case": desc, "blocking_bit1": (got >> 1) & 1, "expected": (exp >> 1) & 1})
            if got != exp:
                bad.append({"scenario": desc, "got": got, "exp": exp})
    return {"functions": ["0x7103c55ed8", "0x7103c34e14", "0x7103c34ce8", "0x7103b0b350"], "cases": cases,
            "mismatches": bad, "scenarios_masks_allones": scen}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rng = random.Random(20261003)
    a = run_a(setup(), rng)
    b = run_b(setup(), rng)
    out = {"A_group_assign": a, "B_bullet_pair_filter": b,
           "stubs": ["IsA 가상 호출(액터·생성정보·탄 바디·강체·표 객체) = 1 반환 코드",
                     "행동 vt+0x1a8 = 1, this+0x170 vt+0x78 = 0(+0x348 바이트 쓰기 생략)",
                     "뮤텍스 PLT 0x7103e99fd0/0x7103e99ff0 = 바로 반환",
                     "유닛+0x90 = 0(월드 추가 생략), *0x710580b8b0 = 0(공간 격자 생략)"],
           "unverified": ["F+0x18/+0x1c 실제 마스크 값(탄 BlockableLayerHitMask=HitAll 은 데이터, BlockableSubLayerHitMask 기본값 미확정, 플레이어 ColBullet 쪽 로더 미실행)",
                          "형상 태그 재정의(F+8 bit28=1) 경로", "넓은 단계 수집·좁은 단계 TOI", "슬롯12와 슬롯9 사이의 실제 호출 순서(풀 생성 0x7100f7f6a4 판독)"]}
    p = ROOT / "analysis/combat/r6_filter_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"A 그룹 지정(슬롯12→슬롯9): {a['cases']}건 불일치 {len(a['mismatches'])}")
    print(f"B 탄↔강체 막는 접촉 비트: {b['cases']}건 불일치 {len(b['mismatches'])}")
    for s in b["scenarios_masks_allones"]:
        print("  ", s)
    print("결과:", p)
    if a["mismatches"] or b["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
