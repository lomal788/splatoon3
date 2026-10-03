"""r8 original HitEffect enqueue/controller/aggregated consumer with original config cells.
No main/SDK code patches; SDK allocation/locks and final XLink/one-emitter emission are captured boundaries.
"""
import sys,json,struct,random
from pathlib import Path
from collections import Counter
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R']
from r5_player_libm_emu import symbols
class E(H):
 def _block(self,mu,a,size,user):
  rd=mu.reg_read;x=[rd(r) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3)]
  if a in [R.RETADDR+0x100,R.RETADDR+0x104]:
   self.stublog[a]+=1;mu.reg_write(UC_ARM64_REG_X0,0 if a==R.RETADDR+0x100 else 0xc0000001);mu.reg_write(UC_ARM64_REG_PC,rd(UC_ARM64_REG_LR));return
  if self.sdkbase<=a<self.sdkbase+self.sdksize:self.executed.add(a);return
  if R.PLT_LO<=a<R.PLT_HI:
   name=self._plt_name(a)
   if name in ['asinf','acosf','sinf','cosf','atan2f','sqrtf']:
    self.mathlog[name]+=1;mu.reg_write(UC_ARM64_REG_PC,self.sdkbase+self.syms[name][0]);return
  if a in [0x710389e830,0x71038a0a08,0x710389e90c,0x710137f558,0x710129e630]:
   self.capture_counts[hex(a)]+=1;ret=0
   if a==0x710389e830:
    self.pending=(x[0],self.cstr(x[2]));ret=1
   elif a==0x71038a0a08:self.w64(x[1],self.resource);ret=1
   elif a==0x710389e90c:
    inst,key=self.pending;handle=self.handles[inst];mu.mem_write(handle,b'\0'*0x200);self.w32(handle+0x20,7);self.w64(handle+0x88,handle+0x80)
    self.w64(x[2],handle);self.w32(x[2]+8,7)
    self.events.append({'instance':self.instnames[inst],'key':key,'props_hex':bytes(mu.mem_read(self.r64(inst+0x80),20)).hex()})
   elif a==0x710137f558:self.emitters.append({'slot':x[0]-self.teamgroup,'matrix_hex':bytes(mu.mem_read(x[1],48)).hex()})
   mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,rd(UC_ARM64_REG_LR));return
  super()._block(mu,a,size,user)
e=E([0x71027b4704]);e.executed=set();e.sdklog=Counter();e.stublog=Counter();e.mathlog=Counter();e.capture_counts=Counter();e.events=[];e.emitters=[]
sdk=(ROOT/'extracted/exefs/sdk.img').read_bytes();e.sdkbase=0x7400000000;e.sdksize=(len(sdk)+0xffff)&~0xffff;e.syms=symbols(sdk);e.mu.mem_map(e.sdkbase,e.sdksize);e.mu.mem_write(e.sdkbase,sdk)
null_reads=[]
def memory_read(mu,access,a,size,value,user):
 if a<0x400000:raise RuntimeError(f'null read {a:#x} PC={mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,memory_read)
G=e.alloc(0x72000);W=e.alloc(16);e.w64(W,0x7105649130);e.w64(W+8,G)
pm=e.alloc(0xe000);e.w64(0x710580e340,pm);e.w32(pm+0xd470,0);e.w32(pm+0xd474,0)
# Native getter handles default invalid ActorID and invalid static ActorRef; initialized reference flags.
e.w64(0x71058bfb80,0);e.w32(0x71058bfb90,0xffffffff)
pobj=e.alloc(0x400);ptable=e.alloc(8);e.w64(ptable,pobj);e.w64(pm+0xb0,ptable);e.w32(pm+0xa8,1);e.w32(pobj+0x160,0);e.w32(pobj+0x18,0xffffffff)
actorManager=e.alloc(0x40);actorVT=e.alloc(0x40);e.w64(actorManager,actorVT);e.w64(actorVT+0x20,R.RETADDR+0x100);e.w64(actorVT+0x28,R.RETADDR+0x104);e.w64(e.r64(0x71057908b0),actorManager)
team=e.alloc(0x15e8*3+8);e.w64(0x710580c5c0,team)
# Resolve GOT storage instead of assuming a BSS name for singleton team emitter.
teamcell=e.r64(0x7105797f10);e.w64(teamcell,team);e.teamgroup=team+8 # supplied local team0 via original ActorID resolution
for got in [0x7105790ae0,0x7105790ae8]:
 p=e.alloc(0x100);e.mu.mem_write(p+0x98,b'\1');e.w64(e.r64(got),p)
e.w32(0x71058e877c,0) # distance culling disabled; separate culling tests below.
e.resource=e.alloc(32);e.instnames={};e.handles={}
for off,name in [(0x690b8,'SLink'),(0x690c0,'ELink')]:
 inst=e.alloc(0x120);props=e.alloc(32);res=e.alloc(32);e.w64(inst+0x80,props);e.w64(inst+0x38,res);e.w64(res+0x18,e.resource);e.w64(G+off,inst);e.instnames[inst]=name;e.handles[inst]=e.alloc(0x200)
# Solo network context needed only for native req3D/3E feedback gate; no serialization is run.
scene=e.alloc(0x200);net=e.alloc(0x6600);peer=e.alloc(0xa08);rep=e.alloc(0x100);e.w64(e.r64(0x7105790fc0),scene);e.w64(scene+0xc8,net);e.w64(net+0xa0,peer);e.w32(peer+0x118,1);e.w32(rep+0x70,1);e.w64(G+0x70170,rep)
# Actual enum names from original getters, original guard initialization.
rows=[];results=[];materials=[]
for fn,n,dst in [(0x71014188b8,48,rows),(0x71027b8258,8,results),(0x71026bc9ac,35,materials)]:
 e.call(fn,[]);arr=e.mu.reg_read(UC_ARM64_REG_X0)
 for i in range(n):dst.append(e.cstr(e.r64(arr+i*8)))
assert rows[1]=='Shooter';assert results==['Through','Constant','Aggregated','NetPriorityFailure','Invincible','Armored','Damaged','Cure']
config=json.loads((ROOT/'analysis/combat/HitEffectConfig.json').read_text(encoding='utf-8'))['CellList'];cells={};used=[]
def string(v):
 p=e.alloc(len(v.encode())+1);e.mu.mem_write(p,v.encode()+b'\0');return p
empty=string('')
for r in range(8):
 for m in range(35):
  key=f'Shooter___{results[r]}_{materials[m]}'
  if key not in config:key=f'Shooter___{results[r]}_Default'
  d=config.get(key,{})
  # Native ctor is reused; data visitor values are supplied typed fields (not claimed native loader execution).
  c=e.alloc(0x80);e.call(0x710279ec14,[c])
  for off,k in [(0x48,'E1'),(0x50,'E2'),(0x58,'S1'),(0x60,'S2')]:e.w64(c+off,string(d[k]) if k in d else empty)
  e.mu.mem_write(c+0x68,b'\1'*4);kind={'Splash':0,'Hit':1,'SplashWater':2}.get(d.get('E2',''),-1)
  for local in range(2):
   idx=1*0x230+r*0x46+m*2|local;slot=G+0xb8+idx*16;e.w64(slot,c);e.w32(slot+8,{'Splash':0,'Hit':1,'SplashWater':2}.get(d.get('E1',''),-1));e.w32(slot+12,kind)
  cells[(r,m)]=(d,kind,key)
# Two exact-capacity pools; sentinel tail as initialized by loader to own list head.
pools=[]
for start,count,free,cap in [(0x50,0x60,0x68,0x78),(0x80,0x90,0x98,0xa8)]:
 pool=e.alloc(64*0x70);pools.append(pool)
 for i in range(64):e.w64(pool+i*0x70,pool+(i+1)*0x70 if i<63 else 0)
 e.w64(G+free,pool);e.w32(G+cap,64);e.w64(G+start,G+start);e.w64(G+start+8,G+start)
req=e.alloc(0x60);fixture=bytes.fromhex(json.loads((ROOT/'analysis/completion/r8/hit_packet_chain_emu.json').read_text(encoding='utf-8'))['fixture'][0]['packet_hex'])
def packet(res,mat=0,owner=0,paint=1,normal=(0,1,0),velocity=(0,0,0),kind=0,flag3d=1,flag3e=1):
 b=bytearray(fixture);b[:36]=struct.pack('<9f',1,2,3,*normal,*velocity)
 struct.pack_into('<III',b,0x24,mat,res,1);struct.pack_into('<fii',b,0x30,0,owner,-1);b[0x3c:0x3f]=bytes([paint,flag3d,flag3e]);struct.pack_into('<I',b,0x40,kind);struct.pack_into('<Q',b,0x48,0);struct.pack_into('<I',b,0x50,0x1234);return b
# queue copy/formula and capacity/drop semantics including grouped nonzero kind.
queue_cases=0;queue_examples=[]
for kind,pool,start,count,free in [(0,pools[0],0x50,0x60,0x68),(1,pools[1],0x80,0x90,0x98)]:
 for i in range(70):
  b=packet(1+(i%7),i%35,0 if i%2 else -1,kind=kind);e.mu.mem_write(req,bytes(b));e.call(0x71027b4704,[G,req]);accepted=min(i+1,64);assert e.r32(G+count)==accepted
  if i<64:
   node=pool+i*0x70;assert bytes(e.mu.mem_read(node,0x44))==bytes(b[:0x44]);assert e.r32(node+0x50)==0x1234
   idx=(1+i%7)*0x46+0x230+(i%35)*2|(int(i%2==1));assert e.r32(node+0x58)==idx
  queue_cases+=1
 # reset fixture queue after capacity exercise; native reset not part of this test.
 e.w64(G+start,G+start);e.w64(G+start+8,G+start);e.w32(G+count,0);e.w64(G+free,pool)
 for i in range(64):e.w64(pool+i*0x70,pool+(i+1)*0x70 if i<63 else 0)
# Original controller invokes native aggregation callback and returns through original E2/S2 conditions.
cases=0;example=[]
for res in range(1,8):
 for mat in range(35):
  for paint in [0,1]:
   for normal,vel in [((0,1,0),(0,0,0)),((0,1,0),(0,-1,0)),((0,0,1),(0,0,-1))]:
    for gate in [0,1,2,3]:
     b=packet(res,mat,0,paint,normal,vel,flag3d=int(gate!=0),flag3e=int(gate!=2));e.mu.mem_write(req,bytes(b));e.call(0x71027b4704,[G,req]);node=e.r64(G+0x50)-0x60
     e.events=[];e.emitters=[];e.mu.mem_write(net+0x650c,bytes([int(gate==3)]));e.call(0x71027b877c,[W,node,1])
     d,kind,key=cells[(res,mat)];agg=(gate in [0,1]);expected=[]
     if agg:
      if d.get('S1'):expected.append(('SLink',d['S1']))
      if d.get('E1'):expected.append(('ELink',d['E1']))
     if d.get('S2'):expected.append(('SLink',d['S2']))
     if d.get('E2'):expected.append(('ELink',d['E2']))
     got=[(v['instance'],v['key']) for v in e.events];
     if '--probe' in sys.argv:print('IDX',e.r32(node+0x58),'KIND',hex(e.r32(G+0xb8+e.r32(node+0x58)*16+12)),'EMIT',e.emitters)
     assert got==expected,(res,mat,paint,normal,gate,key,got,expected)
     # Local Subjective0/IsLocal1, S1/E1 fixed paint1/vel0, S2 live paint and |v|.
     for v in e.events:
      il,pa,num,speed,focused=struct.unpack('<IIIfI',bytes.fromhex(v['props_hex']));assert (il,num,focused)==(1,1,0);is_second=v['key']==d.get('S2') if v['instance']=='SLink' else v['key']==d.get('E2');assert pa==(paint if is_second else 1);assert speed==(sum(a*a for a in vel)**.5 if is_second else 0)
     # G58 FIFO oldest request checked separately below; release this single fixture node.
     e.w64(G+0x50,G+0x50);e.w64(G+0x58,G+0x50);e.w32(G+0x60,0);e.w64(node,e.r64(G+0x68));e.w64(G+0x68,node)
     if mat in [0,2] and paint==1 and normal==(0,1,0) and gate==1:example.append({'result':results[res],'material':materials[mat],'cell':key,'events':e.events,'emitters':e.emitters})
     cases+=1
     if '--probe' in sys.argv:break
    if '--probe' in sys.argv:break
   if '--probe' in sys.argv:break
  if '--probe' in sys.argv:break
 if '--probe' in sys.argv:break
# Native frame consumer drains original FIFO and recycles all nodes. No renderer/system ring claim.
ctx=e.alloc(32);flags=e.alloc(16);e.w64(ctx+0x18,flags)
for off in [0x69140]:e.w64(G+off,G+off);e.w64(G+off+8,G+off)
for inst in e.instnames:e.w32(inst+0x100,1)
e.mu.mem_write(net+0x650c,b'\0');fifo=[]
for res in [6,5,4,1,7]:
 b=packet(res);e.mu.mem_write(req,bytes(b));e.call(0x71027b4704,[G,req]);fifo.append(cells[(res,0)][0])
e.events=[];e.emitters=[];e.call(0x71027b7938,[G,ctx]);expect=[]
for d in fifo:
 for typ,key in [('SLink','S1'),('ELink','E1'),('SLink','S2'),('ELink','E2')]:
  if d.get(key):expect.append((typ,d[key]))
assert [(x['instance'],x['key']) for x in e.events]==expect;assert e.r32(G+0x60)==0;assert e.r64(G+0x50)==G+0x50 and e.r64(G+0x58)==G+0x50
fifo_cases=5
# Original distance gate runs AFTER local S1/E1. Same-team count changes actual radius.
camactor=e.alloc(0x300);cam=e.alloc(0x200);e.w64(camactor+0x268,cam);e.w64(0x710582c4b8,camactor);bulletmanager=e.alloc(0x200);e.w64(0x7105850620,bulletmanager);e.mu.mem_write(0x71058e877c,b'\1');culling_cases=0
for count in [0,10,30,60]:
 e.w32(bulletmanager+0x18,count);radius=400-300*min(count/30,1)
 for distance in [radius-1,radius,radius+1,radius*2]:
  b=packet(6);struct.pack_into('<3f',b,0,0,0,distance);e.mu.mem_write(req,bytes(b));e.call(0x71027b4704,[G,req]);node=e.r64(G+0x50)-0x60;e.events=[];e.emitters=[];e.call(0x71027b877c,[W,node,1]);d=cells[(6,0)][0]
  expected=[('SLink',d['S1']),('ELink',d['E1'])]
  if distance<=radius:expected += [('SLink',d['S2']),('ELink',d['E2'])]
  assert [(v['instance'],v['key']) for v in e.events]==expected,(count,distance,radius,e.events)
  assert len(e.emitters)==int(distance<=radius)
  e.w64(G+0x50,G+0x50);e.w64(G+0x58,G+0x50);e.w32(G+0x60,0);e.w64(node,e.r64(G+0x68));e.w64(G+0x68,node);culling_cases+=1
e.mu.mem_write(0x71058e877c,b'\0')
out={'culling_cases':culling_cases,'fifo_cases':fifo_cases,'queue_cases':queue_cases,'controller_cases':cases,'mismatches':0,'rows':rows,'results':results,'materials':materials,'examples':example,'captured_boundaries':dict(e.capture_counts),'SDK_stubs':dict(e.sdklog),'SDK_original_math':dict(e.mathlog),'non_SDK_stubs':{hex(k):v for k,v in e.stublog.items()},'native_blocks':len(e.executed),'null_reads':null_reads,'scope':'Original queue/controller/aggregation/subjective predicates with original Shooter config field fixtures; final XLink resource lookup/emit and137f558 backend captured. Native enum getters and Cell ctor executed; full config loader/GPU/audio render/live manager startup/targetActorRef not executed.'}
(ROOT/'analysis/completion/r8/hiteffect_consume_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','results','materials','examples']},ensure_ascii=False))
