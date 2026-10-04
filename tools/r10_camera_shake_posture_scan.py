"""Candidate-only field scan; never turns an offset coincidence into a type proof."""
import bisect
import json
from pathlib import Path

import numpy as np
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000
blob = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
words = np.frombuffer(blob[:0x3e99000], dtype="<u4")
starts = []
for line in (ROOT / "analysis/functions/main.nso.tsv").read_text(encoding="utf8").splitlines()[1:]:
    starts.append(int(line.split("\t")[0], 16))
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)


def row(pc):
    ins = next(md.disasm(blob[pc:pc + 4], BASE + pc))
    idx = bisect.bisect_right(starts, BASE + pc) - 1
    return {"pc": hex(BASE + pc), "function": hex(starts[idx]), "insn": ins.mnemonic + " " + ins.op_str}


def offsets(opcode, size, field):
    return np.nonzero(((words & 0xffc00000) == opcode) & (((words >> 10) & 4095) * size == field))[0] * 4


stores = [row(int(pc)) for pc in offsets(0xb9000000, 4, 0x8c)]
dirty = offsets(0x39000000, 1, 8).tolist() + offsets(0x39000000, 1, 9).tolist()
near = []
for r in stores:
    pc = int(r["pc"], 16) - BASE
    d = [int(a) for a in dirty if abs(int(a) - pc) <= 0x90]
    if d:
        near.append({**r, "nearby_dirty8_9": [row(a) for a in d]})

triples = []
read4c4 = offsets(0xbd400000, 4, 0x4c4).tolist() + offsets(0xb9400000, 4, 0x4c4).tolist()
read4c8 = offsets(0xbd400000, 4, 0x4c8).tolist() + offsets(0xb9400000, 4, 0x4c8).tolist()
read4cc = offsets(0xbd400000, 4, 0x4cc).tolist() + offsets(0xb9400000, 4, 0x4cc).tolist()
for pc in read4c4:
    b = [int(a) for a in read4c8 if abs(int(a) - pc) <= 0x100]
    c = [int(a) for a in read4cc if abs(int(a) - pc) <= 0x100]
    if b and c:
        triples.append({"4c4": row(int(pc)), "4c8": [row(a) for a in b], "4cc": [row(a) for a in c]})

out = {"scope": "main text 0..3e99000 unsigned STR W #8c with nearby STRB #8/9; LDR W/S #4c4 with nearby #4c8/#4cc", "limitation": "candidate discovery only; unrelated bases/objects are possible; does not cover STP/STUR/memcpy/aliases or runtime pointers", "str8c_count": len(stores), "near_dirty_candidates": near, "context_triple_candidates": triples}
dest = ROOT / "analysis/camera_100_r10/posture/field_candidates.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
print(json.dumps({"str8c_count": len(stores), "near_dirty_candidates": len(near), "context_triple_candidates": len(triples), "functions": sorted({r["4c4"]["function"] for r in triples})}))
