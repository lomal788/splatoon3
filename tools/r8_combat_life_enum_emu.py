"""New original player life enum metadata; reuse r8 SDK stubs only, no old enum rerun."""
from pathlib import Path
import sys,struct,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
src=Path('web/tools/r8_combat_enum_emu.py').read_text(encoding='utf-8').split('\ne=Meta(')[0]
ns={'__name__':'r8_meta_prefix','__file__':str(Path('web/tools/r8_combat_enum_emu.py').resolve())};exec(compile(src,'r8_meta_prefix','exec'),ns)
M=ns['Meta']; e=M([0x71026bd4e0]);e.call(0x71026bd4e0,[]);p=e.mu.reg_read(ns['UC_ARM64_REG_X0'])
entries=[e.cstr(struct.unpack('<Q',e.mu.mem_read(p+8*i,8))[0]) for i in range(5)]
assert entries==['Dying','AirFall','WaterFall','RespawnWait','Normal'],entries
out={'function':'0x71026bd4e0','entries':[{'value':i,'name':s} for i,s in enumerate(entries)],'boundary_stubs':[{'address':hex(a),'name':b} for a,b,x in e.calls],'scope':'whole original enum splitter and staticliteral init, syntheticguard+SDKlocks and mutexinit/atexit boundary, notplayerstate frame execution'}
d=M([0x71026b82d0]);display=[]
obj=d.alloc(0x40);sub=d.alloc(0x60);d.w64(obj+8,sub);d.w64(sub+0x20,sub);d.w64(sub+0x38,sub)
for i in range(11):
 d.call(0x71026b82d0,[obj,1,i]);display.append(d.cstr(d.mu.reg_read(ns['UC_ARM64_REG_X0'])))
assert display==['Dying','WaterFall','AirFall','RespawnWait','Half','HalfToHuman','Human_RecoverDamage','Human_Normal','Squid_RecoverDamage','Squid_Normal','NoAction']
out['display_type1']={'function':'0x71026b82d0','entries':[{'value':i,'name':s} for i,s in enumerate(display)],'boundary_stubs':[{'address':hex(a),'name':b} for a,b,x in d.calls]}
Path('analysis/completion/r8/combat_life_enum_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
