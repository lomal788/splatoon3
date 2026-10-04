"""Original Fade temporal step/type1/type2/cache epsilon, independent f32 bit comparisons.
Synthetic finite state/input fixtures, original vtables. No math function stub.
Model-null cache tests prove epsilon/cache only, not renderer material upload.
"""
import json, random, struct
from pathlib import Path
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_S0
from r6_player_uc import PUC
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/camera_100_r10/boom'
u=PUC();F=u.alloc(0xb8);I=u.alloc(0x40);rng=random.Random(20261003)
f=np.float32
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def i32(n):return n-(1<<32) if n&(1<<31) else n
def temporal(n,N,flags):
 n&=0xffffffff
 if flags&2:n=max(min(i32(n),N)-1,0) if i32(n)>0 else 0
 elif flags&1:n=min((n+1)&0xffffffff,(N-1)&0xffffffff)
 q=f(f(i32(n))/f(N-1));return n, f(max(0.,min(q,1.)))
def norm(a,order=(0,1,2)):
 ss=f(f(f(a[order[0]]*a[order[0]])+f(a[order[1]]*a[order[1]]))+f(a[order[2]]*a[order[2]]));r=f(np.sqrt(ss))
 return [f(x*f(1/r)) for x in a] if r>0 else a
def geom1(cam,at,obj,r,n,N):
 d=norm([f(cam[k]-at[k]) for k in range(3)],(2,0,1));a=[f(obj[k]-at[k]) for k in range(3)]
 c=[f(f(a[2]*d[1])-f(a[1]*d[2])),f(f(a[0]*d[2])-f(a[2]*d[0])),f(f(a[1]*d[0])-f(a[0]*d[1]))]
 dist=f(np.sqrt(f(f(f(c[2]*c[2])+f(c[0]*c[0]))+f(c[1]*c[1]))))
 dirxz=norm([f(at[0]-cam[0]),f(0),f(at[2]-cam[2])]);oxz=norm([f(obj[0]-cam[0]),f(0),f(obj[2]-cam[2])])
 dot=f(f(f(dirxz[2]*oxz[2])+f(dirxz[1]*oxz[1]))+f(dirxz[0]*oxz[0]))
 flags=2 if max(-1,min(dot,1))>0 else 1
 nn,t=temporal(n,N,flags);x=f(f(dist-r)/f(-.55));near=f(1) if x<0 else f(f(1)-f(min(x,1)))
 return nn,flags,f(max(0,min(f(near+t),1)))
bad=[];counts={};samples={}
def compare(kind,j,got,exp,extra=None):
 counts[kind]=counts.get(kind,0)+1
 if got!=exp:bad.append(dict(kind=kind,case=j,got=got,expected=exp,extra=extra))
 if j<3:samples.setdefault(kind,[]).append(dict(got=got,expected=exp,extra=extra))
for j in range(10000):
 N=rng.choice((10,20,25,30));n=rng.randrange(-3,10005);flags=rng.randrange(256)
 u.w32(F+0x20,n);u.w32(F+0x9c,N);u.w8(F+0x90,flags)
 err=u.call(0x71010aff88,F);nn,v=temporal(n,N,flags)
 compare('temporal',j,[err,u.r32(F+0x20),u.mu.reg_read(UC_ARM64_REG_S0)],[None,nn,bits(v)],dict(N=N,n=n,flags=flags))
u.wq(F,0x710555d0f8)
for j in range(4096):
 N=10;n=rng.randrange(0,15);minimum=f(rng.uniform(0,1));on=rng.randrange(2)
 u.w32(F+0x20,n);u.w32(F+0x9c,N);u.w8(F+0x90,0xa4);u.wf(I+0x1c,minimum);u.w8(I+0x21,on)
 err=u.call(0x71010b0300,F,I);flags=1 if on else 2;nn,v=temporal(n,N,flags)
 compare('type2',j,[err,u.r32(F+0x20),u.r8(F+0x90),u.mu.reg_read(UC_ARM64_REG_S0)],[None,nn,0xa4|flags,bits(f(max(minimum,v)))])
u.wq(F,0x710555d070)
for j in range(4096):
 cam=[f(rng.uniform(-20,20)) for _ in range(3)];at=[f(rng.uniform(-20,20)) for _ in range(3)];obj=[f(rng.uniform(-20,20)) for _ in range(3)];r=f(rng.uniform(.1,4));n=rng.randrange(31)
 u.mu.mem_write(I,struct.pack('<6f',*cam,*at));u.mu.mem_write(F+0x34,struct.pack('<3f',*obj));u.wf(F+0x24,r);u.w32(F+0x20,n);u.w32(F+0x9c,30);u.w8(F+0x90,0xa4)
 err=u.call(0x71010afff4,F,I);nn,flags,v=geom1(cam,at,obj,r,n,30)
 compare('type1',j,[err,u.r32(F+0x20),u.r8(F+0x90),u.mu.reg_read(UC_ARM64_REG_S0)],[None,nn,0xa4|flags,bits(v)],dict(cam=[float(x) for x in cam],at=[float(x) for x in at],obj=[float(x) for x in obj],r=float(r),n=n))
u.wq(F+8,0);u.wq(F+0x10,0)
for j in range(4096):
 old=f(rng.uniform(0,1));alpha=f(old+f(rng.choice((0,1,-1,2,-2))*f(2**-23))) if j%2 else f(rng.uniform(0,1));nativeflag=j%2
 u.wf(F+0x94,old);u.w8(F+0x98,nativeflag);err=u.call(0x71010afabc,F,fargs=(float(alpha),))
 expected=old if abs(f(alpha-old))<=f(2**-23) else alpha
 compare('cacheOnly',j,[err,u.r32(F+0x94)],[None,bits(expected)])
out=dict(scope=__doc__,counts=counts,fields=sum(counts.values()),mismatch_count=len(bad),mismatches=bad[:32],samples=samples,null={str(k):v for k,v in u.null_calls.items()},null_writes={hex(k):v for k,v in u.null_writes.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used)
OUT.mkdir(parents=True,exist_ok=True);(OUT/'fade_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ('counts','mismatch_count','null','auto','faults','plt','libm')},ensure_ascii=False));print(json.dumps(bad[:2],ensure_ascii=False))
