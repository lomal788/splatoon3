"""Original WeaponFreeParam identity, ShotGuideFrame metadata, and predictor step input."""
import json,struct,itertools,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STACK
B=0x7100000000
u=UC();mu=u.mu
I=u.alloc(0x180);handle=u.alloc(0x10);parent_handle=u.alloc(0x10);reader=u.alloc(0x10);reader_vt=u.alloc(0x10)
allocated=[];seen=[]
def ptr(a,v):mu.mem_write(a,struct.pack('<Q',v))
def rp(a):return struct.unpack('<Q',mu.mem_read(a,8))[0]
def cstr(a):
 b=bytearray()
 while mu.mem_read(a,1)!=b'\0':b+=mu.mem_read(a,1);a+=1
 return b.decode('utf-8')
def ret(v):mu.reg_write(UC_ARM64_REG_X0,v);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def hook(mu,pc,n,_):
 if pc==B+0x083d2f0:
  p=u.alloc(mu.reg_read(UC_ARM64_REG_X0),fill=b'\xa5');allocated.append(p);ret(p)
 if pc==0x30000600:
  a=mu.reg_read(UC_ARM64_REG_X1);wrapper=rp(a+0x28)
  seen.append({'key':cstr(rp(a)),'rtti':hex(rp(a+8)),'flag':rp(a+0x10),'index':u.ru32(a+0x18),'object':rp(a+0x20),'wrapperVT':hex(rp(wrapper)),'value':rp(wrapper+8),'default':u.ru32(rp(a+0x30))})
  ret(1)
mu.hook_add(UC_HOOK_CODE,hook)
ptr(B+0x59975c0,0)
for g,p in [(0x58bd9e0,0x58bd9d8),(0x58009e8,0x58009e0),(0x58005a0,0x5800598),(0x58005b0,0x58005a8)]:
 mu.mem_write(B+g,b'\1');ptr(B+p,B+0x555cdc0 if p==0x58bd9d8 else B+0x553d070)
ptr(reader,reader_vt);ptr(reader_vt,0x30000600)
factory_count=0
for j in range(64):
 p=u.call(B+0x27f3f64,0);factory_count+=1
 assert rp(p)==B+0x564b668 and u.ru32(p+0x30)==8 and mu.mem_read(p+0x34,1)==b'\0'
 assert cstr(u.call(B+0x27f4670))=='spl__WeaponFreeParam'
 assert u.call(B+0x27f4338,p,B+0x58bd9d8)==1
 assert u.call(B+0x27f4338,p,B+0x58122a0)==0 # FadeType is a different RTTI singleton despite shared metadata VT.
 seen.clear();assert u.call(B+0x27f4018,p,reader)==1
 assert seen==[{'key':'ShotGuideFrame','rtti':hex(B+0x58bd9d8),'flag':p+0x34,'index':0,'object':p,'wrapperVT':hex(B+0x553d560),'value':p+0x30,'default':8}],seen
P=u.call(B+0x27f3f64,0);Q=u.call(B+0x27f3f64,0)
ptr(handle,P);u.u32(handle+0xc,17);ptr(I+0x40,handle);u.u32(I+0x48,17)
ptr(parent_handle,Q);u.u32(parent_handle+0xc,29);ptr(P+0x10,1);ptr(P+0x18,parent_handle)
rng=random.Random(20261003);vals=[0,1,8,31,60,255,0xffffffff,0x7fffffff]+[rng.getrandbits(32) for _ in range(56)]
step_count=0
for own_flag,parent_flag,parent_valid in itertools.product([0,1],[0,1],[0,1]):
 for value in vals:
  u.u32(P+0x30,value);u.u32(Q+0x30,value^0xa5a5a5a5);mu.mem_write(P+0x34,bytes([own_flag]));mu.mem_write(Q+0x34,bytes([parent_flag]));u.u32(P+0x20,29 if parent_valid else 28)
  mu.reg_write(UC_ARM64_REG_X19,I);mu.reg_write(UC_ARM64_REG_SP,STACK+0xe0000);mu.reg_write(UC_ARM64_REG_X29,STACK+0xe0000+0x140)
  mu.emu_start(B+0x25490c0,B+0x2549230,count=20000)
  expected=(value^0xa5a5a5a5) if not own_flag and parent_valid else value
  assert u.ru32(STACK+0xe0000+0x88)==expected,(own_flag,parent_flag,parent_valid,value,u.ru32(STACK+0xe0000+0x88),expected)
  step_count+=1
out={'factory_metadata_identity':{'pass':factory_count,'mismatch':0},'original_step_consumer':{'pass':step_count,'mismatch':0},'key':'ShotGuideFrame','type':'spl__WeaponFreeParam','value_offset':'0x30','flag_offset':'0x34','default':8,'rtti_singleton':'0x71058bd9d8','boundary':['original27f3f64 factory/getName27f4670/RTTI27f4338/metadata reader27f4018 execute; only allocator and metadata lookup callback intercepted','original25490c0..2549230 including actual RTTI and parent handle inheritance execute; synthetic valid I40 handle and parent records supplied','not full2548c3c,175779c trajectory,actual I40 writer,resource loading,or Havok query; default8 is factory default,not proof of all runtime overrides']}
Path('analysis/completion/r8/shotguide_param_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
