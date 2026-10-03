"""r9 original Lby_Lobby00 actor-pack material/parameter FillUp inventory.
Data only: reads all referenced actor pack bphsh rows and Phive BYML params.
No authoring purpose or native cast/solver behavior is inferred from names.
"""
import json,sys
from pathlib import Path
from collision_mesh import load_blobs
from gimmick_phive import parse
from spl_data import sarc,unzs,byml
stage=Path('analysis/range/pack_LobbyVersus/Banc/Lby_Lobby00.bcett.byml.json')
d=json.loads(stage.read_text(encoding='utf-8-sig'));names=sorted(set(a['Gyaml'] for a in d['Actors']));out={'stage':str(stage),'actors':len(d['Actors']),'gyaml_count':len(names),'packs':[],'missing':[],'errors':[],'fillup_rows':[],'fillup_parameters':[]}
for gyaml in names:
 actor=gyaml.rsplit('/',1)[-1].split('.engine__actor__ActorParam.gyml')[0]
 p=Path('extracted/romfs/Pack/Actor')/(actor+'.pack.zs')
 if not p.exists():out['missing'].append({'gyaml':gyaml,'actor':actor});continue
 entries=sarc(unzs(p.read_bytes()));pack={'gyaml':gyaml,'actor':actor,'bphsh':[],'phive_param_count':0}
 for n,b in entries.items():
  if n.endswith('.bphsh'):
   ph=parse(b);maskrows=[]
   for i,(mi,z,mask) in enumerate(ph['materials']):
    if mask&0x10000000:maskrows.append(i);out['fillup_rows'].append({'actor':actor,'file':n,'row':i,'material':mi,'mask':hex(mask),'filter':hex(ph['filters'][i])})
   pack['bphsh'].append({'file':n,'material_rows':len(ph['materials']),'fillup_rows':maskrows})
  elif n.startswith('Phive/') and (n.endswith('.bgyml') or n.endswith('.byml')):
   pack['phive_param_count']+=1
   try:
    bd=byml(b)
    if 'FillUp' in json.dumps(bd):out['fillup_parameters'].append({'actor':actor,'file':n,'data':bd})
   except Exception as e:out['errors'].append({'actor':actor,'file':n,'error':str(e)})
 out['packs'].append(pack)
out['bphsh_count']=sum(len(p['bphsh']) for p in out['packs']);out['material_rows']=sum(b['material_rows'] for p in out['packs'] for b in p['bphsh']);out['phive_param_count']=sum(p['phive_param_count'] for p in out['packs']);out['scope']=__doc__
Path('analysis/completion/r9/physics_fillup_range_data.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:out[k] for k in ('actors','gyaml_count','bphsh_count','material_rows','phive_param_count','missing','errors','fillup_rows','fillup_parameters')},ensure_ascii=False))
