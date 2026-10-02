"""필드 오프셋 묶음 스캐너: 같은 베이스 레지스터로 여러 오프셋을 읽는 짧은 구간 찾기.
사용: camera_ldscan.py 'f:0x7c,f:0x78,f:0x74' [--win 64] [--min 3]
  f=ldr s(32bit fp), w=ldr w(32bit int), x=ldr x(64bit)
"""
import sys, argparse, numpy as np
IMG = r"C:/dev/splatoon3/extracted/exefs/main.img"
BASE = 0x7100000000
TEXT_END = 0x3e9df50

def enc_mask(kind):
    # LDR (unsigned imm) : size|111|V|01|01|imm12|Rn|Rt
    if kind == 'f': return 0xBD400000, 4
    if kind == 'w': return 0xB9400000, 4
    if kind == 'x': return 0xF9400000, 8
    if kind == 'b': return 0x39400000, 1
    raise ValueError(kind)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec'); ap.add_argument('--win', type=int, default=48)
    ap.add_argument('--min', type=int, default=0); ap.add_argument('--samereg', action='store_true')
    a = ap.parse_args()
    data = np.fromfile(IMG, dtype='<u4', count=TEXT_END // 4)
    specs = []
    for s in a.spec.split(','):
        k, off = s.split(':'); off = int(off, 0)
        base, sc = enc_mask(k)
        specs.append((s, base | ((off // sc) << 10)))
    hits = {}
    for name, val in specs:
        idx = np.nonzero((data & 0xFFFFFC00) == val)[0]
        hits[name] = idx
    need = a.min or len(specs)
    allidx = np.concatenate([np.stack([h, np.full(len(h), i)], 1) for i, h in enumerate(hits.values())])
    allidx = allidx[np.argsort(allidx[:, 0])]
    res = []
    j = 0
    n = len(allidx)
    for i in range(n):
        while allidx[i, 0] - allidx[j, 0] > a.win: j += 1
        kinds = set(allidx[j:i + 1, 1].tolist())
        if len(kinds) >= need:
            res.append(int(allidx[j, 0]))
    seen = -10**9
    for r in res:
        if r - seen > a.win:
            print(hex(BASE + r * 4))
        seen = r
main()
