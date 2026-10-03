"""New r9 whole original property constructor/native-library registration.
Real PhiveConfig rows are supplied in their newly decoded native parser layout.
Root/worldwrapper are fixtures, native Havok World/property library is original.
No original MotionProperties arithmetic/register callback is stubbed.
"""
import json,struct
from pathlib import Path
from r8_physics_native_uc import init_native,make_world
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP,UC_ARM64_REG_X0,UC_ARM64_REG_X19,UC_ARM64_REG_X22,UC_ARM64_REG_X24,UC_ARM64_REG_X27,UC_ARM64_REG_PC
u,errors=init_native();W,D,A,e=make_world(u,mode=1);errors+=e
# Original gamebootstrap 3c4579c grows the MotionProperties library after
# nativeWorld construction: capacity = body-manager +48 count +16.
get_body_manager=u.rq(u.rq(W)+0xa8)
errors.append(['body-manager getter',u.call(get_body_manager,W)])
BM=u.mu.reg_read(UC_ARM64_REG_X0);grow_capacity=u.r32(BM+0x48)+16
errors.append(['game-bootstrap property-library grow',u.call(0x7100a67414,u.rq(W+0x8b0),grow_capacity)])
R=u.alloc(0x500);E=u.alloc(0x500);WB=u.alloc(0x300);CF=u.alloc(0x500);MC=u.alloc(0x500)
u.wq(0x710599dfa8,R);u.wq(R+0x18,CF);u.wq(R+0xe8,E);u.wq(R+0xc8,MC);u.wq(E+0xb8,WB);u.wq(WB+0xc0,W);u.wf(E+0x220,9.8)
data=json.loads(Path('analysis/player/PhiveConfig.json').read_text(encoding='utf-8-sig'))['MotionPropertiesCollection']
P=u.alloc(32*len(data));u.w32(CF+0x20,len(data));u.wq(CF+0x28,P)
fields=('GravityScale','TimeScale','LinearDamping','MaxLinearSpeed','AngularDamping','MaxAngularSpeed')
for i,row in enumerate(data):
 for off,key in zip((8,12,16,20,24,28),fields):u.wf(P+32*i+off,row[key])
trace=[];native_bad=[]
def hook(mu,pc,size,arg):
 s=mu.reg_read(UC_ARM64_REG_SP)
 trace.append({'pc':hex(pc),'native_id':mu.reg_read(UC_ARM64_REG_X0)&65535,'cinfo':bytes(mu.mem_read(s+0x70,0x70)).hex()})
h=u.mu.hook_add(UC_HOOK_CODE,hook,begin=0x7103c52af4,end=0x7103c52af4)
rows=[];bad=[];meta_bad=[]
for i in range(16):
 O=u.alloc(0x98);IX=u.alloc(4);u.w32(IX,i)
 error=u.call(0x7103ade180,O,IX,MC,0,count=2000000);errors.append(['ctor'+str(i),error])
 actual=bytes(u.mu.mem_read(O+8,48));vals=list(struct.unpack('<12f',actual))
 if i<13:
  d=data[i];v=[d['LinearDamping'],d['AngularDamping'],d['MaxLinearSpeed'],d['MaxAngularSpeed'],d['GravityScale'],d['TimeScale']];expected=v+v
 else:
  v=[10000.,10000.,20000.,10000.,0.,1.] if i==14 else [0.,0.,20000.,10000.,0.,1.];expected=v+v
 ref=struct.pack('<12f',*expected)
 if actual!=ref:bad.append({'index':i,'actual':vals,'expected':expected})
 BW=u.rq(O+0x40)
 nid=struct.unpack('<H',u.mu.mem_read(BW+8,2))[0]
 if nid!=65535:
  native_bytes=bytes(u.mu.mem_read(u.rq(u.rq(W+0x8b0)+0x40)+nid*0x70,32))
  native_values=struct.unpack('<6f',native_bytes[8:32])
  expected_native=[v[4],v[5],v[2],v[3],v[0],v[1]]
  if native_bytes[8:32]!=struct.pack('<6f',*expected_native):native_bad.append({'index':i,'values':native_values,'expected':expected_native})
 else:
  native_bytes=b'';native_bad.append({'index':i,'error':'native library full'})
 row={'index':i,'native_bytes':native_bytes.hex(),'name':data[i]['ComponentName'] if i<13 else 'special_'+str(i),'values':vals,'fields_hex':actual.hex(),'backend':hex(BW),'backend_native_id':struct.unpack('<H',u.mu.mem_read(BW+8,2))[0],'backend_owner':hex(u.rq(BW+0x10))}
 if u.r32(O+0x38)!=0 or u.r32(O+0x3c)!=i or u.rq(O+0x48)!=MC or u.rq(BW+0x10)!=O:meta_bad.append(row)
 rows.append(row)
# New original binder block; the already-read whole Character factory supplies
# kind=1. This block itself is executed without substituting its table/loads.
u.wq(E+0xc8,MC);PL=u.alloc(16*8);u.w32(MC+0x170,16);u.wq(MC+0x178,PL)
for i,row in enumerate(rows):u.wq(PL+8*i,int(row['backend_owner'],16))
DESC=u.alloc(0xd0);binder=[];binder_bad=[]
def stop_binder(mu,pc,size,arg):
 from r6_player_uc import RET_MAGIC
 mu.reg_write(UC_ARM64_REG_PC,RET_MAGIC)
stop=u.mu.hook_add(UC_HOOK_CODE,stop_binder,begin=0x7103c4ebd8,end=0x7103c4ebd8)
for kind in (0,1,2,3):
 for wi in (0,1,2,0xffffffff):
  for ix in list(range(16))+[16,17,31,0xffffffff]:
   u.w32(DESC+4,wi);u.w32(DESC+0x84,ix)
   u.mu.reg_write(UC_ARM64_REG_X22,DESC);u.mu.reg_write(UC_ARM64_REG_X24,kind);u.mu.reg_write(UC_ARM64_REG_X27,0x710599dfa8)
   err=u.call(0x7103c4eb7c,count=1000)
   sp=u.mu.reg_read(UC_ARM64_REG_SP);actual=struct.unpack('<H',u.mu.mem_read(sp+0xe8,2))[0]
   selected=13 if kind==1 else (ix if ix<16 else 0);expected=rows[selected]['backend_native_id']
   rr={'kind':kind,'world':wi,'declared_index':ix,'selected_index':selected,'native_id':actual,'expected':expected,'error':err}
   binder.append(rr)
   if err or actual!=expected:binder_bad.append(rr)
u.mu.hook_del(stop)
r={'scope':__doc__,'binder_cases':len(binder),'binder_mismatch':binder_bad,'binder':binder,'rows':rows,'trace':trace,'cases':16,'f32_fields':192,'grow_capacity':grow_capacity,'body_manager':hex(BM),'native_mismatch':native_bad,'mismatch':bad,'metadata_mismatch':meta_bad,'errors':errors,'null':{str(k):v for k,v in u.null_calls.items()},'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed,'os':u.os_calls,'native_library':hex(u.rq(W+0x8b0))}
Path('analysis/completion/r9/physics_motion_property_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'cases':16,'fields':192,'mismatch':len(bad),'native_mismatch':len(native_bad),'metadata_mismatch':len(meta_bad),'errors':[e for e in errors if e[1]],'null':r['null'],'auto':r['auto'],'faults':r['faults'],'binder_cases':len(binder),'binder_mismatch':len(binder_bad),'special13':rows[13]},ensure_ascii=False))
