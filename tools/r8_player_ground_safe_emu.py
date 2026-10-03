"""r8 original SplAlongGnd math and PlayerSafePos writer.
Synthetic inputs: controller/result/state pointers, get-position and ray-query response.
No Havok cast/solver is claimed. Original iterator is used with an empty contact list.
"""
import json,math,random,struct,sys
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,RET_MAGIC
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding='utf-8')
F=lambda x:float(np.float32(x))
A=lambda a,b:F(F(a)+F(b))
S=lambda a,b:F(F(a)-F(b))
M=lambda a,b:F(F(a)*F(b))
D=lambda a,b:F(F(a)/F(b))
pack=lambda a:struct.pack('<'+'f'*len(a),*a)
u=PUC();mu=u.mu
C=u.alloc(0x1400);P=u.alloc(0x100);V=u.alloc(0x100);G=u.alloc(0x100);CTRL=u.alloc(0x200);BODY=u.alloc(0x300)
VT=u.alloc(0x180);states=u.alloc(0x80);state=u.alloc(0x80);stobj=u.alloc(0x30);frame=u.alloc(0x80);chain1=u.alloc(0x80);chain2=u.alloc(0x80);contacts=u.alloc(0x100)
u.wq(P,CTRL);u.wq(P+8,G);u.wq(G+0x20,state);u.wq(CTRL+8,BODY);u.wq(BODY,VT);u.wq(VT+0xe0,RET_MAGIC+0x100)
u.wq(frame+0x58,chain1);u.wq(chain1+8,chain2);u.wq(chain2+0x40,states);u.wq(states+0x28,stobj);u.w32(states+0x40,0)
u.wq(C+0x188,contacts);u.w8(C+0x38,1);u.wf(C+0x34,0.6)
cur={'pos':(0,0,0),'frac':1.0,'hit':True}
def ret(x=0):mu.reg_write(UC_ARM64_REG_X0,x);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def hk(mu,pc,sz,d):
 if pc==RET_MAGIC+0x100:
  mu.mem_write(mu.reg_read(UC_ARM64_REG_X1),pack(cur['pos']));ret()
 elif pc==0x71024f4104:ret(0)
 elif pc==0x7103a5f36c:
  q=mu.reg_read(UC_ARM64_REG_X0);u.w8(q+0x4c,1);u.wf(q+0x50,cur['frac']);ret(int(cur['hit']))
 elif pc==0x71012db7b4:ret(cur.get('rigid',0))
for pc in [RET_MAGIC+0x100,0x71024f4104,0x7103a5f36c,0x71012db7b4]:mu.hook_add(UC_HOOK_CODE,hk,begin=pc,end=pc)
# All original along-ground branches with synthetic query return and empty original contact iterator.
out={'along_cases':0,'along_fields':0,'along_mismatch':[],'safe_cases':0,'safe_fields':0,'safe_mismatch':[],'stubs':__doc__}
rng=random.Random(308)
for i in range(1250):
 kind=i%5;N=[F(rng.uniform(-.4,.4)),F(rng.uniform(.5,1.4)),F(rng.uniform(-.4,.4))];vel=[F(rng.uniform(-5,5)) for _ in range(3)];given=[F(rng.uniform(-5,5)) for _ in range(3)]
 dt=F([1/60,1/30,1/120,.005,.1][i%5]);strength=F(rng.uniform(0,1));target=[F(rng.uniform(-.2,.2)),F(rng.uniform(.5,1.2)),F(rng.uniform(-.2,.2))]
 cur['pos']=tuple(F(rng.uniform(-10,10)) for _ in range(3));cur['frac']=F(rng.random());cur['hit']=i%7!=0
 u.w32(stobj+8,1 if kind==0 else (2 if kind==1 else 0));u.w32(state+0x20,1 if kind!=2 else 0);u.wf(C+0x1308,strength);mu.mem_write(C+0x28,pack(N));mu.mem_write(V,pack(given));mu.mem_write(frame,pack(vel));u.wf(frame+0x44,dt);mu.mem_write(state+0x34,pack(target));u.w8(C+0x38,int(kind!=3))
 expectN=N[:];expectV=given[:];expectStrength=strength;ray=False
 if kind==0:
  z=min(F(1),S(1,N[1]));inv=D(1,dt)
  for j in range(3):expectV[j]=S(given[j],M(inv,M(M(M(N[j],.05),strength),z)))
  expectN=[A(N[j],M(S(1 if j==1 else 0,N[j]),.15)) for j in range(3)];expectStrength=M(strength,.5)
 elif kind in (1,2):pass
 elif kind==3:expectStrength=1
 else:
  expectStrength=1;t=F(.5 if target[1]<u.rf(0x71058f0cb8) else .15)
  expectN=[A(N[j],M(t,S(target[j],N[j]))) for j in range(3)]
  pred=[A(cur['pos'][j],M(dt,given[j])) for j in range(3)]
  ln=F(math.sqrt(A(A(M(vel[0],vel[0]),M(vel[1],vel[1])),M(vel[2],vel[2]))));L=A(A(M(ln,dt),F(.6)),F(-.1));end=[S(pred[j],M(expectN[j],L)) for j in range(3)]
  ray=True
  if cur['hit']:
   hit=[A(pred[j],M(S(end[j],pred[j]),cur['frac'])) for j in range(3)];delta=[S(hit[j],pred[j]) for j in range(3)]
   dl=F(math.sqrt(A(A(M(delta[0],delta[0]),M(delta[1],delta[1])),M(delta[2],delta[2]))));k=max(A(S(dl,F(.6)),F(.1)),0)
   cx=F(-expectN[2]);cy=F(0);cz=expectN[0];cl=F(math.sqrt(A(A(M(cx,cx),M(cy,cy)),M(cz,cz))));angle=F(math.atan2(cl,expectN[1]))
   if angle<F(.7853982):expectV=[A(given[j],M(M(delta[j],k),D(1,dt))) for j in range(3)]
 err=u.call(0x7102c5fdf0,C,P,V,frame)
 gotV=struct.unpack('<3f',mu.mem_read(V,12));gotN=struct.unpack('<3f',mu.mem_read(C+0x28,12));gotStrength=u.rf(C+0x1308)
 expect=expectV+expectN+[expectStrength];got=list(gotV)+list(gotN)+[gotStrength]
 if err or pack(got)!=pack(expect):out['along_mismatch'].append({'i':i,'kind':kind,'error':err,'got':got,'expect':expect})
 out['along_cases']+=1;out['along_fields']+=7
# Safe position raw integer body ID, local inverse transform, optional model SRT inverse.
SP=u.alloc(0x30);POINT=u.alloc(0x10);RB=u.alloc(0x300);SRT=u.alloc(0x80)
for i in range(1800):
 mode=i%4;point=[F(rng.uniform(-20,20)) for _ in range(3)];rid=0 if mode==0 else 0x13579bdf;cur['rigid']=0 if mode==1 else RB
 mu.mem_write(SP,b'\xcd'*0x30);mu.mem_write(POINT,pack(point));trans=[F(rng.uniform(-5,5)) for _ in range(3)]
 rows=[[F(rng.uniform(-1,1)) for _ in range(3)] for _ in range(3)]
 # actual matrix offsets are row-major 3x4; inverse uses columns dot translated world point.
 for j in range(3):mu.mem_write(RB+0xd8+j*16,pack(rows[j]+[trans[j]]))
 u.wq(RB+0x268,SRT if mode==3 else 0)
 local=[F(-431602080)]*3
 if mode==0:local=point[:]
 elif mode!=1:
  d=[S(point[j],trans[j]) for j in range(3)];local=[A(A(M(rows[0][j],d[0]),M(rows[1][j],d[1])),M(rows[2][j],d[2])) for j in range(3)]
  if mode==3:
   t=[F(rng.uniform(-3,3)) for _ in range(3)];rots=[[F(rng.uniform(-1,1)) for _ in range(3)] for _ in range(3)];scale=[F(rng.uniform(.2,2)) for _ in range(3)]
   mu.mem_write(SRT+0x30,pack(t));mu.mem_write(SRT+0x3c,pack(sum(rots,[])));mu.mem_write(SRT+0x60,pack(scale));d=[S(local[j],t[j]) for j in range(3)];local=[D(A(A(M(d[0],rots[j][0]),M(d[1],rots[j][1])),M(d[2],rots[j][2])),scale[j]) for j in range(3)]
 err=u.call(0x7102643148,SP,POINT,rid)
 expected=pack(point+local)+struct.pack('<I',rid);got=bytes(mu.mem_read(SP,28))
 if err or got!=expected:out['safe_mismatch'].append({'i':i,'mode':mode,'error':err,'got':got.hex(),'expected':expected.hex()})
 out['safe_cases']+=1;out['safe_fields']+=7
out['plt_stubbed']=u.plt_stubbed;out['libm_used']=u.libm_used;out['null_calls']=len(u.null_calls);out['auto_pages']=u.auto_pages
(R/'analysis/completion/r8/player_ground_safe_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('along_mismatch','safe_mismatch','stubs')},ensure_ascii=False));print('mismatch',len(out['along_mismatch']),len(out['safe_mismatch']));print(out['along_mismatch'][:2],out['safe_mismatch'][:2])
