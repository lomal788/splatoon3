"""Original normal Main selector/getter→native actor writeback block; scene restart predicate.
No original, rendering, UI or runtime implementation files are modified.
"""
import struct,json,itertools,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STUB,STACK
B=0x7100000000
u=UC();mu=u.mu
p=u.alloc(0x160);rbc=u.alloc(0x40);wrapper=u.alloc(0x20);arr=u.alloc(0x10);entries=u.alloc(0x40);bind=u.alloc(0x40);mapping=u.alloc(0x20);body=u.alloc(0x300);actor=u.alloc(0x650);vt=u.alloc(0x20);out=u.alloc(0x80)
def ptr(a,v):mu.mem_write(a,struct.pack('<Q',v))
ptr(p+0x20,arr);ptr(arr,wrapper);ptr(wrapper+8,rbc);ptr(rbc+0x18,entries);ptr(entries+8,body);ptr(rbc+0x28,bind);ptr(p+0xf0,mapping);ptr(actor+0x4e0,vt);ptr(vt,STUB+0x400)
for a in [p+0x18,p+0xe8,rbc+0x10,rbc+0x20]:u.u32(a,1)
mu.mem_write(bind+4,b'\xff'*4)
case=0;rng=random.Random(88102)
for flags in [0,0x40,0x80,0xc0]:
 u.u32(body+0x88,flags)
 for _ in range(256):
  mat=struct.pack('<12f',*[rng.uniform(-100,100) for _ in range(12)]);vel=struct.pack('<6f',*[rng.uniform(-50,50) for _ in range(6)])
  mu.mem_write(body+0xd8,mat);mu.mem_write(body+0x138,vel)
  assert u.call(B+0x3a102f0,p,0)==body
  assert u.call(B+0x3a13a24,p,out,out+0x30,out+0x40,0,0)==1
  assert bytes(mu.mem_read(out,0x30))==mat
  assert bytes(mu.mem_read(out+0x30,12))==vel[:12] and bytes(mu.mem_read(out+0x40,12))==vel[12:]
  mu.mem_write(actor+0x28c,b'\xcc'*0x90)
  mu.reg_write(UC_ARM64_REG_SP,STACK+0xeff00);mu.reg_write(UC_ARM64_REG_X19,actor);mu.reg_write(UC_ARM64_REG_X27,p)
  mu.emu_start(B+0xf77420,B+0xf77730,count=10000)
  words=struct.unpack('<12I',mat);ref=struct.pack('<12I',words[3],words[7],words[11],words[0],words[1],words[2],words[4],words[5],words[6],words[8],words[9],words[10])
  assert bytes(mu.mem_read(actor+0x28c,48))==ref
  assert bytes(mu.mem_read(actor+0x2f8,24))==vel
  assert bytes(mu.mem_read(actor+0x310,24))==vel
  case+=1
# Selector rejection and controller binder conditions: input is deliberately synthetic.
reject=0
for slot,field,value in [(p,0xe8,0),(mapping,0,1),(mapping,4,1),(mapping,8,1)]:
 old=bytes(mu.mem_read(slot+field,4));u.u32(slot+field,value);assert u.call(B+0x3a102f0,p,0)==0;mu.mem_write(slot+field,old);reject+=1
u.u32(body+0x88,0x20);assert u.call(B+0x3a13a24,p,out,0,0,0,0)==0;reject+=1
u.u32(body+0x88,0x40);mu.mem_write(bind+4,b'\x00'*4);assert u.call(B+0x3a13a24,p,out,0,0,0,0)==0;reject+=1
Path('analysis/completion/r8/range_emu.json').write_text(json.dumps({'main_writeback':{'pass':case,'reject_pass':reject,'mismatch':0},'boundaries':['whole3a102f0/3a13a24 normal rigidbody branches and original0f77420..0f77500 writeback block execute','synthetic minimal physics map, body matrices and velocities; no Havok step or real runtime actor graph','native actor pose-cache callback at4e0.vt0 isolated asret; selector kind0/entry0 mapsbody0 as Main data','controller bone shorts-1; charcontroller specialbranch and missing-body fallback not executed']},indent=2)+'\n',encoding='utf-8')
# Restart direction gate: source scene helper and global state are synthetic.
u=UC();mu=u.mu
scene=u.alloc(0x400);root=u.alloc(0x200);set_=u.alloc(0x6600);plaza=u.alloc(0x100);groups=[u.alloc(0x9200) for _ in range(4)];name=u.alloc(0x80);prev=u.alloc(0x80)
ptr(B+0x58e42f8,root);ptr(root+0xc8,set_);ptr(B+0x582d908,plaza);ptr(scene+0x2e8,name);u.u32(scene+0x2f0,0x80);ptr(plaza+0x168,prev);u.u32(plaza+0x170,0x80)
for off,g in zip([0x6518,0x6528,0x6530,0x6538],groups):ptr(set_+off,g)
def hook(mu,pc,n,_):
 if pc==B+0x1323040:mu.reg_write(UC_ARM64_REG_X0,scene);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
mu.hook_add(UC_HOOK_CODE,hook);n=0
for current,origin,vs,co,loc,fromstate in itertools.product(['LobbyVersus','LobbyCoop','LobbyLocal','Plaza','Lobby','Unknown'],['LobbyVersus','LobbyCoop','LobbyLocal','BigWorld','SmallWorld','StaffRoll','Unknown'],[0,1],[0,1],[0,1,2],[0,2,4]):
 mu.mem_write(name,current.encode()+b'\0'* (0x80-len(current)));mu.mem_write(prev,origin.encode()+b'\0'*(0x80-len(origin)))
 for g,off,x in [(groups[0],0x30,fromstate),(groups[1],0x30,vs),(groups[2],0x30,co),(groups[3],0x34,loc)]:u.u32(g+off,x)
 if current=='LobbyVersus':exp=vs==1
 elif current=='LobbyCoop':exp=co==1
 elif current=='LobbyLocal':exp=loc in [1,2]
 elif current=='Plaza':exp=fromstate==2 and origin in ['LobbyVersus','LobbyCoop','LobbyLocal','BigWorld','SmallWorld','StaffRoll']
 else:exp=False
 got=u.call(B+0x27c95f0)&1
 assert got==int(exp),(current,origin,vs,co,loc,fromstate,got,exp)
 n+=1
Path('analysis/completion/r8/restart_emu.json').write_text(json.dumps({'pass':n,'mismatch':0,'boundaries':['original27c95f0→27c9190/27c9424 whole functions execute; scene singleton1323040stubbed','synthetic scene names/group states, no real Lby startup or full249cb60 restart function']},indent=2)+'\n',encoding='utf-8');print('Main',case,reject,'Restart',n,'PASS')
