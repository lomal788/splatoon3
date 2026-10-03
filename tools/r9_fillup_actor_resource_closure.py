"""Data audit of original solo-range physics resource references, including Bootup parents.
Only Actor inheritance and physics/BulletBody/reservation references are followed.
Unused Chariot/Coop shapes present in SplPlayer are included as data, not gameplay.
This bounded resource closure does not prove arbitrary runtime mask writers absent.
"""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'web/tools')
from spl_data import sarc,unzs,byml
from gimmick_phive import parse
R=Path('C:/dev/splatoon3');P=R/'extracted/romfs/Pack'
boot=sarc(unzs((P/'Bootup.Nin_NX_NVN.pack.zs').read_bytes()))
stage=json.loads((R/'analysis/range/pack_LobbyVersus/Banc/Lby_Lobby00.bcett.byml.json').read_text(encoding='utf-8-sig'))
static=sorted({a['Gyaml'].rsplit('/',1)[-1].split('.engine__actor__ActorParam.gyml')[0] for a in stage['Actors']})
dynamic=['SplPlayer','WeaponShooterNormal','BulletShooterBase','BulletSplashShooter','BulletWallDrop']
out={'scope':__doc__,'roots':[],'errors':[]}
def walk(o,p=''):
 if isinstance(o,dict):
  for k,v in o.items():yield from walk(v,p+'/'+str(k))
 elif isinstance(o,list):
  for i,v in enumerate(o):yield from walk(v,p+'/'+str(i))
 else:yield p,o
def refpath(v):
 if not isinstance(v,str) or not v.startswith('Work/'):return None
 n=v[5:]
 if n.endswith('.gyml'):return n[:-5]+'.bgyml'
 if n.endswith('.phsh'):return n[:-5]+'.Nin_NX_NVN.bphsh'
 return None
def follow(path,k):
 if path.startswith('Phive/'):return True
 if path.startswith(('Component/Physics/','Component/BulletBodyComponentParam/','Component/ActorReservation/')):return True
 if path.startswith('Gyml/') and ('BulletBodyControllerEntityParam' in path or 'BulletBodyEntityParam' in path):return True
 if path.startswith('Actor/') and k=='/$parent':return True
 return False
for actor in static+dynamic:
 pack=P/'Actor'/(actor+'.pack.zs')
 local=sarc(unzs(pack.read_bytes()));queue=[('Actor/'+actor+'.engine__actor__ActorParam.bgyml','root')];seen=set()
 row={'actor':actor,'origin':'static_banc' if actor in static else 'dynamic_solo_root','resources':[],'edges':[],'missing':[],'preset_refs':[],'fillup_refs':[],'mesh_fillup_rows':[]}
 while queue:
  n,from_n=queue.pop(0)
  if n in seen:continue
  seen.add(n)
  if n in local:raw=local[n];source=str(pack.relative_to(R))
  elif n in boot:raw=boot[n];source='extracted/romfs/Pack/Bootup.Nin_NX_NVN.pack.zs'
  else:row['missing'].append({'file':n,'from':from_n});continue
  if n.endswith('.bphsh'):
   m=parse(raw);res={'file':n,'pack':source,'sha256':hashlib.sha256(raw).hexdigest(),'material_rows':m['materials'],'filters':m['filters']}
   for i,(mi,z,mask) in enumerate(m['materials']):
    if mask&0x10000000:row['mesh_fillup_rows'].append({'file':n,'row':i,'mask':hex(mask)})
   row['resources'].append(res);continue
  d=byml(raw);row['resources'].append({'file':n,'pack':source,'sha256':hashlib.sha256(raw).hexdigest(),'data':d})
  for k,v in walk(d):
   if isinstance(v,str) and 'FillUp' in v:row['fillup_refs'].append({'file':n,'path':k,'value':v})
   if isinstance(v,str) and 'MaterialPresets' in k:row['preset_refs'].append({'file':n,'path':k,'name':v})
   q=refpath(v)
   if q and follow(q,k):row['edges'].append({'from':n,'path':k,'to':q});queue.append((q,n))
 out['roots'].append(row)
out['summary']={'static_roots':len(static),'dynamic_roots':len(dynamic),'total_roots':len(out['roots']),'resources_with_repeats':sum(len(r['resources']) for r in out['roots']),'unique_resources':len({(r['pack'],r['file']) for a in out['roots'] for r in a['resources']}),'missing':sum(len(r['missing']) for r in out['roots']),'fillup_refs':sum(len(r['fillup_refs']) for r in out['roots']),'mesh_fillup_rows':sum(len(r['mesh_fillup_rows']) for r in out['roots']),'preset_names':sorted({r['name'] for a in out['roots'] for r in a['preset_refs']}),'dynamic_resources':sum(len(r['resources']) for r in out['roots'] if r['origin']=='dynamic_solo_root')}
config_path=R/'extracted/romfs/Phive/Config/PhiveConfig.byml.zs'
config=byml(unzs(config_path.read_bytes()))
tagdefs={r['ComponentName']:r['MaskValue'] for r in config['UserShapeTagMaskCollection']}
presets={r['ComponentName']:r for r in config['MaterialPresetCollection']}
out['original_config']={'file':str(config_path.relative_to(R)),'sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),'fillup_mask':tagdefs['FillUp'],'fillup_preset':presets['FillUpPlayer']}
out['preset_inputs']=[]
for name in out['summary']['preset_names']:
 rec=presets.get(name)
 if rec is None:out['errors'].append({'preset':name,'error':'Config preset missing'});continue
 mask=0
 for t in rec.get('UserShapeTagMask',[]):mask |= tagdefs[t]
 out['preset_inputs'].append({'name':name,'original_row':rec,'tag_mask_data_OR':hex(mask),'fillup':bool(mask&0x10000000)})
out['summary']['missing_config_presets']=len(out['errors'])
out['summary']['preset_fillup_inputs']=sum(r['fillup'] for r in out['preset_inputs'])
(R/'analysis/completion/r9/fillup_actor_resource_closure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out['summary'],ensure_ascii=False))
for row in out['roots']:
 if row['missing']:print(row['actor'],'MISSING',json.dumps(row['missing'],ensure_ascii=False))
