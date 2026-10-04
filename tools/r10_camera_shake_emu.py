"""r10 native camera shake lifetime, curves and ELink shooter rumble admission.
Analysis-only: original instructions unchanged, all products in analysis/camera_100_r10/shake.
Allocator/mutex/guard are SDK boundaries. ELink parameter getters use decoded original asset values;
the controller rumble start is captured, not actual hardware playback. No null reads allowed.
"""
import sys, json, struct, random, math
from pathlib import Path
from collections import Counter
import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf-8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R']
F=np.float32
def bits(v):return struct.unpack('<I',struct.pack('<f',float(v)))[0]
class E(H):
 def _block(self,mu,a,size,user):
  rd=mu.reg_read
  if a==0x7101017434:
   self.captured['projection']+=1
   self.projection_pose=bytes(mu.mem_read(rd(UC_ARM64_REG_X0),0x4c))
   mu.reg_write(UC_ARM64_REG_PC,rd(UC_ARM64_REG_LR));return
  if self.asset is not None and a in [0x71038931b8,0x7103892e08,0x7103893040,0x710389331c]:
   self.captured[hex(a)]+=1
   idx=rd(UC_ARM64_REG_W1);key=self.indices[idx];v=self.asset.get(key,self.defaults[key])
   if a==0x7103892e08:ret=self.string(v or '')
   elif a==0x710389331c:mu.reg_write(UC_ARM64_REG_S0,bits(v));ret=0
   else:ret=int(v)
   mu.reg_write(UC_ARM64_REG_X0,ret&0xffffffffffffffff);mu.reg_write(UC_ARM64_REG_PC,rd(UC_ARM64_REG_LR));return
  if self.asset is not None and a in [0x710130f0b8,0x7101010f14]:
   self.captured[hex(a)]+=1
   name=self.cstr(self.r64(rd(UC_ARM64_REG_X2 if a==0x710130f0b8 else UC_ARM64_REG_X1)))
   self.starts.append({'kind':'rumble' if a==0x710130f0b8 else 'shake','name':name,'category':rd(UC_ARM64_REG_W1) if a==0x710130f0b8 else None})
   mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_X1,0);mu.reg_write(UC_ARM64_REG_PC,rd(UC_ARM64_REG_LR));return
  super()._block(mu,a,size,user)
 def string(self,s):
  b=s.encode('utf-8')+b'\0';p=self.alloc(len(b));self.mu.mem_write(p,b);return p
e=E([0x71010182e8]);e.executed=set();e.sdklog=Counter();e.stublog=Counter();e.captured=Counter();e.asset=None
def no_null(mu,access,a,size,value,user):
 if a<0x400000:raise RuntimeError(f'null read {a:#x} pc={mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
data=json.loads((ROOT/'analysis/camera/SingletonParam/Gyml/Singleton/game__CameraModuleParam.game__CameraModuleParam.bgyml.json').read_text(encoding='utf-8'))['Rumble']
def parameter(d):
 e.call(0x710100e6b4,[0]);p=e.mu.reg_read(UC_ARM64_REG_X0);c=d['Curve']
 e.w32(p+0x38,{'Linear':0,'Hermit':1,'Sin':3}[c['Type']]);e.wf(p+0x3c,c['MaxX'])
 e.mu.mem_write(p+0x40,bytes([len(c['Data'])]));cp=e.alloc(len(c['Data'])*4);e.mu.mem_write(cp,struct.pack('<%df'%len(c['Data']),*c['Data']));e.w64(p+0x48,cp)
 ax=d.get('Axis',{'X':0,'Y':1,'Z':0});e.mu.mem_write(p+0x50,struct.pack('<3f',ax['X'],ax['Y'],ax['Z']))
 e.wf(p+0x5c,d.get('Scale',1));e.w8(p+0x60,int(d.get('IsLooped',False)));e.mu.mem_write(p+0x61,b'\1'*4)
 handle=e.alloc(0x20);e.w64(handle,p);e.w32(handle+0xc,7);return p,handle
def instance(p,h,frame=0,elapsed=0,gain=1,limit=-1,follow=0,owner=0,owner_gen=9):
 i=e.alloc(0x48);e.w64(i,h);e.w32(i+8,7);e.w32(i+0x10,12);e.w32(i+0x14,frame);e.w32(i+0x18,elapsed)
 e.wf(i+0x28,gain);e.w32(i+0x2c,limit);e.w8(i+0x30,follow);e.w64(i+0x38,owner);e.w32(i+0x40,owner_gen);return i
def result(fn,i):e.call(fn,[i]);return e.mu.reg_read(UC_ARM64_REG_W0)&1
counts=Counter();examples=[]
params={n:parameter(d) for n,d in data.items() if d['Curve']['Type']!='Sin'}
p,h=params['Fuwa'];owner=e.alloc(0x28);e.w32(owner+0x20,9)
for name,(p,h) in params.items():
 for frame in [-1,0,1,7,8,14,15,16,49,50,51,16777217,2147483647]:
  for elapsed in [-1,0,1,5,15]:
   for limit in [-1,0,1,5,15]:
    i=instance(p,h,frame,elapsed,limit=limit)
    expect=(limit>=1 and elapsed>=limit) or (not data[name].get('IsLooped',False) and F(data[name]['Curve']['MaxX'])<=F(frame))
    actual=result(0x7101018b4c,i);assert actual==expect,(name,frame,elapsed,limit,actual,expect)
    assert result(0x7101018998,i)==bool(data[name].get('IsLooped',False));counts['finish_boundary']+=1
# Invalid SafePtr and parent-generation/override boundaries. Original native RTTI still executes.
for kind in ['missing','stale','null_pointee']:
 p,h=parameter(data['Fuwa']);i=instance(p,h)
 if kind=='missing':e.w64(i,0)
 elif kind=='stale':e.w32(i+8,8)
 else:e.w64(h,0)
 assert result(0x7101018998,i)==0 and result(0x7101018b4c,i)==1
 counts['handle_boundary']+=1
for local_override in [0,1]:
 for parent_state in ['valid','stale','missing','null_pointee']:
  for frame in [0,14,15,50]:
   p,h=parameter(data['Fuwa']);parent,ph=parameter(data['ZigZagLoop'])
   e.w64(p+0x10,1);e.w64(p+0x18,ph);e.w32(p+0x20,7)
   e.w8(p+0x61,local_override);e.w8(p+0x62,local_override)
   if parent_state=='stale':e.w32(p+0x20,8)
   elif parent_state=='missing':e.w64(p+0x18,0)
   elif parent_state=='null_pointee':e.w64(ph,0)
   i=instance(p,h,frame=frame)
   inherited=(not local_override and parent_state=='valid')
   assert result(0x7101018998,i)==inherited
   assert result(0x7101018b4c,i)==(not inherited and F(frame)>=F(15))
   counts['inheritance_boundary']+=1
def curve_ref(c,frame):
 ds=[F(x) for x in c['Data']];t=F(F(frame)/F(c['MaxX']));n=len(ds)
 if t<0:return ds[0]
 if c['Type']=='Linear':
  m=n-1;x=F(F(m)*t);k=int(x)
  return F(ds[k]+F(F(x-F(k))*F(ds[k+1]-ds[k]))) if k<m else ds[m]
 m=n//2-1;x=F(F(m)*t);k=int(x)
 if k>=m:return ds[2*m]
 t=F(x-F(k));t2=F(t*t);twice2=F(t*F(t+t));twice3=F(t*twice2);three2=F(t*F(t*F(3)));t3=F(t*t2)
 h00=F(F(twice3-three2)+F(1));h01=F(three2-twice3);h10=F(t+F(t3-twice2));h11=F(t3-t2)
 return F(F(F(F(h00*ds[2*k])+F(h01*ds[2*k+2]))+F(h10*ds[2*k+1]))+F(h11*ds[2*k+3]))
# Original whole instance update, including inherited typed IsA, original curve leaves, owner generation and reset.
for name,(p,h) in params.items():
 d=data[name];loop=d.get('IsLooped',False);mx=d['Curve']['MaxX'];axis=d.get('Axis',{'X':0,'Y':1,'Z':0})
 for follow,owner_state in [(0,'absent'),(1,'match'),(1,'stale'),(1,'absent')]:
  own=owner if owner_state!='absent' else 0;e.w32(owner+0x20,9 if owner_state=='match' else 10)
  i=instance(p,h,gain=.375,follow=follow,owner=own);rf=0;el=0;valid=True
  trace=[]
  for tick in range(int(mx)*2+3):
   if valid:
    v=F(curve_ref(d['Curve'],rf)*F(F(.375)*F(d.get('Scale',1))))
    expected=struct.pack('<3f',* [F(v*F(axis[k])) for k in ['X','Y','Z']])
   else:expected=bytes(e.mu.mem_read(i+0x1c,12)) # empty slots preserve previous output bytes
   e.call(0x71010182e8,[i]);assert bytes(e.mu.mem_read(i+0x1c,12))==expected,(name,tick,owner_state,bytes(e.mu.mem_read(i+0x1c,12)).hex(),expected.hex(),curve_ref(d['Curve'],rf))
   if follow and loop and owner_state!='match':valid=False
   rf+=1;el+=1
   if valid and loop and mx<=F(rf):rf=0
   assert e.r32(i+0x14)==rf and e.r32(i+0x18)==el and bool(e.r64(i))==valid
   finished=(not valid) or (not loop and mx<=F(rf));assert result(0x7101018b4c,i)==finished
   counts['instance_tick']+=1
   if tick in [0,int(mx)-2,int(mx)-1,int(mx),int(mx)+1]:trace.append({'tick':tick,'frame':rf,'elapsed':el,'valid':bool(valid),'finished':bool(finished),'output_hex':expected.hex()})
  examples.append({'name':name,'follow':follow,'owner':owner_state,'trace':trace})
# Whole CameraModule update through original sum/eligibility. Projection is a captured renderer boundary.
M=e.alloc(0x350);pool=e.alloc(0x48*2);e.w32(M+0x130,2);e.w64(M+0x138,pool)
e.mu.mem_write(M+0xd4,struct.pack('<3f4f',1,2,3,0,0,0,1));e.wf(M+0x144,0)
for tick in range(20):
 for j,name in enumerate(['Fuwa','ZigZagLoop']):
  p,h=params[name];i=instance(p,h,frame=tick,elapsed=tick,gain=1);e.mu.mem_write(pool+j*0x48,bytes(e.mu.mem_read(i,0x48)))
 e.call(0x7101010150,[M]);offset=[F(0),F(0),F(0)]
 for j in range(2):
  i=pool+j*0x48
  if not result(0x7101018b4c,i):
   v=struct.unpack('<3f',e.mu.mem_read(i+0x1c,12));offset=[F(offset[k]+F(v[k])) for k in range(3)]
 expected=struct.pack('<3f',*[F(F(k+1)+offset[k]) for k in range(3)])
 assert bytes(e.mu.mem_read(M+0x144,12))==expected
 assert bytes(e.mu.mem_read(M+0x150,16))==struct.pack('<4f',0,0,0,1);counts['module_tick']+=1
# Native ELink function with asset getter boundary sourced by a newly read original XLNK blob.
from effect_xlink import XLink,load_bytes
xlpath=ROOT/'extracted/romfs/XLink/ELink2.Product.100.belnk.zs'
if not xlpath.exists():xlpath=ROOT/'analysis/effect_sound/elink2.Product.100.belnk'
xl=XLink(load_bytes(str(xlpath)));users={n:xl.user(xl.user_index(n)) for n in ['WeaponShooterNormal','HitEffect','SighterTarget','SighterTargetBig','SplPlayer']}
e.defaults={p['name']:p['default'] for p in xl.assetParamDefs};keys=['ForceTeam','ShaderGraphParam','DistanceAttenuate','CameraRumbleName','CameraRumbleFrame','CtrlRumbleName','CtrlRumbleGain','CtrlRumblePitch','CtrlRumbleStretch','CtrlRumbleExtra','CullingDistance'];e.indices=dict(enumerate(keys))
mapobj=e.alloc(0x400);e.w64(0x710582faa0,mapobj)
for j,k in enumerate(keys):e.w32(mapobj+0x3b0+j*4,j)
manager=e.alloc(0xe80);entry=e.alloc(0x40);res=e.alloc(0x140);user=e.alloc(0x70);access=e.alloc(0x50);resource=e.alloc(0x60);extern=e.alloc(0x28)
e.w64(entry+0x28,res);e.w64(res+0x128,extern);e.w8(res+0xac,1);e.w64(entry+0x18,user);e.w64(user+0x38,access);e.w64(access+0x18,resource)
modulemgr=e.alloc(0xf0);e.w64(0x710580c3b0,modulemgr);e.w64(modulemgr+0xe8,M);e.w8(M+0x140,0);e.w64(0x710582a710,manager)
fakevt=e.alloc(0x60);e.w64(resource+0x30,fakevt)
# Native vt+0x38 getter is skipped by returning loop metadata from a resource flag-table fixture.
meta=e.alloc(0x90);metas=e.alloc(16);obj=e.alloc(0x90);e.w64(resource+0x40,meta);e.w32(meta+0x18,2);e.w64(meta+0x20,obj);e.w64(obj+0x28,0);e.w64(obj+0x80,metas);e.w32(obj+0x78,1);e.w8(metas+2,1)
admissions=[]
for uname in ['WeaponShooterNormal','HitEffect','SighterTarget','SighterTargetBig']:
 for ct in users[uname]['callTables']:
  if not ct.get('params'):continue
  e.asset=ct['params'];e.starts=[];e.mu.mem_write(extern,b'\0'*0x28)
  e.call(0x710137b000,[manager,entry]);e.asset=None
  names=[x['name'] for x in e.starts];expect=[ct['params'].get('CtrlRumbleName','')] if ct['params'].get('CtrlRumbleName','') else []
  assert names==expect,(uname,ct['key'],names,expect)
  admissions.append({'user':uname,'key':ct['key'],'starts':e.starts});counts['elink_asset_admission']+=1
out={'counts':dict(counts),'mismatches':0,'null_reads':0,'examples':examples,'elink_admissions':admissions,'SDK_boundaries':dict(e.sdklog),'allocation_boundaries':{hex(k):v for k,v in e.stublog.items()},'captured_boundaries':dict(e.captured),'scope':'whole original finish/isLoop and 9 Linear/Hermit instance curves; original Module sum with projection captured; original ELink admission with original-data parameter getters supplied and rumble start captured; no hardware or full scene execution'}
dest=ROOT/'analysis/camera_100_r10/shake';dest.mkdir(parents=True,exist_ok=True);(dest/'native_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'counts':dict(counts),'mismatches':0,'null_reads':0},ensure_ascii=False))
