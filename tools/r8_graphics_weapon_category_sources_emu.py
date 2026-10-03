"""Four original animation WeaponCategory/Detail caller dataflow blocks, v0 ordinary Shooter. Full caller side effects not executed; actual native WeaponShooter slot230 is reused."""
import json,struct,random
from pathlib import Path
from r6_player_uc import PUC,STACK,STACK_SZ,RET_MAGIC
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from unicorn.arm64_const import *
u=PUC();p=u.alloc(0x100);a=u.alloc(0x80);b=u.alloc(0x80);weapon=u.alloc(0x20);u.wq(weapon,0x7105652468);sm=u.alloc(0x300);sp=STACK+STACK_SZ-0x10000;rng=random.Random(0x824477b4);bad=[];captures=[];null=[]
assert u.rq(0x7105652468+0x230)==0x710289bffc
stop_pc={0x7102491940,0x71024919c8,0x710249cfc8,0x71024bb524}
def stop(mu,addr,size,user):
 captures.append(dict(pc=hex(addr),cat=bytes(mu.mem_read(a,128)).split(b'\0')[0].decode(),detail=bytes(mu.mem_read(b,128)).split(b'\0')[0].decode(),x1=hex(mu.reg_read(UC_ARM64_REG_X1)),x2=hex(mu.reg_read(UC_ARM64_REG_X2))))
 mu.reg_write(UC_ARM64_REG_PC,RET_MAGIC)
for pc in stop_pc:u.mu.hook_add(UC_HOOK_CODE,stop,begin=pc,end=pc)
def read(mu,access,addr,size,value,user):
 if addr<0x400000:null.append(dict(addr=addr,pc=hex(mu.reg_read(UC_ARM64_REG_PC))));raise RuntimeError('null read')
u.mu.hook_add(UC_HOOK_MEM_READ,read)
labels=[('weapon-change',0x7102491900,0x7102491940),('weapon-clear',0x710249198c,0x71024919c8),('restart',0x710249cf84,0x710249cfc8),('transition',0x71024bb4ec,0x71024bb524)]
for label,start,end in labels:
 for i in range(256):
  cap1=[1,2,4,5,8,64][i%6];cap2=rng.randrange(1,65)
  u.mu.mem_write(p,bytes(0x100));u.mu.mem_write(a,b'Z'*128);u.mu.mem_write(b,b'Y'*128)
  u.wq(p+0x28,a);u.w32(p+0x30,cap1);u.wq(p+0x80,b);u.w32(p+0x88,cap2)
  u.mu.reg_write(UC_ARM64_REG_X0,weapon);u.mu.reg_write(UC_ARM64_REG_X26,p);u.mu.reg_write(UC_ARM64_REG_X27,sm);u.mu.reg_write(UC_ARM64_REG_X19,p)
  u.wq(sp+0x70,p);u.wq(sp+0x60,sm)
  error=u.call(start,sp=sp)
  cat=bytes(u.mu.mem_read(a,128)).split(b'\0')[0];detail=bytes(u.mu.mem_read(b,128)).split(b'\0')[0]
  want1=b'' if label=='weapon-clear' else b'Shtr'[:min(4,cap1-1)];want2=b'' if label=='weapon-clear' else b'Shtr'[:min(4,cap2-1)]
  if error or cat!=want1 or detail!=want2 or captures[-1]['pc']!=hex(end):bad.append(dict(label=label,i=i,cat=cat.hex(),detail=detail.hex(),wanted=[want1.hex(),want2.hex()],error=error))
out=dict(cases=len(captures),by_path={l:256 for l,_,_ in labels},mismatch=bad,samples=captures[:3]+[captures[256],captures[512],captures[768]],null_reads=null,null_calls=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__,boundary='Weapon object selected upstream is fixture; actual slot230/native string copy executed; stop before24477b4 sink/pop epilogue. Caller gates read separately.')
Path('analysis/completion/r8/graphics_weapon_category_sources_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False));assert not bad
