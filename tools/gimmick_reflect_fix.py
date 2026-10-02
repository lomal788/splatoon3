"""파라미터 리플렉션 방문 함수를 '역할 기준'으로 다시 읽어 커브 필드 뒤 오프셋 꼬임을 바로잡는다.

param_reflect.py 는 'add xN, this, #imm' 을 나온 순서대로 모아 이름 문자열을 만날 때 [값, 플래그]로 쓴다.
커브(game::Curve 등) 필드는 방문 코드가 '값 포인터 → 이름 → 플래그 포인터' 순서라서
커브의 플래그 오프셋이 다음 필드의 값으로, 다음 필드의 값이 플래그로 밀린다(GrindRail PlayerSideJumpGndColOffsetY 등).

여기서는 블록(방문자 호출 blr 사이)마다
  값   = 'stp xT, xV, [x29, #-0x10]' 의 xV 또는 단순형 경로에서 플래그·이름 외의 this+imm
  플래그 = 'str xF, [sp, #0x18]' 의 xF 가 가리키는 this+imm
  순번 = 'str wK, [sp, #0x20]' 의 즉시값
으로 정한다.

사용: PY web/tools/gimmick_reflect_fix.py spl__PlayerGrindRailParam [spl__PlayerPipelineParam ...] | <방문함수 주소 0x...>
      (analysis/param_reflect/<이름>.json 의 visitor 를 읽고, 기존 값과 다른 필드에 '정정' 표시)
"""
import json
import struct
import sys
from pathlib import Path

from capstone import arm64_const as A

sys.path.insert(0, str(Path(__file__).resolve().parent))
from param_reflect import BASE, func_end, ins_at, load_img, reg_name  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def parse(m, start):
    end = func_end(m, start)
    this = "x0"
    pages = {}
    regs = {}       # reg -> ('this', imm) | ('imm', k)
    blocks = []
    cur = {"vals": [], "flag": None, "idx": None, "name": None}
    p = start
    while p < end:
        ins = ins_at(m, p)
        p += 4
        if ins is None:
            continue
        ops = ins.operands
        mn = ins.mnemonic
        if mn == "mov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_REG and reg_name(ops[1].reg) == "x0" and this == "x0":
            this = reg_name(ops[0].reg)
        elif mn == "mov" and len(ops) == 2 and ops[1].type == A.ARM64_OP_IMM:
            regs[reg_name(ops[0].reg).replace("w", "x")] = ("imm", ops[1].imm)
        elif mn == "adrp":
            pages[reg_name(ops[0].reg)] = ops[1].imm - BASE
        elif mn == "add" and len(ops) == 3 and ops[2].type == A.ARM64_OP_IMM:
            src, dst = reg_name(ops[1].reg), reg_name(ops[0].reg)
            if src == this:
                regs[dst] = ("this", ops[2].imm)
                cur["vals"].append((ops[2].imm, dst))
            elif src in pages:
                t = pages[src] + ops[2].imm
                e = m.find(b"\0", t, t + 100)
                s = m[t:e]
                if e > t + 1 and m[t - 1] == 0 and s.replace(b"_", b"").isalnum():
                    cur["name"] = s.decode()
                regs.pop(dst, None)
            else:
                regs.pop(dst, None)
        elif mn == "str" and len(ops) == 2 and ops[1].type == A.ARM64_OP_MEM and reg_name(ops[1].mem.base) == "sp":
            r = reg_name(ops[0].reg).replace("w", "x")
            if ops[1].mem.disp == 0x18 and regs.get(r, ("",))[0] == "this":
                cur["flag"] = regs[r][1]
            elif ops[1].mem.disp == 0x20 and regs.get(r, ("",))[0] == "imm":
                cur["idx"] = regs[r][1]
        elif mn == "blr":
            if cur["name"]:
                vals = [v for v, _ in cur["vals"] if v != cur["flag"]]
                blocks.append({"name": cur["name"], "offset": vals[0] if vals else None,
                               "flag_offset": cur["flag"], "index": cur["idx"], "call": hex(BASE + p - 4)})
            cur = {"vals": [], "flag": None, "idx": None, "name": None}
    return blocks


def main():
    m = load_img()
    for name in sys.argv[1:]:
        if name.startswith("0x"):
            j = {"visitor": name, "fields": []}
        else:
            j = json.loads((ROOT / "analysis/param_reflect" / f"{name}.json").read_text(encoding="utf-8"))
        old = {f["name"]: f for f in j["fields"]}
        start = int(j["visitor"], 16) - BASE
        print(f"== {name} visitor {j['visitor']}")
        for b in parse(m, start):
            o = old.get(b["name"], {})
            fix = bool(o) and (o.get("offset"), o.get("flag_offset")) != (b["offset"], b["flag_offset"])
            print(f"  [{b['index']}] {b['name']:34s} +{(b["offset"] if b["offset"] is not None else -1):#x} flag +{(b['flag_offset'] or 0):#x}"
                  + (f"   <- 정정 (param_reflect: +{(o.get('offset') or 0):#x} / flag {o.get('flag_offset') and hex(o['flag_offset'])})" if fix else ""))


if __name__ == "__main__":
    main()
