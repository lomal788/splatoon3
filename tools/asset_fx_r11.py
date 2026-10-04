"""r11 gfx-diff 이펙트: effects/shooter 번들에 조준 표시 이미터셋을 추가(기존 행·파일은 건드리지 않음).

추가 이미터셋: WpShtrSite, WpShtrSiteHit, WpShtrFieldHitMarker, WpShtrSiteSide, WpShtrHitMarkerSide
(ELink 사용자 PlayerShotGuide 의 RuntimeAssetName, combat/damage_hit.md §6.7).
행 구성은 asset_fx.py 와 같은 식(web_row + fields + textures/primitive). 없는 텍스처만 asset_fx 와 같은 변환으로 만든다.
그 뒤 asset_fx_port.py 를 다시 돌려 키/렌더/r11 필드를 모든 행에 채운다.
사용: PY web/tools/asset_fx_r11.py && PY web/tools/asset_fx_port.py
"""
import json

import asset_common as A
import asset_fx
import asset_ktx2 as K
import effect_vfxb46
import graphics_bntx
import vfx_emitter46 as E

SITE = ["WpShtrSite", "WpShtrSiteHit", "WpShtrFieldHitMarker", "WpShtrSiteSide", "WpShtrHitMarkerSide"]
OUT = A.ASSETS / 'effects/shooter'


def main():
    path = OUT / 'emitters.json'
    doc = json.loads(path.read_text(encoding='utf8'))
    v = asset_fx.vfxb()
    texmap = {t["id"]: t["name"] for t in v.tex_desc}
    primidx = {t["id"]: i for i, t in enumerate(v.prim_desc)}
    added, need_tex = [], set()
    for es, name, depth, parent, bo, em in E.emitters(v, set(SITE)):
        if any(r['name'] == name for r in doc['emitterSets'].get(es, [])):
            continue
        rec = {"eset": es, "depth": depth, "parent": parent}
        for off, t, fname, _why in E.FIELDS:
            rec[fname] = E.read_field(v.d, bo, off, t)
        buf = v.d[bo:bo + E.SIZE]
        texs = []
        for off, tname in effect_vfxb46.scan_ids(buf, texmap):
            o = int(off, 16)
            slot = (o - 0xD90) // 0x20 if 0xD90 <= o < 0xE50 and (o - 0xD90) % 0x20 == 0 else None
            texs.append({"slot": slot, "offset": off, "name": tname})
            need_tex.add(tname)
        prims = list(effect_vfxb46.scan_ids(buf, {k: "" for k in primidx}))
        assert not prims, (es, name, 'primitive export not handled by this narrow tool')
        row = {"name": name, "depth": depth, "parent": parent, "attrs": [a.magic for a in em.attrs],
               **asset_fx.web_row(rec), "textures": texs, "primitive": None,
               "fields": {k: x for k, x in rec.items() if not k.endswith("Keys")}}
        doc['emitterSets'].setdefault(es, []).append(row)
        added.append(f'{es}/{name}')
    new_tex = []
    tmp = A.WORK / "fx_tex"; tmp.mkdir(parents=True, exist_ok=True)
    for t in graphics_bntx.parse(v.bntx):
        if t.name not in need_tex or t.name in doc['textures']:
            continue
        m = graphics_bntx.to_png(t, str(tmp))
        png = tmp / m["files"][0]
        normal = t.name.endswith("_nrm")
        K.encode(png, OUT / f"tex/{t.name}.ktx2", linear=True, uastc=normal)
        doc['textures'][t.name] = {"file": f"tex/{t.name}.ktx2", "kind": "normal" if normal else "mask",
                                   "width": t.width, "height": t.height, "srcFormat": f"{t.format:#06x}",
                                   "colorSpace": "linear", "channelsNote": "BC4→R, BC5→RG (PNG 경유, 나머지 채널 0/255)"}
        new_tex.append(t.name)
    doc['missingEmitterSets'] = [s for s in doc.get('missingEmitterSets', []) if s not in doc['emitterSets']]
    note = '2026-10-04 r11 gfx-diff 이펙트: 조준 표시 이미터셋(PlayerShotGuide RuntimeAssetName) 추가 — asset_fx_r11.py'
    if note not in doc['notes']:
        doc['notes'].append(note)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    cat_path = A.ASSETS / 'catalog.json'
    cat = json.loads(cat_path.read_text(encoding='utf8'))
    entry = cat['bundles']['effect/shooter']
    for name in new_tex:
        f = f'tex/{name}.ktx2'
        if f not in entry['files']:
            entry['files'].append(f)
    entry['bytes'] = sum((OUT / f).stat().st_size for f in entry['files'])
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    print(json.dumps({'added': added, 'textures': new_tex, 'bundleBytes': entry['bytes']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
