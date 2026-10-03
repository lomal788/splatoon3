"""Original localproperty registration, life enum mapping and property consumer; no image patches."""
from pathlib import Path
import sys,struct,json
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
ns={'__name__':'r8_rate_prefix','__file__':str(Path('web/tools/r8_combat_rate_rows_emu.py').resolve())}
exec(compile(Path('web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],'r8_rate_prefix','exec'),ns)
from unicorn.arm64_const import *
class H(ns['H']):
 def _block(self,mu,a,size,user):
  if 0x7103e99000<=a<0x7103e9e000 and 'ErrorResultVariant' in self._plt_name(a):
   name=self._plt_name(a);self.sdklog[name]+=1;mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  if 0x7103e99000<=a<0x7103e9e000 and 'MakeIpv4Address' in self._plt_name(a):
   self.sdklog[self._plt_name(a)]+=1;mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  super()._block(mu,a,size,user)
h=H([0x71026bd4e0]);h.executed=set();h.sdklog=Counter();h.stublog=Counter()
h.call(0x71026b3370,[])
head=0x71058c1800;cur=h.r64(head);props=[]
while cur and cur!=head:
 obj=h.r64(cur+0x10); name=h.cstr(h.r64(obj+0x10));props.append({'object':hex(obj),'name':name,'kind':h.r32(obj+0x60),'default_bits':h.r32(obj+0x50)})
 cur=h.r64(cur)
 if len(props)>100:raise RuntimeError('list cycle')
ordered=list(reversed(props));assert len(ordered)==33
assert ordered[5]['name']=='TransformType' and ordered[6]['name']=='TroubleType'
assert h.r32(0x71058c1590)==3
entries=[]
for i in range(5):entries.append({'value':h.r32(0x71058c1f68+i*16+8),'name':h.cstr(h.r64(0x71058c1f68+i*16))})
assert [x['name'] for x in entries]==['Dying','AirFall','WaterFall','RespawnWait','Normal']
M=h.alloc(0x400);C=h.alloc(0x2900);h.w64(C+0x27e0,M);users=[]
for off in [0x1d8,0x200,0x2a0,0x278]:
 u=h.alloc(0x150);vals=h.alloc(0x200);h.w64(u+0x80,vals);h.w64(M+off,u);users.append((u,vals))
img=h.img;base=0x7100000000
maps=[list(struct.unpack_from('<10i',img,a-base)) for a in [0x7104a9fe48,0x7104a9fe70]]
checks=0
for common in [3,58,63]:
 h.w32(0x71058c1590,common)
 for state in list(range(11))+[0xffffffff,0x7fffffff]:
  for initial in [0,4,0xffffffff]:
   for u,vals in users:h.mu.mem_write(vals,b'\xff'*0x200);h.mu.mem_write(u+0x70,initial.to_bytes(16,'little'))
   h.w32(C+0x2168,state);h.mu.reg_write(UC_ARM64_REG_SP,0x10010000);h.mu.reg_write(UC_ARM64_REG_X19,C);h.mu.reg_write(UC_ARM64_REG_X25,C+0x27e0);h.mu.reg_write(UC_ARM64_REG_X20,4)
   h.mu.emu_start(0x71025161e4,0x7102516230,count=100000)
   transform=maps[1][state] if state<10 else 0;trouble=maps[0][state] if state<10 else 4
   for u,vals in users:
    assert h.r32(vals+4*(common+5))==transform
    assert h.r32(vals+4*(common+6))==trouble
    mask=int.from_bytes(h.mu.mem_read(u+0x70,16),'little');assert mask==(initial|(1<<(common+5))|(1<<(common+6)))
   checks+=1
# Unchanged property suppresses dirty flag, changed values propagate to all four users.
setter_cases=0
h.w32(0x71058c1590,3)
for idx in [5,6]:
 for old in range(5):
  for new in range(5):
   for u,vals in users:h.w32(vals+4*(3+idx),old);h.mu.mem_write(u+0x70,b'\0'*16)
   h.call(0x71026bbc60,[M,idx,new])
   for u,vals in users:
    assert h.r32(vals+4*(3+idx))==new
    assert int.from_bytes(h.mu.mem_read(u+0x70,16),'little')==((1<<(3+idx)) if old!=new else 0)
   setter_cases+=1
print('mapping',checks,'setter',setter_cases,'mismatch',0)
result={'properties':ordered,'common_count_actual':3,'life_property':'TroubleType','enum_entries':entries,'display_to_trouble':maps[0],'display_to_transform':maps[1],'NoAction_or_invalid':[4,0],'mapping_cases':checks,'setter_cases':setter_cases,'mismatches':0,'SDK_stubs':dict(h.sdklog),'game_stubs':{hex(k):v for k,v in h.stublog.items()},'scope':'whole localpropertyregistration26b3370 and whole integer4user setter26bbc60; model25161e4..6230 originalcallerblock, notfull model tick; ErrorResultVariant/MakeIpv4Address debug config endpoints inert and notusedby properties; allocation/locks/strings SDK boundary; synthetic live users and commoncount boundary variants'}
Path('analysis/completion/r8/combat_life_xlink_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
Path('analysis/completion/r8/combat_life_xlink_probe.json').write_text(json.dumps({'properties_reverse':props,'SDK_stubs':dict(h.sdklog),'game_stubs':{hex(k):v for k,v in h.stublog.items()}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# New actual model producer prefix. Chariot and live alternative actor cases are read-only proof, notemulated here.
import itertools
B=h.alloc(0xb000);PD=h.alloc(0x1000);link=h.alloc(0x200);fp=h.alloc(0x100);actorref=h.alloc(0x200)
h.w64(C+0x27d8,link);h.w64(link+0x108,B);h.w64(B+0xa8a0,PD);h.w64(C+0x27e8,fp);h.w64(B+0xa668,actorref);h.w32(actorref+0x1b8,0xffffffff)
producer_cases=0
for timers in itertools.product([-1,0,1],repeat=4):
 for half,tohuman,force_squid,ink in itertools.product(range(2),repeat=4):
  for hpdelta in [-1,0,1]:
   for previous in [0,4,5,6,9,10]:
    for off,v in zip([0xd60,0xdf0,0xde0,0xd58],timers):h.w32(B+off,v)
    h.mu.mem_write(fp+0x61,bytes([half,force_squid]));h.mu.mem_write(fp+0xac,bytes([tohuman]));h.mu.mem_write(B+0x7a0,bytes([ink]))
    h.w32(PD+0x7c,500+hpdelta);h.w32(PD+0xeec,500);h.w32(C+0x2168,previous)
    h.mu.reg_write(UC_ARM64_REG_SP,0x10010000);h.mu.reg_write(UC_ARM64_REG_X0,C)
    h.mu.emu_start(0x7102515488,0x7102515720,count=100000)
    prior=min(previous,4 if half else 5 if tohuman else previous)
    candidate=next((i for i,v in enumerate(timers) if v>0),None)
    if candidate is None:candidate=(8 if hpdelta>0 and not ink else 9) if (force_squid or ink) else (6 if hpdelta>0 else 7)
    assert h.r32(C+0x2168)==min(prior,candidate),(timers,half,tohuman,force_squid,ink,hpdelta,previous,h.r32(C+0x2168),min(prior,candidate))
    producer_cases+=1
result['display_producer_cases']=producer_cases;result['display_producer_scope']='original2515488..2515720 prefix with originalprologue and priority/min updates; invalidalternative actor; Chariot/liveactor meaning read only; restofmodel excluded'
Path('analysis/completion/r8/combat_life_xlink_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('producer',producer_cases,'mismatch',0)
