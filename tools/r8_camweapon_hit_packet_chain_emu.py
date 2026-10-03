"""Original BulletHitEffect16d99f4→direction/material helpers→16d9c60 packet→queue boundary.
Actual Shooter vtable208, actor wrapper78, HitEffector table reader, owner map execute.
"""
import json,struct,itertools,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC
B=0x7100000000;F=np.float32
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;u=self.u;self.helper=u.alloc(0x40);self.bullet=u.alloc(0x1300);self.spawn=u.alloc(0x100);self.actor=u.alloc(0x300);self.wrapper=u.alloc(0x10);self.contact=u.alloc(0x20);self.lst=u.alloc(0x100);self.nodes=[u.alloc(0x50) for _ in range(3)];self.recs=[u.alloc(0x10) for _ in range(3)];self.points=[u.alloc(0x80) for _ in range(3)];self.info=u.alloc(0x80);self.move=u.alloc(0x10);self.queue=u.alloc(0x100);self.manager=u.alloc(0x100);self.mvt=u.alloc(0x40);self.pm=u.alloc(0x100);self.scene=u.alloc(0x100);self.current=u.alloc(0x100);self.playerrows=u.alloc(0xa08);self.packets=[];self.fixture=[];self.paintmode='none';self.typed=u.alloc(0x240);self.tvt=u.alloc(0x40);self.pinfo=u.alloc(0x10);self.shape=u.alloc(0x100);self.svt=u.alloc(0x80);self.nativewrap=u.alloc(0x10);self.nvt=u.alloc(0x20);self.mat=u.alloc(0x10)
  self.ptr(self.helper+0x30,self.bullet);self.ptr(self.bullet,B+0x55a5030);self.ptr(self.bullet+0x108,self.spawn);self.ptr(self.bullet+0x170,self.wrapper);self.ptr(self.wrapper,B+0x5540810);self.ptr(self.wrapper+8,self.actor);self.ptr(self.contact+0x10,self.lst);u.u32(self.lst+0x54,0x28);self.ptr(self.lst+0x38,self.nodes[0]);self.ptr(self.lst+0x48,self.nodes[0]+0x28)
  for k in range(3):
   self.ptr(self.nodes[k],self.recs[k]);self.ptr(self.recs[k],self.points[k]);self.ptr(self.nodes[k]+0x28,self.lst+0x40 if k==0 else self.nodes[k-1]+0x28);self.ptr(self.nodes[k]+0x30,self.lst+0x40 if k==2 else self.nodes[k+1]+0x28)
  self.ptr(self.lst+0x40,self.nodes[2]+0x28)
  self.ptr(self.rp(B+0x5797f20),0);self.ptr(self.rp(B+0x5798618),self.queue);self.ptr(self.rp(B+0x57908b0),self.manager);self.ptr(self.manager,self.mvt);self.ptr(self.mvt+0x30,0x30000400);self.ptr(self.rp(B+0x5791bd0),self.pm);self.ptr(B+0x58e42f8,self.scene);self.ptr(self.scene+0xc8,self.current);self.ptr(self.current+0xa0,self.playerrows);u.u32(self.current+0xa8,1);u.u32(self.current+0xac,0);u.u32(self.current+0xb0,1);u.u32(self.playerrows+0x118,0)
  self.mu.mem_write(B+0x58e87ac,b'\0');self.mu.mem_write(B+0x58e8784,b'\0');self.mu.mem_write(B+0x5828210,b'\1');self.ptr(B+0x5828208,B+0x5576220);self.ptr(self.spawn+0x1c,1)
  rows=json.load(open('analysis/combat/rsdb/WeaponInfoMain.json',encoding='utf8'));row=next(r for r in rows if int(r['Id'])==40);assert row['DefaultHitEffectorType']=='Shooter' and not row['ExtraHitEffectorInfoSet']
  node=u.alloc(0x98);u.u32(node+0x20,40);self.mu.mem_write(node+0x28,struct.pack('<26I',*([1]*26)));holder=u.alloc(8);self.ptr(holder,node);table=u.alloc(0x200);self.ptr(table+0x118,holder);resource=u.alloc(0x40);items=u.alloc(13*0x28);u.u32(resource+0x10,13);self.ptr(resource+0x18,items);self.ptr(items+10*0x28+0x20,table);self.ptr(B+0x599b420,resource)
  self.ptr(self.typed,self.tvt);self.ptr(self.tvt+0x28,0x30000408);self.ptr(self.typed+0x28,self.shape);self.ptr(self.shape,self.svt);self.ptr(self.svt+0x10,0x30000410);self.ptr(self.svt+0x70,0x30000418);self.ptr(self.svt+0x18,0x30000420);self.ptr(self.nativewrap,self.nvt);self.ptr(self.nvt+0x10,0x30000428);self.ptr(B+0x58f07b8,0);self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def rp(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def ret(self,v=0):self.mu.reg_write(UC_ARM64_REG_X0,v);self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,m,pc,n,_):
  if pc==0x30000400:self.ret(0)
  elif pc==0x30000408:
   assert self.rp(m.reg_read(UC_ARM64_REG_X1))==B+0x5576220;self.ret(1)
  elif pc==0x30000410:self.ret(0)
  elif pc==0x30000418:self.ret(self.nativewrap)
  elif pc==0x30000420:self.ret(0 if self.paintmode=='kind3null' else self.mat)
  elif pc==0x30000428:self.ret(0)
  elif pc in [B+0x3e99fd0,B+0x3e99ff0]:self.ret()
  elif pc==B+0x27b4704:self.packets.append(bytes(m.mem_read(m.reg_read(UC_ARM64_REG_X1),0x58)));assert m.reg_read(UC_ARM64_REG_X0)==self.queue;self.ret()
 def one(self,res,mask,equal,rb,cache,critical,rng,paintmode='none'):
  u=self.u;self.packets=[];self.paintmode=paintmode;self.ptr(self.typed+0x230,0 if paintmode=='noinfo' else self.pinfo);u.u32(self.pinfo,0 if paintmode=='kind0' else 2);self.mu.mem_write(self.pinfo+4,struct.pack('<H',7));self.mu.mem_write(self.pinfo+7,b'\0' if paintmode=='disabled' else b'\1');self.mu.mem_write(self.mat+0xe,bytes([4 if paintmode=='flags4' else 251 if paintmode=='flags251' else 0]));self.mu.mem_write(self.info,b'\0'*0x80);u.u32(self.info,res);u.u32(self.info+4,0);u.u32(self.info+8,40);u.u32(self.info+0xc,17 if critical else 0);u.u32(self.info+0x1c,0x54321);u.u32(self.info+0x20,0x31415926);u.u32(self.info+0x30,0x13579);self.mu.mem_write(self.spawn+0x6d,b'\1')
  vec=[F(rng.uniform(-4,4)) for _ in range(3)];move=[F(rng.uniform(-2.2,2.2)) for _ in range(3)];self.mu.mem_write(self.info+0x10,struct.pack('<3f',*vec));self.mu.mem_write(self.move,struct.pack('<3f',*move))
  if cache:u.u32(self.info+0x10,0x7fc12345)
  data=[]
  for k,(node,rec,point) in enumerate(zip(self.nodes,self.recs,self.points)):
   self.mu.mem_write(node+8,bytes([0,0 if equal else 1]));self.mu.mem_write(rec+8,bytes([rb]));pos=[F(rng.uniform(-100,100)) for _ in range(3)];normal=[F(rng.uniform(-1,1)) for _ in range(3)];depth=F(rng.uniform(-3,3));cached=[F(rng.uniform(-1,1)) for _ in range(3)]
   self.mu.mem_write(point,struct.pack('<6f',*(pos+normal)));u.f32(point+0x30,depth);self.mu.mem_write(node+(0xc if equal else 0x18),struct.pack('<3f',*cached));self.mu.mem_write(point+0x68,bytes([2 if (mask>>k)&1 else 0]));u.u32(point+0x38,0x10000+k);u.u32(point+0x48,0x20000+k);self.ptr(point+0x70,0 if paintmode=='none' else self.typed);self.ptr(point+0x78,0 if paintmode=='none' else self.typed);data.append((pos,normal,depth,cached))
  try:u.call(B+0x16d99f4,self.helper,self.contact,self.move,self.info)
  except Exception:
   print('debug',hex(self.mu.reg_read(UC_ARM64_REG_PC)),[hex(self.mu.reg_read(z)) for z in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X8]],res,mask,equal,rb,cache);raise
  if not res:assert not self.packets;return 1
  assert len(self.packets)==1;packet=self.packets[0];sel=next((k for k in range(3) if (mask>>k)&1),0);pos,normal,depth,cached=data[sel];shift=(rb==equal);refpos=[F(F(depth*n)+p) if shift else p for p,n in zip(pos,normal)];direction=cached if cache else vec;material=(0x10000 if shift else 0x20000)+sel
  expected=[(0,struct.pack('<3f',*refpos)),(0xc,struct.pack('<3f',*direction)),(0x18,struct.pack('<3f',*move)),(0x24,struct.pack('<3I',material,res,1)),(0x30,struct.pack('<3I',0x31415926,0,0xffffffff)),(0x3c,bytes([paintmode in ['kind3null','flags0','flags251'],1,1])),(0x40,struct.pack('<I',0x54321)),(0x48,b'\0'*8),(0x50,struct.pack('<I',0x13579))]
  for off,v in expected:assert packet[off:off+len(v)]==v,(res,mask,equal,rb,cache,critical,hex(off),packet[off:off+len(v)].hex(),v.hex())
  if not any(z['result']==res and z['paintmode']==paintmode for z in self.fixture):self.fixture.append({'result':res,'mask':mask,'equal':equal,'wrapper_side':rb,'cached_direction':cache,'critical':critical,'paintmode':paintmode,'packet_hex':packet.hex(),'selected_contact':sel})
  return 1
r=Run();rng=random.Random(80169);cases=sum(r.one(*x,rng) for x in itertools.product(range(8),range(8),[0,1],[0,1],[0,1],[0,1]));basefixtures=r.fixture.copy();paintcases={};paintfixtures=[]
for mode in ['noinfo','disabled','kind0','kind3null','flags0','flags4','flags251']:
 r.fixture=[];paintcases[mode]=sum(r.one(*x,rng,paintmode=mode) for x in itertools.product([0,1,7],range(8),[0,1],[0,1],[0,1],[0,1]));paintfixtures.extend(r.fixture)
out={'original_hit_packet_chain':{'pass':cases,'mismatch':0},'paint_material_chain':{'pass_by_mode':paintcases,'mismatch':0},'paint_fixture':paintfixtures,'fixture':basefixtures,'fields':{'0':'position Vec3','0xc':'oriented/cached direction Vec3','0x18':'input movement direction Vec3','0x24':'material u32','0x28':'DamageResultType raw','0x2c':'HitEffectorType Shooter1','0x30':'info20','0x34':'owner local player number0','0x38':'-1','0x3c':'contact paintable;null/noinfo/disabled/kind0/flags4 false,kind3null/flags0/flags251 true','0x3d':'actual bullet vt208 true','0x3e':'SpawnInfo6d','0x40':'info1c','0x48':'refptr null','0x50':'info30'},'boundary':['16d99f4 whole→actual12d4f8c cached-direction→actual12d68cc(null body false)→16d9c60 whole→actual28fed18 Shooter40 data-node→actualBullet-vt2081649ba0 true/ActorWrapper-vt780f796ec→actual26437d0 one-player scene map→27b4704 capture','Synthetic finite contact points/list/material codes and cached oriented normals,valid Bullet/SpawnInfo/Actor records;no live Havok or ColPaint normal producer;typed body identity/native-material producer are boundaries','Actor ID resolver virtual method returns player index0;one-player SceneSetting ring injected;actualFocused dispatcher/controller/queue serialization are not executed here','Resource table40 copied from existing actual WeaponInfoMain data;prior r6 hiteffector36,900 proof reused,not rerun as new','Typed body RTTI vt28 is a true boundary stub;shape type/native-pointer/fallback material vtables are injected;mutex SDK stubs;actual12d68cc→12ed800→2c71e50(ObjPaint kind3,manager null)→12ac5e0(default material) execute;terrain kind2/live FieldRigidBody VT identity remain excluded','Result0 early returns before dereferencing contacts;other 7 results all queue. Vector metadata and optional refptr lifetime with nonnull refptr excluded']}
Path('analysis/completion/r8/hit_packet_chain_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['fixture','paint_fixture']}))
