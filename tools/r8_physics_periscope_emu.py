"""New Periscope state names, request receiver and gravity predicate input.
Synthetic actor/type-message/config/time. Original game-state machine executes;
enter/exec/exit callbacks are intercepted (camera/resource/actor-message effects excluded).
"""
import json,random,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
from r6_player_uc import PUC
u=PUC();m=u.mu;C=u.alloc(0x140);Ctx=u.alloc(0x40);Beh=u.alloc(0x200);B=u.alloc(0xac80);SM=u.alloc(0x300);D=u.alloc(0x100);Cfg=u.alloc(0xc0);DT=u.alloc(16)
u.wq(C+0x130,Beh);u.wq(Beh+0x108,B);u.wq(B+0xa8c8,SM);u.wq(B+0xa880,D);u.wq(C+0x138,Cfg);u.wq(C+0x28,0);u.wq(Cfg+16,0)
err=u.call(0x710266f18c,C,Ctx);assert err is None,err
names=[]
for i in range(4):
 p=u.rq(u.rq(C+0x70)+i*8);s=bytes(m.mem_read(p,32)).split(b'\0')[0].decode();names.append(s)
callbacks=[0x710266f780,0x710266f914,0x710266f918,0x710266f9b0,0x710266fcbc,0x710266fd4c,0x710266fd8c,0x710266fe1c,0x710266feb4,0x71026701e0]
seen={};rt={'ok':1}
FAKE=u.alloc(16);m.mem_write(FAKE,struct.pack('<II',0x52800020,0xd65f03c0))
def ret(v=0):m.reg_write(UC_ARM64_REG_X0,v);m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def hook(mu,a,sz,ud):
 seen[hex(a)]=seen.get(hex(a),0)+1
 if a==0x7103d987c0:ret(DT)
 elif a==FAKE:ret(rt['ok'])
 else:ret(0)
for a in callbacks+[0x7103d987c0,FAKE]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
u.w32(DT,0x3f800000);u.w8(Cfg+0xa8,1);u.w8(Cfg+0xac,1)
out={'scope':__doc__,'names':names,'state_cases':0,'receiver_cases':0,'mismatch':[]}
r=random.Random(26703)
for i in range(800):
 phase=i%4;body=r.choice((0x85,0x87,0x89,0x56,0x60,0x99));squid=body in (0x85,0x87,0x89);pending=i%3==0;warp=i%17==0;t=r.choice((0,1,29,30,31,59,60,61,120));ext=r.choice((0,.5,1));shrink=r.choice((0,.5,1))
 u.w32(C+0x38,phase);u.wf(C+0x3c,t);u.w32(C+0x40,phase);u.w8(C+0x50,0);u.w8(C+0x51,0);u.w8(C+0xb0,pending);u.w32(SM+0xc8,body);u.w32(D+0x30,1 if warp else 0);u.wf(Cfg+0x94,ext);u.wf(Cfg+0xa4,shrink)
 eff=0 if warp and phase!=0 else phase;pend=pending;exp=eff
 if eff==0 and pend:exp=1;pend=False
 elif eff==1 and (not squid):exp=3
 elif eff==1 and float(struct.unpack('<f',struct.pack('<f',t*(1/60)))[0])>=ext:exp=2
 elif eff==2 and not squid:exp=3
 elif eff==3 and float(struct.unpack('<f',struct.pack('<f',t*(1/60)))[0])>=shrink:exp=0
 err=u.call(0x71026703b4,C);assert err is None,err;got=(u.rs32(C+0x38),bool(u.r8(C+0xb0)));out['state_cases']+=1
 if got!=(exp,pend):out['mismatch'].append({'i':i,'in':[phase,body,pending,warp,t,ext,shrink],'got':got,'expected':[exp,pend]})
Msg=u.alloc(0x30);Payload=u.alloc(0xd8);VT=u.alloc(0x80);u.wq(Payload,VT);u.wq(VT+0x40,FAKE);u.w8(u.rq(0x710579ed18),1);u.wq(Payload+0xb8,0);u.w32(Payload+0xc0,-1);u.wq(C+0x80,0);u.w32(C+0x88,-1)
for i in range(240):
 goodid=i%3!=0;ptr=i%5!=0;rt['ok']=i%7!=0;u.w32(Msg+4,0x8536a00 if goodid else 0);u.wq(Msg+0x10,Payload if ptr else 0);u.w8(C+0xb0,0)
 vals=[r.getrandbits(32) for _ in range(4)]
 for j,v in enumerate(vals):u.w32(Payload+0xc8+4*j,v);u.w32(C+0xa0+4*j,0)
 err=u.call(0x7102427830,C,Msg);assert err is None,err;gotret=bool(u.x(0));ok=goodid and ptr and bool(rt['ok']);got=(u.r8(C+0xb0),[u.r32(C+0xa0+4*j) for j in range(4)])
 out['receiver_cases']+=1
 if gotret!=ok or got!=(int(ok),vals if ok else [0]*4):out['mismatch'].append({'receiver':i,'got':[gotret,got],'expected':[ok,[int(ok),vals if ok else [0]*4]]})
out.update(callback_stubs=seen,null=u.null_calls,auto=u.auto_pages,plt=u.plt_stubbed)
Path('analysis/completion/r8/physics_periscope_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
