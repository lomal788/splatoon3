"""Original ASB header event getter and bone-mask application; explicit binding API fixture."""
import sys,struct,json,hashlib,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import STUB
from spl_data import load,sarc
R=Path(__file__).resolve().parents[2]
e=GUC();rng=random.Random(0x39ae544);log=[]
mask=e.alloc(0x40);vt=e.alloc(0x40);e.wq(mask,vt)
for off in (8,16,48):e.wq(vt+off,STUB+0x800+off)
def hook(mu,a,size,user):
 if a==STUB+0x808:log.append(('reset',))
 elif a==STUB+0x810:
  nm=e._cstr(e.rq(mu.reg_read(UC_ARM64_REG_X1))).decode(); log.append((nm,mu.reg_read(UC_ARM64_REG_X2)&0xffffffff,mu.reg_read(UC_ARM64_REG_X3)&1))
 elif a==STUB+0x830:log.append(('finish',))
e.mu.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x808,end=STUB+0x830)
obj=e.alloc(0x40);wrapper=e.alloc(0x20);res=e.alloc(0x80);hdr=e.alloc(0x100);table=e.alloc(0x1000);sp=e.alloc(0x1000)
e.wq(obj+0x18,mask);e.wq(obj+0x20,wrapper);e.wq(wrapper+0x10,res);e.wq(res+8,hdr);e.wq(res+0x30,table);e.u32(hdr+0x24,sp-hdr)
counts=0
for k in range(1024):
 g=k%6; n=(k//6)%8; pos=0;expect=[]
 for j in range(6):
  m=n if j==g else (j+k)%8;structb=bytearray(12+8*m);struct.pack_into('<h',structb,0,m)
  for t in range(m):
   nm=f'Bone_{j}_{t}';v=(k+t)%5;rec=(k//5+t)%2;no=j*128+t*12;e.mu.mem_write(sp+no,nm.encode()+b'\0');struct.pack_into('<Ihh',structb,12+8*t,sp+no-hdr-struct.unpack('<I',e.mu.mem_read(hdr+0x24,4))[0],v,rec)
   if j==g:expect.append((nm,v,rec))
  e.mu.mem_write(table+pos,bytes(structb));pos+=len(structb)
 p3=k%2;p4=(k//2)%2;flag=(k//4)%2;e.mu.mem_write(obj+0x33,bytes([flag]));log.clear();e.call(0x71039ae544,obj,g,p3,p4)
 exp=[('reset',)]+expect+([('finish',)] if not flag and not p4 else [])
 assert log==exp,(k,log,exp)
 got=bytes(e.mu.mem_read(obj+0x30,5));assert got[0]==p4 and got[1]==p3 and got[4]==(flag and not p4),(k,got)
 counts+=1
pack=sarc(load(R/'extracted/romfs/Pack/Actor/SplPlayer.pack.zs'));data=[]
for name in ['AS/SplPlayer.root.asb','AS/SplPlayerSquid.root.asb']:
 b=pack[name];h=struct.unpack_from('<26I',b);a=e.alloc(len(b));e.mu.mem_write(a,b);e.wq(res+8,a)
 assert e.call(0x71039afdfc,wrapper)==h[5]
 o=h[13];rows=[]
 for j in range(h[6]):
  n=struct.unpack_from('<h',b,o)[0];es=[]
  for t in range(n):
   no,v,rec=struct.unpack_from('<Ihh',b,o+12+8*t);nm=b[h[9]+no:b.index(b'\0',h[9]+no)].decode();es.append([nm,v,rec])
  e.wq(res+0x30,a+h[13]);log.clear();e.call(0x71039ae544,obj,j,0,1)
  assert log==[('reset',)]+[tuple(x) for x in es],(name,j,log,es)
  rows.append({'offset':hex(o),'entries':es});o+=12+8*n
 data.append({'file':name,'sha256':hashlib.sha256(b).hexdigest(),'header14':h[5],'header18':h[6],'bone_mask_groups':rows})
result={'date':'2026-10-03','original_event_count_getter':2,'original_mask_cases':counts+2,'mismatch':0,'data':data,'stubs':['binding mask API vt8(reset),vt10(add bone name/value/descendants),vt30(finalize) fixture callbacks'],'limits':['39AE15C allocation/actual SDK bone binder not emulated','3DE0F6C upper resource/BAEV loading only disassembly','negative string offsets/global registry not tested'],'unhandled_plt':e.plt_stubbed}
assert not e.plt_stubbed
(R/'analysis/completion/r9/graphics_as_header_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
