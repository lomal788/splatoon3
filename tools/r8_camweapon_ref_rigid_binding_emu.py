"""r8: original RefRigidBody name lookup -> real body receiver pointer binding.
Runs completed receiver-binding block only, not whole DamageHelper constructor.
Physics body name getter3ae5a38 and iterator12ec7c0 are original, no callable stubs.
Supplied object/array/native-name tables follow original layouts; runtime name allocation excluded.
"""
from pathlib import Path
import json,random,struct
from r6_player_uc import PUC,BASE,STACK,STACK_SZ,UC_ARM64_REG_SP,UC_ARM64_REG_PC,UC_ARM64_REG_X0,UC_ARM64_REG_X9,UC_ARM64_REG_X18,UC_ARM64_REG_X29,UC_HOOK_CODE
u=PUC();mu=u.mu
name_reads=0;iter_hits=0;lookup_hits=0

def trace(mu,a,s,z):
 global name_reads,iter_hits,lookup_hits
 if a==BASE+0x3ae5a38:name_reads+=1
 elif a==BASE+0x12ec7c0:iter_hits+=1
 elif a==BASE+0x12ee210:lookup_hits+=1
for p in [0x3ae5a38,0x12ec7c0,0x12ee210]:mu.hook_add(UC_HOOK_CODE,trace,begin=BASE+p,end=BASE+p)

def txt(s):
 p=u.alloc(80);mu.mem_write(p,s.encode()+b'\0');return p

def setup(bnames,params,capacities,initial=None,direct_count=None):
 if direct_count is None:direct_count=len(bnames)
 H=u.alloc(0x400);err=u.call(BASE+0x1a7cd84,0);assert err is None,err;P=mu.reg_read(UC_ARM64_REG_X0);PC=u.alloc(0x130);L=u.alloc(0x30);bodyptr=u.alloc(8*max(1,len(bnames)))
 u.wq(H+0x1f0,P);u.wq(H+0x1f8,PC);u.wq(PC+0x10,L);u.w32(L+0x10,direct_count);u.wq(L+0x18,bodyptr)
 if direct_count<len(bnames):
  ctl=u.alloc(0x20);ctlarr=u.alloc(8);group=u.alloc(0x30);units=u.alloc(0x18*(len(bnames)-direct_count));u.w32(PC+0x18,1);u.wq(PC+0x20,ctlarr);u.wq(ctlarr,ctl);u.wq(ctl+8,group);u.w32(group+0x10,len(bnames)-direct_count);u.wq(group+0x18,units)
 u.w8(P+0xaa,1);u.w32(P+0x38,len(params));paramptr=u.alloc(8*max(1,len(params)));u.wq(P+0x40,paramptr)
 u.w32(H+0x50,len(params));receiver_nodes=u.alloc(8*max(1,len(params)));u.wq(H+0x58,receiver_nodes)
 receivers=[];receiver_names=[]
 for i,(rname,refs) in enumerate(params):
  err=u.call(BASE+0x1a82234,0);assert err is None,err;RP=mu.reg_read(UC_ARM64_REG_X0);u.wq(paramptr+8*i,RP);u.w8(RP+0xbc,1);u.w8(RP+0xbd,1);u.wq(RP+0x60,txt(rname));u.w32(RP+0xb4,len(refs));rp=u.alloc(8*max(1,len(refs)));u.wq(RP+0xa8,rp)
  for j,s in enumerate(refs):u.wq(rp+8*j,txt(s))
  column='Chariot' if rname=='Chariot' else 'Default';u.wq(RP+0x30,txt(column));u.w8(RP+0xbf,1);R=u.alloc(0x220);err=u.call(BASE+0x1a860f0,R,0,0,RP);assert err is None,err;assert u._cstr(u.rq(R+0xd0)).decode()==rname;assert u._cstr(u.rq(R+0x128)).decode()==column;N=u.alloc(0x60);u.wq(receiver_nodes+8*i,N);u.wq(N+8,txt(rname));u.w32(N+0x10,80);u.wq(N+0x58,R);receivers.append(R);receiver_names.append(rname)
 cell=u.alloc(8);mgr=u.alloc(0x130);world=u.alloc(0xe0);level=u.alloc(0xd0);level2=u.alloc(0xd0);names=u.alloc(8*max(1,len(bnames)))
 u.wq(BASE+0x57906f0,cell);u.wq(cell,mgr);u.wq(mgr+0xe8,world);u.wq(world+0xb8,level);u.wq(level+0xc0,level2);u.wq(level2+0xc0,names)
 bodies=[]
 for i,n in enumerate(bnames):
  B=u.alloc(0x300);D=u.alloc(0x40);meta=u.alloc(0x30);arr=u.alloc(8*max(1,capacities[i]));u.wq(B,BASE+(0x57468d8 if n=='Body' else 0x5749048));u.wq(B+0x90,D);u.wq(D+8,i);u.wq(names+8*i,meta);u.wq(meta+0x18,txt(n)|1);u.wq(bodyptr+8*i,B);
  if i>=direct_count:u.wq(units+0x18*(i-direct_count)+8,B)
  u.wq(B+0x248,arr);u.w32(B+0x244,capacities[i]);bodies.append(B)
  if initial:
   u.w32(B+0x240,len(initial[i]))
   for j,v in enumerate(initial[i]):u.wq(arr+8*j,v)
 return H,P,bodies,receivers,receiver_names

def run(bnames,params,capacities,initial=None,direct_count=None):
 H,P,bodies,receivers,rnames=setup(bnames,params,capacities,initial,direct_count);F=STACK+STACK_SZ-0x1000;mu.reg_write(UC_ARM64_REG_SP,F-0x100);mu.reg_write(UC_ARM64_REG_X29,F);mu.reg_write(UC_ARM64_REG_X9,H);mu.reg_write(UC_ARM64_REG_X18,H);u.wq(F-0x30,H)
 before=(name_reads,iter_hits,lookup_hits);mu.emu_start(BASE+0x1e3e120,BASE+0x1e3e29c,count=1000000)
 assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0x1e3e29c,hex(mu.reg_read(UC_ARM64_REG_PC))
 want=[list(z) for z in initial] if initial else [[] for _ in bodies]
 for ri,(rn,refs) in enumerate(params):
  targets=(range(len(bnames)) if not refs else [max([i for i,n in enumerate(bnames) if n==r],default=-1) for r in refs])
  # Name functor scans all bodies without early-out; duplicate body name selects last.
  bound=receivers[rnames.index(rn)]
  for bi in targets:
   if bi>=0 and len(want[bi])<capacities[bi]:want[bi].append(bound)
 actual=[]
 for B,w in zip(bodies,want):
  n=u.r32(B+0x240);got=[u.rq(u.rq(B+0x248)+8*j) for j in range(n)];assert got==w,(bnames,params,capacities,got,w);actual.append([rnames[receivers.index(x)] if x in receivers else hex(x) for x in got])
 assert not u.null_calls and not u.auto_pages and not u.faults,(u.null_calls,u.auto_pages,u.faults)
 return {'body_names':bnames,'direct_count':direct_count,'params':params,'bound_receiver_names':actual,'bound_rate_columns':[['Chariot' if z=='Chariot' else 'Default' for z in row] for row in actual],'calls_delta':[a-b for a,b in zip((name_reads,iter_hits,lookup_hits),before)]}

actualdata=json.loads(Path('extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json').read_text(encoding='utf8'))['GameParameters']['spl__DamageParam']['DamageReceiverArray']
phys=json.loads(Path('extracted/actor/SplPlayer/Phive/ControllerSetParam/SplPlayer.phive__ControllerSetParam.bgyml.json').read_text(encoding='utf8'))
bnames=[z['Name'] for z in phys['MatterRigidBodyNamePathAry']+phys['RigidBodyEntityNamePathAry']]
actual=run(bnames,[(z['Name'],z['RefRigidBody']) for z in actualdata],[8]*len(bnames),direct_count=1)
rng=random.Random(83714);cases=1
fixtures=[actual]
for k in range(1024):
 bn=rng.choices(['Body','ColBullet','ColBullet_CoopZombie','ColBullet_Chariot','日本語','Dup','dup'],k=rng.randrange(0,8));pa=[(rng.choice(['Main','Chariot','Main','Other','日本語']),rng.choices(bn+['Missing'],k=rng.randrange(0,7))) for _ in range(rng.randrange(0,5))];caps=[rng.randrange(0,9) for _ in bn]
 ini=[[0xAA00+i] if caps[i] and rng.randrange(2) else [] for i in range(len(bn))]
 out=run(bn,pa,caps,ini,direct_count=rng.randrange(len(bn)+1));cases+=1
 if k<10:fixtures.append(out)
result={'binding_block':'1e3e120..1e3e29c inside1e3d69c','original_calls':['38a94fc','12ec7c0','12ec970(empty)','12ee210','3ae5a38','1e45a64(empty binder)','1a82234(actual ReceiverParam factory)','1a860f0(original Receiver constructor reused)'],'cases':cases,'mismatches':0,'original_getname_calls':name_reads,'iterator_calls':iter_hits,'lookup_functor_calls':lookup_hits,'actual_SplPlayer':actual,'fixture':fixtures,'null_calls':u.null_calls,'auto_pages':u.auto_pages,'faults':u.faults,'plt_stubs':u.plt_stubbed,'boundary':'original1a7cd84/1a82234 params initialized and names/ref arrays supplied, original1a860f0 receiver constructor+Name/ratecolumn validated, Helper50/58 receiver name nodes supplied, Physics direct body list and controller unit18 records, native registered metadata name chain supplied; no callable stubs; actual body VT0=3ae5a38 uses id lower24bit and metadata18 tagged name; whole component factory/Phive world naming allocation/DamageRate calc excluded; Chariot binding data only, special behavior excluded'}
Path('analysis/completion/r8/ref_rigid_binding_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['fixture','boundary']},ensure_ascii=False))
