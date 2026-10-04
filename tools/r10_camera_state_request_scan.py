"""Search raw +1d byte writes for S request candidates; roots remain unknown."""
import json
import bisect
from pathlib import Path
import numpy as np
from disasm import disasm
from xref import BASE, TEXT_END, load_img
from func_lookup import load

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'analysis/camera_100_r10/state'


def main():
    data = load_img()
    words = np.frombuffer(data[:TEXT_END], dtype='<u4')
    # STRB imm12 and STURB imm9 +29. Neither object type nor absence proof.
    hits = np.flatnonzero((((words & 0xffc00000) == 0x39000000) &
                           (((words >> 10) & 4095) == 29)) |
                          (((words & 0xffe00c00) == 0x38000000) &
                           (((words >> 12) & 511) == 29)))
    starts, functions = load()
    rows = []
    for h in hits:
        address = BASE + int(h)*4
        function = starts[bisect.bisect_right(starts, address)-1]
        listing = disasm(data, max(int(h)*4-100, function-BASE), end=int(h)*4+132)
        fields = ' '.join(a for _, a, _ in listing)
        score = sum(s in fields for s in ['#0x18]', '#0x1c]', '#0x20]', '#0x30]', '#0x38]'])
        if score < 3:
            continue
        rows.append(dict(pc=hex(address), function=hex(function), score=score,
                         asm=[dict(pc=hex(BASE+p), instruction=a) for p,a,_ in listing]))
    result = dict(scope='unknown-root +1d byte-store field-cooccurrence candidates; not type or absence proof',
                  raw_hits=len(hits), candidates=rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'request_candidates.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(raw_hits=len(hits), candidates=[{k:r[k] for k in ['pc','function','score']} for r in rows])))


if __name__ == '__main__':
    main()
