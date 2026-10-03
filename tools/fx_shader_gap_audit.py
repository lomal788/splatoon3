"""New Flash/Ripple data + raw Maxwell attribute audit. No native GPU execution."""
import json,re,hashlib,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'web/tools'))
import effect_vfxb as V
from vfx_emitter46 import emitters
OUT=ROOT/'analysis/visual_gap_r2/fx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for pid in [1385,1202,1885]:
 stages={}
 for st in ['vert','frag']:
  p=OUT/f'p{pid}.{st}.ops.tsv'
  if not p.exists():continue
  ops=[x.split('\t') for x in p.read_text(encoding='utf-8-sig').splitlines() if len(x.split('\t'))==4]
  attrs=[]
  for x in ops:
   if x[2] not in ['Ast','Ipa']:continue
   d=dict(re.findall(r'(\w+)=([\w-]+)',x[3]));attrs.append({'pc':x[0],'opcode':x[1],'op':x[2],**d})
  stages[st]={'instructions':len(ops),'brx':sum(x[2]=='Brx'for x in ops),'attributes':attrs}
 checks={}
 old=ROOT/'analysis/visual_gap' if pid==1385 else OUT
 for st in ['vert','frag']:
  a=old/f'p{pid}.{st}';b=OUT/f'p{pid}_fixed.{st}';checks[st]={'old_sha256':sha(a),'constantBuffer1_fixed_sha256':sha(b),'identical':a.read_bytes()==b.read_bytes()}
 missing=172 if pid==1385 else 204 if pid==1202 else None
 stores=[int(x['Imm11']) for x in stages.get('vert',{}).get('attributes',[])if x['op']=='Ast']
 rows.append({'program':pid,'stages':stages,'old_vs_constantBuffer1_corrected':checks,'watched_attribute':missing,'vertex_writes_watched_attribute':None if missing is None else missing in stores})
v=V.Vfxb(str(ROOT/'analysis/assets_work/r6/static.vfxb'));source=json.loads((OUT/'emitter_fields.json').read_text(encoding='utf8'))
res=[]
for es,name,depth,parent,bo,em in emitters(v,['WpShtrMzfNml','CmnWallSplash1Emit']):
 if name not in ['Flash','Ripple']:continue
 fields=source[f'{es}/{name}'];r={'eset':es,'emitter':name,'offset':hex(bo),'shaderIndex':fields['shaderIndex']}
 for n,key in [('C0','color0Keys'),('A0','alpha0Keys'),('A1','alpha1Keys'),('scale','scaleKeys')]:
  count=fields[{'C0':'numColor0Keys','A0':'numAlpha0Keys','A1':'numAlpha1Keys','scale':'numScaleKeys'}[n]];r[n]=fields[key][:count]
 r.update({'types_C0_C1_A0_A1':[fields[x]for x in ['color0Type','color1Type','alpha0Type','alpha1Type']],'alpha_discard_R8a8':struct.unpack_from('<f',v.d,bo+0x8a8)[0],'near_fade_R890_R894':struct.unpack_from('<2f',v.d,bo+0x890),'PColor_D4c_D5c':[struct.unpack_from('<f',v.d,bo+o)[0]for o in [0xd4c,0xd5c]],'fixed_patch_A1':struct.unpack_from('<f',v.d,bo+0xd5c)[0]if fields['alpha1Type']==0 else None});res.append(r)
report={'level':'original shader/instruction READ + original serialized DATA; no GPU execution','raw_audit':rows,'emitter_data':res,'remaining':['runtime Custom1[12].x VAT speed producer','Custom1[11].xy runtime alpha remap','linked/default fragment attribute 2.w p1385 and 4.w p1202','runtime dynamic team colors','whole GPU pixels']}
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'programs':[{'program':x['program'],'CB1_same':all(y['identical']for y in x['old_vs_constantBuffer1_corrected'].values()),'missing_export':x['watched_attribute'],'written':x['vertex_writes_watched_attribute']}for x in rows],'emitters':res},ensure_ascii=False))

