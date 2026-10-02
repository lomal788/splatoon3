"""원본 실행: AS 노드 종류 21(BoolSelector) 자식 선택 0x71039c46c8 (vt 0x7105742278 +0xe0) + 값 읽기 0x71039982bc.

상수 경로(태그 >= 0)는 외부 호출 없이 원본 그대로 실행한다.
블랙보드 경로(태그 0x8xxxxxxx)는 문맥+0x20 객체 vt+0x130(이름→순번), 문맥+0x28 객체 vt+0x148(순번→값 주소)만 스텁으로 둔다.
재구현: 자식 번호 = (값 != 0) ? 0 : 1. IntSelector(종류 8, 0x71039cda20): 자식 n 개 중 앞 n−1 개의 case 값과 처음 같은 번호, 없으면 n−1(마지막).
사용: PY web/tools/r5_gfx_char_boolsel_emu.py → analysis/completion/r5/gfx_char_boolsel_emu.json
"""
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC, STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = 0x71039c46c8


def main():
    u = GUC()
    m = u.mu
    st = {"byte": 0}
    valbuf = u.alloc(0x10)

    def h130(mu, a, s, d):
        mu.reg_write(UC_ARM64_REG_X0, 3)

    def h148(mu, a, s, d):
        mu.mem_write(valbuf, bytes([st["byte"]]))
        mu.reg_write(UC_ARM64_REG_X0, valbuf)

    m.hook_add(UC_HOOK_CODE, h130, begin=STUB + 0x730, end=STUB + 0x730)
    m.hook_add(UC_HOOK_CODE, h148, begin=STUB + 0x748, end=STUB + 0x748)
    o20 = u.alloc(0x10); vt20 = u.alloc(0x200); u.wq(o20, vt20); u.wq(vt20 + 0x130, STUB + 0x730)
    o28 = u.alloc(0x10); vt28 = u.alloc(0x200); u.wq(o28, vt28); u.wq(vt28 + 0x148, STUB + 0x748)
    ctx = u.alloc(0x40); u.wq(ctx + 0x20, o20); u.wq(ctx + 0x28, o28)
    node = u.alloc(0x40); body = u.alloc(0x40); u.wq(node + 0x18, body); u.wq(node + 0x10, u.alloc(0x10))
    inst = u.alloc(0x100)
    changed = u.alloc(8)
    ok = 0; total = 0; fails = []
    for v in (0, 1, 2, 0xff, 0x100, 0xffffffff):
        m.mem_write(body, struct.pack("<iI", 0, v))
        r = u.call(F, node, ctx, inst, changed) & 0xFFFFFFFF
        exp = 0 if v != 0 else 1
        total += 1; ok += r == exp
        if r != exp: fails.append(["const", v, r, exp])
    for b in (0, 1, 0x80, 0xff):
        st["byte"] = b
        m.mem_write(body, struct.pack("<II", 0x80000002, 0))
        r = u.call(F, node, ctx, inst, changed) & 0xFFFFFFFF
        exp = 0 if b != 0 else 1
        total += 1; ok += r == exp
        if r != exp: fails.append(["bb", b, r, exp])
    # IntSelector(종류 8) 0x71039cda20: 상수 경로
    import random
    rng = random.Random(8)
    F8 = 0x71039cda20
    tbl = u.alloc(0x200)
    base_obj = u.alloc(0x20)
    u.wq(node + 0x10, base_obj)
    u.wq(base_obj + 8, tbl)
    int_ok = 0; int_total = 0
    for n in range(1, 7):
        for trial in range(20):
            cases = [rng.randint(-3, 6) for _ in range(n)]
            x = rng.randint(-4, 7)
            m.mem_write(body, struct.pack("<ii", 0, x))
            m.mem_write(body + 0x18, bytes([n, 0]))
            for i, cv in enumerate(cases):
                u.u32(body + 0x20 + 4 * i, 0x10 * i)
                m.mem_write(tbl + 0x10 * i, struct.pack("<ii", 0, cv))
            r = u.call(F8, node, ctx, inst, 0) & 0xFFFFFFFF
            exp = n - 1
            for i in range(n - 1):
                if cases[i] == x:
                    exp = i
                    break
            if n < 2:
                exp = n - 1
            int_total += 1; int_ok += r == (exp & 0xFFFFFFFF)
            if r != (exp & 0xFFFFFFFF) and len(fails) < 10: fails.append(["int", n, cases, x, r, exp])
    total += int_total; ok += int_ok
    out = {"function": [hex(F), "0x71039982bc", hex(F8)], "int_selector": [int_total, int_ok], "cases": total, "matches": ok, "fails": fails,
           "stubs": ["블랙보드 경로: 문맥+0x20 vt+0x130 → 순번 3, 문맥+0x28 vt+0x148 → 값 바이트 주소"],
           "plt_stubbed": sorted(set(u.plt_stubbed)),
           "not_executed": ["IntSelector 블랙보드 경로", "실수 파라미터 표 경로(태그 0xd/0xe)", "선택 결과의 캐시·재평가 0x71039ce4dc", "변화 플래그 의미"]}
    p = ROOT / "analysis/completion/r5/gfx_char_boolsel_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
