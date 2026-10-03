"""New original controller raw-mask converter + edge producer pipeline.
Original3587e3c -> original3d563ec -> original3586bcc. Synthetic node RTTI true only;
SDK-buffer data is injected, no hardware or SDK GetNpadStates execution claimed.
New scene-name writer2b55abc..c14 is an original instruction block.
"""
import json,random,struct
from pathlib import Path
from r6_player_uc import PUC,RET_MAGIC,STACK,STACK_SZ
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
u=PUC();m=u.mu;C=u.alloc(0x200);Module=u.alloc(0x200);Node=u.alloc(0x200);NV=u.alloc(0x60);RT=u.alloc(16)
m.mem_write(RT,bytes.fromhex('20008052c0035fd6'))
u.wq(NV,RT);u.wq(Node,NV);u.w32(Node+0x18,13);u.w32(Module+0x174,0x20);u.wq(Module+0x168,Node+0x20);u.wq(Node+0x28,Module+0x160)
u.wq(C,0x71057608a0);u.wq(C+0x140,Module);u.wq(C+0x150,C+0x148);u.wq(C+0x168,C+0x160);u.w32(C+0x178,0);u.w32(C+0x104,-1);u.w32(C+0x108,-1);u.w32(C+0x100,0);u.w8(0x71058c4700,1)
R=random.Random(563);out={'scope':__doc__,'pipeline_cases':0,'fields':0,'mismatch':[]};Map={0:[0],1:[1],2:[3],3:[4],4:[7],5:[6],6:[13],7:[14],8:[2],9:[5],10:[10,11],11:[9,12],12:[18],13:[16],14:[19],15:[17]}
def convert(v):
 o=0
 for k,vs in Map.items():
  if v&(1<<k):
   for q in vs:o|=1<<q
 return o
for i in range(2800):
 style=i%3;raw=(1<<(i%16)) if i<48 else R.getrandbits(16);old=convert(R.getrandbits(16))
 u.w32(Node+0x30,style);u.w8(C+0x17d,style);u.w8(C+0x17c,0);u.w8(C+0x139,0);u.w32(C+0x114,old);u.wq(Node+0x58,100+i);u.wq(Node+0x60,raw)
 for q in (0x68,0x6c,0x70,0x74):u.w32(Node+q,0)
 u.w32(Node+0x78,1)
 err=u.call(0x7103587e3c,C);assert err is None,err
 want=convert(raw);got=[u.r32(C+0x114),u.r32(C+8),u.r32(C+0xc),u.r32(C+0x13c)];exp=[want,want&~old,old&~want,old]
 out['pipeline_cases']+=1;out['fields']+=4
 if got!=exp and len(out['mismatch'])<10:out['mismatch'].append({'i':i,'style':style,'raw':raw,'got':got,'expected':exp})
Scene=u.alloc(0x400);Name=u.alloc(64);u.wq(Scene+0x2e8,Name);u.w32(Scene+0x2f0,64)
stop={0x7102b55c14}
def hk(mu,a,z,d):
 if a in stop:mu.reg_write(UC_ARM64_REG_PC,RET_MAGIC)
m.hook_add(UC_HOOK_CODE,hk);out['scene_writer']=[]
for name in ('LobbyVersus','LobbyVersus_GfxTest','LobbyCoop','LobbyLocal','ShootingRange','World','Plaza','Lobby',''):
 m.mem_write(Name,name.encode()+b'\0'*(64-len(name)));u.w8(0x71058e87ac,123)
 m.reg_write(UC_ARM64_REG_SP,STACK+STACK_SZ-0x10000);m.reg_write(UC_ARM64_REG_X19,Scene);m.reg_write(UC_ARM64_REG_X26,1024);m.reg_write(UC_ARM64_REG_X8,Name+64);m.reg_write(UC_ARM64_REG_LR,RET_MAGIC)
 m.emu_start(0x7102b55abc,RET_MAGIC,count=10000);assert m.reg_read(UC_ARM64_REG_PC)==RET_MAGIC
 got=u.r8(0x71058e87ac);want=int(name in ('LobbyVersus','LobbyVersus_GfxTest','LobbyCoop','LobbyLocal'));out['scene_writer'].append([name,got,want])
 if got!=want:out['mismatch'].append({'scene':name,'got':got,'expected':want})
out.update(null=u.null_calls,auto=u.auto_pages,plt=u.plt_stubbed)
Path('analysis/completion/r8/player_pad_pipeline_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
