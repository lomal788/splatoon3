"""Port regression fixtures from previously confirmed original blocks.
No new analysis credit. All files stay inside this repository.
"""
import sys,json,struct,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from r5_player_lerpdir_emu import UC, bits, F
from camera_weapon_completion_emu import basis
from r7_camweapon_emu import Run,norm
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_S10, UC_ARM64_REG_S11
ROOT=Path(__file__).resolve().parents[2]
result={'scope':__doc__,'basis':basis()}
u=UC();a=u.alloc(16);b=u.alloc(16);out=u.alloc(16)
rng=random.Random(20261003);rows=[]
cases=[(.1,[0,1,0],[0,-1,0]),(.1,[0,1,0],[1,0,0]),(.1,[0,0,0],[1,0,0])]
cases += [(rng.uniform(0,1),[rng.uniform(-1,1) for _ in range(3)],[rng.uniform(-1,1) for _ in range(3)]) for _ in range(128)]
for t,v,w in cases:
 t=F(t);v=list(map(F,v));w=list(map(F,w))
 u.mu.mem_write(a,struct.pack('<3f',*v));u.mu.mem_write(b,struct.pack('<3f',*w))
 u.call(0x7101252ff0,out,a,b,0,fargs=(float(t),))
 rows.append(dict(t=float(t),a=list(map(float,v)),b=list(map(float,w)),bits=list(struct.unpack('<3I',u.mu.mem_read(out,12)))))
result['slerp']=rows
# Reuse confirmed r9 harness bodies, change only capture destination and sample retention.
for name in ['collision_spring','boom_gate']:
 src=(ROOT/f'web/tools/r9_camera_{name}_emu.py').read_text(encoding='utf8')
 stop=src.index('out=dict(')
 src=src[:stop].replace('count=2048','count=128').replace('cases=2048','cases=128')
 if name=='collision_spring':
  src=src.replace("if i<3:samples.append(dict(hold=hold,ratio=float(ratio),got=got))","samples.append(dict(hold=hold,ratio=float(ratio),spring=spring,track=prior,input=inp,body=body,vel=vel,aim=aim,bits=list(struct.unpack('<6I',struct.pack('<6f',*got)))))")
 else:
  src=src.replace("if i<3:samples.append(dict(de0=de0,entry=old,native=native,after=got,blend=float(blend),final=got2))","samples.append(dict(de0=de0,entry=old,native=native,at=at,pivot=pivot,dir=direction,ratio=ratio,length=length,height=height,blend=float(blend),bits=list(struct.unpack('<3I',struct.pack('<3f',*got))),finalBits=list(struct.unpack('<3I',struct.pack('<3f',*got2)))))")
 ns={'__doc__':name};exec(compile(src,name,'exec'),ns)
 assert not ns['bad'],ns['bad'][:2]
 result[name]=ns['samples']
r=Run();rows=[];forward=[]
rng=random.Random(7102026)
for i in range(128):
 d=dict(minimum=F(.8),length=F(rng.uniform(1,8)),move=[F(rng.uniform(-.3,.3)) for _ in range(3)],vy=F(rng.uniform(-.2,.2)),dc=F(rng.uniform(0,1)),air=i%8,wall=i%2,normalY=F(rng.uniform(0,1)),basis=norm([F(rng.uniform(-1,1)) for _ in range(3)]),prevBasis=norm([F(rng.uniform(-1,1)) for _ in range(3)]),aim=norm([F(rng.uniform(-1,1)) for _ in range(3)]),dir=norm([F(rng.uniform(-1,1)) for _ in range(3)]),ad0=i%3,d9=i%2,d0=F(rng.uniform(0,1)),blend=F([0,.1,.3,.9,1][i%5]),hitN=norm([F(rng.uniform(-1,1)) for _ in range(3)]),hitDist=F(rng.uniform(.8,2)),camDelta=[F(rng.uniform(-.3,.3)) for _ in range(3)],atDelta=[F(rng.uniform(-.3,.3)) for _ in range(3)],vel=[F(rng.uniform(-.2,.2)) for _ in range(3)],target=F(rng.uniform(.1,1)),ratio=F(rng.uniform(.1,1)),rate=F(rng.uniform(.1,1)),speed=F(rng.uniform(0,.1)),angle=F(rng.uniform(0,1)))
 got,ref=r.boom(d);assert got==ref
 rows.append(dict(input=d,bits=got))
 vel=[F(0)]*3 if i==0 else [F(rng.uniform(-.2,.2)) for _ in range(3)];aim=norm([F(rng.uniform(-1,1)) for _ in range(3)]);state=0x82 if i%2 else 0x42;k=F(rng.uniform(0,2.5))
 got,ref=r.forward(vel,aim,state,k);assert got==ref
 forward.append(dict(vel=vel,aim=aim,squid=state==0x82,old=k,bits=got))
result['boom']=rows;result['forward']=forward

# Mode0 rig, confirmed constants and finite ordinary/ground/wall squid inputs.
rig=[];C=r.u.alloc(0x2000);B=r.u.alloc(0xb000);BH=r.u.alloc(0x200)
r.ptr(C+0x1968,BH);r.ptr(BH+0x108,B)
cam=r.u.alloc(16);at=r.u.alloc(16)
for ofs,values in [(0x17a0,[7.2,6.8,4]),(0x17ac,[2.25,2.25,2.75]),(0x17b8,[1,.5,0]),(0x17c4,[0,0,0]),(0x17e4,[7.2,6.8,5.2]),(0x17f0,[1.45,1.45,2.35]),(0x17fc,[0,.5,.5]),(0x1808,[0,0,0])]:r.vec(C+ofs,values)
r.u.f32(C+0x17dc,.2);r.u.f32(C+0x1820,.5)
valuebits=[]
def capture_rig_values(mu,pc,size,_):
 if pc==0x71024d8c40:
  sp=mu.reg_read(UC_ARM64_REG_SP)
  valuebits[:] = [struct.unpack('<I',mu.mem_read(sp+12,4))[0],mu.reg_read(UC_ARM64_REG_S11)&0xffffffff,struct.unpack('<I',mu.mem_read(sp+8,4))[0],mu.reg_read(UC_ARM64_REG_S10)&0xffffffff]
hook=r.mu.hook_add(UC_HOOK_CODE,capture_rig_values,begin=0x71024d8c40,end=0x71024d8c40)
for i in range(128):
 p=F([-1,-.5,0,.5,1][i%5] if i<10 else rng.uniform(-1,1));sq=F([0,1][i%2]);u0=F(0 if i<10 else rng.uniform(0,1));base=[F(rng.uniform(-5,5)) for _ in range(3)]
 theta=rng.uniform(-3.14,3.14);direction=norm([F(np.sin(theta)),F(0),F(np.cos(theta))])
 if i<10:base=[F(0)]*3;direction=[F(0),F(0),F(1)]
 if 10<=i<=13:
  p=F([-.0001,.0001,1-.0001,1][i-10]);sq=F(0);u0=F(0);base=[F(0)]*3;direction=[F(0),F(0),F(1)]
 elev=F(-7.5+abs(p)*((60 if p>0 else -75)+7.5))
 r.vec(C+0x120,base);r.vec(C+0x1a4,direction);r.u.f32(C+0x13c,F(1-u0));r.u.f32(C+0x1764,sq)
 for ofs,val in [(0x15e0,-7.5),(0x15e4,60),(0x15dc,-75)]:r.u.f32(C+ofs,val)
 r.u.call(0x71024d6e84,C,cam,at,0,fargs=(float(p),))
 rig.append(dict(p=p,squid=sq,u=F(1-F(1-u0)),base=base,dir=direction,elev=elev,valueBits=list(valuebits),bits=list(struct.unpack('<6I',r.mu.mem_read(at,12)+r.mu.mem_read(cam,12)))))
result['rig']=rig
dest=ROOT/'web/games/splatoon3/tests/fixtures/camera_native.json'
dest.parent.mkdir(exist_ok=True)
dest.write_text(json.dumps(result,default=float,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
print('Original fixtures:',{k:len(v) for k,v in result.items() if isinstance(v,list)})
