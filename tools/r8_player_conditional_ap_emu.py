"""r8 original conditional AP whole265ca78 + gearcollector266db4c.
Synthetic PlayerParam/actor/clock/score inputs. Actual enum initializers and f32 arithmetic;
scope conditional AP/gear aggregation, no battle/network/UI state execution claimed.
"""
import json,random,struct
from pathlib import Path
import numpy as np
from r6_player_uc import PUC
u=PUC();m=u.mu;P=u.alloc(0x300);B=u.alloc(0xb000);A=u.alloc(0x800);Fwd=u.alloc(0x1000);Clock=u.alloc(0x200);Mgr=u.alloc(0x200);Score=u.alloc(0x1100);rows=u.alloc(0x180);root=u.alloc(0x30);ptr=u.alloc(16)
u.wq(P+0x190,A);u.wq(A+0x108,B);u.wq(B+8,A);u.wq(B+0xa838,Fwd);u.wq(u.rq(0x7105790610),Clock);u.wq(u.rq(0x7105796510),Mgr);u.wq(Mgr+0x128,Score);u.wq(Score+0x10d0,rows);u.w32(Score+0x10d8,2);u.w32(Score+0x10dc,0);u.w32(Score+0x10e0,2)
# Real enum builders (no invented table order).
ge=u.rq(0x71057910a0);u.call(0x7100ff037c,ge);u.w8(u.rq(0x7105791098),1);GE=[u.rs32(u.rq(ge+8)+i*4) for i in range(u.r32(ge))]
u.call(0x71024cdd94,0x71058bc378);u.w8(0x71058bc388,1)
SP=[u.rs32(u.rq(0x71058bc380)+i*4) for i in range(u.r32(0x71058bc378))]
C={hex(a):u.rs32(a) for a in range(0x71058c035c,0x71058c0410,4)}
F=lambda x:float(np.float32(x))
rng=random.Random(0x265ca78);out={'scope':__doc__,'enum_gear':GE,'enum_special':SP,'constants':C,'collector_cases':0,'conditional_cases':0,'mismatch':[]}
# original collector primary10/sub3 or 6, ring order, special bits.
Gear=u.alloc(0x200);Subs=u.alloc(0x200);u.wq(ptr,P);u.wq(root+8,ptr)
for i in range(900):
 m.mem_write(P+0x3c,b'\0'*0x74);main=rng.choice(GE);n=i%5;subs=[rng.choice(GE) for j in range(n)];base=i%4
 u.w32(Gear+0x84,GE.index(main));u.wq(Gear+0x88,Subs);u.w32(Gear+0x90,4);u.w32(Gear+0x94,base);u.w32(Gear+0x98,n)
 for j,val in enumerate(subs):u.w32(Subs+((base+j)%4)*0x78+0x70,GE.index(val))
 exp=[0]*14;eb=0
 for val,ap in [(main,10)]+[(v,6 if main==108 else 3) for v in subs]:
  if 0<=val<14:exp[val]+=ap
  elif 100<=val<112:eb|=1<<(val-100)
 u.call(0x710266db4c,root,Gear);got=[u.rs32(P+0x3c+j*4) for j in range(14)];gb=u.r32(P+0xac);out['collector_cases']+=1
 if (got,gb)!=(exp,eb) and len(out['mismatch'])<10:out['mismatch'].append({'collector':i,'main':main,'subs':subs,'got':[got,gb],'expected':[exp,eb]})
# Full conditional aggregation; no dirty reload and optionalreplacement null.
def cv(a):return C[hex(a)]
for i in range(1700):
 main=[rng.randrange(0,35) for j in range(14)];old=[rng.randrange(0,22) for j in range(14)]
 for j in range(14):u.w32(P+0x3c+j*4,main[j]);u.w32(P+0x74+j*4,old[j])
 skill=rng.choice((0,1,2,8,3,9,11));frame=rng.choice((-1,0,1,1799,1800,3599,4000,rng.randrange(6000)));fr=max(frame,0)
 end=rng.choice((-2147483648,frame,frame+cv(0x71058c0398)-1,frame+cv(0x71058c0398),frame+5000));count=rng.choice((-5,0,cv(0x71058c03a0),cv(0x71058c039c),cv(0x71058c039c)+1,100));team=i%2
 gate=i%3!=0;active=i%13!=0;start=rng.choice((0,1,1800,4000));birth=rng.choice((-1,0,max(fr-10,0),max(fr-cv(0x71058c0368),0)));fwd=i%7==0;dbg=i%17==0;boost=rng.choice((0,fr,fr+1))
 u.w32(P+0xac,skill);u.w8(P+0x38,0);u.wq(P+0x168,0);u.w32(P+0x178,start);u.w32(Clock+0x148,frame);u.w32(Mgr+0x50,end);u.w32(A+0x668,team);u.w32(rows+(1 if team==0 else 0)*0x80+0x78,count)
 u.w8(0x71058e8774,gate);u.w8(0x71058e8778,0);u.w8(0x71058e87c8,active);u.w32(B+0xe54,birth);u.w32(Fwd+0xe94,fwd);u.w8(u.rq(0x7105795dd8)+0x1f,dbg);u.w32(B+0xa5a0,boost)
 exp=[0]*14 if active else old[:]
 if active:
  if skill&1 and gate and fr<start:
   for j,a in ((3,0x71058c038c),(4,0x71058c0390),(11,0x71058c0394)):exp[j]+=cv(a)
  if skill&2 and gate:
   remain=0x7ffff if end==-2147483648 else end-fr;fac=F(0 if remain>=cv(0x71058c0398) else 1)
   if count<=cv(0x71058c039c):fac=max(fac,min(F(1),F(F(cv(0x71058c039c)+1-count)/F(cv(0x71058c039c)+1-cv(0x71058c03a0)))))
   if fac>0:
    for j,a in ((0,0x71058c03a4),(1,0x71058c03a8),(2,0x71058c03ac)):exp[j]=int(F(F(fac*F(cv(a)))+F(exp[j])))
  if skill&8 and birth>=0 and fr<cv(0x71058c0368)+birth:
   for j,a in enumerate(range(0x71058c036c,0x71058c0384,4)):exp[j]+=cv(a)
  if fwd:
   for j,a in ((3,0x71058c035c),(4,0x71058c0360),(11,0x71058c0364)):exp[j]+=cv(a)
  if dbg or fr<boost:
   for j in (6,8,9,11,13):exp[j]+=cv(0x71058c0408)
   exp[3]=max(exp[3]+main[3],cv(0x71058c0400))-main[3];exp[4]=max(exp[4]+main[4],cv(0x71058c0404))-main[4]
 err=u.call(0x710265ca78,P);gotret=u.x(0);assert err is None,err;got=[u.rs32(P+0x74+j*4) for j in range(14)];eret=active and old!=exp;out['conditional_cases']+=1
 if got!=exp or bool(gotret)!=eret:
  if len(out['mismatch'])<10:out['mismatch'].append({'conditional':i,'in':[skill,frame,end,count,gate,active,start,birth,fwd,dbg,boost],'got':[got,gotret],'expected':[exp,eret]})
# Dirty rebuild through the full original function and all three gear collector calls.
Outfit=u.alloc(0x800);Subsets=[u.alloc(0x200) for _ in range(3)]
out['dirty_rebuild_cases']=0
for i in range(240):
 for j in range(14):u.w32(P+0x3c+4*j,rng.randrange(50));u.w32(P+0x74+4*j,rng.randrange(30))
 u.wq(P+0x30,Outfit);u.w8(P+0x38,1);u.wq(P+0x168,0);u.w8(0x71058e87c8,1);u.w8(0x71058e8774,0);u.w8(0x71058e8778,0)
 u.w32(B+0xe54,-1);u.w32(Fwd+0xe94,0);u.w32(B+0xa5a0,0);u.w8(u.rq(0x7105795dd8)+0x1f,0);u.w32(Clock+0x148,4000)
 exp=[0]*14
 for k,off in enumerate((0x100,0x308,0x510)):
  g=Outfit+off;main=rng.randrange(14);subs=[rng.randrange(14) for _ in range(3)];base=i%4
  u.w32(g+0x84,GE.index(main));u.wq(g+0x88,Subsets[k]);u.w32(g+0x90,4);u.w32(g+0x94,base);u.w32(g+0x98,3)
  exp[main]+=10
  for j,v in enumerate(subs):u.w32(Subsets[k]+((base+j)%4)*0x78+0x70,GE.index(v));exp[v]+=3
 err=u.call(0x710265ca78,P);assert err is None,err
 got=[u.rs32(P+0x3c+4*j) for j in range(14)];bonus=[u.rs32(P+0x74+4*j) for j in range(14)]
 out['dirty_rebuild_cases']+=1
 if got!=exp or bonus!=[0]*14 or u.r8(P+0x38)!=0:
  if len(out['mismatch'])<10:out['mismatch'].append({'dirty':i,'got':[got,bonus,u.r8(P+0x38)],'expected':exp})
# Original AP scene gate: negative bit-table indices force the exact string branch.
Scene=u.alloc(0x400);Name=u.alloc(64);u.wq(Scene+0x2e8,Name);u.w32(Scene+0x2f0,64);u.w32(Scene+0x224,-1)
u.w32(0x71058e90f0,-1);u.w8(0x71058e90f4,1)
out['scene_gate']=[]
for name in ('LobbyVersus','LobbyLocal','ShootingRange','LobbyVersus_GfxTest','LobbyCoop','World','Plaza','TestScene',''):
 m.mem_write(Name,name.encode()+b'\0'+b'\0'*(63-len(name)))
 err=u.call(0x7102b578e0,Scene);assert err is None,err
 got=bool(u.x(0));exp=name in ('LobbyVersus','LobbyLocal','ShootingRange');out['scene_gate'].append([name,got,exp])
 if got!=exp:out['mismatch'].append({'scene':name,'got':got,'expected':exp})
out.update(null_calls=u.null_calls,auto_pages=u.auto_pages,plt_stubbed=u.plt_stubbed)
Path('analysis/completion/r8/player_conditional_ap_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))



