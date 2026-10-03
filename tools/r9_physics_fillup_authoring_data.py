"""r9 FillUp data evidence: original-release Actor/Scene packs and loose BYML.
All material rows with UserShapeTag bit28; geometry only when such rows exist.
Named preset/parameter occurrences and Banc placements. No author intent inferred.
Other maps are reference data for this tag only, not gameplay analysis.
"""
import json,hashlib,collections,re
from pathlib import Path
import numpy as np
from spl_data import sarc,unzs,byml
from gimmick_phive import parse,config
from collision_mesh import analyze,stats
ROOT=Path('extracted/romfs');mats,tags=config();cfg=byml((ROOT/'Phive/Config/PhiveConfig.byml.zs').read_bytes())
def matches(o,path=''):
 out=[]
 if isinstance(o,dict):
  for k,v in o.items():
   q=path+'/'+str(k)
   if 'fillup' in str(k).lower():out.append({'path':q,'key':k,'value':v})
   out.extend(matches(v,q))
 elif isinstance(o,list):
  for i,v in enumerate(o):out.extend(matches(v,path+'/'+str(i)))
 elif isinstance(o,str) and 'fillup' in o.lower():out.append({'path':path,'value':o})
 return out
out={'date':'2026-10-03','scope':__doc__,'pack_count':0,'entry_count':0,'bphsh_count':0,'material_rows':0,'byml_count':0,'byml_phive_count':0,'missing':[],'errors':[],'fillup_rows':[],'named_occurrences':[],'placements':[],'geometry_errors':[]}
cache={};scene_banc=[];pack_actor_names=set();preset_records=[]
# Full named preset records, retaining actual fields rather than label inference.
for collection,rows in cfg.items():
 if isinstance(rows,list):
  for i,row in enumerate(rows):
   if isinstance(row,dict) and 'fillup' in json.dumps(row,ensure_ascii=False).lower():preset_records.append({'collection':collection,'index':i,'row':row})
out['original_config_matches']=preset_records
packs=sorted((ROOT/'Pack/Actor').glob('*.pack.zs'))+sorted((ROOT/'Pack/Scene').glob('*.pack.zs'))
for pi,p in enumerate(packs):
 try:entries=sarc(unzs(p.read_bytes()))
 except Exception as e:out['errors'].append({'pack':str(p),'error':str(e)});continue
 out['pack_count']+=1;actor=p.name[:-8]
 for name,data in entries.items():
  out['entry_count']+=1
  if 'fillup' in name.lower():out['named_occurrences'].append({'pack':str(p),'file':name,'filename':True})
  if name.endswith('.bphsh'):
   out['bphsh_count']+=1
   try:ph=parse(data)
   except Exception as e:out['errors'].append({'pack':str(p),'file':name,'error':str(e)});continue
   out['material_rows']+=len(ph['materials']);selected=[i for i,(_,_,mask) in enumerate(ph['materials']) if mask&0x10000000]
   if selected:
    pack_actor_names.add(actor);digest=hashlib.sha256(data).hexdigest()
    if digest not in cache:
     try:
      info,m,ph2=analyze(data);g={}
      if m is not None:
       st=stats(m,ph,mats,tags,cfg);g={r['shapeTag']:r for r in st['by_shape_tag']}
       vv=m['pos'][m['tri']].astype(np.float64);nn=np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0]);ar=np.linalg.norm(nn,axis=1)*.5;ny=np.divide(nn[:,1],2*ar,out=np.zeros_like(ar),where=ar>0)
       for tag in selected:
        sel=m['tag']==tag
        if tag in g:g[tag].update({'downFacingArea(ny<-0.7)':float(ar[sel&(ny<-.7)].sum()),'verticalArea(abs(ny)<1e-6)':float(ar[sel&(np.abs(ny)<1e-6)].sum()),'nonzero_triangles':int((sel&(ar>1e-6)).sum()),'normal_y_min':float(ny[sel].min()) if sel.any() else None,'normal_y_max':float(ny[sel].max()) if sel.any() else None})
      cache[digest]={'root_type':info['root_type'],'by_tag':g}
     except Exception as e:out['geometry_errors'].append({'pack':str(p),'file':name,'error':str(e)});cache[digest]={'error':str(e)}
    for i in selected:
     mi,z,mask=ph['materials'][i];out['fillup_rows'].append({'pack':str(p),'actor':actor,'file':name,'sha256':digest,'row':i,'material':mats[mi] if mi<len(mats) else mi,'unknown_material_word':z,'mask':hex(mask),'tags':[nm for bit,nm in sorted(tags.items()) if mask&bit],'filter':hex(ph['filters'][i]) if i<len(ph['filters']) else None,'geometry':cache[digest].get('by_tag',{}).get(i),'root_type':cache[digest].get('root_type')})
  elif name.endswith(('.byml','.bgyml')):
   out['byml_count']+=1;out['byml_phive_count']+=name.startswith('Phive/')
   needsnamed=(b'FillUp' in data or b'fillup' in data)
   needsbanc=name.startswith('Banc/') and p.parent.name=='Scene'
   if needsnamed or needsbanc:
    try:d=byml(data)
    except Exception as e:out['errors'].append({'pack':str(p),'file':name,'error':str(e)});continue
    if needsnamed:out['named_occurrences'].append({'pack':str(p),'file':name,'matches':matches(d)})
    if needsbanc:scene_banc.append((str(p),name,d))
 if (pi+1)%500==0:print('progress',pi+1,'packs',out['bphsh_count'],'bphsh',len(out['fillup_rows']),'fillupRows',flush=True)
# Original scenes give placement identifiers/transforms; no synthetic map geometry.
for p,n,d in scene_banc:
 if not isinstance(d,dict):continue
 for a in d.get('Actors',[]):
  gy=a.get('Gyaml','');actor=gy.rsplit('/',1)[-1].split('.engine__actor__ActorParam.gyml')[0]
  if actor in pack_actor_names:out['placements'].append({'scene_pack':p,'banc':n,'actor':actor,'gyaml':gy,'Hash':a.get('Hash'),'Translate':a.get('Translate'),'Rotate':a.get('Rotate'),'Scale':a.get('Scale'),'Fields':sorted(a)})
loose=sorted(p for p in ROOT.rglob('*') if p.is_file() and ('/Pack/' not in p.as_posix()) and p.name.endswith(('.byml','.bgyml','.byml.zs','.bgyml.zs')))
out['loose_byml_count']=len(loose)
for p in loose:
 try:data=unzs(p.read_bytes())
 except Exception as e:out['errors'].append({'file':str(p),'error':str(e)});continue
 if b'FillUp' in data or b'fillup' in data:
  try:d=byml(data);out['named_occurrences'].append({'file':str(p),'matches':matches(d)})
  except Exception as e:out['errors'].append({'file':str(p),'error':str(e)})
out['fillup_material_rows']=len(out['fillup_rows']);out['fillup_actor_packs']=len(pack_actor_names);out['unique_fillup_shapes']=len(cache);out['banc_count']=len(scene_banc);out['placement_count']=len(out['placements']);out['placement_scene_count']=len(set(p['scene_pack'] for p in out['placements']))
out['summary']={'materials':dict(collections.Counter(r['material'] for r in out['fillup_rows'])),'filters':dict(collections.Counter(r['filter'] for r in out['fillup_rows'])),'roots':dict(collections.Counter(r['root_type'] for r in out['fillup_rows']))}
Path('analysis/completion/r9/physics_fillup_authoring_data.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ('fillup_rows','named_occurrences','placements','original_config_matches')},ensure_ascii=False))
print('preset_records',json.dumps(preset_records,ensure_ascii=False));print('named_files',len(out['named_occurrences']))