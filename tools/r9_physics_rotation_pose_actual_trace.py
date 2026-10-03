"""r9 whole game rotation TOI callbacks, exact independent original pose references. Explicit capsule/Yrotation and NULL filters remain fixture scope."""
import json,struct,math
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r9_physics_toi_fixture import make_engine_toi_fixture
# Trusted local reference definitions only, no standalone4097-case runner.
exec(Path('web/tools/r9_physics_rotation_pose_emu.py').read_text(encoding='utf-8-sig').split('u=PhysicsUC();A=')[0],globals())
F=make_engine_toi_fixture();u=F['u'];GB=F['GB'];GBB=F['GBB'];Args=F['Args'];Ang=F['Ang'];Stage=F['Stage'];CL=F['CL'];Points=F['Points'];Entries=F['Entries']
u.wq(GBB,0x7105756338);u.wq(GB+0x88,4)
active={'quat':[],'matrix':[]};results=[];bad=[]
def hook(mu,pc,size,data):
 if pc in (0x71008a8764,0x71008a5ed0):
  O=mu.reg_read(UC_ARM64_REG_X0);A=mu.reg_read(UC_ARM64_REG_X1);a=list(struct.unpack('<4f',bytes(mu.mem_read(A,16))));lr=mu.reg_read(UC_ARM64_REG_X30)
  if pc==0x71008a8764:
   b=list(struct.unpack('<4f',bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X2),16))));t=list(struct.unpack('<4f',bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X3),16))));want=pack(quat_ref(list(map(f,a)),list(map(f,b)),f(t[0])));kind='quat';rec=dict(kind=kind,lr=hex(lr),a=a,b=b,t=t)
   if bits(t[0])!=bits(t[1]):bad.append(dict(scope='nonduplicated_time',record=rec))
  else:want=pack(matrix_ref(list(map(f,a))));kind='matrix';rec=dict(kind=kind,lr=hex(lr),a=a)
  active[kind].append((O,lr,want,rec))
  # Dynamic LR traced from actual caller, duplicate hooks harmless: only live frame consumes.
  if lr not in hooked:
   hooked.add(lr);u.mu.hook_add(UC_HOOK_CODE,hook,begin=lr,end=lr)
  return
 for kind in ('quat','matrix'):
  if active[kind] and active[kind][-1][1]==pc:
   O,lr,want,rec=active[kind].pop();actual=bytes(mu.mem_read(O,len(want)));rec.update(actual=actual.hex(),reference=want.hex(),pass_bits=actual==want);results.append(rec)
   if actual!=want:bad.append(rec)
hooked=set()
for pc in (0x71008a8764,0x71008a5ed0):u.mu.hook_add(UC_HOOK_CODE,hook,begin=pc,end=pc)
cases=[]
for theta in (0.,.1,1.,math.pi/2):
 c=math.cos(theta);s=math.sin(theta);u.mu.mem_write(GB+0xd8,struct.pack('<12f',c,0,s,0,0,1,0,0,-s,0,c,0));u.mu.mem_write(Ang,struct.pack('<3f',0,theta,0))
 for fn in (0x7103c54140,0x7103c54de4):
  u.w32(Stage+0x24,0);u.w32(CL+8,0);u.mu.mem_write(Points,bytes(0x400));u.mu.mem_write(Entries,bytes(0x80));n=len(results);e=u.call(fn,0,Args,count=20000000);cases.append(dict(theta=theta,fn=hex(fn),error=e,records=results[n:],fraction=u.rf(Points+0x60),list_count=u.r32(CL+8)))
  if e:bad.append(dict(scope='whole_return',error=e,theta=theta,fn=hex(fn)))
r=dict(scope=__doc__,cases=len(cases),callback_counts={k:sum(x['kind']==k for x in results) for k in active},fields=sum(4 if x['kind']=='quat' else 12 for x in results),bad_count=len(bad),bad=bad,results=cases,init_errors=F['errors'],null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_rotation_pose_actual_trace.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scope','bad','results')});print('bad',bad[:2])

