"""넷 이벤트/상태 write 함수(vtable 슬롯 12)를 직선 판독해 필드별 비트 수를 뽑는다.
- writer->vt[0xa8](writer, ctx, &val, nbits) 호출 = 비트 쓰기, nbits=w3
- bl 헬퍼(예: 0x71029064bc 속도, 0x7102905f44 방향)는 재귀 분석
- 분기·루프는 무시(호출 위치마다 1회). 합계를 등록 비트 수와 비교해 검증.
사용: PY web/tools/network_bitlayout.py [이름 정규식] [--json out]
"""
import argparse
import csv
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img
from network_emu import _md, regname

ROOT = Path(__file__).resolve().parents[2]
WRITE_SLOT_OFF = 0xA8


def analyze(m, fa, cache, depth=0):
    """fa 함수의 비트 쓰기 목록 [(site, bits, fields, via)]"""
    if fa in cache:
        return cache[fa]
    cache[fa] = []
    out = []
    regs = {}          # reg -> ('this',off) | ('fld',off) | int | ('vt',..)
    recent = []        # 최근 읽은 this 필드 오프셋
    p = fa - BASE
    n = 0
    while n < 3000:
        ins = next(_md.disasm(m[p:p + 4], BASE + p), None)
        n += 1
        if ins is None:
            break
        mn, ops = ins.mnemonic, ins.operands
        if n == 1:
            regs = {"x0": ("this", 0), "x1": ("stream", 0)}
        if mn == "ret":
            break
        if mn in ("mov", "movz") and len(ops) == 2:
            d = regname(ops[0].reg)
            if ops[1].type == 2:  # imm
                regs[d] = ops[1].imm
            elif ops[1].type == 1:
                regs[d] = regs.get(regname(ops[1].reg))
        elif mn == "add" and len(ops) == 3 and ops[2].type == 2:
            s = regs.get(regname(ops[1].reg))
            d = regname(ops[0].reg)
            if isinstance(s, tuple) and s[0] == "this":
                regs[d] = ("this", s[1] + ops[2].imm)
            else:
                regs[d] = None
        elif mn.startswith("ld") and ops and ops[-1].type == 3:
            b = regs.get(regname(ops[-1].mem.base))
            if isinstance(b, tuple) and b[0] == "this":
                off = b[1] + ops[-1].mem.disp
                recent.append(off)
                for o in ops[:-1]:
                    if o.type == 1:
                        regs[regname(o.reg)] = ("fld", off)
            elif mn == "ldr" and ops[-1].mem.disp == WRITE_SLOT_OFF:
                regs[regname(ops[0].reg)] = ("wfn",)
            elif mn == "ldr" and ops[-1].mem.disp == 0x48:
                regs[regname(ops[0].reg)] = ("rfn",)
            else:
                for o in ops[:-1]:
                    if o.type == 1:
                        regs[regname(o.reg)] = None
        elif mn == "blr":
            t = regs.get(regname(ops[0].reg))
            if t == ("wfn",):
                bits = regs.get("x3")
                out.append((ins.address, bits if isinstance(bits, int) else None, sorted(set(recent)), None))
                recent = []
            for i in range(19):
                regs.pop(f"x{i}", None)
        elif mn == "bl":
            tgt = ops[0].imm
            arg = regs.get("x1")
            sub = analyze(m, tgt, cache, depth + 1) if depth < 4 else []
            if sub:
                bits = sum(b for _, b, _, _ in sub if b) if all(b for _, b, _, _ in sub) else None
                fld = [arg[1]] if isinstance(arg, tuple) and arg[0] == "this" else sorted(set(recent))
                out.append((ins.address, bits, fld, tgt))
                recent = []
            for i in range(19):
                regs.pop(f"x{i}", None)
        elif mn in ("b",) and ops[0].type == 2:
            tgt = ops[0].imm
            if not (fa <= tgt < fa + 0x4000):  # 꼬리 호출
                sub = analyze(m, tgt, cache, depth + 1) if depth < 4 else []
                for s in sub:
                    out.append(s)
                break
        else:
            if ops and ops[0].type == 1 and not mn.startswith(("st", "cmp", "tst", "cb", "tb", "b", "fcmp", "cmn")):
                regs[regname(ops[0].reg)] = None
        p += 4
    cache[fa] = out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pat", nargs="?", default=".")
    ap.add_argument("--json")
    a = ap.parse_args()
    m = load_img()
    rows = list(csv.DictReader(open(ROOT / "analysis/network/nettypes.tsv", encoding="utf-8"), delimiter="\t"))
    cache = {}
    res = []
    sys.stdout.reconfigure(encoding="utf-8")
    ok = bad = 0
    for r in rows:
        if not re.search(a.pat, r["name"]) or not r["write"]:
            continue
        lay = analyze(m, int(r["write"], 16), {})
        tot = sum(b for _, b, _, _ in lay if b) if all(b for _, b, _, _ in lay) else None
        want = int(r["bits_max"]) if r["bits_max"] not in ("None", "") else None
        match = tot == want and r["bits_min"] == r["bits_max"]
        ok += match
        bad += not match
        res.append(dict(name=r["name"], write=r["write"], bits_reg=[r["bits_min"], r["bits_max"]], bits_sum=tot, match=match,
                        fields=[dict(site=hex(s), bits=b, this_off=[hex(x) for x in f], helper=hex(h) if h else None) for s, b, f, h in lay]))
        fl = " ".join(f"{'/'.join(hex(x) for x in f) or '?'}:{b}{'(' + hex(h) + ')' if h else ''}" for s, b, f, h in lay)
        print(f"{'OK ' if match else '-- '}{r['name']} reg={r['bits_min']}/{r['bits_max']} sum={tot} | {fl}")
    print(f"match {ok} / {ok + bad}", file=sys.stderr)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
