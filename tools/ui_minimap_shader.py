"""[camrest] 미니맵 템플릿 모델(Model/MiniMapTemplate.bfres) 재질 5개의 Hoian_UBER 프로그램을 찾아 GLSL로 역번역한다.

shader_material_programs.py 의 선택 규칙(재질 옵션 + renderInfo → 키 표 최다 일치)을 그대로 쓰고,
입력만 analysis/camrest/MiniMapTemplate.dump.json(graphics_bfres2gltf dump)으로 바꾼다.
출력: analysis/camrest/minimap_shader/<모델>__<재질>.{opts.json,options.txt,vert,frag}, index.tsv

사용: ui_minimap_shader.py
덤프 재생성(필요 시): romfs/Model/MiniMapTemplate.bfres.zs 를 zstd 해제해 analysis/camrest/MiniMapTemplate.bfres 로 둔 뒤
  analysis/graphics/build/bin/Release/net7.0/graphics_bfres2gltf.exe dump analysis/camrest/MiniMapTemplate.dump.json analysis/camrest/MiniMapTemplate.bfres
  (해제한 .bfres 는 원본 사본이라 끝나면 지움)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import shader_material_programs as S  # noqa: E402

ROOT = S.ROOT
DUMP = ROOT + '/analysis/camrest/MiniMapTemplate.dump.json'
OUT = ROOT + '/analysis/camrest/minimap_shader'


def main():
    head, krows = S.load_keys()
    info = json.load(open(ROOT + '/analysis/shader/Hoian_UBER.Product.info.json', encoding='utf-8'))
    static = {o['name']: o for o in info['models'][0]['staticOptions']}
    dyn = {o['name']: o for o in info['models'][0]['dynamicOptions']}
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(DUMP, encoding='utf-8'))
    rows = []
    for m in d[0]['models']:
        for mt in m['materials']:
            opts = S.material_options(mt, static)
            for k in [k for k in opts if k not in static and k not in dyn]:
                opts.pop(k)
            for k, o in static.items():
                opts.setdefault(k, o['default'])
            op = f"{OUT}/{m['name']}__{mt['name']}.opts.json"
            json.dump(opts, open(op, 'w'))
            cands, diffs = S.select(opts, head, krows)
            diff = diffs[0][1]
            r = subprocess.run(['dotnet', S.DLL, 'prog-bfsha', S.BFSHA, 'hoian_uber', op, f"{OUT}/{m['name']}__{mt['name']}",
                                '--index', str(cands[0])], capture_output=True, text=True)
            line = f'{m["name"]}__{mt["name"]}\t{cands[0]}\tn={len(cands)}\tmismatch={len(diff)}\t' + \
                   ';'.join(f'{h}:want={opts[h]},prog={v}' for h, v in diff) + '\t' + r.stderr.strip()[:200]
            rows.append(line)
            print(line)
    open(f'{OUT}/index.tsv', 'w', encoding='utf-8').write('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
