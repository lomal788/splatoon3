"""r9 read-only actor pack source audit for FillUp dynamic shape references.
All Actor packs are searched only as resource metadata, without interpreting
out-of-scope actor behavior. Explicit solo shooter runtime roots are separately
fully inventoried. This does not prove absence of every runtime tag writer.
"""
import json,sys,time
from pathlib import Path
sys.path.insert(0,'web/tools')
from spl_data import sarc,unzs,byml
from gimmick_phive import parse
ROOT=Path('C:/dev/splatoon3')
PACKS=ROOT/'extracted/romfs/Pack/Actor'
roots=['SplPlayer','WeaponShooterNormal','BulletShooterBase','BulletSplashShooter','BulletWallDrop']
out={'scope':__doc__,'actor_pack_count':0,'byml_count':0,'fillup_ref_files':[],'errors':[],'solo_roots':[],'missing_roots':[]}
def walk(o,path=''):
 if isinstance(o,dict):
  for k,v in o.items():yield from walk(v,path+'/'+str(k))
 elif isinstance(o,list):
  for i,v in enumerate(o):yield from walk(v,path+'/'+str(i))
 else:yield path,o
start=time.monotonic()
for pack in sorted(PACKS.glob('*.pack.zs')):
 out['actor_pack_count']+=1
 try:entries=sarc(unzs(pack.read_bytes()))
 except Exception as e:out['errors'].append({'pack':pack.name,'error':str(e)});continue
 actor=pack.name[:-8]
 for name,b in entries.items():
  if not name.endswith(('.bgyml','.byml')):continue
  out['byml_count']+=1
  if b'FillUp' not in b:continue
  try:
   d=byml(b);refs=[{'path':p,'value':v} for p,v in walk(d) if isinstance(v,str) and 'FillUp' in v]
   if refs:out['fillup_ref_files'].append({'actor':actor,'file':name,'refs':refs,'data':d})
  except Exception as e:out['errors'].append({'pack':pack.name,'file':name,'error':str(e)})
 if actor in roots:
  row={'actor':actor,'byml_files':[],'preset_refs':[],'actor_refs':[],'fillup_refs':[],'bphsh':[]}
  for name,b in entries.items():
   if name.endswith(('.bgyml','.byml')):
    d=byml(b);row['byml_files'].append({'file':name,'data':d})
    for p,v in walk(d):
     if isinstance(v,str) and 'FillUp' in v:row['fillup_refs'].append({'file':name,'path':p,'value':v})
     if isinstance(v,str) and 'MaterialPresets' in p:row['preset_refs'].append({'file':name,'path':p,'value':v})
     if isinstance(v,str) and v.startswith('Work/Actor/') and v.endswith('ActorParam.gyml'):row['actor_refs'].append({'file':name,'path':p,'value':v})
   elif name.endswith('.bphsh'):
    d=parse(b);row['bphsh'].append({'file':name,'materials':d['materials'],'fillup_rows':[i for i,r in enumerate(d['materials']) if r[2]&0x10000000]})
  out['solo_roots'].append(row)
out['missing_roots']=sorted(set(roots)-{r['actor'] for r in out['solo_roots']})
out['elapsed_s']=round(time.monotonic()-start,3)
out['summary']={'actor_pack_count':out['actor_pack_count'],'byml_count':out['byml_count'],'ref_files':len(out['fillup_ref_files']),'ref_actors':sorted({r['actor'] for r in out['fillup_ref_files']}),'errors':len(out['errors']),'solo_roots':len(out['solo_roots']),'solo_fillup_refs':sum(len(r['fillup_refs']) for r in out['solo_roots']),'solo_material_preset_refs':sum(len(r['preset_refs']) for r in out['solo_roots']),'solo_byml_files':sum(len(r['byml_files']) for r in out['solo_roots']),'solo_bphsh':sum(len(r['bphsh']) for r in out['solo_roots']),'elapsed_s':out['elapsed_s']}
(ROOT/'analysis/completion/r9/fillup_actor_source_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out['summary'],ensure_ascii=False))
