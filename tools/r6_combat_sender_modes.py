"""r6 combat: 탄 송신자(DamageSender, vtable 0x71055bdfd0) 설정 functor 전수 → 클래스별 이력 모드 표.

배경 [판독]:
- 송신자 객체(0x80 B)는 spl:DamageHelper 초기화 0x7101e3d69c 안 0x7101e400fc~0x7101e4012c 에서
  +0x60 핸들 = *[0x7105797f20], +0x68 모드 = 0, +0x6c/+0x6d = 1/1, +0x70 상한 = 0, +0x74 간격 = 0.0, +0x78 key = -1.
- 송신자 vtable: vt18 핸들(+0x60), vt20 모드(+0x68), vt28 간격(+0x74), vt30 +0x6c, vt38 +0x6d, vt40 상한(+0x70), vt48 key(+0x78).
- 탄 공통 시작 0x7101645590 이 송신자마다 +0x6c = 생성정보+0x6d, 기본 functor(vt 0x710559ad50, slot0 0x710164b4b8)로 +0x6d = 탄.vt+0x208.
- 클래스별 functor(slot1 = 0x710164b4ec 공유)의 slot0 이 모드 등을 덮어쓴다.
이 도구는 functor vtable 전수(slot1 == 0x710164b4ec)를 찾아 slot0 의 +0x68/+0x6c/+0x6d/+0x70/+0x74/+0x78 쓰기와
즉시값을 뽑고, functor vtable 을 참조하는 함수의 소속 클래스(combat4_owner)를 붙인다.
사용: PY web/tools/r6_combat_sender_modes.py
"""
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import capstone
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import func_lookup  # noqa: E402
import combat4_owner  # noqa: E402

B = 0x7100000000
ROOT = Path(__file__).resolve().parents[2]
img = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
q64 = np.frombuffer(img[: len(img) // 8 * 8], dtype="<u8")
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)


def q(a):
    return struct.unpack_from("<Q", img, a - B)[0]


def dis(fn, n=400):
    out = []
    for k in range(n):
        a = fn + 4 * k
        d = next(md.disasm(img[a - B:a - B + 4], a), None)
        t = (d.mnemonic + " " + d.op_str) if d else "?"
        out.append((a, t))
        if t.startswith("ret"):
            break
    return out


def adrp_refs(target):
    """adrp+add 로 target 을 만드는 명령 위치(텍스트 전수, 느림 → xref.py 사용)."""
    r = subprocess.run([sys.executable, str(ROOT / "web/tools/xref.py"), "addr", hex(target)],
                       capture_output=True, text=True, encoding="utf-8")
    s = r.stdout.split(":", 1)[-1]
    return [int(x, 16) for x in re.findall(r"0x[0-9a-f]+", s)]


def analyze(fn):
    ins = dis(fn)
    regs = {}
    res = {}
    for a, t in ins:
        m = re.match(r"mov (w\d+), #(-?0x[0-9a-f]+|-?\d+)", t)
        if m:
            regs[m.group(1)] = int(m.group(2), 0)
        m = re.match(r"mov (w\d+), wzr", t)
        if m:
            regs[m.group(1)] = 0
        m = re.match(r"str[bh]? (w\d+|wzr|s\d+), \[x(1|19|20|21), #(0x6[89cd]|0x7[0-8])\]", t)
        if m:
            off = int(m.group(3), 16)
            src = m.group(1)
            val = 0 if src == "wzr" else regs.get(src, "계산")
            res.setdefault(hex(off), []).append({"at": hex(a), "src": src, "value": val})
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    starts, frows = func_lookup.load()
    hits = np.nonzero(q64 == 0x710164B4EC)[0]
    rows = []
    for h in hits:
        vt = B + int(h) * 8 - 8
        s0 = q(vt)
        refs = adrp_refs(vt)
        owners = []
        for r in refs:
            lk = func_lookup.lookup(starts, frows, r)
            f = lk[0] if lk else r
            o = [(hex(v), k, nm) for p_, v, k, nm in combat4_owner.owners(f)]
            owners.append({"ref": hex(r), "func": hex(f), "owner": o})
        rows.append({"functor_vt": hex(vt), "slot0": hex(s0), "writes": analyze(s0), "refs": owners})
        print(hex(vt), hex(s0), json.dumps(rows[-1]["writes"], ensure_ascii=False)[:200])
    p = ROOT / "analysis/combat/r6_sender_modes.json"
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("결과:", p, len(rows))


if __name__ == "__main__":
    main()
