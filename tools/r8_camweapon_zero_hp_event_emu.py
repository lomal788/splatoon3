"""Original empty DamageParam→DamageHelper init gate→receiver callback.
Peer-count getter/NetRef buffer RTTI are boundary supplies;serialization excluded.
"""
import struct,json,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC
B=0x7100000000
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.args=self.u.alloc(0x40);self.listener=self.u.alloc(0x30);self.name=self.u.alloc(0x20);self.str=self.u.alloc(0x40);self.result=self.u.alloc(0x20);self.info=self.u.alloc(0x80);self.sender=self.u.alloc(0x80);self.tree=self.u.alloc(0x50);self.net=self.u.alloc(0xc0);self.actor=self.u.alloc(0x300);self.owner=self.u.alloc(0x80);self.buf=self.u.alloc(0x80);self.bvt=self.u.alloc(0x90);self.gmanager=self.u.alloc(0xd00);self.gmode=self.u.alloc(0x40);self.session=self.u.alloc(0x80);self.peer=self.u.alloc(0x40);self.pvt=self.u.alloc(0x90);self.phase='create';self.calls=[];self.peer_count=1
  self.ptr(self.rp(B+0x578ff50),0);self.mu.mem_write(self.rp(B+0x5799078),b'\1');self.ptr(self.rp(B+0x5799080),B+0x555cdc0);self.mu.mem_write(self.rp(B+0x5790da0),b'\1');self.ptr(self.rp(B+0x5790da8),B+0x553d6c0);self.ptr(self.rp(B+0x5790d88),self.gmanager);self.ptr(self.gmanager+0xc70,self.gmode);self.mu.mem_write(self.gmode+0x14,b'\1');self.ptr(self.rp(B+0x5790be8),self.session);self.ptr(self.session+0x58,self.peer);self.ptr(self.peer,self.pvt);self.ptr(self.pvt+0x48,0x30000410);self.ptr(self.buf,self.bvt);self.ptr(self.bvt,0x30000418);self.ptr(self.owner+0x60,self.buf);self.ptr(self.net+0x10,self.actor);self.ptr(self.net+0x30,self.owner);self.mu.mem_write(self.net+0x2c,b'\1');self.u.u32(self.net+0x48,3)
  self.mu.mem_write(self.str,b'Main\0');self.ptr(self.name+8,self.str);self.u.u32(self.name+0x10,64);self.ptr(self.listener+0x10,self.name);self.ptr(self.sender,B+0x55bdfd0);self.ptr(self.tree+0x20,self.str);self.u.u32(self.tree+0x28,0);self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def rp(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def ret(self,v=0):self.mu.reg_write(UC_ARM64_REG_X0,v);self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,m,pc,n,_):
  self.calls.append(pc)
  if pc==B+0x083d2f0:self.ret(self.u.alloc(m.reg_read(UC_ARM64_REG_X0),b'\xcd'))
  elif pc==B+0x3e99f10:
   a=m.reg_read(UC_ARM64_REG_X0);sz=m.reg_read(UC_ARM64_REG_X2);m.mem_write(a,bytes([m.reg_read(UC_ARM64_REG_X1)&255])*sz);self.ret(a)
  elif pc==0x30000410:self.ret(self.peer_count)
  elif pc==0x30000418:self.ret(1)
  elif self.phase=='prefix' and pc==B+0x1e3da1c:m.emu_stop()
  elif self.phase=='dc' and pc==B+0x1e3e054:m.emu_stop()
  elif self.phase=='event' and pc==B+0x1e45654:m.emu_stop() # serializer boundary after actual peer gate
 def create(self):
  self.phase='create';self.P=self.u.call(B+0x1a7cd84,0);self.H=self.u.call(B+0x1e3d53c,0);assert self.rp(self.P)==B+0x55c8e50;assert self.u.ru32(self.P+0x88)==0 and self.rp(self.P+0x98)==0;assert self.mu.mem_read(self.P+0xa8,1)==b'\0';assert self.u.call(B+0x1a7d4b4,self.P,self.rp(B+0x5799080))==1;assert self.u.call(B+0x38b6944,self.P+0x80)==0;assert self.u.ru32(self.H+0x30)==0 and self.rp(self.H+0x38)==0
  self.ptr(self.H+0x1f0,self.P);self.phase='prefix';self.u.call(B+0x1e3d69c,self.H,self.args);assert self.u.ru32(self.H+0x30)==0 and self.rp(self.H+0x38)==0
 def dc(self,initial,present):
  self.ptr(self.H+0x208,self.net if present else 0);self.mu.mem_write(self.H+0xdc,bytes([initial]));self.phase='dc';self.u.call(B+0x1e3e03c,self.H);assert self.mu.mem_read(self.H+0xdc,1)==bytes([bool(initial and present)])
 def event(self,initial,present,peer,dmg):
  self.dc(initial,present);self.phase='event';self.calls=[];self.peer_count=peer;self.ptr(self.listener+8,self.H);self.ptr(self.H+0x98,self.tree);self.mu.mem_write(self.result,b'\0'*0x20);self.u.u32(self.result+4,6);self.mu.mem_write(self.info,b'\0'*0x80);self.u.u32(self.info,dmg);self.u.u32(self.info+8,1);self.u.call(B+0x1e4476c,self.listener,self.result,self.info,self.sender)
  assert self.mu.mem_read(self.result+8,1)==b'\1';selected=B+0x1e44e0c in self.calls;peer_called=0x30000410 in self.calls;send_boundary=B+0x1e45654 in self.calls;want=bool(initial and present and dmg>0)
  assert selected==want and peer_called==want and send_boundary==bool(want and peer>=2),(initial,present,peer,dmg,selected,peer_called,send_boundary)
  return {'initial_dc':initial,'netref_present':present,'peer':peer,'damage':dmg,'single_event_constructed':selected,'peer_gate_reached':peer_called,'serializer_boundary':send_boundary,'result8':1}
r=Run();r.create();rows=[r.event(*a) for a in itertools.product([0,1],[0,1],[0,1,2],[0,1,360])]
data=json.load(open('extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json',encoding='utf-8'));dp=data['GameParameters']['spl__DamageParam'];assert 'HitPointHolderArray' not in dp and '$parent' not in dp and '$parent' not in data;assert all(not z['RefHitPointHolder'] for z in dp['DamageReceiverArray'])
out={'original_empty_param_helper':{'pass':1,'mismatch':0,'param_factory':'1a7cd84','actual_rtti':'1a7d4b4','actual_count':'38b6944','helper_factory':'1e3d53c','init_prefix':'1e3d69c→1e3da1c','helper_hp_count':0},'original_zero_hp_callback':{'pass':len(rows),'mismatch':0},'rows':rows,'data':{'file':'extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json','type':dp['$type'],'HitPointHolderArray':'missing,originalfactoryempty','RefHitPointHolder':{z['Name']:z['RefHitPointHolder'] for z in dp['DamageReceiverArray']}},'boundary':['Original entire receiver listener with H30=0,H38=null,H1e8=0/H e0 listeners0/H98 Mainmask0, sender actualmode0,knockback0 and attackerID1.','NetRef is synthetic valid record;peer getter0/1/2 and buffer RTTItrue are explicit supplies;final serialization stops at1e45654,notnetwork transmission proof.','Actual1e3e03c..e054 gate dc=(H208!=null)&&previousdc;dc0 ornetrefnull never constructs event;peer1 constructs single AttackEvent packet then returns before serializer.','DamageParam actualfactory/rtti/count andHelperfactory/initHPprefix execute;generic BYML loader andfullcomponentinit omitted. Raw GPT absence+constructor count0 are data+originaldefault proof,notinvented HP.','HP0 is not a send blocker;the later ldr[x22+30] is NetRef+30,not HelperHPCount30. Nonzero knockback and authority modes0/1/2 are source-read but not executed here;mode3 is validfixture boundary.']}
Path('analysis/completion/r8/zero_hp_event_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False))
