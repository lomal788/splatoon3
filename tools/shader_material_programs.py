"""샘플 재질(analysis/graphics/dump/samples.json.gz)마다 Hoian_UBER.Product 프로그램을 찾아 GLSL로 역번역.

사용: .venv/Scripts/python web/tools/shader_material_programs.py [파일이름 필터...]
출력: analysis/shader/hoian_uber/<bfres>__<재질>.{options.txt,vert,frag} 와 index.tsv
옵션 구성: 재질 shader.options(<Default Value> 제외, True/False -> 1/0)
          + gsys_assign_type=gsys_assign_material (+ renderInfo 의 gsys_render_state_mode -> gsys_renderstate(opaque 0/mask 1/translucent 2/custom 3, ShaderLibrary TestSP3 와 같은 대응), gsys_alpha_test_enable, gsys_render_state_display_face)
          재질에 없는 정적 옵션은 bfsha 기본값으로 채움(동적 gsys_weight 는 비워 둠). 정적 옵션이 가장 많이 일치하는 프로그램(동률이면 번호가 작은 것)을 고르고 불일치 옵션을 index.tsv 에 남김.
"""
import gzip, json, os, subprocess, sys

ROOT = r'C:/dev/splatoon3'
BFSHA = ROOT + '/extracted/shader/Hoian_UBER.Product.bfsha'
DLL = ROOT + '/analysis/shader/build/bin/Release/net7.0/shader_dump.dll'
OUT = ROOT + '/analysis/shader/hoian_uber'
FACE = {'both': '0', 'front': '1', 'back': '2', 'none': '3'}
RSTATE = {'opaque': '0', 'mask': '1', 'translucent': '2', 'custom': '3'}


def material_options(mt, info_static):
    opts = {}
    for k, v in mt['shader']['options'].items():
        if v == '<Default Value>':
            continue
        v = {'True': '1', 'False': '0'}.get(v, v)
        opts[k] = v
    opts['gsys_assign_type'] = 'gsys_assign_material'
    ri = mt.get('renderInfo') or {}
    at = ri.get('gsys_alpha_test_enable')
    if at and 'gsys_alpha_test_enable' in info_static:
        opts['gsys_alpha_test_enable'] = '1' if at[0] == 'true' else '0'
    rs = ri.get('gsys_render_state_mode')
    if rs and rs[0] in RSTATE:
        opts['gsys_renderstate'] = RSTATE[rs[0]]
    face = ri.get('gsys_render_state_display_face')
    if face and 'gsys_display_face_type' in info_static and face[0] in FACE:
        opts['gsys_display_face_type'] = FACE[face[0]]
    return opts


def load_keys():
    import csv
    rows = list(csv.reader(open(ROOT + '/analysis/shader/Hoian_UBER.Product.keys.tsv', encoding='utf-8'), delimiter='	'))
    return rows[0], rows[1:]


def select(opts, head, rows):
    cols = [(i, h) for i, h in enumerate(head) if i >= 2 and not h.startswith('dyn:') and h in opts]
    cols.append((head.index('dyn:gsys_assign_type'), 'gsys_assign_type'))
    best, bestd = [], None
    for r in rows:
        diff = [(h, r[i]) for i, h in cols if r[i] != opts[h]]
        if bestd is None or len(diff) < len(bestd[0][1]):
            best, bestd = [int(r[0])], [(int(r[0]), diff)]
        elif len(diff) == len(bestd[0][1]):
            best.append(int(r[0]))
            bestd.append((int(r[0]), diff))
    return best, bestd


def main():
    flt = sys.argv[1:]
    head, krows = load_keys()
    info = json.load(open(ROOT + '/analysis/shader/Hoian_UBER.Product.info.json', encoding='utf-8'))
    static = {o['name']: o for o in info['models'][0]['staticOptions']}
    dyn = {o['name']: o for o in info['models'][0]['dynamicOptions']}
    os.makedirs(OUT, exist_ok=True)
    d = json.load(gzip.open(ROOT + '/analysis/graphics/dump/samples.json.gz'))
    rows = []
    for f in d:
        fn = os.path.basename(f['file']).replace('.bfres', '').replace('.zs', '')
        if flt and not any(x in fn for x in flt):
            continue
        for m in f.get('models', []):
            for mt in m['materials']:
                if mt['shader'].get('archive') != 'Hoian_UBER':
                    continue
                opts = material_options(mt, static)
                bad = [k for k in opts if k not in static and k not in dyn]
                for k in bad:
                    opts.pop(k)
                for k, o in static.items():
                    opts.setdefault(k, o['default'])
                tag = f'{fn}__{mt["name"]}'
                op = f'{OUT}/{tag}.opts.json'
                json.dump(opts, open(op, 'w'))
                cands, diffs = select(opts, head, krows)
                diff = diffs[0][1]
                r = subprocess.run(['dotnet', DLL, 'prog-bfsha', BFSHA, 'hoian_uber', op, f'{OUT}/{tag}', '--index', str(cands[0])],
                                   capture_output=True, text=True)
                dtxt = ';'.join(f'{h}:want={opts[h]},prog={v}' for h, v in diff)
                line = f'cands={cands[:12]} n={len(cands)} mismatch={len(diff)} {dtxt}'
                rows.append((tag, str(cands[0]), line, ','.join(bad), r.stderr.strip()[:200]))
                print(tag, line, 'unknown:', bad, r.stderr.strip()[:200])
    with open(f'{OUT}/index.tsv', 'a', encoding='utf-8') as w:
        for r in rows:
            w.write('\t'.join(r) + '\n')


if __name__ == '__main__':
    main()
