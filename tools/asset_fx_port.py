"""Repair only shooter emitter metadata from original v46 data.

No GLB rebuild: native 082c0a0 packs _u0.xy + _u1.xy; shipped GLB uv1.x
already preserves VAT row. Existing VAT half bins are verified, never rewritten.
The script updates emitters.json and only the effect/shooter catalog byte count.
"""
import argparse
import json
import struct
from pathlib import Path

import asset_common as A
import asset_fx
import effect_bntx_float as F
import effect_vfxb as V
import graphics_bntx as G
import vfx_emitter46 as E

WORK = A.ROOT / 'analysis/port_priority_r4/fx_data'
OUT = A.ASSETS / 'effects/shooter'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf8')


def repair(doc, v):
    native = {es + '/' + name: (bo, {field: E.read_field(v.d, bo, off, typ) for off, typ, field, _ in E.FIELDS})
              for es, name, depth, parent, bo, em in E.emitters(v, set(doc['emitterSets']))}
    count = 0
    for es, rows in doc['emitterSets'].items():
        for em in rows:
            bo, rec = native[es + '/' + em['name']]
            pcolor = list(struct.unpack_from('<8f', v.d, bo + 0xd40))
            em['fields'] = {name: value for name, value in rec.items() if not name.endswith('Keys')}
            em['scale']['keys'] = [key[:] for key in rec['scaleKeys'][:max(1, rec['numScaleKeys'])]]
            em['scale']['numKeys'] = rec['numScaleKeys']
            for channel, values in [('color0', pcolor[:3]), ('alpha0', pcolor[3:4]), ('color1', pcolor[4:7]), ('alpha1', pcolor[7:])]:
                n = rec['num' + channel.capitalize() + 'Keys']
                original = [key[:] for key in rec[channel + 'Keys'][:max(1, n)]]
                patched = [key[:] for key in original]
                if rec[channel + 'Type'] == 0:
                    patched[0][:len(values)] = values
                em['color'][channel] = dict(type=asset_fx.TYPE3[rec[channel + 'Type']], numKeys=n,
                                            keys=patched, serializedKeys=original)
            raw = list(v.d[bo + 0xbd8:bo + 0xbe8])
            data = dict(nativeRender=dict(blendEnable=raw[0] != 0, depthTest=raw[1] != 0,
                        depthCompare=raw[2], depthWrite=raw[3] != 0, blendMode=raw[6], cullMode=raw[7], rawBytes=raw),
                        nearFade=list(struct.unpack_from('<2f', v.d, bo + 0x890)),
                        alphaThreshold=struct.unpack_from('<f', v.d, bo + 0x8a8)[0],
                        softDistance=struct.unpack_from('<f', v.d, bo + 0x8b4)[0],
                        vatNormalOffset=rec['unknownE4'], keyInterpolation=list(v.d[bo + 0xc38:bo + 0xc3d]))
            em.update(data)
            em['fields'].update(data)
            em['pColor'] = pcolor
            em['fixedKeyPatch'] = '08190fc: PColor -> key0 for FIXED only'
            count += 1
    assert count == 39, count
    native_tex = {tex.name: tex for tex in G.parse(v.bntx)}
    vat = []
    for name, info in doc['textures'].items():
        tex = native_tex[name]
        info.update(componentSelectors=tex.comp, componentSelectorsApplied=info["kind"] != "vat",
                    nativeFormat=hex(tex.format), nativeMips=tex.mips)
        if info['kind'] == 'vat':
            assert tex.comp == [2, 3, 4, 5], name
            info['componentSelectorsIdentity'] = True
            expected = F.decode_float(tex).astype('<f2').tobytes()
            actual = (OUT / info['file']).read_bytes()
            assert actual == expected, name
            vat.append(dict(name=name, bytes=len(actual), bitExact=True))
    doc['version'] = max(2, doc.get('version', 1))
    note = '2026-10-03 FX port: exact f32 keys, confirmed FIXED PColor patch and native render fields; custom uniform producers remain unconfirmed.'
    if note not in doc['notes']:
        doc['notes'].append(note)
    return dict(emitters=count, vat=vat, glbRebuilds=0)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, help='Generate emitters.json/catalog.json in an analysis directory; leave shipped assets untouched.')
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    path = OUT / 'emitters.json'
    doc = json.loads(path.read_text(encoding='utf8'))
    before = path.read_bytes()
    v = V.Vfxb(str(A.ROOT / 'analysis/assets_work/r6/static.vfxb'))
    result = repair(doc, v)
    if args.output:
        output = args.output.resolve()
        analysis_root = (A.ROOT / 'analysis').resolve()
        if output != analysis_root and analysis_root not in output.parents:
            parser.error('--output must stay inside the project analysis directory')
        write(output / 'emitters.json', doc)
    else:
        backup = WORK / 'backup/emitters.json'
        backup.parent.mkdir(exist_ok=True)
        if not backup.exists():
            backup.write_bytes(before)
        write(path, doc)
    cat_path = A.ASSETS / 'catalog.json'
    cat = json.loads(cat_path.read_text(encoding='utf8'))
    entry = cat['bundles']['effect/shooter']
    result['catalogBefore'] = entry['bytes']
    generated_bytes = (output / 'emitters.json').stat().st_size if args.output else (OUT / 'emitters.json').stat().st_size
    entry['bytes'] = sum((OUT / name).stat().st_size if name != 'emitters.json' else generated_bytes for name in entry['files'])
    result['catalogAfter'] = entry['bytes']
    if args.output:
        write(output / 'catalog.json', cat)
        write(output / 'asset_repair.json', result)
    else:
        backup = WORK / 'backup/catalog.json'
        if not backup.exists():
            backup.write_bytes(cat_path.read_bytes())
        write(cat_path, cat)
        write(WORK / 'asset_repair.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
