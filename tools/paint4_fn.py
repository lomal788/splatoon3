import re, sys, glob
"""paint4_fn.py <주소...> : analysis/decomp 의 .c 에서 함수 본문 출력 (INDEX.tsv 로 파일 찾음)"""
idx = {}
for l in open('C:/dev/splatoon3/analysis/decomp/INDEX.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 3:
        idx[p[0].lower()] = p[2]
for a in sys.argv[1:]:
    a = a.lower().replace('0x', '')
    f = idx.get(a)
    if not f:
        print('// 없음', a); continue
    s = open('C:/dev/splatoon3/' + f if not f.startswith('C:') else f, encoding='utf-8', errors='replace').read()
    m = re.search(r'\n[^\n]*FUN_%s\([^;{]*?\)\s*\n\{' % a, s)
    if not m:
        print('// 정의 못 찾음', a, f); continue
    j = m.start(); k = s.find('\n}\n', j)
    print('// ' + f); print(s[j:k + 3])
