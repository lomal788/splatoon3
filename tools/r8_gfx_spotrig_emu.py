"""Original SpotLightRig static/model-color update, transform, writer, dynamic-provider handoff."""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import BASE,STUB
ROOT=Path(__file__).resolve().parents[2];F=np.float32
rg=random.Random(0x37a1aa8);e=GUC();p=e.alloc(0x600);o=e.alloc(0x400);m=e.alloc(0x100);vt=e.alloc(0x200);arr=e.alloc(8);pool=e.alloc(0x80);frame=e.alloc(0x500);acc=e.alloc(0x1100);colsrc=e.alloc(16)
e.wq(p,BASE+0x572ee30);e.wq(o+0x358,p);e.wq(m,vt);e.wq(vt+0x98,STUB+0xe40);e.wq(vt+0x88,STUB+0xe50);e.wq(arr,o);e.u32(pool+0x18,1);e.wq(pool+0x20,arr);e.wq(frame+0x460,pool);e.mu.mem_write(o+0x360,struct.pack('<h',17));e.u32(m+8,0x87654321)
M=[];handoff=[]
def hook(mu,pc,sz,u):
 if pc==STUB+0xe40:mu.reg_write(UC_ARM64_REG_X0,1);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif pc==STUB+0xe50:
  assert mu.reg_read(UC_ARM64_REG_X2)==17;mu.mem_write(mu.reg_read(UC_ARM64_REG_X1),struct.pack('<12f',*M));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif pc==BASE+0x104560c:
  handoff.append((bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X1),12)),bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X2),12)),bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X3),16)),[mu.reg_read(r)for r in (UC_ARM64_REG_S0,UC_ARM64_REG_S1,UC_ARM64_REG_S2,UC_ARM64_REG_S3)],mu.reg_read(UC_ARM64_REG_X4)))
  mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
def vec(a,v):e.mu.mem_write(a,struct.pack('<%df'%len(v),*v))
def calc(row,v):return F(F(F(row[0]*v[0])+F(row[1]*v[1]))+F(row[2]*v[2]))
for case in range(2048):
 M[:]=[F(rg.uniform(-3,3))for _ in range(12)];off=[F(rg.uniform(-3,3))for _ in range(3)];dire=[F(rg.uniform(-2,2))for _ in range(3)];col=[F(rg.uniform(0,2))for _ in range(4)];spe=[F(rg.uniform(0,2))for _ in range(4)];src=[F(rg.uniform(0,2))for _ in range(3)];mode=(case>>4)&1;anm=2 if mode else 0
 world=case&1;follow=(case>>1)&1;spec=(case>>2)&1;ind=(case>>3)&1;radius=F(rg.uniform(.01,30));ang=F(rg.uniform(.001,4));damp=F(rg.uniform(.1,4));adamp=F(rg.uniform(.1,4));inten=F(rg.uniform(0,40))
 e.mu.mem_write(p+0x58,b'\1');e.mu.mem_write(o+0x58,b'\1');e.u32(p+0x290,anm);e.mu.mem_write(p+0x490,bytes([world]));e.mu.mem_write(p+0x4e8,bytes([follow]));e.mu.mem_write(p+0x2d0,bytes([spec]));e.mu.mem_write(p+0x2f0,bytes([ind]));vec(p+0x468,off);vec(p+0x4c0,dire);vec(p+0x310,col);vec(p+0x360,spe);vec(colsrc,src);e.wq(p+0x498,colsrc if case&32 else 0)
 for ofs,v in ((0x388,radius),(0x508,ang),(0x448,damp),(0x528,adamp),(0x2b0,inten)):e.f32(p+ofs,v)
 e.call(BASE+0x37a1aa8,o,m,0xff0000ff,fargs=(1.,))
 position=[F(off[i]+M[i*4+3])if world else F(M[i*4+3]+calc(M[i*4:i*4+3],off))for i in range(3)]
 direction=[calc(M[i*4:i*4+3],dire)for i in range(3)]if follow else dire
 color=([F(col[i]*src[i])for i in range(3)]+[col[3]])if anm==2 and case&32 else ([F(0),F(0),F(0),F(1)]if anm==2 else col)
 sp=spe if spec and ind else(color if spec else[F(0),F(0),F(0),F(1)])
 for ofs,v in ((0x128,color),(0x150,sp),(0x1e0,position),(0x1b8,direction)):assert bytes(e.mu.mem_read(o+ofs,len(v)*4))==struct.pack('<%df'%len(v),*v),(case,hex(ofs))
 for ofs,v in ((0x198,radius),(0x208,F(ang*F(.5))),(0x178,inten),(0x228,damp),(0x248,F(adamp*F(radius*F(F(1)/radius))))):assert bytes(e.mu.mem_read(o+ofs,4))==struct.pack('<f',v),(case,hex(ofs),e.rf32(o+ofs),v)
 assert e.ru32(o+0x36c)==0x87000021
 handoff.clear();e.call(BASE+0x1048d98,0,acc,frame)
 assert len(handoff)==1
 pos,di,co,sc,kind=handoff[0];assert pos==struct.pack('<3f',*position)and di==struct.pack('<3f',*direction)and co==struct.pack('<4f',*[F(x*inten)for x in color])and kind==1
 assert sc==[struct.unpack('<I',e.mu.mem_read(o+j,4))[0]for j in(0x198,0x208,0x228,0x248)]
out={'cases':2048,'original_reader':'0x71037a1aa8','original_writer':'0x71037a038c','original_provider':'0x7101048d98','AnmType':[0,2],'byte_match':True,'algorithm_stubs':[],'boundary':['synthetic bone matrix/visibility getter','104560c output sink records original insertion input'],'external_services':sorted(set(e.plt_stubbed)),'limits':['AnmType1 modulation read, not executed','provider→grid/GPU tested independently in r8 prior tools','live scene/bone resource loading not executed']}
(ROOT/'analysis/completion/r8/spotrig_emu.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))

