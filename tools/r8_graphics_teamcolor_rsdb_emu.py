"""r8: original TeamColorDataSet RSDB row loader and name query. No original code patches."""
import json,struct,sys,hashlib
from collections import Counter
from pathlib import Path
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
ROOT=Path(__file__).resolve().parents[2]
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py'),'__name__':'support'}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],ns)
H=ns['H'];import spl_data
class T(H):
 def _block(self,mu,a,size,user):
  if a==0x7103585094:self.executed.add(a);return
  super()._block(mu,a,size,user)
h=T([0x71014076b8]);h.executed=set();h.sdklog=Counter();h.stublog=Counter();h.null_reads=0

def read(mu,access,a,size,value,user):
 if a<0x400000:h.null_reads+=1;raise RuntimeError(f'NULL read {a:#x} PC={mu.reg_read(UC_ARM64_REG_PC):#x}')
h.mu.hook_add(UC_HOOK_MEM_READ,read)
h.w64(0x71059975c0,0)
mgr=h.alloc(0x40);h.call(0x7101424e88,[mgr,0]);entry=h.r64(mgr+0x18)+5*0x28
metadata=[h.cstr(h.r64(entry+x)) for x in [0,8,0x10,0x18]]
assert metadata==['game__TeamColorDataSetTable','TeamColorDataSet','Work/Gyml','game__gfx__parameter__TeamColorDataSet']
h.call(0x71038a0d98,[h.r64(entry)]);assert h.mu.reg_read(UC_ARM64_REG_X0)==0x2f368919e2207bcb
h.call(0x71014097cc,[]);assert h.cstr(h.mu.reg_read(UC_ARM64_REG_X0))==metadata[0]
h.call(0x71014092a8,[0]);obj=h.mu.reg_read(UC_ARM64_REG_X0)
assert h.r64(obj)==0x71055820a8
assert h.r64(h.r64(obj)+0x38)==0x71014076b8
assert h.r64(h.r64(obj)+0x40)==0x71014081c8
p=ROOT/'extracted/romfs/RSDB/TeamColorDataSet.Product.100.rstbl.byml.zs';raw=spl_data.load(p);rows=spl_data.Byml(raw).root();base=h.alloc(len(raw));h.mu.mem_write(base,raw)
h.call(0x71014076b8,[obj,base,0])
assert h.r32(obj+0x20)==len(rows),(h.r32(obj+0x20),len(rows))
print('LOADED',len(rows),'blocks',len(h.executed),flush=True)
fields={'AlphaTeamColor':0xc,'AlphaHueOffset':0x8,'AlphaUIColor':0x1c,'BravoTeamColor':0x30,'BravoHueOffset':0x2c,'BravoUIColor':0x40,'CharlieTeamColor':0x54,'CharlieHueOffset':0x50,'CharlieUIColor':0x64,'NeutralColor':0x74,'NeutralHueOffset':0x84}
checked=0;examples=[];gyml_differences=[];gyml_matches=[];gyml_bit_checks=0
for i,row in enumerate(rows):
 rp=h.r64(obj+0x28)+i*0x90
 assert h.cstr(h.r64(rp))==row['__RowId']
 for name,off in fields.items():
  values=[row[name][x] for x in 'RGBA'] if isinstance(row[name],dict) else [row[name]]
  for j,v in enumerate(values):
   got=h.r32(rp+off+j*4);expect=struct.unpack('<I',struct.pack('<f',v))[0];assert got==expect,(i,name,j,hex(got),hex(expect));checked+=1
 for name,off in [('HueOffsetEnable',0x8c),('IsSetUIColor',0x8d)]:assert h.mu.mem_read(rp+off,1)[0]==row[name];checked+=1
 tag=['VersusRegular','VersusOption','Mission','MissionOption','VersusTricolor','VersusTricolorOption','Coop','CoopOption','Gambit','Blitz'].index(row['Tag']);assert h.r32(rp+0x88)==tag;checked+=1
 key=h.alloc(0x200);h.mu.mem_write(key,row['__RowId'].encode()+b'\0');ss=h.alloc(8);h.w64(ss,key)
 h.call(0x710140946c,[obj,ss]);gotp=h.mu.reg_read(UC_ARM64_REG_X0);assert gotp==rp,(i,hex(gotp),hex(rp));checked+=1
 gp=ROOT/'extracted/romfs/Gyml'/Path(row['__RowId']).name.replace('.gyml','.bgyml')
 if gp.exists():
  gyml_matches.append({'file':str(gp.relative_to(ROOT)),'sha256':hashlib.sha256(gp.read_bytes()).hexdigest()})
  gr=spl_data.Byml(spl_data.load(gp)).root()
  diff={k:{'RSDB':row.get(k),'Gyml':v} for k,v in gr.items() if row.get(k)!=v}
  for k,v in gr.items():
   if isinstance(v,dict):
    for component,value in v.items():assert struct.pack('<f',value)==struct.pack('<f',row[k][component]);gyml_bit_checks+=1
   else:assert v==row[k];gyml_bit_checks+=1
  if diff:gyml_differences.append({'row':row['__RowId'],'differences':diff})
 if 'GreenPurple.' in row['__RowId']:examples.append({'row':row['__RowId'],'AlphaTeamColor':row['AlphaTeamColor'],'Gyml':gr,'differences':diff})
print('ROWS QUERY PASS',len(rows),'fields',checked,'Gyml differs',len(gyml_differences),flush=True)
out={'original_functions':['14092a8','14076b8','1407364','1407e58','140946c'],'registry_metadata':metadata,'registry_hash':'2f368919e2207bcb','rows':len(rows),'field_checks':checked,'mismatches':0,'null_reads':h.null_reads,'SDK_stubs':dict(h.sdklog),'nonSDK_stubs':{hex(k):v for k,v in h.stublog.items()},'executed_blocks':len(h.executed),'source':str(p.relative_to(ROOT)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'examples':examples,'Gyml_matched_files':len(gyml_matches),'Gyml_field_bit_checks':gyml_bit_checks,'Gyml_file_hashes':gyml_matches,'Gyml_differences':gyml_differences,'scope':'original whole ctor/typed loader/name lookup from actual decompressed RSDB; SDK allocation/memory/string boundaries; high resource file loader not emulated in this phase'}
(ROOT/'analysis/completion/r8/graphics_teamcolor_rsdb_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False),flush=True)
