"""New original26895c8 producer of B14c. Synthetic recorded launch path/base data.
Final flag setter3ae4c48 intercepted; nativebody/solver effects are excluded.
"""
import json,struct,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
from r6_player_uc import PUC
u=PUC();m=u.mu;C=u.alloc(0xd00);Beh=u.alloc(0x200);B=u.alloc(0xac80);A=u.alloc(0x180);PC=u.alloc(0xe400);P1=u.alloc(16);P2=u.alloc(0x60);GSM=u.alloc(0x80)
u.wq(C+0xc78,Beh);u.wq(Beh+0x108,B);u.wq(C+0xc70,A);u.wq(B+0xa690,PC);u.wq(PC+0xe3b8,P1);u.wq(P1+8,P2);u.wq(P2+0x40,GSM);u.w32(GSM+0x40,1)
count=[0]
def side(mu,a,sz,ud):count[0]+=1;mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
m.hook_add(UC_HOOK_CODE,side,begin=0x7103ae4c48,end=0x7103ae4c48)
F=lambda x:float(np.float32(x));bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
r=random.Random(26895);o={'scope':__doc__,'cases':0,'fields':0,'mismatch':[]}
for i in range(2800):
 active=i%7!=0;idx=r.choice((0,1,179,180,181,500));n=r.choice((0,idx,idx+1,idx+2,idx+15,idx+16,idx+17,1000));early=i%3==0
 base=[F(r.uniform(-2,2)) for _ in range(3)];target=[F(r.uniform(-2,2)) for _ in range(3)];path=[F(r.uniform(-2,2)) for _ in range(3)];normal=[F(r.uniform(-1,1)) for _ in range(3)];oldextra=[F(r.uniform(-1,1)) for _ in range(3)]
 dt=F(r.uniform(0,.04));t=F(r.uniform(0,2));total=F(r.choice((0,-1,r.uniform(.01,3))));gate=F(r.choice((0,.1,.5,1,2)))
 u.w8(C+0xb4,active);u.w32(C+0xb0,idx);u.w32(C+0xa8,n);u.w8(A+0x109,early);u.wf(C+0xa4,t);u.wf(C+0xc60,total);u.wf(C+0xc64,gate)
 for j in range(3):
  u.wf(C+0xc8+4*j,base[j]);u.wf(C+0xd4+4*j,target[j]);u.wf(C+0xe0+12*(idx if idx<181 else 0)+4*j,path[j]);u.wf(C+0x8c+4*j,normal[j]);u.wf(B+0x14c+4*j,oldextra[j]);u.wf(B+0x114+4*j,0);u.wf(B+0x120+4*j,0)
 u.wf(C+0x95c+4*(idx if idx<181 else 0),dt);u.wf(B+0x73c,0);u.w32(B+0x168,0)
 ended=active and not(idx+1<n and (idx+16<n or not early));nt=F(t+dt) if active else t;nb=[F(base[j]+F(F(target[j]-base[j])*F(.13))) for j in range(3)] if active else base[:]
 vel=[F(nb[j]+path[j]) for j in range(3)]
 if active:
  progress=1 if total<=0 else max(0,min(1,F(nt/total)))
  dot=F(F(F(vel[0]*normal[0])+F(vel[1]*normal[1]))+F(vel[2]*normal[2]))
  if progress<gate and dot<0:vel=[F(vel[j]-F(normal[j]*dot)) for j in range(3)]
 ex=([0]*3 if ended else vel if active else oldextra);nv=([oldextra[0],0,oldextra[2]] if ended else [0]*3);sy=oldextra[1] if ended else 0;timer=u.r32(0x71058bc1a0) if ended else 0
 err=u.call(0x71026895c8,C);assert err is None,err
 got=[u.r32(C+0xb0),u.r8(C+0xb4),u.r32(C+0xa4)]+[u.r32(C+0xc8+4*j) for j in range(3)]+[u.r32(B+0x14c+4*j) for j in range(3)]+[u.r32(B+0x114+4*j) for j in range(3)]+[u.r32(B+0x120+4*j) for j in range(3)]+[u.r32(B+0x73c),u.r32(B+0x168)]
 exp=[idx+1 if active else idx,0 if ended else int(active),bits(nt)]+[bits(v) for v in nb+ex+nv+nv]+[bits(sy),timer]
 o['cases']+=1;o['fields']+=len(got)
 if got!=exp and len(o['mismatch'])<5:o['mismatch'].append({'i':i,'got':got,'expected':exp,'in':[active,idx,n,early,t,total,gate]})
o.update(sideeffect_stub=count[0],null=u.null_calls,auto=u.auto_pages,plt=u.plt_stubbed)
Path('analysis/completion/r8/player_extra_launch_emu.json').write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(o,ensure_ascii=False))
