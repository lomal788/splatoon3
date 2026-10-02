"""전 액터 팩에서 ELinkParam/SLinkParam UserName 수집 -> analysis/effect_sound/xlink_usernames.json
사용: PY web/tools/effect_usernames.py
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import spl_data as S

out = {'ELink': {}, 'SLink': {}}
root = 'C:/dev/splatoon3/extracted/romfs/Pack/Actor'
for p in sorted(glob.glob(root + '/*.pack.zs')):
    actor = os.path.basename(p)[:-8]
    try:
        files = S.sarc(S.unzs(open(p, 'rb').read()))
    except Exception as e:
        print('ERR', actor, e); continue
    for name, data in files.items():
        for kind in ('ELink', 'SLink'):
            if name.startswith('Component/%s/' % kind) and name.endswith('.bgyml'):
                try:
                    j = S.byml(data)
                except Exception:
                    continue
                un = j.get('UserName') if isinstance(j, dict) else None
                if un:
                    out[kind].setdefault(un, []).append(actor)
json.dump(out, open('C:/dev/splatoon3/analysis/effect_sound/xlink_usernames.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
print({k: len(v) for k, v in out.items()})
