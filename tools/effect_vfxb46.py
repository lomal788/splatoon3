"""VFXB 버전 46 (Splatoon 3 Effect/*.esetb.byml 내장 PTCL) 보조 판독.

effect_vfxb.py(mpj 에서 복사, 버전 53 필드표)의 섹션 순회(Vfxb 클래스)만 쓰고, 버전 46 EmitterData(0xEF0 B)는
필드표가 맞지 않으므로 해석하지 않는다. 대신
  - 이미터셋 → 이미터 트리, 이미터 바이너리 위치·크기
  - 이미터 바이너리 안에서 GTNT 텍스처 ID(u64)와 일치하는 값의 위치(=샘플러 참조 후보)
  - 같은 방식으로 G3NT 프리미티브 ID 참조
를 뽑는다. 텍스처 ID 일치는 8바이트 해시 일치라 우연 일치 가능성이 매우 낮다.

사용:
  PY web/tools/effect_vfxb46.py eset <x.vfxb> <이미터셋 이름...> [--json out.json]
  PY web/tools/effect_vfxb46.py bntx <x.vfxb> <out.bntx>       # GRTF 안 BNTX 통째 추출
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import effect_vfxb as V  # noqa: E402


def emitter_info(v, em, texmap, primmap):
    d = v.d
    name_data = v.emitter(em)
    o = em.data_off() if hasattr(em, 'data_off') else None
    size = name_data['_binarySize']
    start = em.pos + em.bin_off if hasattr(em, 'bin_off') else None
    return name_data, start, size


def scan_ids(buf, idmap):
    hits = []
    for i in range(0, len(buf) - 7, 4):
        q, = struct.unpack_from('<Q', buf, i)
        if q in idmap:
            hits.append([hex(i), idmap[q]])
    return hits


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    v = V.Vfxb(path)
    if cmd == 'bntx':
        grtf = [s for s in v.top if s.magic == 'GRTF'][0]
        o = grtf.data_off()
        data = v.d[o:grtf.pos + grtf.size]
        i = data.find(b'BNTX')
        sz, = struct.unpack_from('<I', data, i + 0x1c)
        open(sys.argv[3], 'wb').write(data[i:i + sz])
        print('BNTX', hex(o + i), sz)
        return
    texmap = {t['id']: t['name'] for t in v.tex_desc}
    primmap = {t['id']: t['name'] for t in v.prim_desc}
    want = [a for a in sys.argv[3:] if not a.startswith('--') and not a.endswith('.json')]
    out = {}
    for e in v.esets:
        nm = v.eset_name(e)
        if nm not in want:
            continue
        ems = []

        def walk(em, depth):
            data = v.emitter(em)
            bo = em.data_off()
            buf = v.d[bo:bo + data['_binarySize']]
            ems.append({'name': data['name'], 'depth': depth, 'binOff': hex(bo), 'binSize': hex(data['_binarySize']),
                        'attrs': [a.magic for a in em.attrs],
                        'textures': scan_ids(buf, texmap), 'primitives': scan_ids(buf, primmap)})
            for c in em.children:
                walk(c, depth + 1)
        for em in e.children:
            walk(em, 0)
        out[nm] = ems
        print('ESET', nm, 'emitters', len(ems))
        for x in ems:
            print('  ' * (x['depth'] + 1), x['name'], x['attrs'], 'tex', [t[1] for t in x['textures']],
                  'prim', [p[1] for p in x['primitives']])
    if '--json' in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False,
                  indent=1)


if __name__ == '__main__':
    main()
