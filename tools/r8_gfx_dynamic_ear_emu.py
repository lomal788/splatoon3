"""Original dynamic UBO CPU writer/array upload and HideEar bone consumer.
Synthetic local-matrix getter and GPU mapping getter/sinks only; mutex/SDK memory services.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import UC,STUB,BASE
ROOT=Path(__file__).resolve().parents[2];F=np.float32
fb=lambda x:F(struct.unpack('<f',struct.pack('<I',x))[0])
fma=lambda a,b,c:F(float(a)*float(b)+float(c))
def ptr(e,a,v):e.mu.mem_write(a,struct.pack('<Q',v))
def vec(e,a,v):e.mu.mem_write(a,struct.pack('<%df'%len(v),*v))
rg=random.Random(1045218);out={}
e=GUC();a=e.alloc(0x1100);h=e.alloc(0x1500);dirty=e.alloc(0x400);gpu=e.alloc(0x3000);ubo=e.alloc(0x80);hdr=e.alloc(0x100);tbl=e.alloc(0x1000);vt=e.alloc(0x100)
ptr(e,ubo,vt);ptr(e,vt+0x18,STUB+0xe30);ptr(e,ubo+0x10,hdr);ptr(e,hdr,tbl);ptr(e,ubo+0x18,gpu);e.u32(dirty+0x2dc,16)
def service(mu,pc,sz,_):
 if pc in (0x7103585094,STUB+0xe30):mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,service);e.call(BASE+0x104601c,h)
# Original member declarations populate type/stride table.
e.mu.mem_write(hdr+8,struct.pack('<HH',15,0))
memberoffs=[0x3a0,0xa18,0xc30,0xe48,0xfe8,0x1188,0x1238,0x1280,0x12c8,0x1340,0x1380,0x13c0,0x1408,0x1448,0x14b0]
for mo in memberoffs:e.call(e.rq(e.rq(h+mo)+0x10),h+mo,ubo);ptr(e,h+mo+0x30,dirty)
fields=[(0x2b0,0x3a0,400,1,0),(0x8f0,0xa18,30,4,0x1900),(0xad0,0xc30,30,4,0x1ae0),(0xcb0,0xe48,30,3,0x1cc0),(0xe18,0xfe8,30,3,0x1ea0),(0xf80,0x1188,30,1,0x2080)]
for case in range(48):
 e.mu.mem_write(a,b'\0'*0x1100);e.call(BASE+0x10450e8,a)
 assert bytes(e.mu.mem_read(a+0x2b0,0x640))==b'\xff'*0x640
 assert bytes(e.mu.mem_read(a+0x8f0,0x1e0))==struct.pack('<4f',1,1,1,1)*30
 assert bytes(e.mu.mem_read(a+0xad0,0x528))==b'\0'*0x528
 for src,mo,n,c,off in fields:e.mu.mem_write(a+src,struct.pack('<%dI'%(n*c),*[rg.getrandbits(32) for _ in range(n*c)]))
 cell=[F(rg.uniform(.1,40)) for _ in range(3)];origin=[F(rg.uniform(-1000,1000)) for _ in range(3)];vec(e,a+0xff8,cell);vec(e,a+0x1010,origin)
 e.call(BASE+0x1045218,a,h);e.mu.mem_write(gpu,b'\xa5'*0x3000)
 for src,mo,n,c,off in fields:
  assert bytes(e.mu.mem_read(h+mo+0x38,n*c*4))==bytes(e.mu.mem_read(a+src,n*c*4))
  e.call(e.rq(e.rq(h+mo)+0x18),h+mo,ubo)
  raw=bytes(e.mu.mem_read(a+src,n*c*4))
  expected=b''.join(raw[k*c*4:(k+1)*c*4]+b'\xa5'*(16-c*4) for k in range(n))
  assert bytes(e.mu.mem_read(gpu+off,n*16))==expected,(case,hex(mo))
 assert bytes(e.mu.mem_read(h+0x1270,12))==struct.pack('<3f',*origin)
 assert bytes(e.mu.mem_read(h+0x12b8,12))==struct.pack('<3f',*[F(1/x) for x in cell])
 e.call(BASE+0x1047d8c,h+0x1238,ubo);e.call(BASE+0x1047d8c,h+0x1280,ubo)
 assert bytes(e.mu.mem_read(gpu+0x2260,12))==struct.pack('<3f',*origin)
 assert bytes(e.mu.mem_read(gpu+0x2270,12))==struct.pack('<3f',*[F(1/x) for x in cell])
out['dynamic']={'cases':48,'reset_writer_and_8_upload_members':384,'layout_members':15,'byte_match':True,'plt_stubs':sorted(set(e.plt_stubbed)),'services':['mutex init no-op','GPU mapped-buffer getter no-op','SDK memcpy/memset exact byte copy']}
# Static initializer executes with network/error SDK calls stubbed only.
e.call(BASE+0x144f2a0);matrix=list(struct.unpack('<12I',e.mu.mem_read(BASE+0x58388e0,48)));out['ear_matrix_bits']=[hex(x) for x in matrix]
mu=e.mu;obj=e.alloc(0x300);part=e.alloc(0x400);desc=e.alloc(0x20);meta=e.alloc(0x40);comp=e.alloc(0x80);arr=e.alloc(0x20);models=[e.alloc(0x20) for _ in range(2)];wrappers=[e.alloc(8) for _ in range(2)];mvt=e.alloc(0x80)
ptr(e,obj+0x28,comp);ptr(e,comp+0x40,arr);ptr(e,obj+0x210,desc);ptr(e,desc,meta);e.u32(meta+0x24,4);ptr(e,desc+8,part)
for k in range(2):ptr(e,arr+k*8,wrappers[k]);ptr(e,wrappers[k],models[k]);ptr(e,models[k],mvt)
ptr(e,mvt+0x68,STUB+0xe40);ptr(e,mvt+0x50,STUB+0xe50);e.mu.mem_write(obj+0xcc,struct.pack('<4h',0,17,1,29))
poses=[];written=[]
def bone(mu,pc,sz,_):
 if pc==STUB+0xe40:
  i=models.index(mu.reg_read(UC_ARM64_REG_X0));vec(e,mu.reg_read(UC_ARM64_REG_X1),poses[i]);vec(e,mu.reg_read(UC_ARM64_REG_X2),[1,1,1]);assert mu.reg_read(UC_ARM64_REG_X3)==(17,29)[i];mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif pc==STUB+0xe50:
  i=models.index(mu.reg_read(UC_ARM64_REG_X0));assert mu.reg_read(UC_ARM64_REG_X3)==(17,29)[i];assert mu.reg_read(UC_ARM64_REG_X2)==BASE+0x4a999f8;written.append((i,bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X1),48))));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,bone)
M=[[fb(x) for x in matrix[r*4:(r+1)*4]] for r in range(3)]
for case in range(2048):
 flags=(case&1,(case>>1)&1);mu.mem_write(part+0x3b0,bytes(flags));poses[:]=[[F(rg.uniform(-3,3)) for _ in range(12)] for k in range(2)];written.clear();e.call(BASE+0x1454330,obj)
 assert [i for i,b in written]==[k for k in range(2) if flags[k]]
 for i,b in written:
  v=poses[i];ref=[]
  for row in range(3):
   for col in range(4):
    x=F(M[0][col]*v[row*4]);x=fma(M[1][col],v[row*4+1],x);x=fma(M[2][col],v[row*4+2],x);ref.append(F(x+(v[row*4+3] if col==3 else F(0))))
  assert b==struct.pack('<12f',*ref),(case,i)
out['ear']={'cases':2048,'bone_writes':len(range(2048)),'matrix_bit_match':True,'algorithm_stubs':[],'boundary_getters':['synthetic local bone matrices, indices17/29','setter sink records original matrix'],'initializer_sdk_stubs':sorted(set(e.plt_stubbed)-{'_ZN2nn2os9LockMutexEPNS0_9MutexTypeE','_ZN2nn2os11UnlockMutexEPNS0_9MutexTypeE'})}
(ROOT/'analysis/completion/r8/dynamic_ear_emu.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
