"""Original TexSrt30 callback/Maya writer, zero rotation selected contract.
Exact SDK numeric data imports; no trig/math/function stubs. Six native output
floats and 24-byte return only; original Mat UBO padding/upload remains excluded.
"""
from pathlib import Path
import json, struct, random, hashlib, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r7_fx_transform_emu import VM, HEAP, BASE, SDKBASE, symbols
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/port_graphics_r9/material_anim'
F=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
def main():
 vm=VM();raw=json.loads((OUT/'material_channels.proposed.json').read_text(encoding='utf-8'))
 src,dst,assign,defs=HEAP+0x100,HEAP+0x200,HEAP+0x300,HEAP+0x400
 # Actual callback install for TexSrt30, with an explicit one-row descriptor.
 vm.q(assign+0x20,defs);vm.mu.mem_write(assign+0x4a,struct.pack('<H',1))
 vm.mu.mem_write(defs,b'\0'*24);vm.mu.mem_write(defs+0x12,b'\x1e')
 vm.call(0x710088f308,assign)
 callback=struct.unpack('<Q',vm.mu.mem_read(defs,8))[0];assert callback==0x710088efb0,hex(callback)
 plans=[]
 def add(label,sx,sy,tx,ty):plans.append({'label':label,'srt':{'Mode':'ModeMaya','Scaling':{'X':F(sx),'Y':F(sy)},'Rotation':0,'Translation':{'X':F(tx),'Y':F(ty)}}})
 variant_path=ROOT/'analysis/port_graphics_r9/variants/actual_variants.json'
 variants=json.loads(variant_path.read_text(encoding='utf-8'))['rows']
 for label,title,param in [('tank','Tank','tex_mtx1'),('bottle','Bottle','tex_mtx0')]:
  row=next(r for r in variants if r['label']==label);v=row['fres']['params'][param]['value']
  assert v['Mode']=='ModeMaya' and v['Rotation']==0
  add('native static '+title+' '+param,v['Scaling']['X'],v['Scaling']['Y'],v['Translation']['X'],v['Translation']['Y'])
 # Raw native static selected body/eyes SRT values and fractional FMAA Sqd_Surprise outputs.
 for group,g in raw['groups'].items():
  for mat in g['materials']:
   for name,p in mat['params'].items():
    v=p.get('value')
    if name.startswith('tex_mtx') and isinstance(v,dict) and v.get('Mode')=='ModeMaya' and v.get('Rotation')==0:
     add(group+'/'+mat['name']+'/'+name,v['Scaling']['X'],v['Scaling']['Y'],v['Translation']['X'],v['Translation']['Y'])
 fixture=json.loads((ROOT/'web/games/splatoon3/tests/fixtures/material_animation_r9_native.json').read_text(encoding='utf-8'))
 eye=next(a for a in raw['groups']['Player_Squid']['clips'] if a['name']=='Sqd_Surprise')['materials'][0]
 curves={int(c['target'],16):i for i,c in enumerate(eye['curves']) if c['type']=='Cubic'}
 samples={(s['curve'],s['frame']):struct.unpack('<f',struct.pack('<I',s['result']))[0] for s in fixture['samples'] if s['group']=='Player_Squid' and s['clip']=='Sqd_Surprise'}
 frames=sorted(set(f for ci,f in samples if ci in curves.values()))
 for f in frames:
  if all((i,f) in samples for i in curves.values()):
   vals={t:samples[i,f] for t,i in curves.items()};add('native Sqd_Surprise frame '+str(f),vals[4],vals[8],vals[16],vals[20])
 rng=random.Random(20261003)
 for i in range(256):add('synthetic finite zero-rotation '+str(i),rng.uniform(-4,4),rng.uniform(-4,4),rng.uniform(-2,2),rng.uniform(-2,2))
 # Signed zero is observable and must not be simplified away.
 add('signed zero scales',-0.,0.,-0.,0.)
 results=[]
 for p in plans:
  r=p['srt'];vm.mu.mem_write(src,struct.pack('<Ifffff',0,r['Scaling']['X'],r['Scaling']['Y'],0,r['Translation']['X'],r['Translation']['Y']))
  vm.mu.mem_write(dst,b'\x5a'*32);n=vm.call(callback,dst,src)
  assert n==24,n;assert bytes(vm.mu.mem_read(dst+24,8))==b'\x5a'*8
  results.append({**p,'bits':list(struct.unpack('<6I',vm.mu.mem_read(dst,24))),'returnedBytes':n})
 sdk=(ROOT/'extracted/exefs/sdk.img').read_bytes();ss=symbols(sdk)
 table=ss['_ZN2nn4util6detail17SinCosSampleTableE'];table0=list(struct.unpack_from('<4f',sdk,table[0]))
 assert table0[0]==1 and table0[1]==0,table0
 result={'mainSHA256':hashlib.sha256((ROOT/'extracted/exefs/main.reloc.img').read_bytes()).hexdigest(),'sdkSHA256':hashlib.sha256(sdk).hexdigest(),
 'callbackInstall':'0x710088f308','callback':'0x710088efb0','writer':'0x710088f3d0','table0':table0,'SDK_numeric_imports':vm.imports,'stubs':[],
 'variantInputSource':variant_path.relative_to(ROOT).as_posix(),'variantInputSHA256':hashlib.sha256(variant_path.read_bytes()).hexdigest(),
 'samples':results,'scope':'original callback install then whole TexSrt->Maya converter with actual SDK numeric data; only finite zero-rotation six floats/24bytes; no UBO padding/upload or GPU pixels'}
 target=ROOT/'web/games/splatoon3/tests/fixtures/material_texsrt_r9_native.json';target.write_text(json.dumps(result,separators=(',',':'))+'\n',encoding='utf-8')
 (OUT/'texsrt_native_summary.json').write_text(json.dumps({k:v for k,v in result.items() if k!='samples'}|{'cases':len(results)},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'cases':len(results),'callback':hex(callback),'table0':table0,'returnedBytes':24,'stubs':[]}))
if __name__=='__main__':main()
