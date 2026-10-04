"""Readonly bounded camera-state supplier follow-up; candidates are not proofs."""
import json
from pathlib import Path
import numpy as np
from disasm import disasm
from xref import BASE, TEXT_END, load_img

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def main():
    data = load_img()
    words = np.frombuffer(data[:TEXT_END], dtype='<u4')
    indices = np.flatnonzero((words & 0xfc000000) == 0x94000000)
    immediate = words[indices].astype(np.int64) & 0x3ffffff
    immediate = np.where(immediate & 0x2000000, immediate-0x4000000, immediate)
    calls = indices[indices*4+immediate*4 == 0x3c838dc]*4
    candidates = []
    for call in calls:
        rows = disasm(data, int(call)-80, end=int(call)+4)
        if any('#0x78' in asm and asm.startswith('add ') for _, asm, _ in rows):
            candidates.append(dict(call=hex(BASE+int(call)),
                                   rows=[dict(pc=hex(BASE+pc), asm=asm, annotation=n)
                                         for pc, asm, n in rows]))
    owned_ranges = [(0x26b1330,0x26b133c), (0x26b1180,0x26b11dc)]
    result = dict(scope='bounded preceding-20instruction ADD78 filter for ActorRef bind callers; '
                        'not complete pointer dataflow or runtime',
                  actorref_direct_bl_count=len(calls), add78_candidates=candidates,
                  vehicle_subscription_callback=[dict(start=hex(BASE+start), end=hex(BASE+end),
                    rows=[dict(pc=hex(BASE+pc), asm=asm, annotation=n)
                          for pc,asm,n in disasm(data,start,end=end)]) for start,end in owned_ranges])
    (OUT/'followup_candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',
                                                encoding='utf-8')
    print(json.dumps(dict(calls=len(calls), add78_candidates=[c['call'] for c in candidates]),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
