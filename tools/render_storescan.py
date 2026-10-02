"""main 전체 코드에서 같은 함수·같은 기준 레지스터로 '오프셋 패턴'(이동량 허용)을 저장/적재하는 곳을 찾는다.
사용: PY web/tools/render_storescan.py <오프셋,...> [최소일치수] [--load] [--shift] [--range 시작 끝]
  오프셋들은 바이트 오프셋. 저장 명령(STR/STP/STUR, 정수·SIMD)이 덮는 바이트 범위에 오프셋이 들어가면 일치.
  --shift: 기준 이동량 x를 허용(x+오프셋). x는 첫 오프셋 기준으로 후보를 만든다.
  --load : 저장 대신 적재(LDR/LDP/LDUR).
  --simd : SIMD/FP 레지스터(s/d/q) 명령만.
출력: 함수 시작  기준레지스터  이동량  일치 오프셋 목록
"""
import sys, collections
import numpy as np

IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
TSV = r'C:/dev/splatoon3/analysis/functions/main.nso.tsv'
BASE = 0x7100000000
args = sys.argv[1:]
load = '--load' in args
shift = '--shift' in args
simd = '--simd' in args
rng = None
if '--range' in args:
    i = args.index('--range'); rng = (int(args[i + 1], 16), int(args[i + 2], 16)); del args[i:i + 3]
args = [a for a in args if not a.startswith('--')]
offs = [int(x, 16) for x in args[0].split(',')]
need = int(args[1]) if len(args) > 1 else len(offs)

s, e = rng if rng else (0x7100000000, 0x7103e9e000)
w = np.frombuffer(open(IMG, 'rb').read()[s - BASE:e - BASE], dtype='<u4')
addr = s + 4 * np.arange(len(w), dtype=np.int64)
L = 1 if load else 0
rn = ((w >> 5) & 31).astype(np.int64)
recs = []  # (addr, rn, disp, size)
# 단일 레지스터, unsigned offset: size(2) 111 V 01 opc(2) imm12
for size_bits in range(4):
    for V in (0, 1):
        for opc in ((1 if load else 0), (3 if load else 2)) if V else ((1 if load else 0),):
            if V == 0 and opc != (1 if load else 0):
                continue
            pat = (size_bits << 30) | (0b111 << 27) | (V << 26) | (0b01 << 24) | (opc << 22)
            m = (w & 0xffc00000) == pat
            if not m.any():
                continue
            if V == 1 and opc in (2, 3):
                if size_bits != 0:
                    continue
                sc = 16
            else:
                sc = 1 << size_bits
            imm = ((w[m] >> 10) & 0xfff).astype(np.int64) * sc
            if V or not simd:
                recs.append((addr[m], rn[m], imm, np.full(m.sum(), sc)))
# 단일 레지스터, unscaled (STUR/LDUR): size 111 V 00 opc 0 imm9 00
for size_bits in range(4):
    for V in (0, 1):
        opcs = [(1 if load else 0)] + ([(3 if load else 2)] if V and size_bits == 0 else [])
        for opc in opcs:
            pat = (size_bits << 30) | (0b111 << 27) | (V << 26) | (opc << 22)
            m = ((w & 0xffe00c00) == pat)
            if not m.any():
                continue
            sc = 16 if (V and opc >= 2) else (1 << size_bits)
            imm = ((w[m] >> 12) & 0x1ff).astype(np.int64)
            imm = np.where(imm >= 256, imm - 512, imm)
            if simd and not V:
                continue
            recs.append((addr[m], rn[m], imm, np.full(m.sum(), sc)))
# 쌍 (STP/LDP signed offset): opc 101 V 010 L imm7
for opc in (0, 1, 2):
    for V in (0, 1):
        if V == 0 and opc == 1:
            continue
        pat = (opc << 30) | (0b101 << 27) | (V << 26) | (0b010 << 23) | (L << 22)
        m = (w & 0xffc00000) == pat
        if not m.any():
            continue
        sc = (4 << opc) if V else (4 if opc == 0 else 8)
        imm = ((w[m] >> 15) & 0x7f).astype(np.int64)
        imm = np.where(imm >= 64, imm - 128, imm) * sc
        if simd and not V:
            continue
        recs.append((addr[m], rn[m], imm, np.full(m.sum(), 2 * sc)))
A = np.concatenate([r[0] for r in recs]); R = np.concatenate([r[1] for r in recs])
D = np.concatenate([r[2] for r in recs]); S = np.concatenate([r[3] for r in recs])

fs = []
for line in open(TSV, encoding='utf-8', errors='replace').read().splitlines()[1:]:
    p = line.split('\t')
    fs.append(int(p[0], 16))
fs = np.array(sorted(set(fs)), dtype=np.int64)
F = fs[np.searchsorted(fs, A, side='right') - 1]

groups = collections.defaultdict(list)
for f, r, d, sz in zip(F.tolist(), R.tolist(), D.tolist(), S.tolist()):
    if r == 31:
        continue
    groups[(f, r)].append((d, sz))
out = []
for (f, r), lst in groups.items():
    xs = {0}
    if shift:
        xs = {d + k - offs[0] for d, sz in lst for k in range(0, sz, 4)}
    for x in xs:
        hit = [o for o in offs if any(d <= x + o < d + sz for d, sz in lst)]
        if len(hit) >= need:
            out.append((f, r, x, hit))
seen = set()
for f, r, x, hit in sorted(out, key=lambda t: (-len(t[3]), t[0])):
    print(hex(f), 'x%d' % r, hex(x), [hex(h) for h in hit])
