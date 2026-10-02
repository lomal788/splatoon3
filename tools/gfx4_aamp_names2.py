"""gfx4_aamp_names.py 보강: printf 형식(%d, %s) 치환 + snake_case 단어 2~3개 조합으로 남은 AAMP 해시를 찾는다.
사용: PY web/tools/gfx4_aamp_names2.py <AAMP 파일·폴더...>   (결과는 analysis/gfx4/aamp_names.txt 에 추가)
"""
import binascii, itertools, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx4_aamp_names as g

def crc(s):
    return binascii.crc32(s.encode()) & 0xFFFFFFFF

def main():
    hs = set()
    for f in g.files(sys.argv[1:]):
        try:
            hs |= g.aamp_hashes(f)
        except Exception:
            pass
    nf = os.path.join(g.ROOT, 'analysis/gfx4/aamp_names.txt')
    known = set(open(nf, encoding='utf8').read().split()) if os.path.exists(nf) else set()
    left = hs - {crc(n) for n in known}
    lines = open(os.path.join(g.ROOT, 'extracted/main_strings.txt'), encoding='utf8', errors='replace').read().splitlines()
    found = {}
    def test(n):
        c = crc(n)
        if c in left and c not in found:
            found[c] = n
    fmt = [l for l in lines if '%' in l and len(l) < 80]
    for l in fmt:
        for a in range(0, 33):
            s1 = l.replace('%d', str(a), 1).replace('%u', str(a), 1)
            test(s1)
            if '%d' in s1 or '%u' in s1:
                for b in range(0, 33):
                    test(s1.replace('%d', str(b), 1).replace('%u', str(b), 1))
    vocab = set()
    for l in lines:
        for tok in re.findall(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*', l):
            for w in tok.split('_'):
                if 1 < len(w) < 16:
                    vocab.add(w)
    vocab = sorted(vocab)
    print('vocab', len(vocab), 'left', len(left))
    for a in vocab:
        for b in vocab:
            n = a + '_' + b
            test(n)
            test(n + '_0')
    # 3단어: 이미 찾은 이름에서 나온 단어 + 그래픽 단어로 제한
    gv = set()
    for n in list(known) + list(found.values()):
        gv |= set(n.lower().split('_'))
    gv |= {w for w in vocab if any(k in w for k in ('shadow','depth','bloom','light','fog','exposure','tone','cascade','ssao','buffer','pass','enable','size','num','width','height','format','near','far','offset','scale','bias','blur','filter','reduce','resolution','quality','map','cube','env','hdr','lens','flare','glare','sh','probe','volume','mask','lut','color','intensity','gamma','aa','fxaa','smaa','taa','motion','dof','ao'))}
    gv = sorted(w for w in gv if w and len(w) < 16)
    print('3-word vocab', len(gv))
    for a, b, c in itertools.product(gv, repeat=3):
        test(a + '_' + b + '_' + c)
    open(nf, 'a', encoding='utf8').write('\n'.join(found.values()) + '\n')
    print('found', len(found))
    for c, n in sorted(found.items(), key=lambda x: x[1]):
        print('  %08x %s' % (c, n))

main()
