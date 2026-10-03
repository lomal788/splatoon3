"""New original AS request399e340 -> first tick399f848 -> wrapper frame-copy block.
Resource query, FSKA clip metadata and output capacity0 are explicit fixture boundaries.
All request/entry/traversal/advance/report and wrapper stores are original bytes.
"""
import json,math,random,struct
from pathlib import Path
from unicorn.arm64_const import *
from r5_gfx_stage_emu import BASE,HEAP
source=Path('web/tools/r8_camweapon_as_request_tick_probe.py').read_text(encoding='utf8').split('steps=[]')[0];g={};exec(compile(source,'as_fixture','exec'),g);E=g['E'];mu=g['mu'];wrap=E.alloc(0x80);E.w(wrap,'Q',g['AS']);snapshot=bytes(mu.mem_read(HEAP,E.hp-HEAP));rng=random.Random(399e340)
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bit(x):return struct.pack('<f',x).hex()
def r4(x):
 y=f(x*10000.);z=math.floor(y+.5) if y>=0 else math.ceil(y-.5);return f(f(z)/10000.)
def advance(cur,dt,rate,end,loop):
 n=r4(f(cur+f(f(dt*rate)*1.)))
 if n>=end:
  if not loop:n=end
  elif end>0:
   length=end
   if n>=f(length+length):length=f(length*int(f(n/length)))
   n=r4(f(n-length))
  else:n=end
 return n
nfields=0;examples=[];counts={};faults=[];seen=set();ticks=0
for case in range(1025):
 mu.mem_write(HEAP,snapshot);g['trace'].clear();g['seen'].clear();g['fault'].clear()
 dt=1. if case==0 else f(rng.uniform(0,4));rate=1. if case==0 else f(rng.uniform(0,3));end=6. if case==0 else float(rng.randrange(1,121));loop=False if case==0 else bool(case&1);g['FRAME']=end;g['LOOP']=loop;E.w(g['slot']+0xd4,'f',rate)
 E.call(BASE+0x399e340,[g['AS'],g['name'],0,0,0,0,0,0],[-1.,-1.]);assert mu.reg_read(UC_ARM64_REG_PC)==g['RET'];assert not g['fault']
 entry=g['entry'];slot=g['slot'];got=[*E.r(entry+4,'ff'),E.r(entry+0x14,'f')[0],E.r(slot+0x104,'f')[0]];want=[0.,-1.,end,0.];assert [bit(v) for v in got]==[bit(v) for v in want],(case,'request',got,want);nfields+=4
 requesttrace=[dict(a) for a in g['trace']];assert not any(int(a['pc'],16)==BASE+0x39ab2c4 for a in requesttrace);assert any(int(a['pc'],16)==BASE+0x39bcdbc and a['x4']==1 for a in requesttrace)
 cur=0.;series=[]
 for tick in range(1):
  g['trace'].clear();prev=cur;cur=advance(cur,dt,rate,end,loop);
  try:E.call(BASE+0x399f848,[g['AS'],0,0,0,0,0,0,0],[dt])
  except Exception as ex:
   j=dict(case=case,tick=tick,pc=hex(mu.reg_read(UC_ARM64_REG_PC)),lr=hex(mu.reg_read(UC_ARM64_REG_LR)),fault=g['fault'],trace=g['trace'],stubs=g['seen'],error=str(ex));Path('analysis/completion/r8/as_request_first_tick_failure.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');print(json.dumps(j,indent=2));raise
  assert mu.reg_read(UC_ARM64_REG_PC)==g['RET'];assert not g['fault'];ticks+=1
  mu.reg_write(UC_ARM64_REG_X19,wrap);mu.reg_write(UC_ARM64_REG_X21,0);mu.reg_write(UC_ARM64_REG_X24,0x48);mu.reg_write(UC_ARM64_REG_X27,1);mu.emu_start(BASE+0x2450c94,BASE+0x2450d6c,count=100);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0x2450d6c
  got=[*E.r(entry+4,'ff'),E.r(entry+0x14,'f')[0],E.r(slot+0x104,'f')[0],E.r(wrap+0x30,'f')[0]];want=[cur,prev,end,cur,cur];assert [bit(v) for v in got]==[bit(v) for v in want],(case,tick,dt,rate,end,loop,got,want);nfields+=5
  assert any(int(a['pc'],16)==BASE+0x39bcdbc and a['x4']==0 for a in g['trace']);assert any(int(a['pc'],16)==BASE+0x39ab2c4 for a in g['trace']);assert any(int(a['pc'],16)==BASE+0x39d3dcc for a in g['trace'])
  if case<3:series.append(dict(tick=tick+1,cur=got[0],prev=got[1],slotFrame=got[3],wrapperFrame=got[4],trace=[dict(a) for a in g['trace']]))
 for a in g['seen']:counts[a]=counts.get(a,0)+1;seen.add(a)
 if case<3:examples.append(dict(case=case,dt=dt,slotRate=rate,frameCount=end,loop=loop,request=requesttrace,series=series))
out=dict(cases=1025,request_calls=1025,tick_calls=ticks,wrapper_copy_blocks=ticks,f32_fields=nfields,mismatches=0,examples=examples,boundaries=sorted(seen),boundary_counts=counts,faults=[],null_calls=0,auto_pages=0,scope=__doc__,whole_original=['399e340','399f848','399ec94','3997558','3996d84','39cd5d0','39d3608','39bc994','39bcdbc','39ab2c4','39ccc4c','39cd350','39d3dcc'],wrapper_original_block='2450c94..2450d6c',limitations='one skeletal kind3/no attached InitialFrame or FrameController, no transition metadata, one slot/output capacity0; first-frame order is original; full model pose composition/state-change predicate are not claimed')
Path('analysis/completion/r8/as_request_first_tick_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='examples'},indent=2))
