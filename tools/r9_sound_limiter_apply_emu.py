"""NEW full four-kind limiter application, timers and original handle transitions.
Reuses previously read comparators; new coverage executes all 4 actual sorters + timer branches.
Only mutex OS calls are no-op. Original stop/pause/fade routines run; fixture handles have no DSP voice.
"""
import json,random,struct,functools
from pathlib import Path
from network_uc import UC,BASE,STUB,END
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];D=R/'analysis/completion/r9'
u=UC();m=u.mu;f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
q=lambda a:struct.unpack('<Q',m.mem_read(a,8))[0]
putq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
putb=lambda a,v:m.mem_write(a,bytes([v&255]))
raw=lambda a,n:bytes(m.mem_read(a,n))
null=[];fault=[];locks=0;calls={hex(x):0 for x in [0x37dfde4,0x37dfd10,0x37e019c,0x383da0c]}
def hook(mu,a,n,_):
 global locks
 locks+=1;mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
for a in [BASE+0x3e99fd0,BASE+0x3e99ff0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
def cnt(mu,a,n,_):calls[hex(a-BASE)]+=1
for k in calls:
 a=BASE+int(k,16);m.hook_add(UC_HOOK_CODE,cnt,begin=a,end=a)
def unknown(mu,a,n,_):
 if a!=END:raise RuntimeError('unregistered stub '+hex(a))
m.hook_add(UC_HOOK_CODE,unknown,begin=STUB,end=STUB+0xfff)
def invalid(mu,a,b,c,d,e):fault.append([a,hex(b),c]);return False
m.hook_add(UC_HOOK_MEM_INVALID,invalid)
def zero(mu,a,b,c,d,e):null.append([a,hex(b),c]);raise RuntimeError('null')
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,zero,begin=0,end=0xfff)
lim=u.alloc(0x40);lst=u.alloc(0x20);system=u.alloc(0x200);param=u.alloc(0x40)
putq(BASE+0x599a3f8,system);putq(system+0x10,param)
voices=[u.alloc(0x260) for _ in range(12)];handles=[u.alloc(0x80) for _ in range(12)];exts=[u.alloc(0x20) for _ in range(12)]
VTS={1:0x5734888,2:0x57348c8,3:0x5734908,4:0x5734948}
rng=random.Random(0x9a38473e8);bad=[];fields=0;timers=0;sorts=0;counts={k:0 for k in VTS};actions={'stop':0,'pause':0,'release':0,'ignore':0}
def priority(x,g,bit):
 other=x['bits']&~(1<<bit)
 if (g[0] and (x['state']&~1)==6) or (g[1] and other):return -1
 p=f(f(x['c4']*x['cc'])*x['fac'])
 if g[2] and x['bits'] and not other:p=f(p-1.)
 return int(f(p*255.))
def rawp(x):return int(f(f(f(x['c4']*x['cc'])*x['fac'])*255.))
def order(x,g,bit,inv):
 other=x['bits']&~(1<<bit)
 if (g[0] and (x['state']&~1)==6) or (g[1] and other):return -(1<<63)
 o=(~x['serial']&0xffffffff) if inv else x['serial']
 if g[2] and x['bits'] and not other:o-=0xffffffff
 return o
def compare(a,b,typ,g,bit):
 if typ<=2:
  d=priority(b,g,bit)-priority(a,g,bit)
  return d if d else (a['serial']-b['serial'] if typ==1 else b['serial']-a['serial'])
 oa=order(a,g,bit,typ==3);ob=order(b,g,bit,typ==3)
 return -1 if oa>ob else (1 if oa<ob else rawp(b)-rawp(a))
for case in range(4096):
 typ=case%4+1;n=rng.randint(1,12);limit=rng.choice([-1,0,1,2,4,n,n+1]);hard=rng.choice([False,True]);bit=rng.randrange(5);guard=rng.choice([False,True]);on=bool((case//4)%2)
 duration=f(rng.choice([0.,.016,.05,.2]));dt=f(rng.choice([0.,1/60.,1/30.,.1]));before=f(rng.choice([-1.,0.,.01,.04,.19,.2]));prior=rng.randrange(2)
 m.mem_write(lim,b'\0'*0x40);putq(lim,BASE+VTS[typ]);u.u32(lim+8,limit&0xffffffff);putb(lim+0xc,hard);putb(lim+0xd,guard);putb(lim+0xe,on);u.f32(lim+0x10,duration);u.u32(lim+0x14,bit);u.f32(lim+0x28,before);u.f32(param+0x1c,dt);putb(BASE+0x599aa88,prior)
 timer=before
 if not on:timer=-1.;active=False
 elif duration==0:timer=-1.;active=True
 else:
  if timer>=0:timer=f(timer+dt)
  if timer>=0 and timer>=duration:timer=-1.
  active=timer>=0
 g=[guard,guard,active]
 vs=[]
 for i in range(n):
  v,h,e=voices[i],handles[i],exts[i];m.mem_write(v,b'\0'*0x260);m.mem_write(h,b'\0'*0x80);m.mem_write(e,b'\0'*0x20)
  x={'v':v,'h':h,'state':rng.choice([1,2,3,4,6,7]),'bits':rng.choice([0,0,1<<bit,3,1<<(bit+1)]),'serial':i+1,'c4':f(rng.choice([.25,.5,.75,rng.uniform(.01,1)])),'cc':f(rng.uniform(.1,1.2)),'fac':f(rng.uniform(.2,1.)),'flag':rng.choice([0,0,0,2]),'kind':rng.choice([0,1,2]),'hstate':rng.choice([1,3,4]),'fade':f(rng.choice([0.,.016,.2]))}
  u.u32(v+4,x['state']);u.u32(v+8,x['serial']);putb(v+0xe,x['bits']);u.f32(v+0xc4,x['c4']);u.f32(v+0xcc,x['cc']);putq(v+0x210,e);u.f32(e+0x18,x['fac']);putb(v+0x1f8,x['flag']);putq(v+0xe0,h);u.u32(h+0x10,x['hstate']);u.u32(h+0x14,x['kind']);u.f32(h+0x1c,x['fade']);u.u32(h+0x24,0x55);putb(h+0x18,1)
  vs.append(x)
 rng.shuffle(vs);prev=lst
 for x in vs:
  node=x['v']+0x230;putq(prev+8,node);putq(node,prev);prev=node
 putq(prev+8,lst);putq(lst,prev);u.u32(lst+0x10,n);u.u32(lst+0x14,0x230)
 seq=sorted(vs,key=functools.cmp_to_key(lambda a,b:compare(a,b,typ,g,bit))) if limit>0 else vs
 u.call(BASE+0x38473e8,lim,lst);got=[];p=q(lst+8)
 while p!=lst:
  assert len(got)<13;got.append(p-0x230);p=q(p+8)
 if got!=[x['v'] for x in seq]:bad.append([case,'order',typ,got,[x['v'] for x in seq]])
 sorts+=limit>0;cntkeep=0
 for x in seq:
  eb=x['bits'];es=x['state'];hs=x['hstate'];cur=0x55;hb=1;c4=x['c4'];stop=False;pause=False;release=False
  if limit<0:release=(es&~1)!=6
  elif not (x['flag']&2):
   if limit>0 and cntkeep<limit:release=(es&~1)!=6
   elif x['kind']!=0 and (es&~1)!=6:
    if hard or x['kind']==1:stop=True
    else:pause=True
   if limit>0:cntkeep+=1
  if release:
   eb=x['bits']&~(1<<bit)
   if x['bits'] and not eb and hs==3:
    hs=4
    if x['kind']==2:cur=0
   actions['release']+=1
  elif stop:
   if es<=2:es=7;c4=0.;hs=0;cur=0;hb=0
   else:es=6;hs=0;cur=0;hb=0
   actions['stop']+=1
  elif pause:
   eb|=1<<bit
   if not x['bits']:
    if hs==4:hs=3
    elif hs==1:
     # Kind2 with no underlying voice only changes handle state1→3; cursor/18 stay.
     hs=3
   if on and not (x['bits']&(1<<bit)) and duration>0 and (eb&(1<<bit)):timer=0.
   actions['pause']+=1
  else:actions['ignore']+=1
  checks={x['v']+4:es,x['h']+0x10:hs,x['h']+0x24:cur,x['v']+0xc4:struct.unpack('<I',struct.pack('<f',c4))[0]}
  for a,w in checks.items():
   fields+=1
   if u.ru32(a)!=w:bad.append([case,hex(a),u.ru32(a),w,typ,hard,x])
  fields+=2
  if raw(x['v']+0xe,1)!=bytes([eb&255]):bad.append([case,'bits',typ,x,eb])
  if raw(x['h']+0x18,1)!=bytes([hb]):bad.append([case,'h18',typ,x,hb])
 fields+=2;timers+=1
 if raw(lim+0x28,4)!=struct.pack('<f',timer):bad.append([case,'timer',u.rf32(lim+0x28),timer])
 if raw(lim+0x18,1)!=bytes([int(active)]):bad.append([case,'active'])
 assert m.reg_read(UC_ARM64_REG_PC)==END
 counts[typ]+=1
res={'cases':sum(counts.values()),'kind_cases':counts,'checked_fields':fields,'timer_cases':timers,'sort_cases':sorts,'native_calls':calls,'actions':actions,'mismatch':len(bad),'bad':bad[:10],'null':null,'fault':fault,'auto_map':0,'boundary':['mutex Lock/Unlock OS PLT singlethread no-op','fixture handle+8=null: no DSP voice; original stop/pause/fade functions execute','voice ownerD8=null so no owner removal callbacks'],'new_coverage':['allfour native sorter→whole38473e8','timer0/positive/expiry/reset and0/1/60/1/30/.1 inputdt','native383cffc/383d940/383da0c→37dfde4/37dfd10/37e019c']}
(D/'sound_limiter_apply_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(res,ensure_ascii=False));assert not bad and not null and not fault
