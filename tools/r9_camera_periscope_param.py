"""Original Periscope camera param constructor + reflection visitor names/offsets/defaults."""
from pathlib import Path
import json,struct
from network_uc import UC,BASE,END,STUB
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
E=UC();mu=E.mu;P=E.alloc(0xf8,fill=b'\xa5');V=E.alloc(0x20);VT=E.alloc(0x10);records=[];bound={};fault=[]
def w(a,f,*v):mu.mem_write(a,struct.pack('<'+f,*v))
def r(a,f):return struct.unpack('<'+f,mu.mem_read(a,struct.calcsize('<'+f)))
def cs(a):return bytes(mu.mem_read(a,100)).split(b'\0')[0].decode()
def curve(a):
 typ,maxx,n,ptr=r(a+8,'IfI4xQ');return dict(type=typ,MaxX=maxx,count=n,data=list(r(ptr,f'{n}f')))
w(V,'Q',VT);w(VT,'Q',STUB+0x200)
def ret(x=0):mu.reg_write(UC_ARM64_REG_X0,x);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def hook(mu,pc,n,u):
 if pc==BASE+0x083d2f0:bound['malloc']=bound.get('malloc',0)+1;assert mu.reg_read(UC_ARM64_REG_X0)==0xf8;ret(P)
 elif pc==BASE+0x3e99ef0:bound['guard']=bound.get('guard',0)+1;ret(1)
 elif pc==BASE+0x3e99f00:mu.mem_write(mu.reg_read(UC_ARM64_REG_X0),b'\1');ret()
 elif pc==STUB+0x200:
  z=mu.reg_read(UC_ARM64_REG_X1);name,token,flag,idx,owner,wrap,default=r(z,'QQQI4xQQQ');cp=r(wrap+8,'Q')[0];records.append(dict(name=cs(name),index=idx,flag_offset=hex(flag-P),curve_offset=hex(cp-P),owner_same=owner==P,default=curve(default),initial=curve(cp)));ret(0)
def inv(mu,a,ad,sz,val,u):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),address=hex(ad)));return False
mu.hook_add(UC_HOOK_CODE,hook);mu.hook_add(UC_HOOK_MEM_INVALID,inv);w(BASE+0x59975c0,'Q',0);assert E.call(BASE+0x2355fc4,0)==P;assert mu.reg_read(UC_ARM64_REG_PC)==END
assert E.call(BASE+0x235610c,P,V)==0;assert mu.reg_read(UC_ARM64_REG_PC)==END
expected=[('YawAngleVelRateStick','0xd0'),('YawAngleVelRateGyro','0xb0'),('PitchAngleVelRateStick','0x70'),('PitchAngleVelRateGyro','0x50'),('PlayerFollowRate','0x90'),('CameraAttInterpolateCurve','0x30')];assert [(z['name'],z['curve_offset']) for z in records]==expected;assert all(z['owner_same'] for z in records);assert all(z['default']==z['initial'] for z in records)
p=json.loads(Path('extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json').read_text(encoding='utf8'))['GameParameters']['spl__PlayerCameraPeriscopeParam'];out=dict(constructor=hex(BASE+0x2355fc4),visitor=hex(BASE+0x235610c),records=records,actual_gyml_overrides=p,boundaries=bound,faults=fault,null_calls=0,auto_pages=0,mismatches=0,scope='malloc and C++ guards stubbed, all original initialization and 6 metadata descriptors execute; actual resource typed loader not executed')
Path('analysis/completion/r9/camera_periscope_param.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))