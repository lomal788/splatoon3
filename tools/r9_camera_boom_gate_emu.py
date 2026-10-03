"""r9 new original boom position-write gate and subsequent native-pose blend.
Finite synthetic block inputs; collision/actor scheduler/complete frame not executed.
"""
import json,random,struct
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,STACK
from unicorn.arm64_const import *
F=np.float32
def f(x):return F(x)
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
def sqrt(x):return F(np.sqrt(F(x)))
def bits(x):return struct.pack('<f',x).hex()
u=PUC();m=u.mu;C=u.alloc(0x2000);B=u.alloc(0xb000);BH=u.alloc(0x200);P=u.alloc(0x20);SP=STACK+0x3d0000;FP=SP+0x1000
u.wq(C+0x1968,BH);u.wq(BH+0x108,B);u.wq(C+0x60,P)
def vec(p,v):m.mem_write(p,struct.pack('<3f',*v))
def readv(p):return struct.unpack('<3f',m.mem_read(p,12))
def run(lo,hi):
 m.reg_write(UC_ARM64_REG_X19,C);m.reg_write(UC_ARM64_REG_SP,SP);m.reg_write(UC_ARM64_REG_X29,FP);m.emu_start(lo,hi,count=1000)
rng=random.Random(0x9dee);bad=[];cases=2048;fields=0;samples=[]
for i in range(cases):
 old=[F(rng.uniform(-8,8)) for _ in range(3)];native=[F(rng.uniform(-8,8)) for _ in range(3)];at=[F(rng.uniform(-8,8)) for _ in range(3)];pivot=[F(rng.uniform(-2,2)) for _ in range(3)];direction=[F(rng.uniform(-1,1)) for _ in range(3)]
 ratio=F(rng.uniform(.1,1));length=F(rng.uniform(1,6));height=F(rng.uniform(-.2,.2));blend=F(rng.uniform(0,1));de0=(i%8)-3
 vec(P,old);vec(C+0x1770,native);vec(C+0x177c,at);vec(FP-0x68,direction);vec(FP-0x58,pivot);u.wf(FP-0x88,height);u.wf(C+0x14c4,ratio);u.wf(C+0x14cc,length);u.wf(C+0x1760,blend);u.w32(B+0xde0,de0)
 m.reg_write(UC_ARM64_REG_S9,0);m.reg_write(UC_ARM64_REG_S3,0)
 expected=list(old)
 if de0<1:
  distance=mul(ratio,length);expected=[add(mul(direction[j],distance),pivot[j]) for j in range(3)]
  dy=F(abs(sub(native[1],pivot[1])));nd=sqrt(add(mul(sub(pivot[0],native[0]),sub(pivot[0],native[0])),mul(sub(pivot[2],native[2]),sub(pivot[2],native[2]))));hd=sqrt(add(mul(sub(pivot[0],expected[0]),sub(pivot[0],expected[0])),mul(sub(pivot[2],expected[2]),sub(pivot[2],expected[2]))))
  expected[1]=sub(expected[1],div(mul(sub(add(height,dy),dy),sub(nd,hd)),nd))
 run(0x71024dee54,0x71024def74);got=list(readv(P));gotat=list(readv(C+0x70));fields+=6
 if [bits(x) for x in got+gotat]!=[bits(x) for x in expected+at]:bad.append(dict(i=i,phase='gate',de0=de0,got=got,expected=expected))
 # At correction was a separate previous block. This tests exact next blend consumer.
 expected2=[add(expected[j],mul(blend,sub(native[j],expected[j]))) for j in range(3)];run(0x71024df060,0x71024df0fc);got2=list(readv(P));fields+=6
 if [bits(x) for x in got2+list(readv(C+0x70))]!=[bits(x) for x in expected2+at]:bad.append(dict(i=i,phase='blend',got=got2,expected=expected2))
 if i<3:samples.append(dict(de0=de0,entry=old,native=native,after=got,blend=float(blend),final=got2))
out=dict(scope=__doc__,cases=cases,skip_cases=1024,apply_cases=1024,fields=fields,mismatches=bad,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,limits=['captured entry output is preserved when de0>=1; earlier producer and final corrections are read separately','finite synthetic position/at values, no full camera/world frame'])
Path('analysis/completion/r9/camera_boom_gate_emu.json').write_text(json.dumps(out,default=float,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['samples','scope','limits']},default=float))