"""Original PlayerCamera scalar input blocks, not whole24e0178/scene.

Native main-axis snap0bbc..0d78, bias0f38..1008, yaw10bc..12a8,
pitch speed/angle accumulator1674..1c30.
Explicit pre-block stick/delta/state inputs; original SDK pow/log/exp.
Reference preserves native f32 grouping and literal constant bits.
No player state producer, gyro angular remap, aim rotation or GPU proof.
"""
from pathlib import Path
import json, random, struct
import numpy as np
from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ
from r5_player_libm_emu import Sdk

F=np.float32
def val(b):return struct.unpack('<f',struct.pack('<I',b))[0]
def bits(v):return struct.unpack('<I',struct.pack('<f',float(v)))[0]
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
def root(a):return F(np.sqrt(F(a)))
def neg(a):return F(-F(a))
sdk=Sdk();calls={}
trig={BASE+0x3e9bb60:'powf',BASE+0x3e9c2a0:'logf',BASE+0x3e9be20:'expf'}
class InputPUC(PUC):
    def _plt(self,mu,pc,n,_):
        if pc in trig:
            name=trig[pc];calls[name]=calls.get(name,0)+1
            args=[val(mu.reg_read(UC_ARM64_REG_S0)&0xffffffff)]
            if name=='powf':args.append(val(mu.reg_read(UC_ARM64_REG_S1)&0xffffffff))
            mu.reg_write(UC_ARM64_REG_S0,sdk.call(name,*args))
            mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_X30))
        else:super()._plt(mu,pc,n,_)
u=InputPUC();m=u.mu;C=u.alloc(0x2000);H=u.alloc(0x200);B=u.alloc(0xb000)
u.wq(C+0x1968,H);u.wq(H+0x108,B)
sp=STACK+STACK_SZ-0x2000
m.reg_write(UC_ARM64_REG_SP,sp)
rng=random.Random(0x24e0178);bad=[];counts={'axis':4096,'bias':2048,'yaw':4096,'pitch':2048}
def sf(k,v):m.reg_write(globals()['UC_ARM64_REG_S'+str(k)],bits(v))
def rf(k):return val(m.reg_read(globals()['UC_ARM64_REG_S'+str(k)])&0xffffffff)
def run(start,end):
    m.reg_write(UC_ARM64_REG_X19,C);m.reg_write(UC_ARM64_REG_X28,C+0x1521)
    m.reg_write(UC_ARM64_REG_SP,sp)
    m.emu_start(BASE+start,BASE+end,count=2000)
    if m.reg_read(UC_ARM64_REG_PC)!=BASE+end:raise RuntimeError('native block did not reach end')
def native(name,*args):return F(val(sdk.call(name,*args)))

for i in range(counts['axis']):
    gyro=i%2
    x=F(rng.uniform(-1,1));y=F(rng.uniform(-1,1))
    if i<12:x=F([0,.5,-.5,1][i%4]);y=F([0,.5,-.5][i//4])
    ax=abs(x);ay=abs(y);oldA=F(rng.uniform(-1,1));oldB=F(rng.uniform(-1,1));oldE=F(rng.uniform(-1,3))
    dx=F(rng.uniform(-2,2));dy=F(rng.uniform(-2,2))
    u.wf(C+0x180,oldA);u.wf(C+0x184,oldB);u.wf(C+0x188,oldE)
    u.wf(B+0xaa4,dx);u.wf(B+0xaa8,dy)
    m.reg_write(UC_ARM64_REG_W8,gyro);m.reg_write(UC_ARM64_REG_W24,bits(y))
    sf(12,ax);sf(10,ay);sf(9,neg(x));sf(13,0)
    run(0x24e0bbc,0x24e0d78)
    ea=oldA;eb=oldB;stored=F(0)
    if not gyro:
        ea=add(oldA,mul(sub(dx,oldA),val(0x3e4ccccd)))
        eb=add(oldB,mul(sub(dy,oldB),val(0x3e4ccccd)))
        stored=add(oldE,mul(sub(3,oldE),val(0x3dcccccd)))
        diagonal=mul(ax,ay)
        if diagonal>F(.001):diagonal=mul(diagonal,sub(1,div(abs(sub(ax,ay)),add(ax,ay))))
        stored=F(max(add(stored,mul(root(abs(mul(eb,neg(ea)))),-3)),-1))
        stored=F(max(add(stored,mul(root(diagonal),val(0xbf333333))),-1))
    exponent=F(max(stored,0));before=root(add(mul(ax,ax),mul(ay,ay)))
    xx=neg(x);yy=y
    if ax>ay:
        ratio=sub(1,div(sub(ax,ay),ax));yy=mul(native('powf',ratio,exponent),yy)
    elif ay>0:
        ratio=sub(1,div(sub(ay,ax),ay));xx=mul(native('powf',ratio,exponent),xx)
    after=root(add(mul(yy,yy),mul(xx,xx)))
    if after>0:
        scale=div(before,after);yy=mul(yy,scale);xx=mul(scale,xx)
    got=[u.rf(C+0x180),u.rf(C+0x184),u.rf(C+0x188),rf(9),val(m.reg_read(UC_ARM64_REG_W24))]
    expected=[ea,eb,stored,xx,yy]
    if list(map(bits,got))!=list(map(bits,expected)):
        bad.append(dict(block='axis',i=i,got=list(map(bits,got)),expected=list(map(bits,expected))))

for i in range(counts['bias']):
    gyro=i%2;x=F(rng.uniform(-1,1));y=F(rng.uniform(-1,1))
    if i<10:x=F([0,.0001,.001,.1,1][i//2]);y=F(0)
    m.reg_write(UC_ARM64_REG_W8,gyro);sf(13,x);sf(6,y);sf(12,0)
    run(0x24e0f38,0x24e1008)
    length=root(add(mul(x,x),mul(y,y)))
    shape=val(0x3ecccccd) if gyro else val(0x3f4ccccd)
    out=F(0) if length<F(.001) else native('expf',mul(native('logf',length),mul(native('logf',shape),val(0xbfb8aa3b))))
    got=rf(14)
    if bits(got)!=bits(out):bad.append(dict(block='bias',i=i,got=bits(got),expected=bits(out)))

for i in range(counts['yaw']):
    k=F(rng.uniform(-1,1));gyro=i%2;slowToggle=(i//2)%2;state=[0,1,2,3,4,5,0xffffffff][i%7]
    xx=F(rng.uniform(-1,1));mag=F(rng.uniform(0,1.4));fov=F(rng.uniform(0,1));w=F(rng.uniform(0,1))
    cap=F(rng.uniform(.5,7));sw=F(rng.uniform(0,1));pw=F(rng.uniform(0,1));tilt=F(rng.uniform(-1,1));old=F(rng.uniform(-.1,.1))
    if i<6:k=F([-1,0,1][i//2])
    for off,v in [(0x1cc,k),(0x156c,cap),(0x1550,sw),(0x1764,pw),(0x14d4,tilt),(0x14f8,old)]:u.wf(C+off,v)
    u.w8(C+0x15d8,gyro);u.w8(C+0x15d9,slowToggle);u.w32(B+0xf34,state)
    u.wf(sp+0x38,w);m.reg_write(UC_ARM64_REG_X9,B);sf(13,xx);sf(14,mag);sf(8,fov)
    run(0x24e10bc,0x24e12a8)
    base=add(mul(k,val(0x3fcccccc) if k<0 else 3),4)
    slow=add(mul(k,val(0x3f75c290) if k<0 else val(0x3fe66664)),val(0x4019999a))
    if not slowToggle:base=add(base,mul(w,sub(slow,base)))
    if base>cap:base=add(base,mul(sub(cap,base),mul(sw,pw)))
    degrees=slow if state in (2,3,4) else base
    rad=mul(degrees,val(0x3c8efa35))
    term=mul(xx,fov)
    if mul(term,tilt)<0:term=mul(term,sub(1,abs(tilt)))
    a0=add(mul(k,val(0x3ca3d70c) if k<0 else val(0x3ca3d708)),val(0x3dcccccd)) if gyro else F(.8)
    a1=F(.2) if gyro else F(.3)
    alpha=add(a0,mul(mag,sub(a1,a0)))
    target=mul(rad,mul(mag,term))
    velocity=add(old,mul(alpha,sub(target,old)))
    got=[u.rf(C+0x14fc),u.rf(C+0x14f8)];expected=[rad,velocity]
    if list(map(bits,got))!=list(map(bits,expected)):
        bad.append(dict(block='yaw',i=i,got=list(map(bits,got)),expected=list(map(bits,expected))))

manager=u.alloc(0x200);controller=u.alloc(0x200)
u.wq(BASE+0x59a57d0,manager);u.wq(manager+0x20,controller);u.wq(manager+0xd0,controller)
def bias(v,s):
    if abs(v)<F(.001):return F(0)
    return native('expf',mul(native('logf',abs(v)),mul(native('logf',s),val(0xbfb8aa3b))))
for i in range(counts['pitch']):
    gyro=i%2;k=F(rng.uniform(-1,1));gk=F(rng.uniform(-1,1));state=[0,2,4,5][i%4]
    yy=F(rng.uniform(-1,1));mag=F(rng.uniform(0,1.4));fov=F(rng.uniform(0,1));w=F(rng.uniform(0,1))
    old=F(rng.uniform(-.08,.08));angle=F(rng.uniform(-100,100));blend=F(rng.uniform(0,1))
    device=[0,1,2][i%3];slot=[0,1,0xffffffff][i%3];offsets=[F(rng.uniform(-5,5)) for _ in range(4)]
    if i<6:gk=F(0);angle=F([-28,0,44][i//2])
    u.wf(C+0x1cc,k);u.wf(C+0x1c8,gk);u.wf(C+0x1504,old);u.wf(C+0x150c,angle);u.wf(C+0x1680,blend)
    u.wf(C+0x16c,.4);u.w8(C+0x15d8,gyro);u.w8(C+0x15d9,0);u.w32(C+0x15f0,slot)
    for off,v in zip([0x15f4,0x15f8,0x15fc,0x1600],offsets):u.wf(C+off,v)
    u.wf(C+0x1604,.5);u.wf(C+0x1608,.5);u.w8(controller+0x17d,device);u.w32(manager+0x164,i%8)
    u.w32(B+0xf34,state);u.wf(sp+0x38,w);m.reg_write(UC_ARM64_REG_X9,B)
    m.reg_write(UC_ARM64_REG_W8,0 if gyro else 1);sf(6,yy);sf(8,fov);sf(14,mag);sf(11,0)
    run(0x24e1674,0x24e1c30)
    degrees=add(mul(k,val(0x3f4ccccc)) if k<0 else k,val(0x3fe66666))
    rad=mul(degrees,val(0x3c8efa35))
    a0=add(mul(k,val(0x3ca3d70c) if k<0 else val(0x3ca3d708)),val(0x3dcccccd)) if gyro else F(.8)
    a1=F(.2) if gyro else F(.3)
    alpha=add(a0,mul(mag,sub(a1,a0)))
    velocity=add(old,mul(alpha,sub(mul(mul(mag,mul(yy,fov)),rad),old)))
    adjust=F(10) if device==1 else F(0)
    lo=add(add(mul(gk,11 if gk<0 else 3),-103),adjust)
    hi=add(add(mul(gk,-18 if gk<0 else -6),-31),adjust)
    base=add(-75,adjust)
    if gyro:
        slotIndex=slot if slot<2 else 0
        lo=sub(add(lo,offsets[slotIndex]),offsets[slotIndex+2])
        hi=sub(add(hi,offsets[slotIndex]),offsets[slotIndex+2])
    rel=add(angle,base)
    t=F(0) if rel<=lo else F(1) if hi<=rel else div(sub(rel,lo),sub(hi,lo))
    slope=div(sub(bias(add(t,F(.001)),val(0x3ee66666)),bias(t,val(0x3ee66666))),F(.001))
    result=add(angle,mul(mul(velocity,val(0x42652ee0)),slope))
    limit=add(mul(blend,-75),90)
    result=F(min(max(result,neg(limit)),limit))
    got=[u.rf(C+0x1508),u.rf(C+0x1504),u.rf(C+0x150c)];expected=[rad,velocity,result]
    if list(map(bits,got))!=list(map(bits,expected)):
        bad.append(dict(block='pitch',i=i,got=list(map(bits,got)),expected=list(map(bits,expected))))

out=dict(scope=__doc__,cases=counts,mismatches=bad,sdkOriginalCalls=calls,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,fault=u.faults,plt=u.plt_stubbed)
p=Path('analysis/camera_100_r10/input/input_emu.json');p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['scope','mismatches']}));print('mismatches',len(bad),bad[:6])
raise SystemExit(bool(bad or u.null_calls or u.auto_pages or u.faults or u.plt_stubbed))
