"""r9 new live PlayerCamera snapshot factory/publish/swap and actor reader proof.
Originalsnapshot RTTI runs; only malloc and handle/thread resolution are boundaries.
"""
from pathlib import Path
import json,random,struct
from network_uc import UC,BASE,END
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
e=UC();m=e.mu
C=e.alloc(0x1978);Own=e.alloc(0x1978);Beh=e.alloc(0x200);Ctx=e.alloc(0x500);Actor=e.alloc(0x400);Arr=e.alloc(0x200);Slot=e.alloc(0x40);Arg=e.alloc(0x30);Handle=e.alloc(0x90);P=e.alloc(0x18)
def w(a,f,*v):m.mem_write(a,struct.pack('<'+f,*v))
def r(a,f):return struct.unpack('<'+f,m.mem_read(a,struct.calcsize('<'+f)))
w(BASE+0x59975c0,'Q',0);w(BASE+0x59a37c8,'Q',Ctx)
w(C+0x1968,'Q',Beh);w(Beh+0xe8,'QQ',Beh+0xe8,Beh+0xe8);w(Beh+0xfc,'i',8)
w(Actor+0x200,'I',25);w(Actor+0x208,'Q',Arr);w(Arr+24*8,'Q',Slot);w(Slot+0x20,'Q',Beh);w(P,'Q',Actor)
w(BASE+0x58bc548,'B',1);w(BASE+0x5802440,'B',1)
w(Own+0x16a0,'Q',Handle);w(Own+0x16a8,'I',71);w(Handle+0x80,'Q',Actor);w(Handle+0x88,'I',71);w(Actor+0x24,'I',6)
bound={};fault=[];null=[]
def ret(v=None):
 if v is not None:m.reg_write(UC_ARM64_REG_X0,v)
 m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def hook(mu,pc,n,_):
 if pc==BASE+0x083d2f0:
  bound['malloc']=bound.get('malloc',0)+1;ret(e.alloc(mu.reg_read(UC_ARM64_REG_X0)))
 elif pc==BASE+0x3c88280:bound['thread_valid']=bound.get('thread_valid',0)+1;ret(1)
 elif pc==BASE+0x10ad4b8:
  bound['handle_lookup']=bound.get('handle_lookup',0)+1;w(mu.reg_read(UC_ARM64_REG_X8),'QQ',Actor,0);ret()
 elif pc==0:null.append(1);raise RuntimeError('null call')
def bad(mu,access,a,size,value,_):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),address=hex(a)));return False
m.hook_add(UC_HOOK_CODE,hook);m.hook_add(UC_HOOK_MEM_INVALID,bad)
assert e.call(BASE+0x24e6184,C,Arg)==1
S=r(Beh+0xf0,'Q')[0]-8
assert r(S,'Q')[0]==BASE+0x5633a90 and r(Beh+0xf8,'I')[0]==1
assert r(Beh+0xe8,'QQ')==(S+8,S+8) and r(S+8,'QQ')==(Beh+0xe8,Beh+0xe8)
# Opposite write/read buffer selections, both invalid context sentinels and valid phases.
contexts=[a | (b<<8) | (c<<16) for a in [0,1,2,3] for b in [0,1,2,254] for c in [0,1,254]]
rng=random.Random(249000);cases=reads=swaps=selections=copyfields=0
maskparts=[(0,0x2d),(0x30,0x45),(0x48,0x4c)]
for n in range(1024):
 ctx=contexts[n%len(contexts)];w(Ctx+0x4c8,'I',ctx)
 a=ctx&255;b=(ctx>>8)&255;c=(ctx>>16)&255;special=a==2 and b!=254 and c!=254 and (b==0 or (b==1 and c==0))
 dst=S+(0x18 if special else 0x6c);src=S+(0x6c if special else 0x18)
 m.mem_write(S+0x18,b'\xaa'*0xa8);w(S+0xc0,'2B',0,0)
 raw=rng.randbytes(0x4c);death=n%2;mode=(n%4)-2;progress=rng.getrandbits(32)
 m.mem_write(C+0x88,raw);w(C+0x16ec,'B',death);w(C+0x1878,'i',mode);w(C+0x16e0,'I',progress)
 e.call(BASE+0x24dffd8,C)
 assert r(dst,'2B')==(death,int(mode!=0));assert r(dst+4,'I')[0]==progress
 out=bytes(m.mem_read(dst+8,0x4c));want=bytearray(b'\xaa'*0x4c)
 for lo,hi in maskparts:want[lo:hi]=raw[lo:hi]
 assert out==want,(n,'publish')
 assert r(S+0xc0,'2B')==(1,0) if special else r(S+0xc0,'2B')==(0,1)
 before=e.call(BASE+0x2676548,P);assert before==src;reads+=1
 m.reg_write(UC_ARM64_REG_SP,0x100ef000);m.reg_write(UC_ARM64_REG_X0,Beh)
 m.emu_start(BASE+(0x0ffdb6c if special else 0x0ffdaa4),BASE+(0x0ffdbc8 if special else 0x0ffdb00),count=1000)
 assert m.reg_read(UC_ARM64_REG_PC)==BASE+(0x0ffdbc8 if special else 0x0ffdb00)
 assert r(S+0xc0,'2B')==(0,0)
 # pose copy is selected chunks; padding remains inherited, not a memcpy promise
 got=bytes(m.mem_read(src+8,0x4c));want2=bytearray(b'\xaa'*0x4c)
 for lo,hi in maskparts:want2[lo:hi]=raw[lo:hi]
 assert got==want2,(n,'swap');assert r(src,'2B')==(death,int(mode!=0));assert r(src+4,'I')[0]==progress
 selected=e.call(BASE+0x2676548,P);assert selected==src;reads+=1;swaps+=1
 # Original main replacement copy with actor reader supplied as packet on stack.
 SP=0x100ef000;m.reg_write(UC_ARM64_REG_SP,SP);m.reg_write(UC_ARM64_REG_X19,Own);w(SP+0x90,'QQ',Actor,0)
 m.mem_write(Own+0xd4,b'\x55'*0x4c)
 m.emu_start(BASE+0x24df8bc,BASE+0x24df94c,count=1000);assert m.reg_read(UC_ARM64_REG_PC)==BASE+0x24df94c
 expected=bytearray(b'\x55'*0x4c)
 if death:
  for lo,hi in maskparts:expected[lo:hi]=raw[lo:hi]
 assert bytes(m.mem_read(Own+0xd4,0x4c))==expected,(n,'maincopy');copyfields+=1
 ptr=e.call(BASE+0x24e50c0,Own);assert ptr==Own+(0xd4 if death else 0x88);selections+=1;cases+=1
# exact reset leaves pose data untouched, disabled swap is no-op
reset=0
for values in [0,1,255]:
 m.mem_write(S+0x18,b'\xf3'*0xa8);w(S+0x18,'2B',values,values);w(S+0x6c,'2B',values,values)
 old=bytes(m.mem_read(S+0x20,0x4c));e.call(BASE+0x24e7004,S)
 assert r(S+0x18,'2B')==(0,0) and r(S+0x1c,'I')==(0,) and r(S+0x6c,'2B')==(0,0) and r(S+0x70,'I')==(0,)
 assert bytes(m.mem_read(S+0x20,0x4c))==old;reset+=1
out=dict(factory_cases=1,publish_cases=cases,contexts=contexts,reader_cases=reads,swap_cases=swaps,main_alternate_copy_cases=copyfields,getter_selection_cases=selections,reset_cases=reset,mismatches=0,faults=fault,null_calls=len(null),auto_pages=0,stubs=bound,boundaries=['Original constructor24e6184 alloc0xc8 and intrusive list; malloc only boundary','Original RTTI24e6e48,24dffd8,actualBehaviorListDispatch0ffdaa4/0ffdb6c to24e7018/7070,2676548 execute with supplied frame context and random pose bytes','Original main replacement block24df8bc..24df94c; complete24d9ae8 not run','Original24e50c0 uses handle lookup10ad4b8 suppliedActor and3c88280 returnsThreadValid=1; handle generation/state validation runs, but thread scheduling and atomic handle ownership are not executed','Original snapshot/type/value proof, not actual solo death event or renderer/posture/presentation'])
Path('analysis/completion/r9/camera_snapshot_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))