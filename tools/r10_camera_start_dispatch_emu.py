"""Original startup bridge0f57018->0ffd64c->Player slot15 2353a18.

Real bridge/Behavior VTs and empty Behavior component list.
Signal-subscription2352f88 and player setup2472c4c are capture boundaries.
Actor lifecycle0f73ecc/0f7400c/0f746b4 call edges are read separately, not
executed here with a real ActorSystem. No whole camera reset/scene proof.
"""
from pathlib import Path
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import PUC,BASE
u=PUC();m=u.mu
A=u.alloc(0x700);G=u.alloc(0x40);H=u.alloc(0x200);B=u.alloc(0xb000)
u.wq(G,BASE+0x553e788);u.wq(G+0x10,A);u.wq(G+0x20,H)
u.wq(H,BASE+0x5632b08);u.wq(H+0x108,B)
u.wq(H+0x30,H+0x30);u.wq(H+0x38,H+0x30)
for off,val in [(0xa690,0x12340000),(0xa8d0,0x12341000),(0xa878,0x12342000),(0xa658,0x12343000)]:u.wq(B+off,val)
calls=[];subscriptions=[]
def hook(mu,pc,n,_):
    if pc==BASE+0x2352f88:
        subscriptions.append(mu.reg_read(UC_ARM64_REG_X0))
        mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
    elif pc==BASE+0x2472c4c:
        sp=mu.reg_read(UC_ARM64_REG_SP)
        calls.append(dict(args=[mu.reg_read(globals()['UC_ARM64_REG_X'+str(k)]) for k in range(8)],stack=list(struct.unpack('<5Q',mu.mem_read(sp,40))),flag=mu.mem_read(sp+40,1)[0]))
        mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
m.hook_add(UC_HOOK_CODE,hook)
bad=[]
for i in range(1024):
    generation=[0,1,2,0xffffffff][i%4];flag=i%256
    u.w32(A+0x5cc,generation);u.w8(G+0x28,flag)
    u.call(BASE+0x0f57018,G,count=1000)
    exp=dict(args=[B+0xa5fc,0x12340000,0x12341000,B+0x10,0x12342000,B+0xb68,0x12343000,B+0x9218],stack=[B+0x678,B+0x9208,B+0xbd0,B+0xd58,B+0xf88],flag=int(generation<2))
    if calls[-1]!=exp or u.r8(G+0x28)!=(flag&254) or subscriptions[-1]!=H:bad.append(dict(i=i,got=calls[-1],expected=exp,bridgeFlag=u.r8(G+0x28)))
out=dict(scope=__doc__,cases=1024,mismatches=bad,signalBoundaryCalls=len(subscriptions),setupBoundaryCalls=len(calls),null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,fault=u.faults,plt=u.plt_stubbed)
p=Path('analysis/camera_100_r10/module/start_dispatch_emu.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out));raise SystemExit(bool(bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed))
