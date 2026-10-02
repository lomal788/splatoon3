"""원본 실행: 팀색 선택기 번호 0x7101179a24(선택 상태, 분류, 씬 이름)와 이름 해시 0x7101179f90.

0x7101178030(씬 진입 팀색 갱신)이 부르는 선택기 번호 함수를 unicorn 으로 그대로 실행해 판독식과 비교한다.
- 분류(인자2)는 0x71011795b0 결과: Scene_Versus 플래그 → 0, Scene_Coop → 1, Scene_Mission → 2, 없음 → 3
  (플래그 이름은 정적 초기화 0x7102b582d0 가 0x71058e90f8/0x71058e9278/0x71058e9158 에 넣는 문자열 [실행: player_initemu]).
- 전역 게임 객체 *0x71058e42f8 (+200 → +0x6548/+0x6550/+0x6518), 전역 바이트 0x71058e87dc 는 합성 값으로 채운다.
- 해시 0x7101179f90(재귀, 표 0x7104a98728)는 원본 실행 값과 파이썬 표 계산을 비교한다.
스텁: 없음(PLT 호출 없음). 0x71011795b0(게임 데이터 플래그 조회)와 선택기 슬롯 0 본문은 실행하지 않았다.
사용: PY web/tools/r6_gfx_char_teamcolor_emu.py → analysis/completion/r6/gfx_char_teamcolor_emu.json
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SEL = 0x7101179a24
HASH = 0x7101179f90
G_GAME = 0x71058e42f8
G_87DC = 0x71058e87dc
NAMES = ["PlayerMake", "Plaza", "LobbyCoop", "LobbyLocal", "DayChange", "Boot", "LobbyVersus", "VersusScene", ""]


def expect(flag128, cat, name, b6548, b6550, p6518_30, b87dc):
    if flag128:
        return 8
    if cat == 2:
        return 3
    if cat == 1:
        return 2 if b6550 else 4
    if cat == 0:
        if b6548:
            return 2
        return 5 if b87dc else 4
    if name == "PlayerMake":
        return 6
    if name == "Plaza" and p6518_30 == 0:
        return 7
    if name == "LobbyCoop":
        return 1
    if name in ("LobbyLocal", "DayChange", "Boot"):
        return 0
    return 5 if b87dc else 0


def crc_tbl(u, s):
    h = 0
    for c in s.encode():
        h = struct.unpack("<H", u.mu.mem_read(0x7104a98728 + ((h ^ c) & 0xFF) * 2, 2))[0] ^ (h >> 8)
    return h & 0xFFFF


SEL0 = 0x7101179fd0
G_MGR = 0x7105818920
G_RSDB = 0x710599b420


def selector0(u):
    """선택기 0(로비·LobbyLocal·Boot 등) 슬롯 0 0x7101179fd0 원본 실행.
    스텁: 0x710140946c(RSDB 이름 조회) → 합성 행(+0x88 Tag) 또는 0, 0x7101179c80(Tag==0 행 무작위 선택) → 합성 이름 또는 0."""
    from unicorn import UC_HOOK_CODE
    from unicorn.arm64_const import UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2
    m = u.mu
    mgr = u.alloc(0xc00)
    u.wq(G_MGR, mgr)
    rsdb = u.alloc(0x40)
    u.wq(G_RSDB, rsdb)
    u.u32(rsdb + 0x10, 3)
    tbls = u.alloc(0x200)
    u.wq(rsdb + 0x18, tbls)
    u.wq(tbls + 0x20, 0x1234)
    names = ["Work/Gyml/OrangeBlue.game__gfx__parameter__TeamColorDataSet.gyml",
             "Work/Gyml/YellowPurple.game__gfx__parameter__TeamColorDataSet.gyml",
             "Work/Gyml/PinkGreen.game__gfx__parameter__TeamColorDataSet.gyml",
             "Work/Gyml/CoopBlue.game__gfx__parameter__TeamColorDataSet.gyml"]
    keyed = {}
    nodes = []
    for n in names:
        h = crc_tbl(u, n)
        node = u.alloc(0x40)
        buf = u.alloc(0x80)
        m.mem_write(buf, n.encode() + b"\x00")
        u.wq(node + 0x30, buf)
        u.u32(node + 0x38, 0x80)
        m.mem_write(node + 0x20, struct.pack("<H", h))
        keyed[h] = n
        nodes.append((h, node))
    nodes.sort()
    def build(lst):
        if not lst:
            return 0
        mid = len(lst) // 2
        h, nd = lst[mid]
        u.wq(nd + 8, build(lst[:mid]))
        u.wq(nd + 0x10, build(lst[mid + 1:]))
        return nd
    u.wq(mgr + 0xb80, build(nodes))
    state = {"row": None, "pick": None, "log": []}
    rowbuf = u.alloc(0x100)
    pickbuf = u.alloc(0x10)

    def hk_rsdb(mu, addr, size, d):
        nm = u._cstr(u.rq(mu.reg_read(UC_ARM64_REG_X1))).decode()
        state["log"].append(("rsdb", nm))
        if state["row"] is None:
            mu.reg_write(UC_ARM64_REG_X0, 0)
        else:
            u.u32(rowbuf + 0x88, state["row"])
            mu.reg_write(UC_ARM64_REG_X0, rowbuf)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def hk_pick(mu, addr, size, d):
        col = mu.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF
        val = struct.unpack("<I", mu.mem_read(mu.reg_read(UC_ARM64_REG_X2), 4))[0]
        state["log"].append(("pick", col, val))
        if state["pick"] is None:
            mu.reg_write(UC_ARM64_REG_X0, 0)
        else:
            u.wq(pickbuf, u.cstr(state["pick"]))
            mu.reg_write(UC_ARM64_REG_X0, pickbuf)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    m.hook_add(UC_HOOK_CODE, hk_rsdb, begin=0x710140946c, end=0x710140946c)
    m.hook_add(UC_HOOK_CODE, hk_pick, begin=0x7101179c80, end=0x7101179c80)
    sel = u.alloc(0x20)
    st = u.alloc(0x20)
    u.wq(sel + 8, st)
    ok = total = 0
    fails = []
    yp = crc_tbl(u, names[1])
    for cur in names:
        for tag in [None] + list(range(10)):
            for pick in (None, names[2], names[0]):
                hcur = crc_tbl(u, cur)
                m.mem_write(st + 0xc, struct.pack("<H", hcur) + b"Z")
                state.update(row=tag, pick=pick, log=[])
                got = u.call(SEL0, sel) & 0xFFFFFFFF
                gid = struct.unpack("<H", m.mem_read(st + 0xc, 2))[0]
                gsw = m.mem_read(st + 0xe, 1)[0]
                if tag is not None and tag <= 1:
                    exp = (hcur, hcur, 0x5a, [("rsdb", cur)])
                else:
                    e = crc_tbl(u, pick) if pick else yp
                    exp = (e, e, 0, [("rsdb", cur), ("pick", 0xc, 0)])
                good = (got, gid, gsw, state["log"]) == exp
                total += 1
                ok += good
                if not good and len(fails) < 5:
                    fails.append({"cur": cur, "tag": tag, "pick": pick, "got": [got, gid, gsw, state["log"]], "exp": list(exp)})
    return {"function": hex(SEL0), "cases": total, "matches": ok, "fail_examples": fails,
            "stubs": ["0x710140946c RSDB 이름 → 행: 합성 행(+0x88 = Tag) 또는 0",
                      "0x7101179c80 (열 0xc == 0 인 행 무작위): 호출 인자만 기록하고 합성 이름 또는 0 반환",
                      "관리자 +0xb80 트리(키 = 이름 해시)는 합성 노드 4개"]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    u = GUC()
    st = u.alloc(0x200)
    game = u.alloc(0x100)
    o6548 = u.alloc(0x100)
    o6550 = u.alloc(0x300)
    o6518 = u.alloc(0x40)
    big = u.alloc(0x7000)
    u.wq(G_GAME, game)
    u.wq(game + 200, big)
    u.wq(big + 0x6548, o6548)
    u.wq(big + 0x6550, o6550)
    u.wq(big + 0x6518, o6518)
    name_ptr = {n: u.cstr(n) for n in NAMES}
    ok = total = 0
    fails = []
    for flag128 in (0, 1):
        for cat in range(4):
            for n in NAMES:
                for b6548 in (0, 1):
                    for b6550 in (0, 1):
                        for p30 in (0, 1):
                            for b87dc in (0, 1):
                                u.mu.mem_write(st + 0x128, bytes([flag128]))
                                u.mu.mem_write(o6548 + 0xb4, struct.pack("<H", b6548))
                                u.mu.mem_write(o6550 + 600, struct.pack("<H", b6550))
                                u.u32(o6518 + 0x30, p30)
                                u.mu.mem_write(G_87DC, bytes([b87dc]))
                                got = u.call(SEL, st, cat, name_ptr[n]) & 0xFFFFFFFF
                                exp = expect(flag128, cat, n, b6548, b6550, p30, b87dc)
                                total += 1
                                if got == exp:
                                    ok += 1
                                elif len(fails) < 5:
                                    fails.append({"flag128": flag128, "cat": cat, "name": n, "got": got, "exp": exp})
    rows = ["Work/Gyml/YellowPurple.game__gfx__parameter__TeamColorDataSet.gyml",
            "Work/Gyml/OrangeBlue.game__gfx__parameter__TeamColorDataSet.gyml",
            "Work/Gyml/WarmingUpYellowBlue.game__gfx__parameter__TeamColorDataSet.gyml", "", "A"]
    hok = 0
    hres = []
    for r in rows:
        got = u.call(HASH, u.cstr(r), 0) & 0xFFFF
        exp = crc_tbl(u, r)
        hok += got == exp
        hres.append({"name": r, "hash": hex(got), "py": hex(exp)})
    s0 = selector0(u)
    out = {"selector0": s0, "selector": hex(SEL), "cases": total, "matches": ok, "fail_examples": fails,
           "hash": hex(HASH), "hash_cases": len(rows), "hash_matches": hok, "hash_samples": hres,
           "lobby": {"LobbyVersus, 분류 3, 87dc=0": expect(0, 3, "LobbyVersus", 0, 0, 0, 0),
                     "LobbyVersus, 분류 3, 87dc=1": expect(0, 3, "LobbyVersus", 0, 0, 0, 1)},
           "stubs": ["없음(외부 호출 없음). 게임 객체·0x71058e87dc 는 합성 값",
                     "분류를 만드는 0x71011795b0(게임 데이터 플래그)과 선택기 슬롯 본문은 실행하지 않음"],
           "plt_stubbed": sorted(set(u.plt_stubbed))}
    p = ROOT / "analysis/completion/r6/gfx_char_teamcolor_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cases", "matches", "hash_cases", "hash_matches", "lobby", "plt_stubbed")}, ensure_ascii=False))
    if fails:
        print(fails)
    sys.exit(0 if ok == total and hok == len(rows) and s0["matches"] == s0["cases"] else 1)


if __name__ == "__main__":
    main()
