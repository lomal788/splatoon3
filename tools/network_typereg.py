"""0x71012f8808(타입 등록) 호출을 모두 찾아 인자(이름·해시·크기·함수 포인터)를 표로 만든다.
사용: PY web/tools/network_typereg.py [--json analysis/network/typereg.json] [--grep Net]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img
from disasm import func_start
from network_emu import bl_callers, run_to, s

REG = 0x71012F8808


def scan(m, target=REG):
    calls = bl_callers(m, target)
    by_func = {}
    for c in calls:
        f = func_start(m, c, 0x40000)
        by_func.setdefault(f, []).append(c)
    rows = []
    for f, cs in sorted(by_func.items()):
        want = set(cs)
        end = max(cs) + 4

        def on_call(e, p, tgt):
            if p not in want:
                return
            x2 = e.get("x2")
            name = None
            if isinstance(x2, tuple):
                name = s(m, e.stk.get(x2))
            elif isinstance(x2, int):
                import struct
                off = x2 - BASE
                if 0 <= off < len(m):
                    name = s(m, struct.unpack_from("<Q", m, off)[0])
            sp = e.get("sp")
            a0 = e.stk.get((sp[0], sp[1])) if isinstance(sp, tuple) else None
            a1 = e.stk.get((sp[0], sp[1] + 8)) if isinstance(sp, tuple) else None
            hx = lambda v: f"{v:#x}" if isinstance(v, int) else None
            rows.append(dict(call=hex(BASE + p), func=hex(BASE + f), name=name,
                             entry=hx(e.get("x0")), hash32=hx(e.get("x1")),
                             w3=e.get("x3"), w4=e.get("x4"), w5=e.get("x5"),
                             x6=hx(e.get("x6")), x7=hx(e.get("x7")), sp0=hx(a0), sp8=hx(a1)))
        run_to(m, f, end, on_call)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--grep")
    ap.add_argument("--target", default=hex(REG))
    a = ap.parse_args()
    m = load_img()
    rows = scan(m, int(a.target, 16))
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for r in rows:
        if a.grep and (not r["name"] or a.grep not in r["name"]):
            continue
        print(f'{r["call"]} {r["entry"]} {r["hash32"]} w3={r["w3"]} w4={r["w4"]} w5={r["w5"]} x6={r["x6"]} x7={r["x7"]} sp0={r["sp0"]} sp8={r["sp8"]} {r["name"]}')
    print("total", len(rows), "named", sum(1 for r in rows if r["name"]), file=sys.stderr)


if __name__ == "__main__":
    main()


def ctor_vtable(m, ctor):
    """생성 함수(sp0) 첫 adrp+add 가 기본 vtable."""
    import struct
    from network_emu import _md
    off = ctor - BASE
    page = None
    for ins in _md.disasm(m[off:off + 0x40], ctor):
        if ins.mnemonic == "adrp":
            page = ins.operands[1].imm
        elif ins.mnemonic == "add" and page is not None:
            return page + ins.operands[2].imm
    return None


SLOTS = {2: "reset", 6: "equals", 7: "copy", 10: "bits_a", 11: "bits_b", 12: "write", 13: "read", 14: "getname"}


def vt_slots(m, vt):
    import struct
    return {k: struct.unpack_from("<Q", m, vt - BASE + k * 8)[0] for k in SLOTS}
