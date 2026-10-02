"""스테이지 bfres 재질마다 Hoian_UBER.Product 프로그램을 골라 GLSL 로 역번역(shader_material_programs.py 의 절차 재사용).
사용: PY web/tools/gfx4_stage_programs.py <덤프.json(graphics_bfres2gltf dump)> <출력폴더> [재질 이름 필터...]
출력: <출력폴더>/<모델>__<재질>.{opts.json,vert,frag,options.txt} + index.tsv(재질, 프로그램, 불일치)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shader_material_programs as smp  # noqa: E402


def main():
    dump, out = sys.argv[1], sys.argv[2]
    flt = sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    head, krows = smp.load_keys()
    info = json.load(open(smp.ROOT + '/analysis/shader/Hoian_UBER.Product.info.json', encoding='utf-8'))
    static = {o['name']: o for o in info['models'][0]['staticOptions']}
    dyn = {o['name']: o for o in info['models'][0]['dynamicOptions']}
    d = json.load(open(dump, encoding='utf-8'))
    rows = []
    seen = set()
    for f in d:
        for m in f.get('models', []):
            for mt in m['materials']:
                if mt['shader'].get('archive') != 'Hoian_UBER':
                    continue
                if flt and not any(x in mt['name'] for x in flt):
                    continue
                tag = f'{m["name"]}__{mt["name"]}'
                if tag in seen:
                    continue
                seen.add(tag)
                opts = smp.material_options(mt, static)
                for k in [k for k in opts if k not in static and k not in dyn]:
                    opts.pop(k)
                for k, o in static.items():
                    opts.setdefault(k, o['default'])
                op = f'{out}/{tag}.opts.json'
                json.dump(opts, open(op, 'w'))
                cands, diffs = smp.select(opts, head, krows)
                diff = diffs[0][1]
                r = subprocess.run(['dotnet', smp.DLL, 'prog-bfsha', smp.BFSHA, 'hoian_uber', op, f'{out}/{tag}', '--index', str(cands[0])],
                                   capture_output=True, text=True)
                dtxt = ';'.join(f'{h}:want={opts[h]},prog={v}' for h, v in diff)
                rows.append((tag, str(cands[0]), str(len(cands)), str(len(diff)), dtxt, r.stderr.strip()[:200]))
                print(tag, cands[0], 'n=%d' % len(cands), 'mismatch=%d' % len(diff), dtxt, r.stderr.strip()[:120])
    with open(f'{out}/index.tsv', 'w', encoding='utf-8') as w:
        w.write('tag\tprogram\tcandidates\tmismatch\tdiff\tstderr\n')
        for r in rows:
            w.write('\t'.join(r) + '\n')


if __name__ == '__main__':
    main()
