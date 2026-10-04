"""r10 original CameraModule whole update + device projection.

Synthetic Spectator output, viewport, and device posture are explicit inputs.
Actual VT56467f8 callbacks, whole1010150,1017434,LookAt,Perspective and
device-matrix3589b48 execute. SDK trig is routed to original SDK instructions.
No shakes, pose transition, listener/resource backend or GPU. Draw-context
aspect fields are synthetic and tested separately after projection updates.
These results do not establish the live Lby device posture or full game frame.
"""
import json, random, struct, sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE
from r5_player_libm_emu import Sdk, bits

F = np.float32
OUT = Path('analysis/camera_100_r10/module')
OUT.mkdir(parents=True, exist_ok=True)
def add(a,b): return F(F(a)+F(b))
def mul(a,b): return F(F(a)*F(b))
def sub(a,b): return F(F(a)-F(b))
def div(a,b): return F(F(a)/F(b))
def fbits(v): return struct.unpack('<I',struct.pack('<f',float(v)))[0]
def floats(b): return list(struct.unpack('<'+str(len(b)//4)+'f',b))

sdk=Sdk()
trig={BASE+0x3e9be40:'sinf',BASE+0x3e9be30:'cosf',BASE+0x3e9c1f0:'tanf'}
calls={}
class NativePUC(PUC):
    def _plt(self,mu,pc,n,opaque):
        if pc in trig:
            v=struct.unpack('<f',struct.pack('<I',mu.reg_read(UC_ARM64_REG_S0)&0xffffffff))[0]
            name=trig[pc];calls[name]=calls.get(name,0)+1
            mu.reg_write(UC_ARM64_REG_S0,sdk.call(name,v))
            mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
        else:super()._plt(mu,pc,n,opaque)
u=NativePUC();m=u.mu
M=u.alloc(0x400); S=u.alloc(0x760); V=u.alloc(0x60)
u.wq(S+0x288,BASE+0x56467f8); u.wq(S+0x290,S)
rng=random.Random(0x1010150); failures=[]; fields=0; traces=[]
def projected(n,f,angle,aspect,ox,oy):
    half=mul(angle,.5)
    tan=struct.unpack('<f',struct.pack('<I',sdk.call('tanf',half)))[0]
    h=mul(add(n,n),tan); w=mul(h,aspect)
    offset=mul(w,ox); left=sub(offset,mul(w,.5));right=add(mul(w,.5),offset)
    offset=mul(h,oy); bottom=sub(offset,mul(h,.5));top=add(mul(h,.5),offset)
    rw=div(1,sub(right,left));rh=div(1,sub(top,bottom));rd=div(1,sub(f,n))
    return [mul(add(n,n),rw),F(0),mul(add(right,left),rw),F(0),
            F(0),mul(rh,add(n,n)),mul(add(top,bottom),rh),F(0),
            F(0),F(0),mul(rd,F(-add(f,n))),mul(rd,mul(mul(f,-2),n)),
            F(0),F(0),F(-1),F(0)]
def device(p,k,zs,zo):
    a=list(map(F,p));r=a[:]
    if k==1:r[:4]=a[4:8];r[4:8]=[F(-v) for v in a[:4]]
    elif k==2:r[:4]=[F(-v) for v in a[4:8]];r[4:8]=a[:4]
    elif k==3:r[:8]=[F(-v) for v in a[:8]]
    elif k==4:r[:4]=[F(-v) for v in a[:4]]
    elif k==5:r[4:8]=[F(-v) for v in a[4:8]]
    r[8]=mul(zs,a[8]);r[9]=mul(zs,a[9])
    r[10]=mul(zs,add(a[10],mul(zo,a[14])))
    r[11]=add(mul(zs,a[11]),mul(zo,a[15]))
    return r

# Standalone whole device transform: arbitrary finite 4x4 matrix, all cases,
# unsupported posture values follow native default (no XY adjustment).
P=u.alloc(0xc0);A=u.alloc(64);D=u.alloc(64); device_bad=[]
for i in range(4096):
    a=[F(rng.uniform(-20,20)) for _ in range(16)]
    k=[0,1,2,3,4,5,6,0xffffffff][i%8]
    zs=F(rng.uniform(-2,2));zo=F(rng.uniform(-2,2))
    u.wf(P+0x90,zs);u.wf(P+0x94,zo);m.mem_write(A,struct.pack('<16f',*a))
    u.call(BASE+0x3589b48,P,D,A,k,count=200)
    got=bytes(m.mem_read(D,64));exp=struct.pack('<16f',*device(a,k,zs,zo))
    if got!=exp:device_bad.append(dict(i=i,posture=k,got=got.hex(),expected=exp.hex()))

# Original whole Module update. The aspect written at the end becomes input
# to the next update; valid is only set by non-null viewport in this branch.
for i in range(1024):
    m.mem_write(M,b'\0'*0x400)
    u.wq(M+0x120,S+0x288);u.wq(M+0x190,BASE+0x5721238);u.wq(M+0x220,BASE+0x57213b8)
    u.w8(M+0x228,1);u.w8(M+0x229,1)
    n=F(rng.uniform(.05,.4));far=F(rng.uniform(100,2500));angle=F(rng.uniform(.4,1.5))
    oldaspect=F(rng.uniform(.7,2.5));ox=F(rng.uniform(-.2,.2));oy=F(rng.uniform(-.2,.2))
    k=i%6;zs=F(rng.uniform(.5,1.5));zo=F(rng.uniform(-.2,.2))
    for off,val in [(0x2d0,oldaspect),(0x2d4,ox),(0x2d8,oy),(0x2b0,zs),(0x2b4,zo)]:u.wf(M+off,val)
    u.w32(M+0x2ac,k)
    pose=bytearray(0x4c)
    pos=[F(rng.uniform(-30,30)) for _ in range(3)]
    # Identity rotation allows independent verification of LookAt's exact basis.
    struct.pack_into('<11f',pose,0,*pos,0,0,0,1,n,far,angle,1)
    pose[0x2c]=0
    m.mem_write(S+0x2fc,bytes(pose))
    have=i%2;u.wq(M+0x10,V if have else 0)
    width=F(rng.uniform(600,2400));height=F(rng.uniform(500,1800))
    for off,val in [(0x30,0),(0x34,0),(0x38,width),(0x3c,height)]:u.wf(V+off,val)
    u.call(BASE+0x1010150,M,count=10000)
    target=projected(n,far,angle,oldaspect,ox,oy)
    actual=bytes(m.mem_read(M+0x22c,64));expected=struct.pack('<16f',*target)
    actualdev=bytes(m.mem_read(M+0x26c,64));expecteddev=struct.pack('<16f',*device(target,k,zs,zo))
    copy=bytes(m.mem_read(M+0x144,0x4c));copy_ok=all(copy[a:b]==pose[a:b] for a,b in [(0,0x2d),(0x30,0x45),(0x48,0x4c)])
    nextaspect=div(width,height) if have else oldaspect
    view_expected=[-1.,0.,0.,float(pos[0]),0.,1.,0.,float(F(-pos[1])),0.,0.,-1.,float(pos[2])]
    view=bytes(m.mem_read(M+0x198,48))
    ok=(actual==expected and actualdev==expecteddev and copy_ok and
        fbits(u.rf(M+0x2d0))==fbits(nextaspect) and u.r8(M+0x140)==have and
        view==struct.pack('<12f',*view_expected) and u.r8(M+0x229)==0 and u.r8(M+0x228)==have)
    if not ok:failures.append(dict(i=i,projection=actual.hex(),expected=expected.hex(),device=actualdev.hex(),expectedDevice=expecteddev.hex(),view=view.hex(),expectedView=struct.pack('<12f',*view_expected).hex(),copy=copy_ok,valid=u.r8(M+0x140),aspect=u.rf(M+0x2d0),expectedAspect=float(nextaspect),dirty=u.r8(M+0x228)))
    fields+=45
    if i<6:traces.append(dict(i=i,posture=k,viewport=have,oldAspect=float(oldaspect),newAspect=float(nextaspect),projectionP00=float(floats(actual)[0]),valid=u.r8(M+0x140)))
ctx=u.alloc(0x500);context_bad=[];latch_bad=[]
# Draw context supplies aspect after matrices, and does not set valid140.
# Type3 permits zero height; preserve original infinity instead of inventing
# a clamp. These cases stop before another projection consumes that infinity.
for i in range(256):
    m.mem_write(M,b'\0'*0x400)
    u.wq(M+0x120,S+0x288);u.wq(M+0x190,BASE+0x5721238);u.wq(M+0x220,BASE+0x57213b8)
    u.w8(M+0x228,1);u.w8(M+0x229,1);u.wf(M+0x2d0,1.3);u.wf(M+0x2b0,1)
    have=i%2;u.wq(M+0x10,V if have else 0);u.wq(M+0x18,ctx)
    width=[0,1,640,1920][i%4];height=[0,1,360,1080][(i//4)%4];kind=[0,3][(i//16)%2]
    m.mem_write(ctx+0x40,struct.pack('<HH',width,height));m.mem_write(ctx+0x4a,struct.pack('<H',kind))
    u.call(BASE+0x1010150,M,count=10000)
    numerator=max(width,1);denominator=height if kind==3 else max(height,1)
    with np.errstate(divide='ignore'):wanted=div(numerator,denominator)
    p=projected(n,far,angle,F(1.3),F(0),F(0))
    got=bytes(m.mem_read(M+0x22c,64));expected=struct.pack('<16f',*p)
    if got!=expected or fbits(u.rf(M+0x2d0))!=fbits(wanted) or u.r8(M+0x140)!=have or u.r8(M+0x228)!=1:
        context_bad.append(dict(i=i,valid=u.r8(M+0x140),expectedValid=have,aspect=u.rf(M+0x2d0),expectedAspect=float(wanted),projectionMatch=got==expected))
# Non-null viewport -> null on the next update: valid140 is retained.
for i in range(128):
    u.wq(M+0x18,0);u.wq(M+0x10,V);u.w8(M+0x140,0);u.wf(M+0x2d0,1.3)
    u.w8(M+0x228,1);u.w8(M+0x229,1)
    u.call(BASE+0x1010150,M,count=10000)
    previous=u.rf(M+0x2d0);u.wq(M+0x10,0)
    u.call(BASE+0x1010150,M,count=10000)
    if u.r8(M+0x140)!=1 or fbits(u.rf(M+0x2d0))!=fbits(previous):latch_bad.append(i)
out=dict(scope=__doc__,deviceCases=4096,deviceMismatches=device_bad,moduleCases=1024,moduleMismatches=failures,independentFloatFields=fields,drawContextCases=256,drawContextMismatches=context_bad,validLatchSequences=128,validLatchMismatches=latch_bad,sdkOriginalCalls=calls,examples=traces,null=u.null_calls,auto=u.auto_pages,fault=u.faults,plt=u.plt_stubbed)
path=OUT/'module_emu.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2,default=float)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['scope','examples','moduleMismatches','deviceMismatches']},default=float))
print('mismatches',len(device_bad),len(failures),len(context_bad),len(latch_bad))
sys.exit(bool(device_bad or failures or context_bad or latch_bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed))
