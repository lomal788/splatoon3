"""Candidates for B+ad0 stores; offsets alone are not object/type or absence proofs.

Only direct STR/STUR u32 stores at literal ad0 and ADD-immediate aliases are
enumerated. Register-offset stores, passed pointers and nonlinear paths remain.
"""
import bisect
import json
from pathlib import Path
import numpy as np
from xref import BASE, TEXT_END, load_img
from disasm import disasm, func_start
from func_lookup import load

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/timer'


def main():
    data = load_img()
    words = np.frombuffer(data[:TEXT_END & ~3], dtype='<u4')
    direct = np.flatnonzero(((words & 0xffc00000) == 0xb9000000) &
                           ((((words >> 10) & 4095) * 4) == 0xad0))
    aliases = np.flatnonzero(((words & 0xffc00000) == 0x91000000) &
                            (((words >> 10) & 4095) == 0xad0))
    starts, _ = load()
    rows = []
    for kind, hits in [('direct_u32_store', direct), ('add_alias', aliases)]:
        for h in hits:
            address = BASE + int(h) * 4
            guessed = starts[bisect.bisect_right(starts, address)-1]
            prologue = func_start(data, int(h)*4)
            listing = disasm(data, max(0, int(h)*4-80), end=int(h)*4+100)
            rows.append(dict(kind=kind, pc=hex(address), listedFunction=hex(guessed),
                             rawPrologue=hex(BASE+prologue) if prologue else None,
                             asm=[dict(pc=hex(BASE+p), instruction=a) for p,a,_ in listing]))
    result = dict(scope=__doc__, counts=dict(direct=len(direct), aliases=len(aliases)), candidates=rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'writer_candidates.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    selected = [r for r in rows if 0x7102400000 <= int(r['pc'],16) < 0x71024f0000]
    print(json.dumps(dict(counts=result['counts'], playerRangeCandidates=[{k:r[k] for k in ['kind','pc','listedFunction','rawPrologue']} for r in selected])))


if __name__ == '__main__':
    main()
