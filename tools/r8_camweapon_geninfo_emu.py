"""r8: original Shooter primary VT55→common generation info owner/team binder."""
import struct,json,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STACK
B=0x7100000000
u=UC();mu=u.mu
I=u.alloc(0x300);W=u.alloc(0x700);Beh=u.alloc(0x200);body=u.alloc(0xb000);actor=u.alloc(0x900);rec=u.alloc(0x110);info=u.alloc(0x260);pr=u.alloc(0x100);handle=u.alloc(0x10);pvt=u.alloc(0x10)
def ptr(a,v):mu.mem_write(a,struct.pack('<Q',v))
def rp(a):return struct.unpack('<Q',mu.mem_read(a,8))[0]
def ret(v=None):
 if v is not None:mu.reg_write(UC_ARM64_REG_X0,v)
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
entered=[]
def hook(mu,pc,n,_):
 if pc==B+0x146cb20:mu.mem_write(mu.reg_read(UC_ARM64_REG_X0),struct.pack('<I',0x1234));ret()
 if pc==0x30000600:ret(1)
 if pc==B+0x2865f18:entered.append('WeaponShooter71ret')
mu.hook_add(UC_HOOK_CODE,hook)
ptr(I,B+0x56376a0);ptr(I+0x38,W);ptr(I+0x2c0,Beh);ptr(W,B+0x5652468);ptr(Beh+0x108,body);ptr(body+8,actor);ptr(actor+0x348,rec);ptr(rp(B+0x57908b0),0);ptr(I+0x48,handle);ptr(handle,pr);u.u32(handle+0xc,17);u.u32(I+0x50,17);ptr(pr,pvt);ptr(pvt,0x30000600);mu.mem_write(pr+0x9c,b'\1');mu.mem_write(rp(B+0x5797ef0),b'\1')
n=0
for team,owner in itertools.product([-1,0,1,2,3,4], [0,1]):
 for old in range(16):
  mu.mem_write(info,b'\xa5'*0x260);u.u32(info+0x2c,old);ptr(I+0x2c0,Beh if owner else 0);u.u32(actor+0x668,team);entered.clear();u.call(B+0x258801c,I,info)
  assert u.ru32(info+0x2c)==(team&0xffffffff if owner else old);assert entered==['WeaponShooter71ret'];n+=1
# Actual conditional generation writer, with original TripleShotSpanFrame predicate. This is a local output-field block only.
nc=0
for span,shot,cnt in itertools.product([0,1,2,6],[-1,0,99],[1,2,3,257]):
 mu.mem_write(info,b'\0'*0x260);u.u32(info+0x94,0xffffffff);mu.mem_write(info+0x91,b'\0\1');u.u32(pr+0x80,span);u.u32(I+0x9c,shot);u.u32(I+0x80,cnt);ptr(I+0x38,0)
 mu.reg_write(UC_ARM64_REG_X21,I);mu.reg_write(UC_ARM64_REG_X19,info);mu.reg_write(UC_ARM64_REG_SP,STACK+0xe0000);mu.emu_start(B+0x25827d8,B+0x25827fc,count=5000)
 assert u.ru32(info+0x94)==(shot&0xffffffff if span>0 else 0xffffffff);assert bytes(mu.mem_read(info+0x91,2))==bytes([0,cnt&255 if span>0 else 1]);nc+=1
out={'owner_team_binder':{'pass':n,'mismatch':0},'triple_span_writer':{'pass':nc,'mismatch':0},'boundaries':['original258801c→2552da0 and actual WeaponShooter primaryVT+238 ret execute, actorID pack146cb20 stub only','conditional25827d8..27fc→2580354 original executes, synthetic generation-valid normal WeaponParam; RTTI true stub; I38null excludes variable parameter branch','SpawnInfo constructor defaults statically read from25817c8; full shot function/resource table loader/copy/pool excluded']}
Path('analysis/completion/r8/weapon_geninfo_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
