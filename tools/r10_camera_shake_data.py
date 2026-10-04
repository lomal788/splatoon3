"""Re-read original ELink and ID40 hit rows; static compiled-image call audit.
Analysis only. All generated files are under analysis/camera_100_r10/shake.
No keys, no original writes. Pointer absence is static evidence, not dynamic-game capture.
"""
import json, sys, struct, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from effect_xlink import XLink,load_bytes
from xref import load_idx,refs_to

path=ROOT/'extracted/romfs/XLink/ELink2.Product.100.belnk.zs'
if not path.exists():path=ROOT/'analysis/effect_sound/elink2.Product.100.belnk'
blob=load_bytes(str(path)); xl=XLink(blob)
users={n:xl.user(xl.user_index(n)) for n in ['WeaponShooterNormal','HitEffect','SighterTarget','SighterTargetBig','SplPlayer']}
defaults={p['name']:p['default'] for p in xl.assetParamDefs}
assets={}
for n,u in users.items():
 rows=[]
 for c in u['callTables']:
  if not c.get('params'):continue
  row={'i':c['i'],'key':c['key'],'assetId':c['assetId'],'params':c['params']}
  for key in ['CameraRumbleName','CameraRumbleFrame','CtrlRumbleName','CtrlRumbleGain','CtrlRumblePitch','CtrlRumbleStretch','DistanceAttenuate']:
   row[key]=c['params'].get(key,defaults[key])
  chain=[];cur=c
  while True:
   chain.append({k:cur[k] for k in ['i','key','parent','container','condition'] if k in cur})
   if cur['parent']<0:break
   cur=u['callTables'][cur['parent']]
  row['ancestors']=chain;rows.append(row)
 assets[n]=rows
hit=json.loads((ROOT/'analysis/combat/HitEffectConfig.json').read_text(encoding='utf-8'))['CellList']
shooter={k:v for k,v in hit.items() if k.startswith('Shooter___')}
weapons=json.loads((ROOT/'analysis/combat/rsdb/WeaponInfoMain.json').read_text(encoding='utf-8'))
w40=next(r for r in weapons if int(r['Id'])==40)
assert w40['__RowId']=='Shooter_Normal_00'
assert w40['DefaultHitEffectorType']=='Shooter'
assert not any(x['ExtraInfo']=='CriticalHit' and x['HitEffectorType']!='Shooter' for x in w40.get('ExtraHitEffectorInfoSet',[]))
e1keys=sorted(set(v.get('E1','') for v in shooter.values())-{''})
e2keys=sorted(set(v.get('E2','') for v in shooter.values())-{''})
available={c['key']:c for c in assets['HitEffect']}
assert all(not available[k]['CameraRumbleName'] and not available[k]['CtrlRumbleName'] for k in e1keys)
crit={k:v for k,v in available.items() if v['CameraRumbleName'] or v['CtrlRumbleName']}
assert all(not c['CameraRumbleName'] for c in assets['HitEffect'])
emu=json.loads((ROOT/'analysis/combat/r6_hiteffect_emu.json').read_text(encoding='utf-8'))
reused40=next(x for x in emu['shooter_rows_normal_vs_critical'] if x['id']==40)
image=(ROOT/'extracted/exefs/main.reloc.img').read_bytes(); BASE=0x7100000000
word=np.frombuffer(image[:0x3e9df50//4*4],dtype='<u4');idx=np.nonzero((word&0x7c000000)==0x14000000)[0]
imm=(word[idx].astype(np.int64)&0x3ffffff);imm=np.where(imm&(1<<25),imm-(1<<26),imm);dest=BASE+idx*4+imm*4
calls={}
for a in [0x710130f0b8,0x7101010f14]:
 needle=struct.pack('<Q',a);refs=[];at=image.find(needle)
 while at>=0:refs.append(hex(BASE+at));at=image.find(needle,at+1)
 calls[hex(a)]={'B_BL': [{'site':hex(BASE+int(i)*4),'op':'BL' if int(word[i])&(1<<31) else 'B'} for i in idx[dest==a]],'pointer_all_byte_positions':refs,'aligned_pointer_refs':[r for r in refs if int(r,16)%8==0]}
# xref.py has its own persisted ADRP+ADD/LDR window index. This is a static known-address audit.
adrp=load_idx()
for a in [0x710130f0b8,0x7101010f14]:
 calls[hex(a)]['ADRP_add_or_load_refs']=[{'site':hex(BASE+x),'kind':k} for x,k in refs_to(a-BASE,adrp)]
out={'version':'Splatoon 3 v0','source':str(path.relative_to(ROOT)).replace('\\','/'),'uncompressed_sha256':hashlib.sha256(blob).hexdigest(),'assets':assets,'ID40':w40,'Shooter_cells':shooter,'Shooter_E1_keys':e1keys,'Shooter_E2_keys':e2keys,'HitEffect_rumble_leafs':crit,'reuse_r6_native_ID40':reused40,'static_calls':calls,'limits':['No arithmetic-generated function pointer absence proof','No actual controller SDK playback','SubjectiveType live producer/receiver/writer validated separately in focused_native.json']}
dest=ROOT/'analysis/camera_100_r10/shake';dest.mkdir(parents=True,exist_ok=True)
(dest/'data_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'leaf_counts':{k:len(v) for k,v in assets.items()},'Shooter_cells':len(shooter),'E1':e1keys,'E2':e2keys,'critical_ctrl_leafs':list(crit),'ID40':reused40,'static_calls':calls},ensure_ascii=False))
